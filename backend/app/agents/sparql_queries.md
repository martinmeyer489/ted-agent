# TED SPARQL Queries Documentation

This document contains example SPARQL queries for the TED Open Data Service and guidance on when to use SPARQL vs the REST API.

## 🔗 SPARQL Endpoint

- **URL**: https://publications.europa.eu/webapi/rdf/sparql
- **Web Interface**: https://data.ted.europa.eu (with built-in SPARQL editor)
- **Documentation**: https://github.com/OP-TED/ted-open-data

**✅ Status**: The endpoint is operational and contains TED Open Data! You can query EU public procurement notices directly.

## 📊 When to Use SPARQL vs REST API

### Use REST API (`search_ted_tenders`) for:
- ✅ Simple keyword searches
- ✅ Filtering by country or CPV code
- ✅ Browsing recent notices
- ✅ Quick lookups
- ✅ User-friendly formatted results

### Use SPARQL (`query_ted_sparql`) for:
- ✅ Statistical analysis and aggregations
- ✅ Winner and award amount queries
- ✅ Complex filters and JOINs
- ✅ Historical data analysis
- ✅ Relationships between organizations
- ✅ Custom analytics (TOP N, GROUP BY, SUM, AVG)

## 🔤 Common Prefixes

```sparql
PREFIX adms: <http://www.w3.org/ns/adms#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX epo: <http://data.europa.eu/a4g/ontology#>
PREFIX m8g: <http://data.europa.eu/m8g/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
```

## 📋 Example Queries

### 1. Winners Published on a Specific Date

**Use Case**: Find all winning tenderers and their awarded amounts for a specific publication date.

```sparql
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX epo: <http://data.europa.eu/a4g/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?publicationNumber ?winnerLegalName ?amount ?currency

WHERE {
  # Filter by publication date
  FILTER (?publicationDate = "2024-11-04"^^xsd:date)
  # Only EUR amounts
  FILTER (?currencyUri = <http://publications.europa.eu/resource/authority/currency/EUR>)
  # Only first-ranked (winning) tenders
  FILTER (?rank = 1)
  # Only tenders with "selected as winner" status
  FILTER (?awardStatusUri = <http://publications.europa.eu/resource/authority/winner-selection-status/selec-w>)

  # Traverse from notice through award decision to tender and winner
  ?noticeUri a epo:Notice ;
      epo:hasPublicationDate ?publicationDate ;
      epo:hasNoticePublicationNumber ?publicationNumber ;
      epo:announcesAwardDecision [
          a epo:AwardDecision ;
          epo:comprisesAwardOutcome [
              a epo:LotAwardOutcome ;
              epo:hasAwardStatus ?awardStatusUri ;
              epo:concernsLot ?lotUri ;
              epo:comprisesTenderAwardOutcome [
                  a epo:TenderAwardOutcome ;
                  epo:hasAwardRank ?rank ;
                  epo:concernsTender [
                      a epo:Tender ;
                      epo:isSubmitedBy [
                          a epo:Tenderer ;
                          epo:playedBy ?winnerUri
                      ] ;
                      epo:hasFinancialOfferValue [
                          a epo:MonetaryValue ;
                          epo:hasAmountValue ?amount ;
                          epo:hasCurrency ?currencyUri
                      ]
                  ]
              ]
          ]
      ] .

  ?winnerUri epo:hasLegalName ?winnerLegalName .
  ?currencyUri dc:identifier ?currency .
}
ORDER BY DESC(?amount)
```

### 2. Awarded Amounts for a Specific Procedure

**Use Case**: Get all tenders, winners, and amounts for a specific procurement procedure.

```sparql
PREFIX adms: <http://www.w3.org/ns/adms#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX epo: <http://data.europa.eu/a4g/ontology#>
PREFIX m8g: <http://data.europa.eu/m8g/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?procedureIdentifier ?publicationDate ?publicationNumber ?tenderIdentifier ?tendererLegalName ?offerAmountValue ?currency ?lotGroupIdentifier ?lotIdentifier

WHERE {
  # Change this to the procedure you want to look up
  VALUES (?procedureIdentifier) { ("d4f39891-4114-4199-829b-57437df27872") }

  GRAPH ?g {
    # Get the procedure by its identifier
    ?procedure a epo:Procedure ;
               adms:identifier / skos:notation ?procedureIdentifier .

    # Get notice and link to procedure
    ?notice a epo:Notice ;
            epo:hasPublicationDate ?publicationDate ;
            epo:hasNoticePublicationNumber ?publicationNumber ;
            epo:refersToProcedure ?procedure .

    # Get tender details: identifier, tenderer name, and financial offer
    ?tender a epo:Tender ;
            adms:identifier / skos:notation ?tenderIdentifier ;
            epo:isSubmitedBy ?tenderer ;
            epo:hasFinancialOfferValue ?offerValue .

    ?offerValue epo:hasAmountValue ?offerAmountValue ;
                epo:hasCurrency ?currencyUri .

    ?tenderer epo:playedBy / epo:hasLegalName ?tendererLegalName .

    # Optionally get the lot the tender was submitted for
    OPTIONAL {
      ?tender epo:isSubmittedForLot ?lot .
      OPTIONAL { ?lot adms:identifier / skos:notation ?lotIdentifier . }
    }

    # Optionally get the lot group
    OPTIONAL {
      ?tender epo:isSubjectToGrouping ?lotGroup .
      ?lotGroup epo:setsGroupingContextForLot ?lot .
      OPTIONAL { ?lotGroup adms:identifier / skos:notation ?lotGroupIdentifier . }
      OPTIONAL { ?lot adms:identifier / skos:notation ?lotIdentifier . }
    }
  }

  # Resolve currency label
  ?currencyUri skos:prefLabel ?currency .
  FILTER (lang(?currency) = "en")
}
ORDER BY ?publicationNumber ?lotGroupIdentifier ?lotIdentifier
```

