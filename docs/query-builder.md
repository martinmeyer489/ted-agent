# TED API Query Builder - Implementation Guide

## Overview

The TED API uses an "Expert Search" query language that requires specific syntax. The query builder will translate natural language user queries into valid TED expert search queries.

## Query Language Syntax

### Basic Structure
```
FIELD=VALUE              # Exact match
FIELD>=VALUE             # Greater than or equal
FIELD<=VALUE             # Less than or equal
QUERY1 AND QUERY2        # Logical AND
QUERY1 OR QUERY2         # Logical OR
NOT QUERY               # Logical NOT
FIELD=value*            # Wildcard
```

### Common Fields

| User Intent | TED Field | Example Query |
|-------------|-----------|---------------|
| Country | `CY` | `CY=DE` |
| Publication date | `PD` | `PD>=20260401` |
| Title contains | `TI` | `TI=infrastructure` |
| CPV code | `classification-cpv` | `classification-cpv=72*` |
| Buyer/Authority | `buyer-name` | `buyer-name=ministry` |
| Notice type | `notice-type` | `notice-type=contract` |
| Deadline | `deadline` or `deadline-date-lot` | `deadline>=20260501` |

## Implementation

### Query Builder Class

```python
from datetime import datetime
from typing import List, Dict, Optional
import re

class TEDQueryBuilder:
    """Build TED Expert Search queries from natural language."""
    
    # Field mappings
    COUNTRY_CODES = {
        "germany": "DE", "france": "FR", "spain": "ES",
        "italy": "IT", "poland": "PL", # ... add all EU countries
    }
    
    CPV_CATEGORIES = {
        "it": "72*", "construction": "45*", "services": "71*",
        "software": "48*", "consulting": "79*",
        # ... add common categories
    }
    
    def __init__(self):
        self.query_parts = []
    
    def country(self, country: str) -> 'TEDQueryBuilder':
        """Add country filter."""
        code = self.COUNTRY_CODES.get(country.lower())
        if not code:
            # Try as direct code
            code = country.upper()
        self.query_parts.append(f"CY={code}")
        return self
    
    def countries(self, countries: List[str]) -> 'TEDQueryBuilder':
        """Add multiple country filter."""
        country_queries = []
        for country in countries:
            code = self.COUNTRY_CODES.get(country.lower(), country.upper())
            country_queries.append(f"CY={code}")
        
        if country_queries:
            self.query_parts.append(f"({' OR '.join(country_queries)})")
        return self
    
    def published_after(self, date: str) -> 'TEDQueryBuilder':
        """Add publication date filter (>= date)."""
        # Convert from various formats to YYYYMMDD
        clean_date = self._normalize_date(date)
        self.query_parts.append(f"PD>={clean_date}")
        return self
    
    def published_before(self, date: str) -> 'TEDQueryBuilder':
        """Add publication date filter (<= date)."""
        clean_date = self._normalize_date(date)
        self.query_parts.append(f"PD<={clean_date}")
        return self
    
    def published_between(self, start: str, end: str) -> 'TEDQueryBuilder':
        """Add publication date range."""
        start_date = self._normalize_date(start)
        end_date = self._normalize_date(end)
        self.query_parts.append(f"(PD>={start_date} AND PD<={end_date})")
        return self
    
    def deadline_after(self, date: str) -> 'TEDQueryBuilder':
        """Add deadline filter."""
        clean_date = self._normalize_date(date)
        self.query_parts.append(f"deadline>={clean_date}")
        return self
    
    def cpv_code(self, cpv: str) -> 'TEDQueryBuilder':
        """Add CPV code filter."""
        # Check if it's a category keyword
        if cpv.lower() in self.CPV_CATEGORIES:
            cpv = self.CPV_CATEGORIES[cpv.lower()]
        
        self.query_parts.append(f"classification-cpv={cpv}")
        return self
    
    def title_contains(self, text: str) -> 'TEDQueryBuilder':
        """Add title search."""
        # Escape special characters
        text = self._escape_query_text(text)
        self.query_parts.append(f"TI={text}")
        return self
    
    def buyer_name(self, name: str) -> 'TEDQueryBuilder':
        """Add buyer/contracting authority filter."""
        name = self._escape_query_text(name)
        self.query_parts.append(f"buyer-name={name}")
        return self
    
    def min_value(self, value: float, currency: str = "EUR") -> 'TEDQueryBuilder':
        """Add minimum estimated value filter."""
        # Note: May need to query both lot and total values
        self.query_parts.append(f"estimated-value-lot>={value}")
        return self
    
    def raw_query(self, query: str) -> 'TEDQueryBuilder':
        """Add raw expert search query."""
        self.query_parts.append(query)
        return self
    
    def build(self) -> str:
        """Build final query string."""
        if not self.query_parts:
            return "ND=*"  # Default: all notices
        
        return " AND ".join(self.query_parts)
    
    def reset(self) -> 'TEDQueryBuilder':
        """Reset builder."""
        self.query_parts = []
        return self
    
    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Convert date to YYYYMMDD format."""
        # Try various formats
        formats = [
            "%Y-%m-%d",     # 2026-04-01
            "%Y/%m/%d",     # 2026/04/01
            "%d-%m-%Y",     # 01-04-2026
            "%d/%m/%Y",     # 01/04/2026
            "%Y%m%d",       # 20260401
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y%m%d")
            except ValueError:
                continue
        
        # If all fail, try to extract YYYYMMDD if already in that format
        if re.match(r'^\d{8}$', date_str):
            return date_str
        
        raise ValueError(f"Invalid date format: {date_str}")
    
    @staticmethod
    def _escape_query_text(text: str) -> str:
        """Escape special characters in query text."""
        # TED API may require specific escaping - adjust as needed
        # For now, just handle basic cases
        text = text.replace('"', '\\"')
        
        # If contains spaces or special chars, quote it
        if ' ' in text or any(c in text for c in ['(', ')', '&', '|']):
            return f'"{text}"'
        
        return text


# Natural Language Query Interpreter

class NaturalLanguageQueryParser:
    """Parse natural language queries to TED Expert Search."""
    
    def __init__(self):
        self.builder = TEDQueryBuilder()
    
    def parse(self, user_query: str) -> str:
        """Parse natural language query into expert search query."""
        user_query_lower = user_query.lower()
        
        # Extract countries
        countries = self._extract_countries(user_query_lower)
        if countries:
            self.builder.countries(countries)
        
        # Extract date ranges
        dates = self._extract_dates(user_query_lower, user_query)
        if dates.get('after'):
            self.builder.published_after(dates['after'])
        if dates.get('before'):
            self.builder.published_before(dates['before'])
        
        # Extract CPV categories
        cpv = self._extract_cpv(user_query_lower)
        if cpv:
            self.builder.cpv_code(cpv)
        
        # Extract value filters
        min_value = self._extract_min_value(user_query_lower)
        if min_value:
            self.builder.min_value(min_value)
        
        # Extract keywords for title search
        keywords = self._extract_keywords(user_query_lower)
        if keywords:
            self.builder.title_contains(keywords)
        
        return self.builder.build()
    
    def _extract_countries(self, query: str) -> List[str]:
        """Extract country references from query."""
        countries = []
        
        # Check for country names
        for country_name, code in TEDQueryBuilder.COUNTRY_CODES.items():
            if country_name in query:
                countries.append(code)
        
        # Check for direct country codes (DE, FR, etc.)
        country_code_pattern = r'\b([A-Z]{2})\b'
        codes = re.findall(country_code_pattern, query.upper())
        countries.extend(codes)
        
        return list(set(countries))
    
    def _extract_dates(self, query_lower: str, original_query: str) -> Dict:
        """Extract date references."""
        dates = {}
        
        # Look for date patterns
        date_pattern = r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{8}'
        found_dates = re.findall(date_pattern, original_query)
        
        # Look for temporal keywords
        if 'after' in query_lower or 'since' in query_lower or 'from' in query_lower:
            if found_dates:
                dates['after'] = found_dates[0]
        
        if 'before' in query_lower or 'until' in query_lower or 'to' in query_lower:
            if len(found_dates) > 1:
                dates['before'] = found_dates[-1]
            elif found_dates and 'before' in query_lower:
                dates['before'] = found_dates[0]
        
        # Recent/latest -> last 7 days
        if 'recent' in query_lower or 'latest' in query_lower:
            from datetime import timedelta
            dates['after'] = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Today
        if 'today' in query_lower:
            dates['after'] = datetime.now().strftime("%Y-%m-%d")
        
        return dates
    
    def _extract_cpv(self, query: str) -> Optional[str]:
        """Extract CPV category keywords."""
        for keyword, cpv_code in TEDQueryBuilder.CPV_CATEGORIES.items():
            if keyword in query:
                return cpv_code
        return None
    
    def _extract_min_value(self, query: str) -> Optional[float]:
        """Extract minimum value from query."""
        # Look for patterns like "above 1M", "over 500k", "> 100000"
        patterns = [
            r'above\s+(\d+\.?\d*)\s*([mk]?)',
            r'over\s+(\d+\.?\d*)\s*([mk]?)',
            r'>\s*(\d+\.?\d*)\s*([mk]?)',
            r'minimum\s+(\d+\.?\d*)\s*([mk]?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                value = float(match.group(1))
                multiplier = match.group(2).lower() if len(match.groups()) > 1 else ''
                
                if multiplier == 'm':
                    value *= 1_000_000
                elif multiplier == 'k':
                    value *= 1_000
                
                return value
        
        return None
    
    def _extract_keywords(self, query: str) -> Optional[str]:
        """Extract search keywords from query."""
        # Remove common words and extract meaningful keywords
        stop_words = {
            'find', 'search', 'show', 'get', 'tenders', 'tender', 'notice',
            'notices', 'in', 'from', 'for', 'the', 'a', 'an', 'above', 'below',
            'after', 'before', 'with', 'and', 'or'
        }
        
        words = query.split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Skip if keywords are likely already handled (countries, dates, etc.)
        if keywords and not all(w.isdigit() or len(w) == 2 or w in ['eur', 'usd'] for w in keywords):
            return ' '.join(keywords[:5])  # Limit to 5 keywords
        
        return None


# Usage Examples

def example_usage():
    """Examples of using the query builder."""
    
    # Example 1: Programmatic building
    builder = TEDQueryBuilder()
    query = (builder
             .countries(['DE', 'FR'])
             .published_after('2026-04-01')
             .cpv_code('72*')  # IT services
             .min_value(100000)
             .build())
    
    print(f"Query 1: {query}")
    # Output: (CY=DE OR CY=FR) AND PD>=20260401 AND classification-cpv=72* AND estimated-value-lot>=100000
    
    # Example 2: Natural language parsing
    parser = NaturalLanguageQueryParser()
    
    user_input = "Find IT tenders in Germany published after 2026-04-01 above 1M EUR"
    query = parser.parse(user_input)
    
    print(f"Query 2: {query}")
    
    # Example 3: Simple query
    builder2 = TEDQueryBuilder()
    query3 = builder2.country('DE').title_contains('construction').build()
    
    print(f"Query 3: {query3}")
    # Output: CY=DE AND TI=construction


if __name__ == "__main__":
    example_usage()
```

