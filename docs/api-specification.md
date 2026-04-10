# API Specification

## Overview

The TED Bot API is built with FastAPI and provides RESTful endpoints for interacting with the tender notification system. All responses are in JSON format unless otherwise specified.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://ted-bot.vercel.app` (or your domain)

## API Versioning

Current version: **v1**
All endpoints are prefixed with `/api/v1` (except health check).

## Authentication

**Current**: No authentication (single-user system)
**Future**: API key or JWT bearer token

```http
Authorization: Bearer <token>
```

## Common Response Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required (future)
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Endpoints

### 1. Health & Status

#### GET /health

Health check endpoint.

**Response**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-09T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "up",
    "ollama": "up",
    "ted_api": "up"
  }
}
```

---

### 2. Chat Interface

#### POST /api/v1/chat

Send a message to the Agno agent and receive a response.

**Request Body**
```json
{
  "message": "Find me construction tenders in Germany above 1M EUR",
  "session_id": "optional-session-uuid",
  "context": {
    "preferences": {}
  }
}
```

**Response**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": {
    "message": "I found 15 construction tenders in Germany above 1M EUR...",
    "type": "text",
    "data": {
      "results": [...],
      "count": 15
    }
  },
  "agent": "search_agent",
  "timestamp": "2026-04-09T10:30:00Z"
}
```

#### WebSocket /api/v1/chat/ws

WebSocket endpoint for real-time chat streaming.

**Message Format (Client → Server)**
```json
{
  "type": "message",
  "message": "What are the latest IT tenders?",
  "session_id": "optional-session-uuid"
}
```

**Message Format (Server → Client)**
```json
{
  "type": "response_chunk",
  "content": "I found...",
  "done": false
}
```

```json
{
  "type": "response_complete",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-09T10:30:00Z"
}
```

---

### 3. Tender Search

#### POST /api/v1/tenders/search

Search for tenders using structured criteria.

**Request Body**
```json
{
  "query": "IT services",
  "filters": {
    "countries": ["DE", "FR"],
    "cpv_codes": ["72000000"],
    "min_value": 100000,
    "max_value": 5000000,
    "deadline_after": "2026-04-15",
    "deadline_before": "2026-12-31"
  },
  "search_mode": "hybrid",
  "limit": 20,
  "offset": 0
}
```

**Parameters**
- `query` (string, optional): Search text
- `filters` (object, optional): Filter criteria
- `search_mode` (string): `"keyword"`, `"semantic"`, or `"hybrid"` (default: `"hybrid"`)
- `limit` (integer): Max results (default: 20, max: 100)
- `offset` (integer): Pagination offset (default: 0)

**Response**
```json
{
  "results": [
    {
      "id": "tender_123456",
      "title": "IT Infrastructure Services",
      "contracting_authority": "Federal Ministry XYZ",
      "country": "DE",
      "cpv_codes": ["72000000", "72200000"],
      "value": 2500000,
      "currency": "EUR",
      "deadline": "2026-06-30T23:59:59Z",
      "publication_date": "2026-04-01T00:00:00Z",
      "url": "https://ted.europa.eu/...",
      "summary": "AI-generated summary of tender...",
      "relevance_score": 0.92
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0,
  "search_mode": "hybrid"
}
```

#### GET /api/v1/tenders/{tender_id}

Get detailed information about a specific tender.

**Response**
```json
{
  "id": "tender_123456",
  "title": "IT Infrastructure Services",
  "contracting_authority": {
    "name": "Federal Ministry XYZ",
    "address": "...",
    "contact": "..."
  },
  "description": "Full tender description...",
  "country": "DE",
  "location": "Berlin",
  "cpv_codes": [
    {"code": "72000000", "description": "IT services"}
  ],
  "value": 2500000,
  "currency": "EUR",
  "deadline": "2026-06-30T23:59:59Z",
  "publication_date": "2026-04-01T00:00:00Z",
  "procedure_type": "Open procedure",
  "award_criteria": "Most economically advantageous tender",
  "documents": [
    {
      "title": "Technical Specifications",
      "url": "https://..."
    }
  ],
  "url": "https://ted.europa.eu/...",
  "summary": "AI-generated summary...",
  "key_requirements": [
    "ISO 27001 certification required",
    "Minimum 5 years experience"
  ],
  "created_at": "2026-04-01T10:00:00Z",
  "updated_at": "2026-04-01T10:00:00Z"
}
```

