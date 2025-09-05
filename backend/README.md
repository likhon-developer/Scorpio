# Scorpio Backend - AI Agent System API

A comprehensive backend API for the Scorpio AI Agent System, built with FastAPI and following Domain-Driven Design (DDD) principles.

## 🚀 Features

- **Multi-LLM Support**: OpenAI, Anthropic Claude, Google Gemini
- **MCP Integration**: Model Context Protocol for tool orchestration
- **Real-time Streaming**: Server-Sent Events (SSE) for live chat
- **Session Management**: Persistent conversation sessions with MongoDB
- **File Operations**: Read, write, search, and manage files
- **Docker Sandbox**: Isolated environment for tool execution
- **Caching**: Redis-based caching for performance
- **Structured Logging**: Comprehensive logging with structlog

## 🏗️ Architecture

### Domain-Driven Design Structure

```
backend/
├── app/
│   ├── domain/              # Business logic layer
│   │   ├── models/          # Domain entities
│   │   ├── services/        # Domain services
│   │   └── external/        # External interfaces (MCP, etc.)
│   ├── application/         # Application orchestration layer
│   ├── interfaces/          # API and external interfaces
│   │   └── api/
│   │       └── v1/
│   │           ├── endpoints/    # API route handlers
│   │           └── routes.py     # Route configuration
│   └── infrastructure/      # Technical implementation
│       ├── database.py      # Database setup
│       ├── cache.py         # Redis setup
│       └── llm/             # LLM client implementations
├── core/                   # Shared configuration and utilities
├── main.py                 # Application entry point
└── requirements.txt        # Python dependencies
```

## 📋 Prerequisites

- Python 3.11+
- MongoDB 4.4+
- Redis 6.0+
- Docker (optional, for sandbox)

## 🛠️ Installation

### Local Development

1. **Clone and setup**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start dependencies**:
   ```bash
   # Using Docker Compose (recommended)
   docker-compose up -d mongodb redis

   # Or install locally
   # MongoDB: https://docs.mongodb.com/manual/installation/
   # Redis: https://redis.io/download
   ```

4. **Run the development server**:
   ```bash
   python run_dev.py
   ```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t scorpio-backend .
docker run -p 8000:8000 --env-file .env scorpio-backend
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `MONGODB_URL` | MongoDB connection URL | `mongodb://localhost:27017` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |

## 📚 API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

### Key Endpoints

#### Sessions
- `POST /api/v1/sessions` - Create new session
- `GET /api/v1/sessions` - List all sessions
- `GET /api/v1/sessions/{session_id}` - Get session details
- `DELETE /api/v1/sessions/{session_id}` - Delete session

#### Chat
- `POST /api/v1/chat/sse` - Stream chat with SSE
- `POST /api/v1/chat/{session_id}/message` - Send message

#### Files
- `POST /api/v1/files/read` - Read file content
- `POST /api/v1/files/write` - Write to file
- `POST /api/v1/files/search` - Search file content

#### Tools
- `GET /api/v1/tools/list` - List available tools
- `POST /api/v1/tools/execute` - Execute tool
- `GET /api/v1/tools/resources` - List MCP resources

## 🔌 MCP Integration

The backend supports Model Context Protocol (MCP) for tool integration:

```python
# Configure MCP client
from app.domain.external.mcp_client import HTTPMCPClient

mcp_client = HTTPMCPClient(
    base_url="http://localhost:3001",
    api_key="your-api-key"
)
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## 📊 Monitoring

### Health Checks
- **Endpoint**: `GET /health`
- **Returns**: Service health status

### Logging
- Structured logging with `structlog`
- Configurable log levels
- JSON format for production

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Configure production database URLs
- [ ] Set secure `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Configure proper CORS origins
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation

### Docker Production

```bash
# Build production image
docker build -t scorpio-backend:latest .

# Run with production compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🛠️ Development

### Code Style
```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/
```

### Database Migrations
```bash
# MongoDB doesn't require migrations
# Indexes are created automatically on startup
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**MongoDB Connection Failed**
```bash
# Check if MongoDB is running
docker ps | grep mongodb

# Check connection
python -c "from motor.motor_asyncio import AsyncIOMotorClient; client = AsyncIOMotorClient('mongodb://localhost:27017'); print('Connected')"
```

**Redis Connection Failed**
```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
redis-cli ping
```

**Port Already in Use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: This README and API docs
