# Technology Stack

## Overview

This document details the technology choices for TED Bot and the rationale behind each decision.

## Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Agent Framework** | Agno | Latest | Multi-agent orchestration |
| **Backend API** | FastAPI | 0.109+ | REST API and WebSocket |
| **Database** | Supabase (PostgreSQL) | 15+ | Data persistence |
| **Vector DB** | pgvector | 0.6+ | Semantic search |
| **LLM** | Ollama Cloud | Latest | Cloud-hosted LLM inference |
| **Embedding Model** | nomic-embed-text | Latest | Text embeddings |
| **Chat Model** | llama3.1 (or user choice) | Latest | Conversational AI |
| **Frontend** | Vanilla HTML/CSS/JS | - | Simple chat interface |
| **Deployment** | Vercel / Docker | - | Hosting |
| **Language** | Python | 3.11+ | Primary language |
| **Package Manager** | Poetry / pip | - | Dependency management |

## Detailed Technology Choices

### 1. Agent Framework: Agno

**What is it?**
Python framework for building multi-agent AI applications.

**Why Agno?**
- ✅ **Multi-agent support**: Natural fit for specialized agents (search, analysis, monitoring)
- ✅ **LLM-agnostic**: Works with Ollama (local) or cloud LLMs
- ✅ **Built-in tools**: Easy integration of custom functions
- ✅ **Workflow management**: Orchestrate complex multi-step processes
- ✅ **Memory management**: Conversation history and context
- ✅ **Active development**: Growing ecosystem and community

**Alternatives Considered**:
- **LangChain**: More complex, heavier dependencies
- **AutoGen**: Microsoft framework, more research-oriented
- **Custom implementation**: More control but higher development effort

**Installation**:
```bash
pip install agno
```

**Key Dependencies**:
- `agno-core` - Core framework
- `agno-models` - LLM integrations
- `agno-tools` - Tool definitions

---

### 2. Backend API: FastAPI

**What is it?**
Modern, high-performance Python web framework.

**Why FastAPI?**
- ✅ **Performance**: Async support, comparable to Node.js/Go
- ✅ **Type safety**: Pydantic integration for request/response validation
- ✅ **Auto documentation**: OpenAPI/Swagger UI generated automatically
- ✅ **WebSocket support**: Real-time chat streaming
- ✅ **Dependency injection**: Clean, testable code
- ✅ **Vercel compatible**: Can run as serverless functions
- ✅ **Developer experience**: Excellent error messages, auto-reload

**Alternatives Considered**:
- **Flask**: Simpler but lacks async support and type safety
- **Django**: Too heavy for this use case, REST framework overhead
- **Node.js/Express**: Different language, less type safety

**Installation**:
```bash
pip install "fastapi[all]"
```

**Key Dependencies**:
- `fastapi` - Core framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-multipart` - File uploads (if needed)

---

### 3. Database: Supabase (PostgreSQL)

**What is it?**
Open-source Firebase alternative, managed PostgreSQL with additional features.

**Why Supabase?**
- ✅ **PostgreSQL**: Mature, reliable, feature-rich RDBMS
- ✅ **pgvector support**: Native vector similarity search
- ✅ **Managed service**: Minimal ops overhead
- ✅ **Auto-generated APIs**: REST and GraphQL (optional)
- ✅ **Real-time subscriptions**: Database change notifications
- ✅ **Free tier**: Generous limits for development
- ✅ **Good Python SDK**: Easy integration
- ✅ **Row-level security**: Built-in for future multi-user support

**Alternatives Considered**:
- **MongoDB**: NoSQL good for flexibility, but lacks pgvector
- **Pinecone/Qdrant**: Vector-only DBs, need separate relational DB
- **Azure Cosmos DB**: More expensive, overkill for single user
- **Self-hosted PostgreSQL**: More ops overhead

**Setup**:
```bash
pip install supabase
```

**Configuration**:
```python
from supabase import create_client

supabase = create_client(
    supabase_url="https://xxx.supabase.co",
    supabase_key="your-anon-key"
)
```

---

### 4. Vector Database: pgvector

**What is it?**
PostgreSQL extension for vector similarity search.

**Why pgvector?**
- ✅ **Integrated**: Part of PostgreSQL, no separate database
- ✅ **Performance**: HNSW index for fast approximate search
- ✅ **Mature**: Battle-tested in production
- ✅ **Flexible**: Supports various distance metrics (cosine, L2, inner product)
- ✅ **Supabase support**: Built-in, easy to enable

**Alternatives Considered**:
- **Pinecone**: Cloud vector DB, monthly costs
- **Qdrant**: Separate service, more complexity
- **Weaviate**: Heavy, complex setup
- **FAISS**: Library not database, need persistence layer

**Setup in Supabase**:
```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with vector column
CREATE TABLE tender_embeddings (
    id UUID PRIMARY KEY,
    tender_id UUID REFERENCES tender_notices(id),
    embedding vector(768)  -- Dimension depends on model
);

