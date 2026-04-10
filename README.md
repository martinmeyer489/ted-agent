# TED Bot - Intelligent Tender Notice Agent

**🎉 STATUS: SEARCH API FULLY FUNCTIONAL ✅**

> The TED search API is working! See [API-WORKING.md](API-WORKING.md) for usage examples.

An AI-powered agent system for retrieving, analyzing, and monitoring public procurement notices from the TED (Tenders Electronic Daily) platform.

## 🚀 Quick Start

```bash
# Start the server
./start-dev.sh

# Test the API
poetry run python test_api.py

# Open interactive docs
open http://localhost:8000/docs
```

## Overview

TED Bot is an intelligent agent built with Agno framework that helps users discover and analyze public procurement opportunities from the European Union's central tender platform. The system provides conversational access to tender data, automated monitoring, and intelligent analysis capabilities.

## Key Features

- 🤖 **Conversational Interface**: Natural language queries to search and analyze tenders
- 🔍 **Semantic Search**: Vector-based search for finding relevant opportunities
- 📊 **Automated Monitoring**: Scheduled checks for new tender notices
- 📝 **Document Analysis**: AI-powered summarization of tender documents
- 🔔 **Smart Notifications**: Alerts for matching tenders based on preferences
- 📈 **Insights & Reports**: Generate reports and insights from tender data

## Technology Stack

- **Agent Framework**: Agno
- **Backend API**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL + pgvector)
- **LLM**: Ollama Cloud (hosted models)
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
│   │   ├── api/            # FastAPI routes
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── core/           # Configuration
│   └── tests/
├── frontend/               # Simple web interface
└── scripts/                # Utility scripts
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

## Getting Started

See the [Deployment Guide](docs/deployment.md) for setup instructions.

## License

TBD
# ted-agent
