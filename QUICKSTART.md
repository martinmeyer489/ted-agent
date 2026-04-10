# TED Bot - Quick Start Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry (Python dependency manager)
- Supabase account (for database)
- TED API key
- Ollama Cloud API key

### 1. Install Dependencies

```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

### 2. Configure Environment

Update `.env` file with your credentials:

```bash
# TED API
TED_API_KEY="your-ted-api-key"
TED_API_URL="https://api.ted.europa.eu/v3"

# Ollama Cloud
OLLAMA_API_URL="https://api.ollama.cloud"
OLLAMA_API_KEY="your-ollama-api-key"
OLLAMA_CHAT_MODEL="llama3.1"
OLLAMA_EMBED_MODEL="nomic-embed-text"

# Supabase
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-supabase-key"

# App Settings
ENVIRONMENT="development"
LOG_LEVEL="DEBUG"
CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
```

### 3. Set Up Database

1. Create a Supabase project at https://supabase.com
2. Run the schema from `database/schema.sql` in the SQL Editor
3. Update `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

### 4. Start the Application

#### Option A: Using the start script (recommended)
```bash
chmod +x start-dev.sh
./start-dev.sh
```

#### Option B: Manual start
```bash
poetry run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: Open `frontend/index.html` in your browser
  - Or serve with: `python3 -m http.server 3000 --directory frontend`

## 📡 API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Search Tenders
```bash
curl -X POST http://localhost:8000/api/v1/tenders/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "IT services",
    "countries": ["Germany", "France"],
    "published_after": "2024-01-01",
    "max_results": 10
  }'
```

### Chat with Bot
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What are the latest IT tenders in Germany?"}
    ],
    "stream": false
  }'
```

### Create Subscription
```bash
curl -X POST http://localhost:8000/api/v1/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "IT Services Germany",
    "query": "software development",
    "countries": ["Germany"],
    "notification_channel": "email",
    "frequency": "daily"
  }'
```

## 🧪 Testing

### Test TED API Connection
```bash
poetry run python -c "
import asyncio
from backend.app.services.ted_client import get_ted_client

async def test():
    client = get_ted_client()
    result = await client.search_notices('ND=*', ['ND', 'notice-title'])
    print(f'Found {len(result.get(\"notices\", []))} notices')

asyncio.run(test())
"
```

### Test Ollama Chat
```bash
poetry run python -c "
import asyncio
from backend.app.services.ollama_client import get_ollama_client

async def test():
    client = get_ollama_client()
    messages = [{'role': 'user', 'content': 'Hello!'}]
    response = await client.chat(messages)
    print(response.get('message', {}).get('content'))

asyncio.run(test())
"
```

## 📁 Project Structure

```
ted-bot/
├── backend/
│   └── app/
│       ├── api/
│       │   └── routes/          # FastAPI routes
│       ├── core/                # Configuration, logging
│       ├── models/              # Pydantic schemas
│       └── services/            # Service clients
├── frontend/                    # Simple web UI
├── database/                    # SQL schemas
├── docs/                        # Documentation
├── pyproject.toml              # Dependencies
├── .env                        # Environment variables
└── start-dev.sh                # Startup script
```

## 🔧 Development

### Run with Auto-reload
```bash
poetry run uvicorn backend.app.main:app --reload
```

### Format Code
```bash
poetry run black backend/
```

### Lint Code
```bash
poetry run ruff check backend/
```

## 📚 Documentation

Full documentation available in `docs/`:
- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [API Specification](docs/api-specification.md)
- [Database Schema](docs/database-schema.md)
- [TED API Integration](docs/ted-api-integration.md)
- [Deployment Guide](docs/deployment.md)

## ❓ Troubleshooting

### Import Errors
```bash
# Ensure you're in the project root
cd /path/to/ted-bot

# Reinstall dependencies
poetry install
```

### Database Connection Errors
- Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Check that you ran `database/schema.sql` in Supabase SQL Editor
- Ensure pgvector extension is enabled

### TED API Errors
- Verify your API key is valid
- Check rate limits (if applicable)
- Ensure query syntax is correct

### Ollama Cloud Errors
- Verify API key is valid
- Check model names match available models
- Ensure API URL is correct

## 🚢 Deployment

See [Deployment Guide](docs/deployment.md) for production deployment instructions.

## 📝 License

MIT License