#### POST /api/v1/tenders/{tender_id}/analyze

Request AI analysis of a tender.

**Response**
```json
{
  "tender_id": "tender_123456",
  "analysis": {
    "summary": "This tender is for...",
    "key_points": [
      "High-value IT infrastructure project",
      "Requires ISO 27001 certification",
      "Deadline in 3 months"
    ],
    "requirements": {
      "technical": [...],
      "financial": [...],
      "administrative": [...]
    },
    "risk_factors": [
      "Tight deadline",
      "Complex technical requirements"
    ],
    "opportunity_score": 7.5,
    "recommendation": "Good fit for companies with cloud expertise"
  },
  "generated_at": "2026-04-09T10:30:00Z"
}
```

---

### 4. Notifications & Monitoring

#### POST /api/v1/notifications/subscriptions

Create a new notification subscription.

**Request Body**
```json
{
  "name": "German IT Tenders",
  "criteria": {
    "countries": ["DE"],
    "cpv_codes": ["72000000"],
    "min_value": 100000,
    "keywords": ["cloud", "infrastructure"]
  },
  "notification_method": "log",
  "active": true
}
```

**Response**
```json
{
  "id": "sub_123",
  "name": "German IT Tenders",
  "criteria": {...},
  "notification_method": "log",
  "active": true,
  "created_at": "2026-04-09T10:30:00Z",
  "last_triggered": null,
  "match_count": 0
}
```

#### GET /api/v1/notifications/subscriptions

List all notification subscriptions.

**Response**
```json
{
  "subscriptions": [
    {
      "id": "sub_123",
      "name": "German IT Tenders",
      "criteria": {...},
      "active": true,
      "match_count": 15,
      "last_triggered": "2026-04-08T14:00:00Z"
    }
  ],
  "total": 1
}
```

#### PUT /api/v1/notifications/subscriptions/{subscription_id}

Update a notification subscription.

**Request Body**
```json
{
  "name": "Updated name",
  "criteria": {...},
  "active": true
}
```

#### DELETE /api/v1/notifications/subscriptions/{subscription_id}

Delete a notification subscription.

**Response**
```json
{
  "message": "Subscription deleted successfully"
}
```

#### GET /api/v1/notifications/history

Get notification history.

**Query Parameters**
- `limit` (integer): Max results (default: 50)
- `offset` (integer): Pagination offset
- `subscription_id` (string, optional): Filter by subscription