-- Create HNSW index for fast search
CREATE INDEX ON tender_embeddings USING hnsw (embedding vector_cosine_ops);
```

---

### 5. LLM: Ollama Cloud

**What is it?**
Cloud-hosted Ollama service for running large language models via API.

**Why Ollama Cloud?**
- ✅ **No infrastructure**: No need to host LLM servers
- ✅ **Scalability**: Auto-scales with demand
- ✅ **Flexibility**: Choose from many models (Llama, Mistral, etc.)
- ✅ **Simple API**: OpenAI-compatible REST API
- ✅ **Consistent performance**: No local hardware constraints
- ✅ **Model library**: Easy to switch models
- ✅ **Lower complexity**: Simplified deployment

**Alternatives Considered**:
- **OpenAI API**: Higher costs, specific models only
- **Azure OpenAI**: Requires Azure setup, more expensive
- **Anthropic Claude**: Different API, costs vary
- **Local Ollama**: Requires separate server hosting, ops overhead

**Configuration**:
```bash
# Set environment variables
OLLAMA_API_URL=https://api.ollama.cloud  # Or your Ollama Cloud endpoint
OLLAMA_API_KEY=your-api-key
```

**Available Models**:
- **Chat models**: llama3.1, llama3.2, mistral, mixtral, codellama
- **Embedding models**: nomic-embed-text (768 dimensions), mxbai-embed-large

**Python Client**:
```bash
pip install ollama
# Or use requests/httpx directly
```

**Usage**:
```python
import ollama

# Configure for cloud
client = ollama.Client(
    host='https://api.ollama.cloud',  # Cloud endpoint
    headers={'Authorization': f'Bearer {api_key}'}
)

