# TED Bot Backend

FastAPI application with an Agno agent for searching EU tender notices.

## Setup

**Install dependencies:**
```bash
poetry install
# or
pip install -r requirements.txt
```

**Set environment variables** (create `.env` in project root):
```bash
TED_API_KEY=your-ted-api-key
OLLAMA_API_URL=http://localhost:11434
OLLAMA_API_KEY=your-key  # if using Ollama Cloud
OLLAMA_CHAT_MODEL=llama3.1
```

**Run the server:**
```bash
poetry run uvicorn app.main:app --reload --port 8000
```

API docs will be at http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── agents/
│   │   ├── ted_agent.py      # Main agent logic
│   │   └── tools.py          # TED search tools
│   ├── api/routes/
│   │   ├── agentos.py        # AgentOS-compatible endpoints
│   │   ├── chat.py           # Chat endpoint
│   │   ├── search.py         # Direct search endpoint
│   │   ├── subscriptions.py  # Subscriptions (optional)
│   │   └── health.py         # Health check
│   ├── services/
│   │   ├── ted_client.py     # TED API client
│   │   ├── ollama_client.py  # Ollama client (if needed)
│   │   └── supabase_client.py # Database (optional)
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   ├── core/
│   │   ├── config.py         # Settings
│   │   └── logging.py        # Logging setup
│   └── main.py               # FastAPI app
└── requirements.txt
```

## Main Endpoints

### AgentOS API (used by frontend)

- `GET /agents` - List available agents
- `POST /agents/{agent_id}/runs` - Run agent with a message
- `GET /sessions` - List sessions
- `GET /sessions/{id}/runs` - Get session history
- `DELETE /sessions/{id}` - Delete session

### Direct API

- `POST /api/v1/chat` - Direct chat endpoint (SSE streaming)
- `POST /api/v1/search` - Direct tender search
- `GET /health` - Health check

## Agent Tools

The TED agent has access to these tools:

1. **search_ted_tenders** - Search TED using the Expert Search API
2. **get_ted_notice_details** - Get details for a specific notice ID
3. **query_ted_sparql** - Run SPARQL queries against TED data
4. **update_workspace_table** - Update the workspace table in the UI

## Development

**Run tests:**
```bash
poetry run pytest
```

**Format code:**
```bash
poetry run black .
poetry run ruff check .
```

**Type checking:**
```bash
poetry run mypy app
```

## Key Dependencies

- `fastapi` - Web framework
- `agno` - Agent framework
- `ollama` - LLM client
- `httpx` - HTTP client for TED API
- `supabase` - Database (optional)
- `pydantic` - Data validation
- `loguru` - Logging
