# TED API Integration Guide

Based on testing with the TED Public API v3.

## API Overview

- **Base URL**: `https://api.ted.europa.eu/v3`
- **Authentication**: API Key in header (`apiKey: your-api-key`)
- **Primary Endpoint**: `POST /notices/search`
- **Documentation**: https://api.ted.europa.eu/swagger-ui/index.html

## Authentication

```bash
curl -H "apiKey: your-api-key" https://api.ted.europa.eu/v3/...
```

## Search Endpoint

### Endpoint: POST /v3/notices/search

**Request Format**:
```json
{
  "query": "expert search query string",
  "fields": ["field1", "field2", "..."]
}
```

### Query Language (Expert Search)

TED uses an expert search query language:

**Basic Queries**:
```
ND=*                     # All notices
PD>=20260401             # Published on or after April 1, 2026
CY=DE                    # Country = Germany
TI=infrastructure        # Title contains "infrastructure"
```

**Operators**:
- `=` - Equals
- `>=`, `<=` - Greater/less than or equal
- `AND`, `OR`, `NOT` - Logical operators
- `*` - Wildcard

**Example Queries**:
```json
{
  "query": "CY=DE AND PD>=20260401",
  "fields": ["ND", "notice-title", "publication-date", "classification-cpv"]
}
```

```json
{
  "query": "TI=construction AND (CY=DE OR CY=FR)",
  "fields": ["notice-identifier", "notice-title", "country-origin"]
}
```

### Available Fields

The API has hundreds of available fields. Key fields for tender notices:

**Core Fields**:
- `ND` - Notice document number
- `notice-identifier` - Official notice identifier
- `notice-title` - Title (multilingual)
- `publication-date` - Publication date
- `publication-number` - Publication number
- `notice-type` - Type of notice
- `country-origin` - Country
- `classification-cpv` - CPV codes

**Business/Organization**:
- `business-name` - Business name
- `business-identifier` - Business ID
- `buyer-name` - Buyer/contracting authority name
- `buyer-country` - Buyer country
- `organisation-name-buyer` - Organization name

**Procurement Details**:
- `description-lot` - Lot description
- `description-proc` - Procedure description
- `deadline` - Deadline
- `deadline-date-lot` - Lot deadline date
- `estimated-value-lot` - Estimated value per lot
- `total-value` - Total value

**Contract Details**:
- `contract-title` - Contract title
- `contract-nature` - Contract nature
- `contract-conclusion-date` - When contract was concluded

**Links**:
- `links` - Contains XML, PDF, HTML links to full notice

### Response Format

```json
{
  "notices": [
    {
      "ND": "119307-2016",
      "publication-number": "119307-2016",
      "notice-identifier": "...",
      "notice-title": {
        "eng": "Luxembourg-Luxembourg: EIB - Project management...",
        "fra": "Luxembourg-Luxembourg: BEI - Gestion de projet...",
        "deu": "Luxemburg-Luxemburg: EIB - Projektmanagement..."
      },
      "links": {
        "xml": {"MUL": "https://ted.europa.eu/en/notice/119307-2016/xml"},
        "pdf": {"ENG": "https://ted.europa.eu/en/notice/119307-2016/pdf"},
        "html": {"ENG": "https://ted.europa.eu/en/notice/-/detail/119307-2016"}
      }
    }
  ]
}
```

## Field Reference (Partial)

Due to extensive field list, here are categories:

### Identification & Basic Info
- `ND`, `notice-identifier`, `notice-title`, `notice-purpose`, `notice-type`, `notice-version`

### Publication & Dates
- `publication-date`, `publication-number`, `dispatch-date`, `issue-date`, `deadline`

### Classification
- `classification-cpv` (CPV codes)
- `additional-classification-lot`, `additional-classification-proc`

### Organizations
- `buyer-*` fields (buyer-name, buyer-city, buyer-country, etc.)
- `organisation-*` fields (organisation-name-buyer, organisation-country-buyer, etc.)
- `business-*` fields (business-name, business-identifier, etc.)

### Lots & Procedures
- `lot-*` fields (lot-included-proc, etc.)
- `description-lot`, `description-proc`
- `procedure-type`, `procedure-identifier`

### Values & Finances
- `estimated-value-*` (estimated-value-lot, estimated-value-proc)
- `total-value`, `framework-estimated-value-*`
- Value with currency: `*-cur` fields

### Contract Information
- `contract-*` fields (contract-title, contract-nature, contract-conclusion-date)

### Geographic
- `country-origin`, `place-of-performance-*`

### Links & Documents
- `links` (xml, pdf, html URLs)
- `document-*` fields

## Recommended Fields for TED Bot

```json
{
  "query": "your-expert-query",
  "fields": [
    // Core identification
    "ND",
    "notice-identifier",
    "publication-number",
    
    // Title & description
    "notice-title",
    "notice-type",
    "description-lot",
    "description-proc",
    
    // Dates
    "publication-date",
    "deadline",
    "deadline-date-lot",
    
    // Classification
    "classification-cpv",
    "country-origin",
    
    // Organizations
    "buyer-name",
    "buyer-country",
    "organisation-name-buyer",
    
    // Values
    "estimated-value-lot",
    "total-value",
    
    // Contract
    "contract-title",
    "contract-nature",
    "procedure-type",
    
    // Links
    "links"
  ]
}
```