**Response**
```json
{
  "notifications": [
    {
      "id": "notif_789",
      "subscription_id": "sub_123",
      "tender_id": "tender_456",
      "tender_title": "IT Infrastructure Services",
      "sent_at": "2026-04-08T14:00:00Z",
      "status": "delivered"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

---

### 5. Reports & Insights

#### POST /api/v1/reports/generate

Generate a report on tender activity.

**Request Body**
```json
{
  "report_type": "trend_analysis",
  "parameters": {
    "date_from": "2026-01-01",
    "date_to": "2026-04-09",
    "countries": ["DE", "FR"],
    "cpv_codes": ["72000000"]
  },
  "format": "json"
}
```

**Report Types**
- `trend_analysis` - Tender trends over time
- `sector_analysis` - Breakdown by CPV codes
- `geographic_analysis` - Breakdown by country/region
- `contracting_authority` - Most active authorities
- `value_distribution` - Tender value statistics

**Response**
```json
{
  "report_type": "trend_analysis",
  "generated_at": "2026-04-09T10:30:00Z",
  "data": {
    "summary": {
      "total_tenders": 345,
      "total_value": 123456789,
      "average_value": 357899,
      "countries": 12
    },
    "trends": [
      {
        "period": "2026-01",
        "count": 78,
        "value": 23456789
      },
      {
        "period": "2026-02",
        "count": 82,
        "value": 28765432
      }
    ],
    "insights": [
      "20% increase in IT tenders in Q1 2026",
      "Germany leads with 45% of total value"
    ]
  }
}
```

#### GET /api/v1/reports/insights

Get AI-generated insights about current tender landscape.

**Query Parameters**
- `scope` (string): `"all"`, `"subscriptions"`, or `"recent"` (default: `"recent"`)

**Response**
```json
{
  "insights": [
    {
      "type": "trend",
      "title": "Surge in Cloud Infrastructure Tenders",
      "description": "30% increase in tenders with CPV 72000000...",
      "confidence": 0.87,
      "data_points": 45
    },
    {
      "type": "opportunity",
      "title": "High-Value Tenders in Germany",
      "description": "15 tenders above 1M EUR published this week...",
      "confidence": 0.95,
      "data_points": 15
    }
  ],
  "generated_at": "2026-04-09T10:30:00Z"
}
```

---

### 6. User Preferences

#### GET /api/v1/preferences

Get user preferences.

**Response**
```json
{
  "search_defaults": {
    "countries": ["DE"],
    "cpv_codes": [],
    "search_mode": "hybrid"
  },
  "notification_settings": {
    "enabled": true,
    "email": null
  },
  "display_settings": {
    "results_per_page": 20,
    "date_format": "DD/MM/YYYY"
  }
}
```

#### PUT /api/v1/preferences

Update user preferences.

**Request Body**
```json
{
  "search_defaults": {
    "countries": ["DE", "FR"],
    "search_mode": "hybrid"
  }
}
```

---

### 7. Query History

#### GET /api/v1/history/queries

Get query history.

**Query Parameters**
- `limit` (integer): Max results (default: 50)
- `offset` (integer): Pagination offset

**Response**
```json
{
  "queries": [
    {
      "id": "query_456",
      "query": "Find construction tenders in Germany",
      "timestamp": "2026-04-09T10:15:00Z",
      "results_count": 15,
      "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "total": 123,
  "limit": 50,
  "offset": 0
}
```

#### GET /api/v1/history/queries/{query_id}

Get specific query details with results.

---

### 8. System Administration

#### POST /api/v1/admin/sync

Manually trigger TED data synchronization.

**Request Body**
```json
{
  "date_from": "2026-04-01",
  "date_to": "2026-04-09"
}
```

**Response**
```json
{
  "task_id": "task_789",
  "status": "started",
  "message": "Sync started"
}
```

#### GET /api/v1/admin/sync/{task_id}

Check sync task status.

**Response**
```json
{
  "task_id": "task_789",
  "status": "completed",
  "started_at": "2026-04-09T10:30:00Z",
  "completed_at": "2026-04-09T10:35:00Z",
  "statistics": {
    "tenders_fetched": 145,
    "tenders_new": 23,
    "tenders_updated": 12
  }
}
```

---

## Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "cpv_codes",
      "issue": "Invalid CPV code format"
    },
    "request_id": "req_123456"
  }
}
```

### Error Codes

- `VALIDATION_ERROR` - Invalid input
- `NOT_FOUND` - Resource not found
- `TED_API_ERROR` - Error communicating with TED API
- `DATABASE_ERROR` - Database operation failed
- `LLM_ERROR` - LLM service error
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Unexpected server error

---

## Rate Limiting

**Current**: No rate limiting (single user)
**Future**: 
- 100 requests per minute per IP
- 1000 requests per hour per user
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## OpenAPI Documentation

Interactive API documentation available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