## Integration with Agno Agents

The query builder should be used by the Search Agent:

```python
from agno import tool

@tool
def search_tenders(
    user_query: str,
    countries: List[str] = None,
    cpv_codes: List[str] = None,
    date_from: str = None,
    min_value: float = None
) -> List[Dict]:
    """
    Search TED tenders based on user criteria.
    
    Args:
        user_query: Natural language query or specific search terms
        countries: ISO country codes (e.g., ["DE", "FR"])
        cpv_codes: CPV classification codes
        date_from: Publication date (YYYY-MM-DD)
        min_value: Minimum tender value
    
    Returns:
        List of matching tenders
    """
    # Build query
    builder = TEDQueryBuilder()
    
    if countries:
        builder.countries(countries)
    
    if cpv_codes:
        for cpv in cpv_codes:
            builder.cpv_code(cpv)
    
    if date_from:
        builder.published_after(date_from)
    
    if min_value:
        builder.min_value(min_value)
    
    # If no structured params, try parsing user_query
    if not any([countries, cpv_codes, date_from, min_value]):
        parser = NaturalLanguageQueryParser()
        expert_query = parser.parse(user_query)
    else:
        expert_query = builder.build()
    
    # Call TED API
    ted_client = get_ted_client()
    
    fields = [
        "ND",
        "notice-title",
        "notice-type",
        "publication-date",
        "classification-cpv",
        "country-origin",
        "buyer-name",
        "deadline-date-lot",
        "estimated-value-lot",
        "description-lot",
        "links"
    ]
    
    response = ted_client.search_notices(expert_query, fields)
    
    # Parse and normalize response
    notices = parse_ted_response(response)
    
    return notices
```