## Example Usage

### Search for Recent IT Tenders in Germany

```bash
curl -X POST "https://api.ted.europa.eu/v3/notices/search" \
  -H "Content-Type: application/json" \
  -H "apiKey: your-api-key" \
  -d '{
    "query": "CY=DE AND classification-cpv=72*",
    "fields": [
      "ND",
      "notice-title",
      "publication-date",
      "buyer-name",
      "classification-cpv",
      "estimated-value-lot",
      "deadline-date-lot",
      "links"
    ]
  }'
```

### Search by Publication Date Range

```bash
curl -X POST "https://api.ted.europa.eu/v3/notices/search" \
  -H "Content-Type: application/json" \
  -H "apiKey: your-api-key" \
  -d '{
    "query": "PD>=20260401 AND PD<=20260430",
    "fields": ["ND", "notice-title", "publication-date", "country-origin"]
  }'
```

## Rate Limiting

- **Unknown**: Not documented in public API
- **Recommendation**: Implement exponential backoff
- **Best Practice**: Cache responses and don't poll excessively

## Error Handling

### Common Errors

**Field Not Supported**:
```json
{
  "message": "Parameter 'fields' contains unsupported value...",
  "error": {
    "type": "UNSUPPORTED_VALUE",
    "parameterName": "fields",
    "unsupportedValue": "INVALID_FIELD"
  }
}
```

**Query Syntax Error**:
```json
{
  "message": "Syntax error in expert query at line 1, col 3...",
  "error": {
    "type": "QUERY_SYNTAX_ERROR",
    "location": {
      "beginColumn": 3,
      "beginLine": 1
    }
  }
}
```

**Validation Error**:
```json
{
  "message": "Validation error",
  "error": [
    {
      "objectName": "publicExpertSearchRequestV1",
      "field": "fields",
      "message": "must not be empty"
    }
  ]
}
```

## Integration with TED Bot

### Python Client Example

```python
import requests
from typing import List, Dict, Optional

class TEDAPIClient:
    BASE_URL = "https://api.ted.europa.eu/v3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "apiKey": api_key
        })
    
    def search_notices(
        self, 
        query: str, 
        fields: List[str]
    ) -> Dict:
        """Search TED notices using expert query."""
        endpoint = f"{self.BASE_URL}/notices/search"
        
        payload = {
            "query": query,
            "fields": fields
        }
        
        try:
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Handle errors
            return {"error": str(e), "response": response.json() if response else None}
    
    def search_by_country(
        self,
        country_code: str,
        date_from: str = None,
        additional_query: str = ""
    ) -> Dict:
        """Search notices by country."""
        query_parts = [f"CY={country_code}"]
        
        if date_from:
            query_parts.append(f"PD>={date_from}")
        
        if additional_query:
            query_parts.append(additional_query)
        
        query = " AND ".join(query_parts)
        
        fields = [
            "ND",
            "notice-title",
            "publication-date",
            "classification-cpv",
            "buyer-name",
            "deadline-date-lot",
            "estimated-value-lot",
            "links"
        ]
        
        return self.search_notices(query, fields)

# Usage
client = TEDAPIClient(api_key="your-api-key")
results = client.search_by_country("DE", date_from="20260401")
```

## Best Practices

1. **Field Selection**: Only request fields you need to minimize response size
2. **Query Optimization**: Use specific queries to reduce result sets
3. **Error Handling**: Always handle API errors gracefully
4. **Caching**: Cache responses for repeated queries
5. **Retry Logic**: Implement exponential backoff for transient failures
6. **Logging**: Log all API interactions for debugging

## Limitations Discovered

1. **No Pagination Parameters**: API doesn't seem to support `pageSize` or `page` parameters
2. **Expert Query Required**: Must use expert query language, not simple text search
3. **Field Names**: Complex field naming (hyphenated, specific to TED schema)
4. **Multilingual Responses**: Titles and text fields returned in multiple languages
5. **Date Format**: Dates in YYYYMMDD format for queries
6. **No Full-Text Search**: Must use field-specific queries

## Recommendations for TED Bot

1. **Create Query Builder**: Helper class to build expert queries from natural language
2. **Field Mapping**: Map common user terms to TED field names
3. **Extract English Fields**: Filter multilingual responses to English (or user preference)
4. **Cache Field List**: Store valid field names to avoid API errors
5. **Batch Processing**: Fetch full XML/PDF for detailed analysis (via links)
6. **Query Templates**: Pre-build common query patterns

## Updated Architecture Implications

1. **TED Service Layer**: Need sophisticated query builder for expert search
2. **Response Parser**: Extract and normalize multilingual fields
3. **Full Notice Fetcher**: Use `links` field to fetch XML/PDF for detailed analysis
4. **Field Validator**: Validate requested fields before API call
5. **Smart Caching**: Cache by query hash to avoid duplicate API calls
