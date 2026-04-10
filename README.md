# TED Bot - Intelligent Tender Notice Agent

**🎉 STATUS: FULLY FUNCTIONAL WITH MODERN UI ✅**

> An AI-powered agent system with a modern chat interface for searching EU tender opportunities!

An AI-powered agent system for retrieving, analyzing, and monitoring public procurement notices from the TED (Tenders Electronic Daily) platform.

## 🚀 Quick Start

### Option 1: Start Everything (Recommended)

```bash
# Install dependencies and start both backend + frontend
chmod +x start.sh
./start.sh
```

This will start:
- **Backend API** at http://localhost:8000
- **Frontend UI** at http://localhost:3000

### Option 2: Start Services Separately

**Backend:**
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend/agent-ui
pnpm install
pnpm dev
```

### Testing the API

```bash
# Test the chat endpoint
poetry run python test_api.py

# Open interactive API docs
open http://localhost:8000/docs
```

## Overview

TED Bot is an intelligent agent built with Agno framework that helps users discover and analyze public procurement opportunities from the European Union's central tender platform. The system provides conversational access to tender data, automated monitoring, and intelligent analysis capabilities.

## Key Features

- 🤖 **Modern Chat Interface**: Beautiful, responsive UI built with Next.js and Tailwind CSS
- 💬 **Conversational Interface**: Natural language queries to search and analyze tenders
- 🔍 **Semantic Search**: Vector-based search for finding relevant opportunities
- 🛠️ **Tool Visualization**: See when the agent uses search tools in real-time
- 📊 **Session Management**: Maintains conversation history across sessions
- 📝 **Document Analysis**: AI-powered summarization of tender documents
- 🔔 **Smart Notifications**: Alerts for matching tenders based on preferences
- 📈 **Insights & Reports**: Generate reports and insights from tender data

## Technology Stack

- **Frontend UI**: Next.js, TypeScript, Tailwind CSS, shadcn/ui
- **Database**: Supabase (PostgreSQL + pgvector)
- **LLM**: Ollama Cloud (hosted models)
- **Deployment**: Vercel (frontend), Railway/Render (backendodels)
- **Frontend**: Simple HTML/JavaScript chat interface
- **Deployment**: Vercel (primary)

## Project Structure

This is a monorepo containing both frontend and backend:

```
ted-bot/
├── docs/                    # Comprehensive documentation
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── agents/         # Agno agent implementations
│   │   ├── api/            # API routes (including AgentOS API)
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── core/           # Configuration
│   └── tests/
├── frontend/
│   └── agent-ui/           # Modern Next.js chat interface
└── scripts/                 # Utility scripts
```

## Documentation

Detailed documentation is available in the `/docs` directory:

- [Requirements](docs/requirements.md) - Detailed functional and non-functional requirements
- [Architecture](docs/architecture.md) - System architecture and design decisions
- [API Specification](docs/api-specification.md) - FastAPI endpoints and contracts
- [Database Schema](docs/database-schema.md) - Supabase schema and data model
- [Agent Design](docs/agent-design.md) - Agno agent architecture and workflows
- [Tech Stack](docs/tech-stack.md) - Technology choices and rationale
- [Deployment](docs/deployment.md) - Deployment guide for Vercel and Docker

## Frontend UI

The agent-ui provides a modern, production-ready chat interface for interacting with the TED Bot agent:

- **Real-time Streaming**: See agent responses as they're generated
- **Session History**: All conversations are saved with session management
- **Tool Visualization**: Watch the agent use tools like search_ted_tenders
- **Markdown Support**: Tables and formatted responses render beautifully
- **Mobile Responsive**: Works seamlessly on all device sizes

See [frontend/agent-ui/SETUP.md](frontend/agent-ui/SETUP.md) for detailed setup instructions.

### Example Queries

Try these in the chat interface:

- "Find software development contracts in Germany"
- "Show me IT services tenders in France"
- "Any construction projects in Spain?"
- "Show me awarded contracts for IT services in Poland"
- "Find design contest notices"

## API Endpoints

The backend provides two API interfaces:

### AgentOS API (for agent-ui)

- **GET /agents** - List available agents
- **POST /agents/{agent_id}/runs** - Run agent with streaming
- **GET /sessions** - List all sessions
- **GET /sessions/{id}/runs** - Get session history
- **DELETE /sessions/{id}** - Delete session

### Legacy API (deprecated)

- **POST /api/v1/chat** - Simple chat endpoint
- **GET /api/v1/search** - Direct TED search
- **GET /api/v1/health** - Health check

## Getting Started

See the [Deployment Guide](docs/deployment.md) for setup instructions.

## License

TBD
# ted-agent
