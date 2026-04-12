# Deployment Guide

Quick guide for deploying TED Bot to production.

## Prerequisites

- GitHub repository with your code
- TED API key
- Ollama setup (local or cloud)
- Vercel account (for easy deployment)

## Environment Variables

You'll need these environment variables in production:

```bash
# Required
TED_API_KEY=your-ted-api-key
OLLAMA_API_URL=http://localhost:11434  # or Ollama Cloud URL
OLLAMA_CHAT_MODEL=llama3.1

# Optional
OLLAMA_API_KEY=your-key  # if using Ollama Cloud
SUPABASE_URL=your-url    # if using Supabase
SUPABASE_KEY=your-key    
```

## Deployment to Vercel (Recommended)

Vercel can host both the frontend and backend.

### 1. Install Vercel CLI

```bash
npm i -g vercel
```

### 2. Deploy

```bash
cd ted-bot
vercel
```

Follow the prompts:
- Link to your GitHub repo
- Set root directory to your project
- Add environment variables in Vercel dashboard

### 3. Configure Backend

Vercel will detect Next.js automatically. For the FastAPI backend, you may need to:

- Add `api/` folder in root with serverless functions, OR
- Deploy backend separately to Render/Railway/Fly.io

**Option A: Separate Backend Deployment**

1. Deploy backend to Render/Railway:
   ```bash
   # Render will auto-detect your Dockerfile
   # Or use their Python buildpack
   ```

2. Update frontend `.env.local`:
   ```bash
   NEXT_PUBLIC_AGENTOS_URL=https://your-backend.onrender.com
   ```

## Alternative: Docker Deployment

Use Docker Compose for full-stack deployment:

```bash
docker-compose up -d
```

This starts:
- Frontend on port 3000
- Backend on port 8000

### Environment Setup

Create `.env` file (see Prerequisites section above).

### Deploy to Cloud

Push to any Docker-compatible host:
- Google Cloud Run
- AWS ECS/Fargate
- Azure Container Apps
- DigitalOcean App Platform

## Local Development

See main [README.md](../README.md) for local development setup.

**Backend:**
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
pnpm install
pnpm dev
```

## Troubleshooting

### Backend not connecting

- Check CORS settings in `backend/app/main.py`
- Ensure `CORS_ORIGINS` includes your frontend URL

### Ollama not working

- Test Ollama endpoint: `curl http://your-ollama-url/api/tags`
- Check API key if using Ollama Cloud
- Verify model name exists: `ollama list` (if local)

### TED API errors

- Verify API key is correct
- Check rate limits (TED API may have usage limits)
- Review logs: backend shows detailed error messages

## Production Checklist

- [ ] Set all environment variables
- [ ] Test TED API key
- [ ] Test Ollama connection
- [ ] Set `ENVIRONMENT=production` in backend
- [ ] Add custom domain (optional)
- [ ] Set up monitoring (optional)
- [ ] Enable HTTPS (Vercel does this automatically)
  -H "Authorization: Bearer $OLLAMA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

### Step 1.6: Initialize Data (Optional)

Fetch initial tender data:

```bash
poetry run python scripts/initial_sync.py
```

### Step 1.7: Run Backend

```bash
# Using Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or directly
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: http://localhost:8000
API docs: http://localhost:8000/docs

### Step 1.8: Run Frontend

```bash
# Simple HTTP server for frontend
cd frontend
python -m http.server 3000

# Or use any static server
npx serve -p 3000
```

Frontend will be available at: http://localhost:3000

### Step 1.9: Test the Application

```bash
# Run tests
poetry run pytest

# Or
pytest tests/
```

---

## 2. Vercel Deployment

### Architecture

```
Vercel
├── Frontend (static site)
└── Backend (serverless functions)

