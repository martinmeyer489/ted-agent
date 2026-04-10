# TED API Expert Search Query Examples

This document contains tested and working query patterns for the TED API v3 Expert Search.

## API Documentation
- **Expert Search UI**: https://ted.europa.eu/en/expert-search
- **API Documentation**: https://ted.europa.eu/api/documentation/index.html
- **Search Endpoint**: `POST https://api.ted.europa.eu/v3/notices/search`

## Query Syntax Overview

All queries **MUST** include a `SORT BY` clause. The expert query language supports:
- Field operators: `=`, `>`, `>=`, `<`, `<=`
- Logical operators: `AND`, `OR`, `NOT`
- Parentheses for grouping: `(condition1 OR condition2) AND condition3`
- Text search with quotes: `TI="software development"`

## Common Search Fields

### Basic Fields (Short Codes)
- `FT` - Full Text (searches all text content)
- `TI` - Title (search in notice title only)
- `TD` - Text Description (full-text search in description field)
- `PD` - Publication Date (format: YYYYMMDD)
- `PC` - Main Classification (CPV code) - shorthand for `classification-cpv`
- `NC` - Nature of Contract (e.g., services, supplies, works) - shorthand for `contract-nature`
- `RC` - Region/Country of Performance (ISO3 code like DEU, FRA) - shorthand for `place-of-performance`
- `TV` - Total Value (numeric value in base currency)
- `TV_CUR` - Total Value Currency (e.g., EUR, USD, GBP)

### Full Field Names (Alternative to Short Codes)
- `classification-cpv` - CPV classification codes (same as `PC`)
- `contract-nature` - Main nature of the contract (same as `NC`)
- `place-of-performance` - Place of performance (same as `RC`)
- `total-value` - Total value (same as `TV`)
- `total-value-cur` - Currency (same as `TV_CUR`)
- `notice-type` - Type of notice (various types)
- `BT-02-notice` - Notice type using BT code

### Buyer/Authority Fields
- `buyer-name` - Name of contracting authority
- `buyer-city` - City of contracting authority
- `buyer-country` - Country code of contracting authority

### Notice Details
- `notice-identifier` - Unique notice ID
- `publication-date` - Publication date
- `deadline-receipt-tender-date-lot` - Tender deadline
- `estimated-value-lot` - Estimated contract value
- `description-lot` - Lot description
- `description-proc` - Procedure description
- `place-of-performance-country-lot` - Where work will be performed

## Working Query Examples

