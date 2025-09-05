from typing import List, Dict, Any, Optional
from uuid import UUID
from app.domain.models.core import Session, Message, Tool, ToolExecution
from app.infrastructure.database import mongodb_db, redis_client
from datetime import datetime

class SessionService:
    async def create_session(self, user_id: str, title: Optional[str] = None) -> Session:
        session = Session(user_id=user_id, title=title)
        await mongodb_db.sessions.insert_one(session.dict())
        return session
    
    async def get_session(self, session_id: UUID) -> Optional[Session]:
        if session_data := await mongodb_db.sessions.find_one({"id": session_id}):
            return Session(**session_data)
        return None
    
    async def list_user_sessions(self, user_id: str) -> List[Session]:
        cursor = mongodb_db.sessions.find({"user_id": user_id})
        sessions = []
        async for session_data in cursor:
            sessions.append(Session(**session_data))
        return sessions
    
    async def update_session(self, session_id: UUID, updates: Dict[str, Any]) -> Optional[Session]:
        updates["updated_at"] = datetime.utcnow()
        result = await mongodb_db.sessions.find_one_and_update(
            {"id": session_id},
            {"$set": updates},
            return_document=True
        )
        if result:
            return Session(**result)
        return None
    
    async def delete_session(self, session_id: UUID) -> bool:
        result = await mongodb_db.sessions.delete_one({"id": session_id})
        if result.deleted_count:
            await mongodb_db.messages.delete_many({"session_id": session_id})
            return True
        return False