External
├── Supabase (database)
└── Ollama Server (separate VPS/dedicated server)
```

### Step 2.1: Prepare for Vercel

Install Vercel CLI:
```bash
npm install -g vercel
vercel login
```

### Step 2.2: Configure Project Structure

Create `vercel.json` in project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/**",
      "use": "@vercel/static"
    },
    {
      "src": "backend/app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/app/main.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ],
  "env": {
    "SUPABASE_URL": "@supabase-url",
    "SUPABASE_KEY": "@supabase-key",
    "OLLAMA_API_URL": "@ollama-api-url",
    "OLLAMA_API_KEY": "@ollama-api-key",
    "TED_API_KEY": "@ted-api-key"
  }
}
```

### Step 2.3: Create `requirements.txt` for Vercel

Vercel doesn't use Poetry directly in serverless functions:

```bash
poetry export -f requirements.txt --output backend/requirements.txt --without-hashes
```

### Step 2.4: Adjust FastAPI for Serverless

Create `backend/api/index.py` (Vercel entry point):

```python
from app.main import app
from mangum import Mangum

# Wrap FastAPI app for AWS Lambda/Vercel
handler = Mangum(app)
```

Add `mangum` to dependencies:
```bash
poetry add mangum
```

### Step 2.5: Set Environment Variables in Vercel

```bash
# Using CLI
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY
vercel env add OLLAMA_API_URL
vercel env add OLLAMA_API_KEY
vercel env add TED_API_KEY
vercel env add OLLAMA_CHAT_MODEL
vercel env add OLLAMA_EMBED_MODEL

# Or use Vercel Dashboard:
# 1. Go to project settings
# 2. Environment Variables
# 3. Add each variable
```

### Step 2.6: Setup Scheduled Tasks (Monitoring)

**Option A: Vercel Cron**

Create `vercel.json` cron configuration:

```json
{
  "crons": [
    {
      "path": "/api/admin/sync",
      "schedule": "0 * * * *"
    }
  ]
}
```

**Option B: GitHub Actions**

Create `.github/workflows/scheduled-sync.yml`:

```yaml
name: Scheduled TED Sync

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:  # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Sync
        run: |
          curl -X POST https://your-app.vercel.app/api/admin/sync \
            -H "Authorization: Bearer ${{ secrets.API_KEY }}"
```

### Step 2.7: Deploy to Vercel

```bash
# Deploy
vercel

# Or for production
vercel --prod

# Link to Git repository for auto-deploy
vercel git connect
```

### Step 2.8: Verify Deployment

1. Check frontend: `https://your-app.vercel.app`
2. Check API: `https://your-app.vercel.app/api/health`
3. Check API docs: `https://your-app.vercel.app/docs`

---

## 3. Docker Deployment

### Step 3.1: Create Dockerfiles