### 1. Simple Title Search
```json
{
  "query": "TI=software SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns notices with "software" in title

### 2. Title with Phrase Search
```json
{
  "query": "TI=\"IT services\" SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns notices with exact phrase "IT services" in title

### 3. CPV Code Search
```json
{
  "query": "classification-cpv=72000000 SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns IT services tenders (CPV 72000000)

### 4. Combined Title + CPV
```json
{
  "query": "TI=software AND classification-cpv=72000000 SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns IT tenders with "software" in title

### 5. Date Range Search
```json
{
  "query": "PD>=20260401 AND PD<=20260410 SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns notices published between April 1-10, 2026

### 6. Multiple CPV Codes (OR)
```json
{
  "query": "classification-cpv=45000000 OR classification-cpv=72000000 SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns construction OR IT services tenders

### 7. Exclusion with NOT
```json
{
  "query": "TI=services AND NOT TI=construction SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns service tenders excluding construction

### 8. Complex Query with Grouping
```json
{
  "query": "(TI=software OR TI=development) AND classification-cpv=72000000 SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns IT tenders with "software" OR "development" in title

### 9. Full Text Search (FT)
```json
{
  "query": "FT=software SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Searches "software" across all text content (title, description, etc.)

### 10. Using Short Code PC (Main Classification)
```json
{
  "query": "PC=72000000 SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Same as `classification-cpv=72000000` but shorter

### 11. Contract Nature Filter (NC)
```json
{
  "query": "NC=services SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns only service contracts (not supplies or works)

### 12. Place of Performance (RC) - Single Country
```json
{
  "query": "RC=DEU SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns tenders for work in Germany (ISO3 code: DEU)

### 13. Multiple Countries with OR
```json
{
  "query": "RC=FRA OR RC=ESP SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns tenders in France OR Spain

### 14. Total Value Greater Than (TV >)
```json
{
  "query": "TV>100000 SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns tenders with value over 100,000

### 15. Total Value Range (TV with AND)
```json
{
  "query": "TV>=50000 AND TV<=500000 SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns tenders valued between 50,000 and 500,000

### 16. Currency Filter (TV_CUR)
```json
{
  "query": "TV_CUR=EUR SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns tenders denominated in EUR

### 17. IN Operator - Multiple Values
```json
{
  "query": "PC IN (72000000, 73000000, 80000000) SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns tenders matching any of the listed CPV codes

### 18. NOT IN Operator - Exclusion List
```json
{
  "query": "PC NOT IN (45000000, 90000000) SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns tenders excluding construction and environmental services

### 19. Wildcard Search (*)
```json
{
  "query": "TI=soft* SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Returns tenders with title containing "soft", "software", "softwares", etc.

### 20. Complex Multi-Field Query
```json
{
  "query": "FT=software AND PC=72000000 AND TV>50000 AND RC IN (DEU, FRA, ESP) SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ IT software tenders over 50k EUR in Germany, France, or Spain

### 21. Realistic Business Query
```json
{
  "query": "FT=cloud AND NC=services AND TV_CUR=EUR AND PD>=20260401 SORT BY publication-date DESC",
  "fields": ["publication-date"],
  "page": 1,
  "limit": 10,
  "scope": "ACTIVE"
}
```
**Result**: ✅ Cloud services tenders in EUR published since April 2026

## Important Notes

### Mandatory Elements
1. **SORT BY clause is REQUIRED** - All queries must end with `SORT BY field-name ASC|DESC`
2. **Fields parameter is REQUIRED** - Must specify at least one field to return
3. **Scope parameter recommended** - Use `"ACTIVE"` for current tenders

### Supported Operators

#### Comparison Operators
- `=` - Equals (exact match or contains for text)
- `>` - Greater than (numeric/date fields)
- `>=` - Greater than or equal to
- `<` - Less than (numeric/date fields)
- `<=` - Less than or equal to

#### Logical Operators
- `AND` - Both conditions must be true
- `OR` - At least one condition must be true
- `NOT` - Negation (excludes matching results)
- `IN (value1, value2, ...)` - Matches any value in the list
- `NOT IN (value1, value2, ...)` - Excludes all values in the list

#### Text Operators
- Wildcard `*` - Use at end of term for prefix matching (e.g., `soft*` matches "soft", "software", "softwares")
- Fuzzy/Proximity `~` - Use after term for fuzzy matching (e.g., `software~` finds similar terms, `"software engineer"~5` allows words within 5 positions)
- Quoted phrases `"exact phrase"` - Exact phrase matching
- Case-insensitive - All text searches are case-insensitive

### Operator Precedence
1. Parentheses `()` - Highest priority, use for grouping
2. `NOT` - Negation
3. `AND` - Conjunction
4. `OR` - Disjunction (lowest priority)

**Example**: `A OR B AND C` is interpreted as `A OR (B AND C)`  
**Better**: Use explicit parentheses: `(A OR B) AND C` or `A OR (B AND C)`

### Country Codes (ISO 3166-1 alpha-3)
Common codes for RC (place-of-performance):
- `DEU` - Germany
- `FRA` - France
- `ESP` - Spain
- `ITA` - Italy
- `POL` - Poland
- `NLD` - Netherlands
- `BEL` - Belgium
- `AUT` - Austria
- `SWE` - Sweden
- `DNK` - Denmark
- `FIN` - Finland
- `PRT` - Portugal
- `GRC` - Greece
- `CZE` - Czech Republic
- `HUN` - Hungary
- `ROU` - Romania
- `BGR` - Bulgaria
- `HRV` - Croatia
- `IRL` - Ireland
- `LTU` - Lithuania
- `LVA` - Latvia
- `EST` - Estonia
- `SVK` - Slovakia
- `SVN` - Slovenia
- `LUX` - Luxembourg
- `MLT` - Malta
- `CYP` - Cyprus

### Contract Nature Values (NC)
- `services` - Service contracts
- `supplies` - Supply/goods contracts
- `works` - Construction/works contracts

### Field Behavior
- **Fields are restrictive**: Only requested fields are returned in `_source`
- **Metadata always included**: `publication-number`, `links`, and `publication-date` always present
- **Test fields first**: Some field names may not be supported despite documentation

### Common CPV Codes
- `45000000` - Construction work
- `71000000` - Architectural, engineering services
- `72000000` - IT services (consulting, software, Internet, support)
- `73000000` - Research and development
- `75000000` - Administration, defence, social security
- `80000000` - Education and training
- `85000000` - Health and social work
- `90000000` - Sewage, refuse, cleaning, environmental

## Pagination

```json
{
  "page": 1,
  "limit": 50,
  "paginationMode": "PAGE_NUMBER"
}
```
- Maximum `limit`: 50 results per page
- Page numbering starts at 1
- Use `paginationMode: "PAGE_NUMBER"` for standard pagination

## Scope Options

- `"ACTIVE"` - Only active/current tender notices
- `"ALL"` - All notices including expired
- `"ARCHIVED"` - Only archived notices

## Testing Queries

Use curl to test queries:

```bash
curl -X POST "https://api.ted.europa.eu/v3/notices/search" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "query": "YOUR_QUERY_HERE SORT BY publication-date DESC",
    "fields": ["publication-date"],
    "page": 1,
    "limit": 5,
    "scope": "ACTIVE"
  }'
```

## Query Builder Patterns

When building queries programmatically:

1. **Start with base conditions**: Title, CPV codes, keywords
2. **Add filters**: Date ranges, countries, value thresholds
3. **Combine with AND/OR**: Group conditions logically
4. **Always add SORT BY**: `SORT BY publication-date DESC` for most recent first
5. **Request minimal fields initially**: Test with `["publication-date"]` first
6. **Expand fields as needed**: Add specific fields once query works

### Query Optimization Tips

1. **Use short codes when possible**: `PC` instead of `classification-cpv`, `RC` instead of `place-of-performance`
2. **Prefer FT over multiple TI/TD**: `FT=keyword` searches everywhere at once
3. **Use IN for multiple values**: `PC IN (72000000, 73000000)` is cleaner than `PC=72000000 OR PC=73000000`
4. **Filter early with specific fields**: `PC=72000000 AND TV>100000` is more efficient than just `FT=software`
5. **Date ranges for recent tenders**: `PD>=20260401` limits to recent publications
6. **Combine country codes with OR**: `RC=DEU OR RC=FRA OR RC=ESP` for multi-country
7. **Use wildcards sparingly**: `TI=soft*` works but can be slower than exact matches

### Common Query Patterns

**Pattern 1: Industry-Specific Search**
```
PC=[cpv_code] AND NC=[contract_type] AND RC=[country] SORT BY publication-date DESC
```

**Pattern 2: Value-Based Search**
```
FT=[keyword] AND TV>=[min_value] AND TV<=[max_value] AND TV_CUR=EUR SORT BY total-value DESC
```

**Pattern 3: Recent Publications**
```
FT=[keyword] AND PD>=[date] SORT BY publication-date DESC
```

**Pattern 4: Multi-Criteria Search**
```
(FT=[keyword1] OR FT=[keyword2]) AND PC IN ([cpv1], [cpv2]) AND RC IN ([country1], [country2]) SORT BY publication-date DESC
```

## Troubleshooting

### Query Returns 0 Results
- Check SORT BY clause is present
- Verify field names match API documentation
- Try simpler query first (e.g., just `TI=test`)
- Check date formats (YYYYMMDD)
- Verify country codes are ISO3 (DEU not DE)
- Check if values are in correct format (numeric for TV, etc.)

### Fields Return null
- Field name may not be supported
- Field might not exist for that notice type
- Request the field in `fields` array

### HTTP 400 Errors
- Missing SORT BY clause (most common)
- Invalid field name in `fields` parameter
- Syntax error in query (unmatched quotes, parentheses)
- Empty `fields` parameter (must have at least one field)

### Known Limitations

**❌ These patterns do NOT work:**

1. **CPV Code Ranges**
   ```
   PC>=72000000 AND PC<73000000  ❌ Does not work
   ```
   Use `IN` operator instead: `PC IN (72000000, 72100000, ...)`

2. **Notice Type Filtering** (often unreliable)
   ```
   notice-type=contract-notice  ❌ May return 0 results
   BT-02-notice=contract-notice  ❌ May return 0 results
   ```
   Filter by other criteria instead (PC, NC, TV)

3. **Buyer Country Direct Filter** (buyer-country field)
   ```
   buyer-country=DE  ❌ May not work reliably
   ```
   Use `RC` (place of performance) instead

4. **Partial CPV Code Matching**
   ```
   PC=720*  ❌ Wildcards don't work with PC
   ```
   List specific codes with `IN` operator

5. **Text Description Field** (TD)
   ```
   TD=software  ❌ Often returns 0 results
   ```
   Use `FT` (full text) instead: `FT=software`

**✅ Use these alternatives:**
- CPV ranges → `PC IN (code1, code2, code3)`
- Notice type → Filter by `NC` and `PC` instead
- Buyer country → Use `RC` for place of performance
- Partial CPV → List all relevant full codes
- Description search → Use `FT` for full-text search

## Testing Queries

Use curl to test queries:

```bash
curl -X POST "https://api.ted.europa.eu/v3/notices/search" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "query": "YOUR_QUERY_HERE SORT BY publication-date DESC",
    "fields": ["publication-date"],
    "page": 1,
    "limit": 5,
    "scope": "ACTIVE"
  }'
```

### Quick Test Examples

**Test basic connectivity:**
```bash
curl -X POST "https://api.ted.europa.eu/v3/notices/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "FT=software SORT BY publication-date DESC", "fields": ["publication-date"], "page": 1, "limit": 3, "scope": "ACTIVE"}' | jq '.notices | length'
```

**Test CPV codes:**
```bash
curl -X POST "https://api.ted.europa.eu/v3/notices/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "PC=72000000 SORT BY publication-date DESC", "fields": ["publication-date"], "page": 1, "limit": 3, "scope": "ACTIVE"}' | jq '.notices | length'
```

**Test value filtering:**
```bash
curl -X POST "https://api.ted.europa.eu/v3/notices/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "TV>100000 AND TV_CUR=EUR SORT BY publication-date DESC", "fields": ["publication-date"], "page": 1, "limit": 3, "scope": "ACTIVE"}' | jq '.notices | length'
```

## Summary of Tested Operators

| Operator | Status | Example | Use Case |
|----------|--------|---------|----------|
| `=` | ✅ Works | `TI=software` | Exact/contains match |
| `>`, `>=`, `<`, `<=` | ✅ Works | `TV>100000`, `PD>=20260401` | Numeric/date ranges |
| `AND` | ✅ Works | `TI=software AND PC=72000000` | Combine conditions |
| `OR` | ✅ Works | `RC=DEU OR RC=FRA` | Alternative values |
| `NOT` | ✅ Works | `TI=services AND NOT TI=construction` | Exclude terms |
| `IN (...)` | ✅ Works | `PC IN (72000000, 73000000)` | Match any in list |
| `NOT IN (...)` | ✅ Works | `PC NOT IN (45000000, 90000000)` | Exclude list |
| `*` (wildcard) | ✅ Works | `TI=soft*` | Prefix matching |
| `~` (fuzzy) | ✅ Works | `FT~software`, `"software engineer"~5` | Fuzzy/proximity search |
| `FT` | ✅ Works | `FT=software` | Full text search |
| `PC` | ✅ Works | `PC=72000000` | CPV classification |
| `RC` | ✅ Works | `RC=DEU` | Place of performance |
| `NC` | ✅ Works | `NC=services` | Contract nature |
| `TV` | ✅ Works | `TV>50000` | Total value |
| `TV_CUR` | ✅ Works | `TV_CUR=EUR` | Currency filter |
| `PD` | ✅ Works | `PD>=20260401` | Publication date |
| `notice-type` | ⚠️ Unreliable | Returns 0 often | Avoid |
| `buyer-country` | ⚠️ Unreliable | Use `RC` instead | Unreliable |
| `TD` | ⚠️ Unreliable | Use `FT` instead | Unreliable |
| CPV ranges | ❌ Not supported | Use `IN` with list | N/A |

## Field Selection Guide

### Reliable Fields (Always Request These)
```json
"fields": [
  "publication-date",
  "notice-identifier", 
  "publication-number"
]
```

### Additional Working Fields
- **Buyer Info**: `buyer-name`, `buyer-city`, `buyer-country`
- **Contract**: `contract-nature`, `classification-cpv`
- **Location**: `place-of-performance-country-lot`
- **Descriptions**: `notice-title`, `description-lot`, `description-proc`
- **Deadlines**: `deadline-receipt-tender-date-lot`
- **Value**: `estimated-value-lot`, `total-value`, `total-value-cur`

### Note on Fields
- Only fields in your `fields` array are returned in `_source`
- `publication-number`, `links`, `publication-date` always included in top-level response
- Many field names don't work despite API documentation - test before relying on them
- Use minimal fields for fastest queries, add more as needed

## Quick Reference: Best Practices

### For General Searches
Use `FT` (full text) - searches across all content
```json
{"query": "FT=cloud AND TV>50000 SORT BY publication-date DESC"}
```

### For Specific Industries  
Combine `PC` (CPV) with `NC` (nature) and `RC` (region)
```json
{"query": "PC=72000000 AND NC=services AND RC=DEU SORT BY publication-date DESC"}
```

### For Value-Based Searches
Use `TV` with `TV_CUR` for currency-specific searches
```json
{"query": "TV>=100000 AND TV<=1000000 AND TV_CUR=EUR SORT BY total-value DESC"}
```

### For Recent Tenders
Filter by `PD` (publication date) for time-bound searches
```json
{"query": "PC=72000000 AND PD>=20260401 SORT BY publication-date DESC"}
```

## Last Updated
2026-04-10 - Comprehensive testing of all operators (FT, PC, RC, NC, TV, TV_CUR, IN, NOT IN, wildcards, ranges). Added 21 working query examples, country codes, troubleshooting guide, and known limitations.
