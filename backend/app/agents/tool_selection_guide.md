# Tool Selection Guide for TED Agent

This document helps the agent choose the right tool for user queries.

## Quick Reference

| User Request | Tool to Use | Example |
|--------------|-------------|---------|
| "Find IT tenders in Germany" | `search_ted_tenders` | Simple keyword search |
| Show me winners from Nov 4, 2024" | `query_ted_sparql` | Date-specific award query |
| "Get details for notice 245804-2026" | `get_ted_notice_details` | Specific notice lookup |
| "Top 10 biggest contracts" | `query_ted_sparql` | Aggregation and ranking |
| "Construction projects in France" | `search_ted_tenders` | Keyword + country filter |
| "Total value awarded in 2024" | `query_ted_sparql` | Statistical analysis |
| "Show me tender #3 details" | `get_ted_notice_details` | Follow-up on search result |
| "Award notices for software" | `search_ted_tenders` | Notice type filter |
| "Average contract value by country" | `query_ted_sparql` | Aggregation by group |

## Decision Tree

```
User Query
    │
    ├─ Asking for statistics/analytics? (total, average, top N, count)
    │   └─> Use query_ted_sparql
    │
    ├─ Asking about specific winners or award amounts?
    │   └─> Use query_ted_sparql
    │
    ├─ Asking for details of a specific notice ID?
    │   └─> Use get_ted_notice_details
    │
    └─ Everything else (browse, search, filter)
        └─> Use search_ted_tenders
```

## Tool Capabilities Matrix

### search_ted_tenders
**Best For:**
- ✅ Keyword searches ("software", "construction", "IT services")
- ✅ Country filtering (Germany, France, etc.)
- ✅ CPV code filtering
- ✅ Notice type filtering (cn-standard, can-standard, etc.)
- ✅ Recent tenders
- ✅ Quick browsing
- ✅ Simple filters

**Cannot Do:**
- ❌ Aggregations (SUM, AVG, COUNT)
- ❌ Statistical analysis
- ❌ Winner information
- ❌ Award amounts
- ❌ Complex JOINs
- ❌ Historical trends

**Response Format:**
- Compact table (>5 results) or detailed cards (≤5 results)
- Shows: title, buyer, country, publication date, publication number
- Direct links to TED website

### query_ted_sparql
**Best For:**
- ✅ Winner and award queries
- ✅ Statistical analysis
- ✅ Aggregations (TOP 10, TOTAL, AVG, etc.)
- ✅ Complex filters
- ✅ Date range analysis
- ✅ Relationships between entities
- ✅ Custom analytics

**Cannot Do:**
- ❌ Simple keyword searches (use REST API instead)
- ❌ User-friendly browsing
- ❌ Quick lookups

**Response Format:**
- Markdown table with query results
- Raw data from SPARQL endpoint
- Supports JSON, CSV, or table output

**Requires:**
- Knowledge of SPARQL syntax
- Understanding of TED ontology
- Specific entity URIs and prefixes

### get_ted_notice_details
**Best For:**
- ✅ Full tender details by publication number
- ✅ Follow-up from search results
- ✅ Complete specifications
- ✅ All contact information
- ✅ Detailed requirements

**Cannot Do:**
- ❌ Search or filter
- ❌ Multiple notices at once
- ❌ Analytics

**Response Format:**
- Complete HTML notice converted to markdown
- All sections from official TED notice
- Truncated if >15,000 characters

## Example Scenarios

### Scenario 1: User asks "Find software tenders in Germany"
**Tool**: `search_ted_tenders`
**Why**: Simple keyword + country filter
**Parameters**:
```python
query="software"
countries=["Germany"]
```

### Scenario 2: User asks "Who won the most contracts in November 2024?"
**Tool**: `query_ted_sparql`
**Why**: Requires aggregation and winner information
**Query Pattern**:
```sparql
SELECT ?winnerName (COUNT(*) as ?contractCount)
WHERE {
  # Filter by date
  # Get winner information
  # Group by winner
}
GROUP BY ?winnerName
ORDER BY DESC(?contractCount)
LIMIT 10
```

### Scenario 3: User asks "Show me details for tender #3"
**Tool**: `get_ted_notice_details`
**Why**: Following up on a search result
**Parameter**:
```python
notice_id=<extract publication number from previous search>
```

### Scenario 4: User asks "Total value of IT contracts in 2024"
**Tool**: `query_ted_sparql`
**Why**: Requires SUM aggregation and date filtering
**Query Pattern**:
```sparql
SELECT (SUM(?amount) as ?totalValue)
WHERE {
  # Filter by CPV code (IT = 72000000)
  # Filter by publication date 2024
  # Get award amounts
}
```

### Scenario 5: User asks "Recent construction projects in France and Spain"
**Tool**: `search_ted_tenders`
**Why**: Simple multi-country keyword search
**Parameters**:
```python
query="construction"
countries=["France", "Spain"]
```

### Scenario 6: User asks "Show me only contract award notices"
**Tool**: `search_ted_tenders`
**Why**: Notice type filter supported by REST API
**Parameters**:
```python
query=<user's keywords>
notice_types=["can-standard"]
```

## Keywords That Trigger SPARQL

Watch for these phrases that indicate SPARQL is needed:
- "total value", "sum of", "aggregate"
- "average", "mean"
- "top 10", "biggest", "largest", "smallest"
- "how many", "count"
- "winners", "who won", "awarded to"
- "group by", "per country", "by organization"
- "trend", "over time", "historical"
- "all contracts from [specific date]"
- "awarded in [month/year]"

## Keywords That Trigger REST API

Watch for these phrases that indicate REST API is sufficient:
- "find", "search for", "look for"
- "show me", "get me", "list"
- "tenders in [country]"
- "recent", "latest", "new"
- "available", "open", "active"
- "[keyword] contracts" (software, construction, etc.)

## Error Handling

### If SPARQL Fails:
1. Check if query has syntax errors
2. Suggest user try REST API for simpler queries
3. Provide link to SPARQL documentation

### If REST API Fails:
1. Check TED API status
2. Verify query syntax (SORT BY required)
3. Try with fewer filters

### If Details Fetch Fails (404):
1. Verify publication number format (XXXXXX-YYYY)
2. Notice might be archived or removed
3. Try searching for the notice first

## Testing Checklist

When implementing queries:
- [ ] Does the query require aggregation? → SPARQL
- [ ] Does the query ask about winners/amounts? → SPARQL
- [ ] Is it a simple keyword search? → REST API
- [ ] Does it filter by country/CPV? → REST API
- [ ] Does it need a specific notice ID? → Details tool
- [ ] Does it ask for statistics? → SPARQL
- [ ] Is it browsing or exploring? → REST API

## Performance Notes

- REST API: Fast (typically <2 seconds)
- SPARQL: Can be slow (5-30 seconds for complex queries)
- Details: Fast (typically <3 seconds)

**Recommendation**: Always try REST API first for simple queries, only use SPARQL when advanced analytics are needed.
