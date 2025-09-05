# Scorpio AI Agent System

<div align="center">
  <img src="https://www.pngitem.com/pimgs/m/70-709977_transparent-scorpion-clipart-scorpio-zodiac-sign-golden-hd.png" alt="Scorpio Logo" width="200" height="200"/>
</div>

Scorpio is a multi-component Retrieval-Augmented Generation (RAG) system that provides a general-purpose AI agent capable of running various tools and operations in isolated sandbox environments.

## Developer
- Telegram: [t.me/likhonsheikh](https://t.me/likhonsheikh)
- Twitter: [x.com/likhonymous](https://x.com/likhonymous)

## Key Features

- 🤖 **Intelligent AI Agent**: Powered by advanced language models with tool orchestration
- 🛠️ **Extensive Tool Support**: Terminal, Browser, File operations, Web Search, and messaging tools
- 🐳 **Isolated Sandbox Environment**: Each task runs in a dedicated Docker container
- 💬 **Real-time Communication**: Server-Sent Events (SSE) for live updates and streaming responses
- 🖥️ **Remote Desktop Access**: VNC integration for browser and desktop visualization
- 🔄 **Session Management**: Persistent conversation history with MongoDB/Redis
- 🌐 **Multilingual Support**: Chinese and English language support
- 🔐 **Authentication**: User login and session management
- 📁 **File Operations**: Upload/download capabilities with secure file handling
- 🎯 **Background Task Support**: Long-running tasks with status tracking

## Architecture Overview

### System Components

Scorpio consists of three main architectural layers:

1. **Web Frontend** (Port 5173): Vue.js/React interface for user interaction
2. **Server Backend** (Port 8000): FastAPI/Python service orchestrating agents and sessions
3. **Sandbox Environment** (Port 8080): Isolated Docker containers for tool execution

### How It Works

When a user initiates a conversation:

1. **Session Creation**: Web sends a request to create an Agent to the Server, which creates a Sandbox through Docker and returns a session ID
2. **Environment Setup**: The Sandbox is an Ubuntu Docker environment that starts Chrome browser and API services for tools like File/Shell
3. **Message Processing**: Web sends user messages to the session ID, and the Server forwards them to the PlanAct Agent for processing
4. **Tool Execution**: During processing, the PlanAct Agent calls relevant tools to complete tasks
5. **Real-time Updates**: All events generated during Agent processing are sent back to Web via Server-Sent Events (SSE)

### Tool Visualization

When users interact with tools:

- **Browser Tools**: The Sandbox's headless browser starts a VNC service through xvfb and x11vnc, converting VNC to WebSocket through websockify. The Web's NoVNC component connects to the Sandbox through the Server's WebSocket Forward, enabling browser viewing
- **Other Tools**: File operations, terminal commands, and other tools work through similar WebSocket-based real-time communication

## Environment Requirements

### Prerequisites

- **Docker**: 20.10+ with Docker Compose
- **Python**: 3.9+ (for backend services)
- **Node.js**: 20.18.0 (for frontend and sandbox Node environment)
- **MongoDB**: 4.4+ (for session persistence)
- **Redis**: 6.0+ (for caching and background tasks)
- **PostgreSQL**: with pgvector extension (for embeddings and vector search)

## Project Structure

Scorpio consists of three main components:

### Web Frontend
- **Technology**: Vue.js/React with modern UI framework
- **Port**: 5173
- **Purpose**: User interface for interacting with AI agents

### Server Backend
- **Technology**: FastAPI/Python with domain-driven architecture
- **Port**: 8000
- **Purpose**: Orchestrates agents, manages sessions, and coordinates tools

### Sandbox Environment
- **Technology**: Docker container with Ubuntu, Python, Node.js, and Chrome
- **Ports**:
  - 8080: API service
  - 5900: VNC service
  - 9222: Chrome DevTools Protocol
- **Purpose**: Isolated execution environment for tools and operations

**Note**: In Debug mode, only one sandbox instance runs globally for development efficiency.

## Quick Start

### Prerequisites

Before getting started, ensure you have the following installed:

- **Docker & Docker Compose**: 20.10+
- **Node.js**: 20.18.0+ (for frontend development)
- **Python**: 3.9+ (for backend development)
- **Git**: For cloning the repository

### Local Development Setup

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd scorpio
```

#### 2. Environment Configuration

Create a `.env.local` file in the root directory:
```bash
# Database Configuration
DATABASE_URL="postgresql://username:password@localhost:5432/scorpio"
DIRECT_URL="postgresql://username:password@localhost:5432/scorpio"

# AI Service Configuration
GEMINI_API_KEY="your-gemini-api-key"

# Authentication (Optional)
NEXTAUTH_SECRET="your-nextauth-secret"
NEXTAUTH_URL="http://localhost:3000"
```

#### 3. Database Setup

**Option A: Using Docker (Recommended)**
```bash
# Start all services including databases
docker-compose up -d

# The following services will be available:
# - MongoDB: localhost:27017
# - Redis: localhost:6379
# - PostgreSQL: localhost:5432 (if configured)
```

**Option B: Local Database Installation**
```bash
# Install PostgreSQL locally and create database
createdb scorpio

# Enable pgvector extension
psql -d scorpio -c "CREATE EXTENSION vector;"
```

#### 4. Install Dependencies

```bash
# Install frontend dependencies
pnpm install

# Install backend dependencies (if developing backend locally)
cd backend
pip install -r requirements.txt
cd ..
```

#### 5. Database Migration

```bash
# Generate and run database migrations
pnpm run db:generate
pnpm run db:migrate
```

#### 6. Start Development Server

```bash
# Start the frontend development server
pnpm run dev
```

Access the application at: http://localhost:3000

### Docker Development (Alternative)

For full Docker-based development:

```bash
# Build and start all services
docker-compose up --build

# Access services:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - Sandbox: http://localhost:8080
# - VNC: http://localhost:5900 (password: password)
```

### Production Deployment

#### Using Docker Compose
```bash
# Set production environment variables
export IMAGE_REGISTRY=your-registry-url
export IMAGE_TAG=v1.0.0

# Build and deploy
docker-compose -f docker-compose.prod.yml up -d
```

#### Manual Production Setup
```bash
# Build the application
pnpm run build

# Start production server
pnpm run start
```

### Troubleshooting

#### Common Issues

**Database Connection Issues:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Reset database (development only)
pnpm run db:push
```

**Port Conflicts:**
- Frontend: Change port in `next.config.ts`
- Backend: Modify docker-compose.yml port mappings
- Database: Update connection strings in environment variables

**Docker Issues:**
```bash
# Clean up Docker resources
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

**Environment Variables:**
- Copy `.env.example` to `.env.local`
- Ensure all required API keys are set
- Check file permissions for `.env` files

## Development Workflow

### Domain-Driven Architecture (Backend)

The backend follows a clean architecture pattern:

```
backend/app/
├── domain/          # Business logic and models
│   ├── models/      # Core domain entities
│   ├── services/    # Domain services
│   ├── external/    # External service interfaces
│   └── prompts/     # LLM prompt templates
├── application/     # Orchestration layer
├── interfaces/      # API routes and external interfaces
└── infrastructure/  # Technical implementation
```

### Tool Integration

- **Shell Sessions**: Persistent command execution with session IDs
- **File Operations**: Absolute path requirements for security
- **Browser Automation**: Playwright-based with Chrome DevTools Protocol access
- **VNC Streaming**: Binary WebSocket protocol for remote desktop viewing

## API Documentation

### Unified Response Format

All API endpoints return responses in a standardized format:

```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

### Common Error Codes

- `400`: Request parameter error
- `404`: Resource not found
- `500`: Server internal error

### Server API Endpoints (Port 8000)

#### Session Management

**Create Session**
```http
POST /api/v1/sessions
Content-Type: application/json

{
  "title": "My Development Session"
}
```

**Response:**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "session_id": "sess_123456",
    "title": "My Development Session",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

**Get Session**
```http
GET /api/v1/sessions/{session_id}
```

**List Sessions**
```http
GET /api/v1/sessions?limit=50
```

**Update Session**
```http
PUT /api/v1/sessions/{session_id}
Content-Type: application/json

{
  "title": "Updated Session Title",
  "status": "active"
}
```

**Delete Session**
```http
DELETE /api/v1/sessions/{session_id}
```

**Stop Session**
```http
POST /api/v1/sessions/{session_id}/stop
```

#### Chat Endpoints

**Stream Chat (Server-Sent Events)**
```http
POST /api/v1/chat/sse
Content-Type: application/json
X-Session-ID: sess_123456

{
  "messages": [
    {
      "role": "user",
      "content": "Help me debug this Python function"
    }
  ],
  "llm_provider": "openai"
}
```

**Send Message (Non-streaming)**
```http
POST /api/v1/chat/{session_id}/message
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "Hello, can you help me?"
    }
  ],
  "llm_provider": "openai"
}
```

#### Tool Management

**List Available Tools**
```http
GET /api/v1/tools/list
```

**Execute Tool**
```http
POST /api/v1/tools/execute
Content-Type: application/json
X-Session-ID: sess_123456

{
  "tool_name": "run_terminal_cmd",
  "parameters": {
    "command": "ls -la",
    "cwd": "/home/user"
  }
}
```

**List MCP Resources**
```http
GET /api/v1/tools/resources
```

**Read MCP Resource**
```http
GET /api/v1/tools/resources/{uri}
```

#### Real-time Events

Scorpio uses Server-Sent Events (SSE) for real-time communication. Event types include:

- `message` - Assistant responses
- `title` - Session title updates
- `plan` - Execution plan with steps
- `step` - Step status updates
- `tool` - Tool invocation details
- `error` - Error information
- `done` - Conversation completion

**SSE Event Format:**
```json
{
  "type": "message",
  "data": {
    "content": "Assistant response text",
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

## Contributing

We welcome contributions to Scorpio! Please see our development setup guide above and feel free to submit issues and pull requests.

## License

MIT