## Testing

```python
import pytest

def test_country_filter():
    builder = TEDQueryBuilder()
    query = builder.country("DE").build()
    assert query == "CY=DE"

def test_multiple_countries():
    builder = TEDQueryBuilder()
    query = builder.countries(["DE", "FR", "IT"]).build()
    assert "(CY=DE OR CY=FR OR CY=IT)" in query

def test_date_range():
    builder = TEDQueryBuilder()
    query = builder.published_between("2026-04-01", "2026-04-30").build()
    assert "PD>=20260401" in query
    assert "PD<=20260430" in query

def test_natural_language():
    parser = NaturalLanguageQueryParser()
    query = parser.parse("Find construction tenders in Germany above 500k EUR")
    assert "CY=DE" in query
    assert "classification-cpv=45*" in query or "TI=construction" in query

def test_cpv_code():
    builder = TEDQueryBuilder()
    query = builder.cpv_code("IT").build()
    assert "classification-cpv=72*" in query
```

## Future Enhancements

1. **Fuzzy Matching**: Handle misspellings in country names
2. **Smart Date Parsing**: Handle "next week", "Q1 2026", etc.
3. **Value Currency Conversion**: Handle USD, GBP, etc.
4. **Query Optimization**: Combine overlapping filters
5. **Query Validation**: Validate generated queries before API call
6. **Template Library**: Pre-built queries for common use cases
7. **Learning System**: Improve parsing based on user feedback
