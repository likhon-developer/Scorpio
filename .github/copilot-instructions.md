# Scorpio AI Agent System - Copilot Instructions

## Project Overview
Scorpio is a multi-component Retrieval-Augmented Generation (RAG) system with a Next.js frontend, FastAPI backend, and Docker-based sandbox environment for AI agent operations.

## Key Architecture Patterns

### Frontend (Next.js)
- **Real-time Communication**: Uses Server-Sent Events (SSE) in `components/data-stream-handler.tsx`
- **Component Architecture**: 
  - Base artifacts (`components/artifact.tsx`) extend to specialized types (code, text, image, sheet)
  - Messages (`components/message.tsx`) support reasoning, actions, and suggestions
- **Data Flow**: State management through React Context and custom hooks in `hooks/` directory

### Backend (FastAPI)
- **Domain-Driven Design**: Clear separation in `backend/app/`:
  - `domain/`: Core business logic and models
  - `interfaces/`: API endpoints
  - `infrastructure/`: Technical implementations (DB, cache, LLM)
- **LLM Integration**: Multiple provider support through adapter pattern in `backend/app/infrastructure/llm/`

### Database Structure
- **PostgreSQL**: Main data store with DrizzleORM (`lib/db/`)
- **MongoDB**: Session state in backend
- **Redis**: Caching and real-time features

## Common Development Tasks

### Setting Up Development Environment
```bash
# Frontend
npm install
npm run dev

# Backend
cd backend
python -m venv .venv
pip install -r requirements.txt
python run_dev.py
```

### Testing
- Frontend: Playwright E2E tests in `tests/e2e/`
- Backend: Pytest in `backend/tests/`
- Run all tests with `npm test`

### Adding New Features
1. **New Tool/Agent Capability**:
   - Add tool definition in `backend/app/domain/tools/`
   - Implement handler in `backend/app/infrastructure/tools/`
   - Create frontend UI component in `components/`

2. **New Artifact Type**:
   - Extend base `Artifact` component
   - Add type definitions in `lib/types.ts`
   - Implement backend handler in `backend/app/domain/artifacts/`

## Project-Specific Conventions

### Code Organization
- Frontend components are function components with named exports
- Backend uses class-based services with dependency injection
- All database queries are centralized in `lib/db/queries.ts`

### Error Handling
- Frontend: Structured error types in `lib/errors.ts`
- Backend: Domain exceptions in `backend/app/domain/exceptions/`
- Always use type-safe error handling with proper error boundaries

### Authentication
- NextAuth.js implementation in `app/(auth)/`
- Protected routes use middleware checks
- Guest sessions supported through temporary tokens

## Integration Points
- **LLM Providers**: Add new providers in `backend/app/infrastructure/llm/`
- **External Tools**: Implement in `backend/app/infrastructure/tools/`
- **Authentication**: Configure providers in `app/(auth)/auth.config.ts`

## Common Gotchas
- Always use `DataStreamProvider` for real-time features
- Test tool executions in sandbox environment first
- Handle proper cleanup in `useEffect` hooks for SSE connections