**Backend Dockerfile** (`backend/Dockerfile`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile** (`frontend/Dockerfile`):

```dockerfile
FROM nginx:alpine

# Copy frontend files
COPY . /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

Frontend nginx config (`frontend/nginx.conf`):

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Proxy API requests to backend
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Step 3.2: Create Docker Compose

**`docker-compose.yml`**:

```yaml
version: '3.8'

services:
  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - OLLAMA_HOST=http://ollama:11434
      - TED_API_URL=${TED_API_URL}
      - TED_API_KEY=${TED_API_KEY}
      - OLLAMA_CHAT_MODEL=${OLLAMA_CHAT_MODEL}
      - OLLAMA_EMBED_MODEL=${OLLAMA_EMBED_MODEL}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - ted-bot-network

  # Ollama LLM service
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    networks:
      - ted-bot-network
    # Optional: Use GPU
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  # Frontend web server
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - ted-bot-network

  # Background scheduler for monitoring
  scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python -m app.scheduler
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - OLLAMA_HOST=http://ollama:11434
      - TED_API_URL=${TED_API_URL}
      - TED_API_KEY=${TED_API_KEY}
    depends_on:
      - backend
      - ollama
    restart: unless-stopped
    networks:
      - ted-bot-network

volumes:
  ollama_data:

networks:
  ted-bot-network:
    driver: bridge
```

### Step 3.3: Create Environment File

**`.env.docker`**:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
TED_API_URL=https://ted.europa.eu/api/v1
TED_API_KEY=your-ted-api-key
OLLAMA_CHAT_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### Step 3.4: Initialize Ollama Models

Create initialization script (`scripts/init-ollama.sh`):

```bash
#!/bin/bash

echo "Waiting for Ollama to be ready..."
sleep 10

echo "Pulling chat model..."
docker exec ted-bot-ollama-1 ollama pull llama3.1

echo "Pulling embedding model..."
docker exec ted-bot-ollama-1 ollama pull nomic-embed-text

echo "Models initialized!"
```

### Step 3.5: Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Initialize Ollama models (first time only)
chmod +x scripts/init-ollama.sh
./scripts/init-ollama.sh

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Step 3.6: Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Check Ollama
curl http://localhost:11434/api/tags

# Access frontend
open http://localhost
```

### Step 3.7: Production Considerations

For production Docker deployment:

1. **Reverse Proxy**: Use Traefik or NGINX for HTTPS
2. **SSL**: Add Let's Encrypt certificates
3. **Monitoring**: Add Prometheus + Grafana
4. **Logging**: Centralized logging (ELK stack)
5. **Backups**: Automated database backups

---

## 4. Database Migrations

### Initial Schema Setup

```bash
# Apply schema
psql $SUPABASE_URL -f database/schema.sql

# Or via Supabase CLI
supabase db push
```

### Version Control Migrations

Use Alembic for database versioning:

```bash
# Install
poetry add alembic

# Initialize
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

---

## 5. CI/CD Pipeline

### GitHub Actions Workflow

**`.github/workflows/deploy.yml`**:

```yaml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      
      - name: Run tests
        run: poetry run pytest
      
      - name: Lint
        run: |
          poetry run black --check .
          poetry run ruff check .

  deploy-vercel:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

---

## 6. Monitoring & Maintenance

### Health Checks

Implement health check endpoint:

```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "ollama": await check_ollama(),
        "ted_api": await check_ted_api()
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now(),
        "services": checks
    }
```

### Logging

Configure structured logging:

```python
from loguru import logger

logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)
```

### Backup Strategy

1. **Database**: Supabase automatic backups + manual exports
2. **Embeddings**: Regular vector data exports
3. **Configuration**: Version controlled in Git

---

## 7. Troubleshooting

### Common Issues

**Issue**: Ollama connection refused
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
# macOS: killall ollama && ollama serve
# Docker: docker-compose restart ollama
```

**Issue**: Supabase connection error
```bash
# Verify credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test connection
python -c "from supabase import create_client; client = create_client('$SUPABASE_URL', '$SUPABASE_KEY'); print(client.table('tender_notices').select('*').limit(1).execute())"
```

**Issue**: Vector search returns no results
```bash
# Check embeddings table
psql $SUPABASE_URL -c "SELECT COUNT(*) FROM tender_embeddings;"

# Regenerate embeddings
python scripts/regenerate_embeddings.py
```

---

## 8. Scaling Considerations

When traffic grows:

1. **Add caching**: Redis for API responses
2. **Database read replicas**: For read-heavy workloads
3. **Load balancer**: Distribute traffic
4. **CDN**: CloudFlare for static assets
5. **Ollama cluster**: Multiple Ollama instances
6. **Horizontal scaling**: Multiple backend containers
7. **Queue background jobs**: Celery/RQ for async tasks

---

## Summary Checklist

- [ ] Supabase project created and database schema applied
- [ ] TED API credentials obtained
- [ ] Ollama installed and models downloaded
- [ ] Environment variables configured
- [ ] Backend running and accessible
- [ ] Frontend running and can connect to backend
- [ ] Database migrations applied
- [ ] Initial data sync completed
- [ ] Tests passing
- [ ] Deployed to production (Vercel or Docker)
- [ ] Scheduled monitoring tasks configured
- [ ] Health checks working
- [ ] Logging configured