# Chat completion
response = client.chat(
    model="llama3.1",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Embeddings
embedding = client.embeddings(
    model="nomic-embed-text",
    prompt="This is a test"
)
```

---

### 6. Frontend: Vanilla HTML/CSS/JavaScript

**What is it?**
Simple web interface without frameworks.

**Why Vanilla JS?**
- ✅ **Simplicity**: No build process, no framework overhead
- ✅ **Fast loading**: Minimal dependencies
- ✅ **Easy deployment**: Static files
- ✅ **Maintainability**: Easy to understand and modify
- ✅ **Vercel compatible**: Deploy as static site

**Alternatives Considered**:
- **React**: Overkill for simple chat interface
- **Vue**: Lighter than React but still framework overhead
- **Streamlit**: Python-based, but less flexible for custom UI

**Stack**:
- **HTML5**: Structure
- **CSS3**: Styling (with CSS Grid/Flexbox)
- **Vanilla JavaScript**: Interactivity
- **Fetch API**: HTTP requests
- **WebSocket API**: Real-time chat (optional)
- **Marked.js**: Markdown rendering (optional)

**Libraries** (minimal):
```html
<!-- Optional: Markdown rendering -->
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

<!-- Optional: Syntax highlighting for code -->
<script src="https://cdn.jsdelivr.net/npm/highlight.js"></script>
```

---

### 7. Deployment: Vercel (Primary) / Docker (Fallback)

#### Vercel

**What is it?**
Serverless platform for frontend and backend deployments.

**Why Vercel?**
- ✅ **Free tier**: Generous limits for personal projects
- ✅ **Zero config**: Deploy from Git repos
- ✅ **Serverless functions**: FastAPI can run as functions
- ✅ **Static hosting**: Frontend served efficiently
- ✅ **Global CDN**: Fast worldwide
- ✅ **Automatic HTTPS**: SSL included
- ✅ **Environment variables**: Secure secrets management

**Considerations**:
- ⚠️ **Ollama hosting**: Need separate server for Ollama (can't run in serverless)
- ⚠️ **Cold starts**: Serverless functions may have latency
- ⚠️ **Scheduled tasks**: Need external cron (Vercel Cron or GitHub Actions)

**Setup**:
```bash
npm install -g vercel
vercel login
vercel deploy
```

#### Docker (Fallback)

**What is it?**
Containerization for portable deployments.

**Why Docker?**
- ✅ **Portability**: Run anywhere (cloud, on-prem, local)
- ✅ **Isolation**: All dependencies bundled
- ✅ **Ollama included**: Can run Ollama in same container/compose
- ✅ **Scheduled tasks**: Can run background workers
- ✅ **Development parity**: Same environment dev/prod

**Docker Compose Stack**:
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama
  
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
  
  frontend:
    build: ./frontend
    ports:
      - "3000:80"

volumes:
  ollama_data:
```

---

### 8. Python Version: 3.11+

**Why Python 3.11+?**
- ✅ **Performance**: 10-60% faster than 3.10
- ✅ **Better errors**: Improved stack traces
- ✅ **Type hints**: Enhanced typing features
- ✅ **Modern syntax**: Pattern matching, structural pattern matching
- ✅ **AsyncIO improvements**: Better async performance

---

### 9. Package Management: Poetry

**What is it?**
Modern Python dependency management and packaging tool.

**Why Poetry?**
- ✅ **Deterministic builds**: Lock file for reproducible installs
- ✅ **Dependency resolution**: Better than pip
- ✅ **Virtual env management**: Automatic venv creation
- ✅ **Build tool**: Create packages easily
- ✅ **Modern pyproject.toml**: Standard Python config

**Alternative**: `pip + requirements.txt` (simpler, but less robust)

**Installation**:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Usage**:
```bash
poetry init
poetry add fastapi supabase ollama agno
poetry install
poetry run uvicorn app.main:app
```

---

## Additional Tools

### Development Tools

1. **Black** - Code formatter
   ```bash
   poetry add --group dev black
   ```

2. **Ruff** - Fast Python linter
   ```bash
   poetry add --group dev ruff
   ```

3. **MyPy** - Type checker
   ```bash
   poetry add --group dev mypy
   ```

4. **Pytest** - Testing framework
   ```bash
   poetry add --group dev pytest pytest-asyncio
   ```

### Monitoring & Logging

1. **Loguru** - Better logging
   ```bash
   poetry add loguru
   ```

2. **Python-dotenv** - Environment variables
   ```bash
   poetry add python-dotenv
   ```

### Scheduled Tasks

1. **APScheduler** - Background job scheduling
   ```bash
   poetry add apscheduler
   ```
   
   **Alternative**: GitHub Actions cron (for Vercel deployment)

---

## Environment Variables

Required environment variables:

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text

# TED API
TED_API_URL=https://ted.europa.eu/api/v1
TED_API_KEY=your-ted-api-key

# App Config
ENVIRONMENT=development  # or production
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000

# Vercel (auto-populated in production)
VERCEL_URL=your-app.vercel.app
```

---

## Performance Characteristics

### Expected Performance

| Operation | Expected Latency | Notes |
|-----------|-----------------|-------|
| Keyword search | < 200ms | PostgreSQL full-text search |
| Vector search | < 500ms | HNSW index, 10K vectors |
| Hybrid search | < 700ms | Combined keyword + vector |
| LLM chat response | 1-3s | Ollama Cloud API latency |
| Embedding generation | 100-200ms | nomic-embed-text via API |
| TED API fetch | 1-3s | External API, depends on network |

### Scalability Limits (Current Design)

- **Tenders stored**: 10K-100K (PostgreSQL can handle millions)
- **Concurrent users**: 10-50 (Ollama Cloud auto-scales)
- **Vector search**: Sub-second for 100K vectors with HNSW
- **LLM throughput**: Scales with Ollama Cloud capacity

---

## Cost Analysis

### Development Costs

- **Supabase**: Free tier (500MB database, 50K requests/month)
- **Ollama Cloud**: Free tier or pay-as-you-go (check current pricing)
- **Vercel**: Free tier (100GB bandwidth, serverless functions)
- **TED API**: Free (public API)

**Total**: $0-10/month for development (depending on LLM usage)

### Production Costs (Estimated)

- **Supabase**: $25/month (Pro plan, more storage/bandwidth)
- **Ollama Cloud**: $20-50/month (depending on usage and model choice)
- **Vercel**: $0-20/month (Pro if needed for more bandwidth)
- **Domain**: $10-15/year

**Total**: ~$45-95/month depending on scale and usage

---

## License Considerations

| Technology | License | Commercial Use |
|-----------|---------|----------------|
| Agno | MIT | ✅ Yes |
| FastAPI | MIT | ✅ Yes |
| Supabase | Apache 2.0 | ✅ Yes |
| pgvector | PostgreSQL | ✅ Yes |
| Ollama | MIT | ✅ Yes |
| Llama 3.1 | Meta License | ✅ Yes (with restrictions) |
| PostgreSQL | PostgreSQL | ✅ Yes |

**Note**: Check specific model licenses if using commercially. Llama models have usage restrictions at scale.

---

## Future Technology Considerations

When scaling to multi-user or enterprise:

1. **Caching**: Add Redis for response and LLM caching
2. **Message Queue**: Add Celery/RQ for background jobs
3. **Alternative LLMs**: Consider Azure OpenAI or Anthropic for specific use cases
4. **CDN**: CloudFlare or similar for global performance
5. **Monitoring**: Add Sentry, DataDog, or similar
6. **Load balancer**: NGINX or cloud load balancer
7. **Database read replicas**: For read-heavy workloads
8. **API gateway**: Kong or similar for rate limiting, auth
