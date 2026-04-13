# TED Bot 🤖

> A hobby project: AI-powered chat interface for searching EU tender opportunities

## What It Does

Search and chat with EU public procurement data (TED - Tenders Electronic Daily) using natural language. Ask questions like "Find software tenders in Germany" and get results in a nice table that you can filter and sort by talking to the agent.

## Quick Start

**Start backend:**
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

**Start frontend (in another terminal):**
```bash
cd frontend
pnpm install
pnpm dev
```

Then open http://localhost:3000

## Features

- 💬 Chat interface for natural language tender search
- 📊 Interactive workspace table that updates based on your questions
- 🔧 Multiple tools: TED API search, SPARQL queries, and notice details
- 📝 Session history to continue conversations
- 🎨 Clean, modern UI built with Next.js and shadcn/ui

## Tech Stack

- **Backend**: FastAPI + Agno agent framework + Python 3.11+
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS
- **LLM**: Ollama (local or cloud)
- **Database**: Supabase (PostgreSQL - optional for persistence)
- **Deployment**: Vercel

## Project Structure

```
ted-bot/
├── backend/           # FastAPI + Agno agent
│   ├── app/
│   │   ├── agents/   # TED agent + tools
│   │   ├── api/      # Routes
│   │   ├── services/ # TED API client, Supabase, etc.
│   │   └── core/     # Config
│   └── requirements.txt
├── frontend/         # Next.js UI
│   └── src/
│       ├── components/
│       ├── app/
│       └── hooks/
└── docs/            # Architecture and specs
```

## Documentation

- [Backend README](backend/README.md) - Backend setup and API details
- [Frontend README](frontend/README.md) - Frontend setup and components
- [Architecture](docs/architecture.md) - System design

## Environment Variables

Create `.env` in the project root:

```bash
# Required
TED_API_KEY=your-ted-api-key
OLLAMA_API_URL=http://localhost:11434  # or Ollama Cloud URL
OLLAMA_API_KEY=your-key  # if using Ollama Cloud
OLLAMA_CHAT_MODEL=llama3.1


```

## License

MIT - This is a hobby project, use it however you like!
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


### AgentOS API (for agent-ui)

- **GET /agents** - List available agents
- **POST /agents/{agent_id}/runs** - Run agent with streaming
- **GET /sessions** - List all sessions
- **GET /sessions/{id}/runs** - Get session history
- **DELETE /sessions/{id}** - Delete session



## Getting Started

See the [Deployment Guide](docs/deployment.md) for setup instructions.

## License


