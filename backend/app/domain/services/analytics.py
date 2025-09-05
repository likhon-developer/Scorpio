from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from app.domain.models.organization import AnalyticsMetric, Alert, AuditLog
from app.infrastructure.database import mongodb_db, redis_client
import asyncio
import json

class AnalyticsService:
    async def record_metric(self, metric: AnalyticsMetric):
        """Record a new analytics metric"""
        await mongodb_db.metrics.insert_one(metric.dict())
        
        # Store in Redis for real-time access
        redis_key = f"metric:{metric.name}:latest"
        await redis_client.set(
            redis_key,
            json.dumps(metric.dict()),
            ex=3600  # Expire after 1 hour
        )
    
    async def get_metric_history(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        dimensions: Optional[Dict[str, str]] = None
    ) -> List[AnalyticsMetric]:
        """Get historical metrics for a specific metric name"""
        query = {
            "name": metric_name,
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }
        
        if dimensions:
            for key, value in dimensions.items():
                query[f"dimensions.{key}"] = value
        
        cursor = mongodb_db.metrics.find(query).sort("timestamp", 1)
        return [AnalyticsMetric(**metric) async for metric in cursor]
    
    async def calculate_aggregate_metrics(
        self,
        metric_name: str,
        interval: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Calculate aggregate metrics over time intervals"""
        pipeline = [
            {
                "$match": {
                    "name": metric_name,
                    "timestamp": {
                        "$gte": start_time,
                        "$lte": end_time
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d-%H",
                            "date": "$timestamp"
                        } if interval == "hourly" else {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp"
                        }
                    },
                    "avg_value": {"$avg": "$value"},
                    "max_value": {"$max": "$value"},
                    "min_value": {"$min": "$value"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        return await mongodb_db.metrics.aggregate(pipeline).to_list(None)
    
    async def generate_forecast(
        self,
        metric_name: str,
        horizon_days: int = 7
    ) -> List[Dict[str, float]]:
        """Generate simple forecasts for metrics"""
        # Get historical data for training
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)
        
        historical_data = await self.get_metric_history(
            metric_name,
            start_time,
            end_time
        )
        
        if not historical_data:
            return []
            
        # Calculate trend
        values = [m.value for m in historical_data]
        avg_change = sum(values[i] - values[i-1] for i in range(1, len(values))) / (len(values) - 1)
        
        # Generate forecast
        last_value = values[-1]
        forecast = []
        
        for day in range(horizon_days):
            forecast_value = last_value + (avg_change * (day + 1))
            forecast.append({
                "date": (end_time + timedelta(days=day+1)).date().isoformat(),
                "value": max(0, forecast_value)  # Ensure non-negative values
            })
            
        return forecast
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> Alert:
        """Create a new alert"""
        alert = Alert(**alert_data)
        await mongodb_db.alerts.insert_one(alert.dict())
        
        # Store in Redis for real-time access
        redis_key = f"alert:{alert.id}"
        await redis_client.set(
            redis_key,
            json.dumps(alert.dict()),
            ex=86400  # Expire after 24 hours
        )
        
        return alert
    
    async def resolve_alert(
        self,
        alert_id: UUID,
        resolver_id: UUID,
        resolution_notes: str
    ) -> Optional[Alert]:
        """Resolve an existing alert"""
        update = {
            "status": "resolved",
            "resolved_at": datetime.utcnow(),
            "resolved_by": resolver_id,
            "resolution_notes": resolution_notes
        }
        
        if result := await mongodb_db.alerts.find_one_and_update(
            {"id": alert_id},
            {"$set": update},
            return_document=True
        ):
            # Remove from Redis
            redis_key = f"alert:{alert_id}"
            await redis_client.delete(redis_key)
            
            return Alert(**result)
        return None
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        cursor = mongodb_db.alerts.find({"status": "new"})
        return [Alert(**alert) async for alert in cursor]
    
    async def get_audit_logs(
        self,
        start_time: datetime,
        end_time: datetime,
        actor_id: Optional[UUID] = None,
        resource_type: Optional[str] = None
    ) -> List[AuditLog]:
        """Get audit logs within a time range with optional filters"""
        query = {
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }
        
        if actor_id:
            query["actor_id"] = actor_id
        if resource_type:
            query["resource_type"] = resource_type
            
        cursor = mongodb_db.audit_logs.find(query).sort("timestamp", -1)
        return [AuditLog(**log) async for log in cursor]
