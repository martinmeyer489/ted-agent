# System Architecture

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Web Chat Interface                          │
│                  (HTML/JavaScript)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Agno Agent Layer                         │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │  - Search Agent                               │    │  │
│  │  │  - Analysis Agent                             │    │  │
│  │  │  - Monitoring Agent                           │    │  │
│  │  │  - Notification Agent                         │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Service Layer                            │  │
│  │  - TED API Client                                     │  │
│  │  - Vector Search Service                             │  │
│  │  - Notification Service                              │  │
│  │  - Scheduler Service                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────┬──────────────────────┬──────────────────────────┘
            │                      │
            │                      │
            ▼                      ▼
┌───────────────────────┐  ┌──────────────────────────────────┐
│   Ollama Cloud        │  │        Supabase                   │
│   - Embedding Model   │  │  ┌──────────────────────────┐    │
│   - Chat Model        │  │  │  PostgreSQL + pgvector   │    │
│   (Hosted API)        │  │  │  - tender_notices        │    │
│                       │  │  │  - embeddings            │    │
│                       │  │  │  - user_preferences      │    │
│                       │  │  │  - query_history         │    │
│                       │  │  │  - notifications         │    │
│                       │  │  └──────────────────────────┘    │
└───────────────────────┘  └──────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────┐
│                    TED API                                 │
│            (Tenders Electronic Daily)                      │
└───────────────────────────────────────────────────────────┘
```

## 2. Component Architecture

### 2.1 Frontend Layer

#### Chat Interface
- **Technology**: Vanilla HTML, CSS, JavaScript
- **Responsibilities**:
  - Render chat messages
  - Capture user input
  - Display tender results
  - Handle loading states
  - Manage WebSocket/HTTP communication
- **Key Features**:
  - Lightweight (no heavy frameworks)
  - Responsive design
  - Markdown rendering for rich responses
  - Copy-to-clipboard for tender details

### 2.2 Backend Layer

#### FastAPI Application
- **Technology**: FastAPI (Python 3.11+)
- **Responsibilities**:
  - HTTP API endpoints
  - WebSocket endpoint for chat
  - Request validation (Pydantic)
  - Error handling
  - CORS configuration
  - OpenAPI documentation
- **Key Routes**:
  - `/api/chat` - Chat interface
  - `/api/search` - Direct search endpoint
  - `/api/tenders/{id}` - Get tender details
  - `/api/notifications` - Manage notifications
  - `/api/reports` - Generate reports
  - `/health` - Health check

#### Agno Agent Layer
- **Technology**: Agno framework
- **Architecture**: Multi-agent system with specialized agents
- **Agents**:

  1. **Search Agent**
     - Handles tender search queries
     - Constructs search criteria from natural language
     - Interacts with vector search service
     - Formats results for user

  2. **Analysis Agent**
     - Analyzes tender documents
     - Extracts key information
     - Generates summaries
     - Answers questions about specific tenders

  3. **Monitoring Agent**
     - Runs on schedule (cron job or background task)
     - Checks for new tenders
     - Matches against user preferences
     - Triggers notifications

  4. **Notification Agent**
     - Manages notification preferences
     - Sends alerts (currently logs, future: email/webhook)
     - Tracks notification history

  5. **Report Agent**
     - Generates insights and reports
     - Aggregates tender statistics
     - Provides trend analysis

#### Service Layer

1. **TED API Client Service**
   - Authenticates with TED API
   - Fetches tender notices
   - Handles rate limiting
   - Caches responses
   - Parses and normalizes TED data

2. **Vector Search Service**
   - Generates embeddings using Ollama
   - Stores embeddings in Supabase pgvector
   - Performs similarity search
   - Hybrid search (keyword + semantic)
   - Reranking logic

3. **Notification Service**
   - Evaluates user preferences
   - Matches tenders to criteria
   - Creates notification records
   - Future: Email/webhook delivery

4. **Scheduler Service**
   - Background task management
   - Scheduled TED data refresh
   - Periodic monitoring checks
   - Cleanup old data

### 2.3 Data Layer

#### Supabase (PostgreSQL + pgvector)
- **Responsibilities**:
  - Persistent data storage
  - Vector similarity search
  - Transaction management
  - Connection pooling

#### Database Schema (see [database-schema.md](database-schema.md))
- `tender_notices` - Core tender data
- `tender_embeddings` - Vector embeddings
- `user_preferences` - Search and notification preferences
- `query_history` - User query logs
- `notification_subscriptions` - Monitoring criteria
- `notification_history` - Sent notifications log

### 2.4 LLM Layer

#### Ollama Cloud
- **Technology**: Cloud-hosted Ollama API
- **Models**:
  - **Embedding Model**: `nomic-embed-text` or `mxbai-embed-large`
  - **Chat Model**: `llama3.1`, `mistral`, or user preference
- **Endpoint**: `https://api.ollama.cloud` (or configured endpoint)
- **Authentication**: API key in headers
- **Responsibilities**:
  - Generate text embeddings
  - Chat completion for agent responses
  - Summarization
  - Question answering