### 3. Top 10 Biggest Contracts (Example)

**Use Case**: Find the 10 largest awarded contracts.

```sparql
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX epo: <http://data.europa.eu/a4g/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?publicationNumber ?winnerLegalName ?amount ?currency ?publicationDate

WHERE {
  ?noticeUri a epo:Notice ;
      epo:hasPublicationDate ?publicationDate ;
      epo:hasNoticePublicationNumber ?publicationNumber ;
      epo:announcesAwardDecision [
          a epo:AwardDecision ;
          epo:comprisesAwardOutcome [
              a epo:LotAwardOutcome ;
              epo:comprisesTenderAwardOutcome [
                  a epo:TenderAwardOutcome ;
                  epo:hasAwardRank 1 ;
                  epo:concernsTender [
                      a epo:Tender ;
                      epo:isSubmitedBy [
                          a epo:Tenderer ;
                          epo:playedBy ?winnerUri
                      ] ;
                      epo:hasFinancialOfferValue [
                          a epo:MonetaryValue ;
                          epo:hasAmountValue ?amount ;
                          epo:hasCurrency ?currencyUri
                      ]
                  ]
              ]
          ]
      ] .

  ?winnerUri epo:hasLegalName ?winnerLegalName .
  ?currencyUri dc:identifier ?currency .
}
ORDER BY DESC(?amount)
LIMIT 10
```

## 🎯 Query Patterns

### Pattern 1: Filter by Date Range
```sparql
FILTER (?publicationDate >= "2024-01-01"^^xsd:date && ?publicationDate <= "2024-12-31"^^xsd:date)
```

### Pattern 2: Filter by Currency
```sparql
# EUR only
FILTER (?currencyUri = <http://publications.europa.eu/resource/authority/currency/EUR>)

# Multiple currencies
FILTER (?currencyUri IN (
  <http://publications.europa.eu/resource/authority/currency/EUR>,
  <http://publications.europa.eu/resource/authority/currency/USD>
))
```

### Pattern 3: Filter by Winner Status
```sparql
# Only selected winners
FILTER (?awardStatusUri = <http://publications.europa.eu/resource/authority/winner-selection-status/selec-w>)
```

### Pattern 4: Aggregations
```sparql
# Total amount by winner
SELECT ?winnerLegalName (SUM(?amount) as ?totalAmount) (COUNT(*) as ?contractCount)
WHERE {
  # ... query body ...
}
GROUP BY ?winnerLegalName
ORDER BY DESC(?totalAmount)
LIMIT 20
```

## 🔧 Testing Queries

To test these queries:

1. **Via Web Interface**: Visit https://data.ted.europa.eu (built-in SPARQL editor)
2. **Via API**:
   ```bash
   curl -G "https://publications.europa.eu/webapi/rdf/sparql" \
     --data-urlencode "query=YOUR_SPARQL_QUERY" \
     -H "Accept: application/sparql-results+json"
   ```

3. **Via Agent Tool**:
   - Ask: "Query TED SPARQL: show me winners from November 4, 2024"
   - The agent will use `query_ted_sparql` tool with the appropriate query

**✅ Verified Working**: The endpoint successfully returns real TED procurement data including awards, winners, and contract values!

## ⚠️ Important Notes

### Performance Considerations
- Complex queries with many OPTIONAL blocks can be slow
- Use LIMIT to restrict result sets for faster responses
- Add specific FILTER conditions early in the query
- Avoid SELECT * - specify only needed fields

### Common Errors
1. **Parse Error**: Missing PREFIX declarations or syntax errors
2. **Timeout**: Query too complex - add more filters or LIMIT
3. **No Results**: Check date formats (must be `"YYYY-MM-DD"^^xsd:date`)
4. **URI Errors**: Ensure URIs are enclosed in `< >`

### Data Freshness
- TED Open Data is updated regularly but may lag behind the REST API
- For most recent notices, use `search_ted_tenders`
- For historical analysis, SPARQL is more complete

## 📚 Resources

- **TED Ontology**: https://docs.ted.europa.eu/EPO/latest/index.html
- **SPARQL Tutorial**: https://www.w3.org/TR/sparql11-query/
- **GitHub Repo**: https://github.com/OP-TED/ted-open-data
- **SPARQL UI**: https://data.ted.europa.eu/sparql-ui