### 2.5 External Integration

#### TED API
- **Endpoint**: TED eForms API or TED Open Data API
- **Authentication**: API credentials (stored as env variables)
- **Data Format**: JSON/XML
- **Rate Limits**: Respect TED API limits

## 3. Data Flow

### 3.1 User Query Flow

```
1. User enters query in chat interface
2. Frontend sends request to FastAPI /api/chat endpoint
3. FastAPI routes to Agno Search Agent
4. Agent analyzes query intent
5. Agent calls Vector Search Service
6. Vector Search Service:
   - Generates query embedding (Ollama Cloud API)
   - Searches pgvector for similar tenders
   - Optionally combines with keyword search
7. Results returned to Agent
8. Agent formats results with LLM (Ollama Cloud)
9. Response sent back to Frontend
10. Frontend displays results to user
```

### 3.2 Scheduled Monitoring Flow

```
1. Scheduler triggers Monitoring Agent (e.g., hourly)
2. Monitoring Agent:
   - Calls TED API Client to fetch new notices
   - Stores new notices in database
   - Generates embeddings via Vector Search Service
3. Monitoring Agent retrieves active notification subscriptions
4. For each new tender:
   - Check if it matches any subscription criteria
   - If match found, create notification record
5. Notification Agent processes pending notifications
6. Notifications delivered (log/email/webhook)
```

### 3.3 Document Analysis Flow

```
1. User requests analysis of specific tender
2. Frontend sends request to /api/tenders/{id}/analyze
3. Analysis Agent retrieves tender data
4. Agent extracts full document text
5. Agent uses LLM (Ollama Cloud) to:
   - Summarize document
   - Extract key dates, values, requirements
   - Generate structured output
6. Analysis result cached in database
7. Response returned to user
```



## 5. Scalability Considerations

### 5.1 Current Design (Single User)
- Simple architecture
- Minimal infrastructure
- Local LLM execution
- Suitable for <10K tenders

### 5.2 Future Scaling (Multi-User)
- Add authentication layer (Supabase Auth)
- Row-level security in database
- Move Ollama to dedicated server/container
- Add caching layer (Redis)
- Consider cloud LLM for high concurrency
- Implement rate limiting per user
- Add background job queue (Celery/RQ)

## 6. Deployment Architecture

### 6.1 Vercel Deployment (Primary)

```
┌─────────────────────────────────────────┐
│           Vercel                        │
│  ┌─────────────────────────────────┐   │
│  │  Frontend (static site)         │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Backend (serverless functions) │   │
│  │  - /api/* routes                │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
           │                  │
           ▼                  ▼
    ┌──────────────┐   ┌──────────────┐
    │   Supabase   │   │ Ollama Cloud │
    │   (Cloud)    │   │   (Hosted)   │
    │              │   │              │
    └──────────────┘   └──────────────┘
```

**Note**: Scheduled tasks need external cron (Vercel Cron or GitHub Actions)

```

## 7. Security Architecture

### 7.1 Secrets Management
- Environment variables for all credentials
- `.env` file for local development (not committed)
- Vercel environment variables for production
- Supabase API keys with appropriate scopes

### 7.2 Data Security
- HTTPS only in production
- Supabase encryption at rest
- No sensitive data in logs
- Input sanitization on all endpoints

### 7.3 LLM Security
- Prompt injection detection
- User input sanitization before LLM
- Rate limiting on LLM calls
- Timeout limits on LLM generation

## 8. Monitoring and Observability

### 8.1 Logging
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request/response logging
- Agent action logging
- TED API interaction logs

### 8.2 Metrics (Future)
- API response times
- LLM latency
- Vector search performance
- TED API call counts
- Database query performance

### 8.3 Error Tracking
- Exception handling at all layers
- Error context preservation
- User-friendly error messages
- Detailed logs for debugging
