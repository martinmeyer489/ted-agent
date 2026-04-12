"""
Tools for Agno agents.

Provides TED API search functionality as agent tools.
"""

from typing import List, Optional, Dict, Any
import httpx
import json
import uuid
from agno.tools import tool
from loguru import logger
from markdownify import markdownify as md
from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.query_builder import TEDQueryBuilder


@tool
def search_ted_tenders(
    query: str,
    countries: Optional[List[str]] = None,
    cpv_codes: Optional[List[str]] = None,
    notice_types: Optional[List[str]] = None,
    procedure_types: Optional[List[str]] = None,
    max_results: int = 10,
) -> str:
    """
    Search for tender notices on the European TED (Tenders Electronic Daily) platform.
    
    This tool searches the official EU procurement database for public tender opportunities.
    You can search by keywords, filter by countries, CPV codes, and notice types.
    
    Args:
        query: Search keywords (e.g., "software development", "IT services", "construction")
        countries: Optional list of countries to filter by (e.g., ["Germany", "France", "Poland"])
        cpv_codes: Optional list of CPV classification codes (e.g., ["72000000"] for IT services)
        notice_types: Optional list of notice type codes to filter by. Common types:
            - "cn-standard": Contract notice – standard regime
            - "can-standard": Contract award notice – standard regime
            - "cn-social": Contract notice – light regime
            - "can-social": Contract award notice – light regime
            - "can-modif": Contract modification notice
            - "corr": Change notice
            - "compl": Contract completion notice
            - "can-tran": Contract award notice for public passenger transport
            - "cn-desg": Design contest notice
            - "can-desg": Design contest award notice
            - "pin-only": Prior information notice
            - "veat": Voluntary ex-ante transparency notice
        procedure_types: Optional list of procedure type codes to filter by. Common types:
            - "open": Open procedure
            - "4": Negotiated procedure
            - "6": Accelerated negotiated procedure
            - "A": Direct award
            - "E": Concession award procedure
            - "F": Concession award without prior concession notice
            - "V": Contract award without prior publication
            - "comp-dial": Competitive dialogue
            - "comp-tend": Competitive tendering (article 5(3) of Regulation 1370/2007)
            - "innovation": Innovation partnership
            - "neg-w-call": Negotiated with prior publication / competitive with negotiation
            - "neg-wo-call": Negotiated without prior call for competition
        max_results: Maximum number of results to return (default: 10, max: 50)
    
    Returns:
        A formatted string with tender information including:
        - Tender title and description
        - Contracting authority (buyer)
        - Country
        - Publication date
        - CPV codes
        - Publication number and link to full details
    
    Example usage:
        - "Search for software development tenders in Germany"
        - "Find IT services contracts in France and Spain"
        - "Look for construction projects with CPV code 45000000"
        - "Find contract award notices in Poland" (use notice_types=["can-standard"])
        - "Show me design contest notices" (use notice_types=["cn-desg"])
        - "Find open negotiated procedures" (use procedure_types=["4", "neg-wo-call"])
        - "Show competitive dialogue tenders" (use procedure_types=["comp-dial"])
    """
    try:
        logger.info(f"Tool called: search_ted_tenders(query='{query}', countries={countries}, cpv_codes={cpv_codes}, notice_types={notice_types}, procedure_types={procedure_types}, max_results={max_results})")
        
        # Limit max_results
        max_results = min(max_results, 50)
        
        # Build query
        query_builder = TEDQueryBuilder()
        
        # Add query term (uses FT= for full-text search)
        if query:
            query_builder.title_contains(query)
        
        # Add country filters using RC (place of performance)
        if countries:
            query_builder.countries(countries)
        
        # Add CPV codes (these work in the API)
        if cpv_codes:
            for code in cpv_codes:
                query_builder.cpv_code(code)
        
        # Add notice type filters
        if notice_types:
            query_builder.notice_types(notice_types)
        
        # Add procedure type filters
        if procedure_types:
            query_builder.procedure_types(procedure_types)
        
        expert_query = query_builder.build(sort_by="publication-date DESC")
        
        # Request essential fields from TED API (verified from API documentation)
        # These fields are confirmed to be supported by the TED API v3
        fields = [
            "publication-date",
            "notice-title",
            "buyer-name",
            "buyer-city",
            "buyer-country",
            "description-lot",
            "description-proc",
            "deadline-receipt-tender-date-lot",
            "estimated-value-lot",
            "classification-cpv",
            "place-of-performance-country-lot",
            "notice-identifier",
        ]
        
        # Call TED API synchronously using httpx
        logger.info(f"Calling TED API with query: '{expert_query}'")
        try:
            with httpx.Client(timeout=60.0) as client:
                payload = {
                    "query": expert_query,
                    "fields": fields,
                    "page": 1,
                    "limit": max_results,
                    "scope": "ACTIVE",
                    "checkQuerySyntax": False,
                    "paginationMode": "PAGE_NUMBER",
                    "onlyLatestVersions": False,
                }
                logger.debug(f"TED API payload: {payload}")
                
                response = client.post(
                    f"{settings.ted_api_url}/notices/search",
                    json=payload,
                    headers={
                        "accept": "*/*",
                        "Content-Type": "application/json",
                    }
                )
                logger.info(f"TED API responded with status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                logger.info(f"TED API returned {len(result.get('notices', []))} notices")
                
                # Debug: Log first notice structure
                if result.get('notices') and len(result['notices']) > 0:
                    logger.debug(f"First notice structure: {result['notices'][0]}")
        except httpx.HTTPStatusError as e:
            error_msg = f"Error searching TED API: HTTP {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            return error_msg
        except httpx.RequestError as e:
            error_msg = f"Error connecting to TED API: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error searching TED API: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
        
        # Check for errors
        if "error" in result:
            error_msg = result["error"].get("message", "Unknown error")
            return f"Error searching TED API: {error_msg}"
        
        notices = result.get("notices", [])
        
        if not notices:
            return f"No tender notices found matching your search criteria.\n\nQuery: {query}\nCountries: {countries or 'All'}\nCPV Codes: {cpv_codes or 'None'}"
        
        # Helper function to safely extract field values
        def get_field(notice: Dict, field_name: str, default: str = "N/A") -> str:
            """Safely extract field from notice structure."""
            # Fields can be at top level or in _source depending on API response format
            value = notice.get(field_name)
            if value is None:
                source = notice.get("_source", {})
                value = source.get(field_name, default)
            
            if value == default:
                return default
            
            # Handle multilingual fields - try English first, then any language
            if isinstance(value, dict):
                # Try English variants first
                for eng_key in ["eng", "en", "ENG", "EN"]:
                    if eng_key in value:
                        val = value[eng_key]
                        if isinstance(val, list) and len(val) > 0:
                            return str(val[0])
                        elif val:
                            return str(val)
                # Fall back to first available language
                for lang_val in value.values():
                    if isinstance(lang_val, list) and len(lang_val) > 0:
                        return str(lang_val[0])
                    elif lang_val:
                        return str(lang_val)
                return default
            elif isinstance(value, list) and len(value) > 0:
                # Handle direct arrays (e.g., ["DEU", "DEU"])
                if isinstance(value[0], dict):
                    # Array of language objects
                    for item in value:
                        for eng_key in ["eng", "en", "ENG", "EN"]:
                            if eng_key in item:
                                return str(item[eng_key])
                        # Fall back to first available
                        for v in item.values():
                            if v:
                                return str(v)
                else:
                    # Direct array of values
                    return str(value[0])
            elif value:
                return str(value)
            return default
        
        # Format results as markdown
        response_parts = [
            f"# 🎯 Found {len(notices)} Tender Notice(s)\n",
            f"**Search Query:** {query}",
        ]
        
        # Build structured table rows for workspace panel
        table_rows = []
        for i, notice in enumerate(notices, 1):
            title_full = get_field(notice, "notice-title", "Untitled")
            buyer_full = get_field(notice, "buyer-name", "N/A")
            place_country = get_field(notice, "place-of-performance-country-lot", "N/A")
            pub_date = get_field(notice, "publication-date", "N/A")[:10]
            deadline = get_field(notice, "deadline-receipt-tender-date-lot", "N/A")[:10]
            notice_id = get_field(notice, "publication-number")
            link = f"https://ted.europa.eu/en/notice/-/detail/{notice_id}"
            table_rows.append({
                "index": i,
                "title": title_full,
                "buyer": buyer_full,
                "country": place_country,
                "published": pub_date,
                "deadline": deadline,
                "noticeId": notice_id,
                "link": link,
            })
        
        if countries:
            response_parts.append(f"**Countries:** {', '.join(countries)}")
        if cpv_codes:
            response_parts.append(f"**CPV Codes:** {', '.join(cpv_codes)}")
        if notice_types:
            response_parts.append(f"**Notice Types:** {', '.join(notice_types)}")
        
        response_parts.append("\n---\n")
        
        # For many results (>5), show compact table. For few results, show full details
        if len(notices) > 5:
            # Compact table view
            response_parts.extend([
                "\n| # | Title | Buyer | Country | Published | Publication Number |",
                "|---|-------|-------|---------|-----------|-------------------|",
            ])
            
            for i, notice in enumerate(notices, 1):
                title = get_field(notice, "notice-title", "Untitled")[:60]
                if len(get_field(notice, "notice-title", "")) > 60:
                    title += "..."
                buyer_name = get_field(notice, "buyer-name", "N/A")[:30]
                if len(get_field(notice, "buyer-name", "")) > 30:
                    buyer_name += "..."
                place_country = get_field(notice, "place-of-performance-country-lot", "N/A")
                pub_date = get_field(notice, "publication-date", "N/A")[:10]  # Just date part
                notice_id = get_field(notice, "publication-number")
                
                # Display the full publication number (format: XXXXXX-YYYY)
                display_id = notice_id
                
                response_parts.append(
                    f"| {i} | {title} | {buyer_name} | {place_country} | {pub_date} | `{display_id}` |"
                )
            
            response_parts.extend([
                f"\n📊 **Showing {len(notices)} tender(s)** in compact view.",
                f"\n💡 **Want full details?** Ask me to show details for a specific tender by number (e.g., 'Show me details for tender #1') or provide a Publication Number.",
                f"\n🔗 **View on TED:** You can also visit [TED Expert Search](https://ted.europa.eu/en/expert-search) and use the query: `{query}`",
            ])
        else:
            # Full detail view for 5 or fewer results
            for i, notice in enumerate(notices, 1):
                source = notice.get("_source", {})
                
                # Extract all available fields
                title = get_field(notice, "notice-title", "Untitled Notice")
                buyer_name = get_field(notice, "buyer-name")
                buyer_city = get_field(notice, "buyer-city")
                buyer_country = get_field(notice, "buyer-country")
                description_lot = get_field(notice, "description-lot", "")
                description_proc = get_field(notice, "description-proc", "")
                pub_date = get_field(notice, "publication-date")
                deadline = get_field(notice, "deadline-receipt-tender-date-lot")
                estimated_value = get_field(notice, "estimated-value-lot")
                cpv_classification = get_field(notice, "classification-cpv")
                place_country = get_field(notice, "place-of-performance-country-lot")
                notice_id = get_field(notice, "publication-number")
                
                # Use best available description
                description = description_lot if description_lot and description_lot != "N/A" else description_proc
                if description == "N/A" or not description:
                    description = "No description available"
                
                # Truncate long descriptions
                if len(description) > 250:
                    description = description[:250] + "..."
                
                # Build buyer info
                buyer_info = buyer_name
                if buyer_city != "N/A" and buyer_city:
                    buyer_info += f", {buyer_city}"
                if buyer_country != "N/A" and buyer_country:
                    buyer_info += f", {buyer_country}"
                
                # Build tender card
                tender_card = [
                    f"\n## 📋 Tender #{i}: {title}\n",
                    f"| Field | Value |",
                    f"|-------|-------|",
                    f"| **🏢 Buyer** | {buyer_info} |",
                    f"| **🌍 Country** | {place_country if place_country != 'N/A' else buyer_country} |",
                    f"| **📅 Published** | {pub_date} |",
                ]
                
                if deadline != "N/A":
                    tender_card.append(f"| **⏰ Deadline** | {deadline} |")
                
                if estimated_value != "N/A":
                    tender_card.append(f"| **💰 Est. Value** | {estimated_value} |")
                
                if cpv_classification != "N/A":
                    tender_card.append(f"| **🏷️ CPV Code** | {cpv_classification} |")
                
                tender_card.extend([
                    f"| **🆔 Publication Number** | {notice_id} |",
                    f"| **🔗 Full Details** | [View on TED](https://ted.europa.eu/en/notice/-/detail/{notice_id}) |",
                    f"\n**Description:** {description}\n",
                    f"\n---\n",
                ])
                
                response_parts.extend(tender_card)
            
            response_parts.append(f"\n📊 **Showing {len(notices)} tender(s)** with full details")
            response_parts.append("\n💡 *Tip: You can click the links above to view complete tender details on the official TED website.*")
        
        result_text = "\n".join(response_parts)
        logger.info(f"Tool returning {len(result_text)} characters of formatted results")
        
        # Return JSON with text (for LLM) and table (for workspace panel)
        return json.dumps({
            "text": result_text,
            "table": {
                "id": str(uuid.uuid4()),
                "title": f"{query} — {len(notices)} results",
                "columns": [
                    {"key": "index", "label": "#"},
                    {"key": "title", "label": "Title"},
                    {"key": "buyer", "label": "Buyer"},
                    {"key": "country", "label": "Country"},
                    {"key": "published", "label": "Published"},
                    {"key": "deadline", "label": "Deadline"},
                    {"key": "noticeId", "label": "Publication Number"},
                    {"key": "link", "label": "TED Link"},
                ],
                "rows": table_rows,
            }
        })
    
    except httpx.HTTPStatusError as e:
        error_msg = f"Error searching TED API: HTTP {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        return error_msg
    except httpx.RequestError as e:
        error_msg = f"Error connecting to TED API: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error searching TED API: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@tool
def get_ted_notice_details(notice_id: str) -> str:
    """
    Fetch the full details of a specific TED notice by its Notice ID.
    
    This tool retrieves the complete HTML notice from the TED platform and converts it
    to clean, readable markdown format. This includes all sections: description, requirements,
    deadlines, contact information, technical specifications, and more.
    
    Args:
        notice_id: The TED Notice identifier (e.g., "247404-2026" or "123456-2024")
    
    Returns:
        A formatted markdown string with the complete tender notice including:
        - Title and reference information
        - Complete description and specifications
        - Contracting authority details and contacts
        - All dates, deadlines, and procedure information
        - CPV codes and classifications
        - Award criteria and requirements
        - All other information from the official notice
    
    Example usage:
        - "Get details for notice 247404-2026"
        - "Show me the full information for TED notice 654321-2024"
    """
    try:
        logger.info(f"Tool called: get_ted_notice_details(notice_id='{notice_id}')")
        
        # Clean up notice ID (remove prefix if present)
        clean_id = notice_id.replace("TED:NOTICE:", "").strip()
        
        # Construct URL to TED notice HTML endpoint
        html_url = f"https://ted.europa.eu/en/notice/{clean_id}/html"
        logger.info(f"Fetching HTML from: {html_url}")
        
        # Fetch the notice HTML
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(html_url)
            response.raise_for_status()
            
            # Parse HTML with BeautifulSoup for better control
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script, style, and navigation elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Remove any elements with specific classes that are navigation/UI
            for element in soup.find_all(class_=['navigation', 'menu', 'breadcrumb', 'footer']):
                element.decompose()
            
            # Get the main content area (usually the notice content)
            main_content = soup.find('main') or soup.find('body') or soup
            
            # Convert to markdown
            markdown_content = md(
                str(main_content),
                heading_style="ATX",  # Use # headers
                bullets="-",  # Use - for bullet points
                strip=['a'],  # Keep links but simplify
            )
            
            # Clean up the markdown
            # Remove excessive blank lines
            lines = markdown_content.split('\n')
            cleaned_lines = []
            prev_blank = False
            for line in lines:
                is_blank = not line.strip()
                if is_blank and prev_blank:
                    continue
                cleaned_lines.append(line)
                prev_blank = is_blank
            
            markdown_content = '\n'.join(cleaned_lines)
            
            # Add header with notice information
            result_parts = [
                f"# 📄 TED Notice: {clean_id}\n",
                f"**Direct Link:** https://ted.europa.eu/udl?uri=TED:NOTICE:{clean_id}",
                f"**Download HTML:** {html_url}\n",
                f"---\n",
                markdown_content,
                f"\n---\n",
                f"📌 **Notice ID:** {clean_id}",
                f"🔗 **View original:** https://ted.europa.eu/udl?uri=TED:NOTICE:{clean_id}",
            ]
            
            result = '\n'.join(result_parts)
            
            # Limit output if too long (keep first part for context)
            max_length = 15000
            if len(result) > max_length:
                result = result[:max_length] + f"\n\n... (Content truncated. Full notice contains {len(result)} characters)\n\n🔗 **View complete notice at:** https://ted.europa.eu/udl?uri=TED:NOTICE:{clean_id}"
            
            logger.info(f"Successfully converted notice {clean_id} to markdown, returning {len(result)} characters")
            return result
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Could not fetch TED notice {notice_id}: HTTP {e.response.status_code}"
        logger.error(error_msg)
        if e.response.status_code == 404:
            return f"❌ Notice {notice_id} not found.\n\nThe notice may not exist, may have been removed, or the ID format may be incorrect.\nPlease verify the Notice ID (format: XXXXXX-YYYY) and try again."
        return f"❌ {error_msg}\n\nPlease try again or verify the notice ID."
    except httpx.RequestError as e:
        error_msg = f"Connection error fetching notice {notice_id}: {str(e)}"
        logger.error(error_msg)
        return f"❌ {error_msg}\n\nPlease check your internet connection and try again."
    except Exception as e:
        error_msg = f"Unexpected error fetching notice {notice_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"❌ {error_msg}\n\nPlease try again or contact support if the issue persists."


@tool
def update_workspace_table(
    table_id: str,
    title: str,
    columns_json: str,
    rows_json: str,
) -> str:
    """
    Update a table in the user's workspace panel. Use this to:
    - Filter or remove rows
    - Add new columns with enriched data (e.g., deadline, estimated value from notice details)
    - Re-order or rename columns
    
    Args:
        table_id: The table ID from the workspace context (provided in the [WORKSPACE TABLE] block)
        title: Updated title for the table (can be same as before)
        columns_json: JSON array of ALL columns (existing + new), e.g. '[{"key":"title","label":"Title"},{"key":"deadline","label":"Deadline"}]'
        rows_json: JSON array of ALL rows with all fields populated
    
    To add columns: first call get_ted_notice_details for each notice to get the details,
    extract the new fields, then call this tool with the combined column list and updated rows.
    
    Returns:
        JSON with text confirmation and updated table data for the workspace panel.
    """
    try:
        columns = json.loads(columns_json)
        rows = json.loads(rows_json)
        logger.info(f"update_workspace_table: id={table_id}, {len(columns)} cols, {len(rows)} rows")
        return json.dumps({
            "text": f"Updated table '{title}' ({len(rows)} rows, {len(columns)} columns).",
            "table": {"id": table_id, "title": title, "columns": columns, "rows": rows}
        })
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in columns or rows: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def query_ted_sparql(
    sparql_query: str,
    output_format: str = "table"
) -> str:
    """
    Execute a SPARQL query against TED Open Data Service (Linked Open Data).
    
    This tool provides access to structured procurement data using SPARQL queries.
    Use this for advanced analytics, aggregations, and complex data exploration
    that goes beyond simple keyword searches.
    
    **When to use this tool:**
    - Analyzing awarded contracts and winners
    - Aggregating tender values by buyer, country, or CPV code
    - Finding relationships between organizations
    - Statistical analysis across multiple tenders
    - Retrieving detailed tender award outcomes
    - Complex queries with JOINs and filters
    
    **When to use search_ted_tenders instead:**
    - Simple keyword searches ("find IT tenders in Germany")
    - Browsing recent notices
    - Quick lookups by country or CPV code
    - Finding specific tender titles
    
    Args:
        sparql_query: A valid SPARQL query using TED ontology namespaces.
            Common prefixes:
            - epo: <http://data.europa.eu/a4g/ontology#> (TED ontology)
            - dc: <http://purl.org/dc/elements/1.1/>
            - adms: <http://www.w3.org/ns/adms#>
            - skos: <http://www.w3.org/2004/02/skos/core#>
            
        output_format: How to format results. Options:
            - "table": Markdown table (default, best for displaying results)
            - "json": Raw JSON response
            - "csv": Comma-separated values
    
    Returns:
        Formatted query results as a string
    
    Example queries:
        - "Show me winners and amounts for tenders published on 2024-11-04"
        - "Get total awarded amounts by country"
        - "Find all tenders from a specific buyer organization"
    
    Note: This tool requires knowledge of SPARQL syntax and TED ontology.
    For simple searches, use search_ted_tenders instead.
    """
    try:
        logger.info(f"Tool called: query_ted_sparql(output_format='{output_format}')")
        logger.debug(f"SPARQL query:\n{sparql_query}")
        
        # EU Publications Office SPARQL endpoint (official TED Open Data endpoint)
        sparql_endpoint = "https://publications.europa.eu/webapi/rdf/sparql"
        
        # Prepare request headers based on output format
        accept_headers = {
            "json": "application/sparql-results+json",
            "csv": "text/csv",
            "table": "application/sparql-results+json",  # We'll convert to table
        }
        
        accept_header = accept_headers.get(output_format.lower(), accept_headers["table"])
        
        # Execute SPARQL query using GET (standard SPARQL protocol)
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            response = client.get(
                sparql_endpoint,
                params={"query": sparql_query},
                headers={
                    "Accept": accept_header,
                }
            )
            
            logger.info(f"SPARQL endpoint responded with status: {response.status_code}")
            response.raise_for_status()
            
            # Handle different output formats
            if output_format.lower() == "json":
                result = response.json()
                logger.info(f"SPARQL query returned {len(result.get('results', {}).get('bindings', []))} results")
                return f"```json\n{response.text}\n```"
            
            elif output_format.lower() == "csv":
                logger.info(f"SPARQL query returned CSV data ({len(response.text)} chars)")
                return f"```csv\n{response.text}\n```"
            
            else:  # table format (default)
                result = response.json()
                bindings = result.get("results", {}).get("bindings", [])
                
                if not bindings:
                    return "✅ Query executed successfully but returned no results.\n\n💡 **Possible reasons:**\n- Date filters may be too restrictive\n- The query syntax may need adjustment\n- Try a broader date range or remove filters\n\n**Alternative**: Try the REST API with `search_ted_tenders` for keyword-based searches."
                
                # Extract column headers from first result
                headers = list(bindings[0].keys())
                
                # Build markdown table
                table_parts = [
                    f"# 📊 SPARQL Query Results\n",
                    f"**Total rows:** {len(bindings)}\n",
                    "---\n",
                ]
                
                # Table header
                header_row = "| " + " | ".join(headers) + " |"
                separator = "|" + "|".join(["---" for _ in headers]) + "|"
                table_parts.extend([header_row, separator])
                
                # Table rows (limit to 100 for readability)
                max_rows = 100
                for i, binding in enumerate(bindings[:max_rows]):
                    row_values = []
                    for header in headers:
                        value = binding.get(header, {}).get("value", "N/A")
                        # Truncate long values
                        if len(str(value)) > 100:
                            value = str(value)[:97] + "..."
                        row_values.append(str(value))
                    
                    row = "| " + " | ".join(row_values) + " |"
                    table_parts.append(row)
                
                if len(bindings) > max_rows:
                    table_parts.append(f"\n⚠️ *Showing first {max_rows} of {len(bindings)} results*")
                
                table_parts.append("\n✅ Query completed successfully")
                
                result_text = "\n".join(table_parts)
                logger.info(f"Formatted SPARQL results as table ({len(result_text)} chars)")
                return result_text
                
    except httpx.HTTPStatusError as e:
        error_msg = f"SPARQL query failed: HTTP {e.response.status_code}"
        logger.error(f"{error_msg}\nResponse: {e.response.text}")
        
        # Special handling for 404 - endpoint may not be available
        if e.response.status_code == 404:
            return (
                "❌ **SPARQL Endpoint Not Found**\n\n"
                f"The endpoint returned HTTP 404. The SPARQL service may be temporarily unavailable.\n\n"
                "📊 **Current endpoint**: https://publications.europa.eu/webapi/rdf/sparql\n\n"
                "**Alternative Approaches:**\n"
                "1. Use `search_ted_tenders` for keyword searches and filtering\n"
                "2. Visit https://data.ted.europa.eu for the web SPARQL editor\n"
                "3. Check TED Open Data documentation at https://github.com/OP-TED/ted-open-data\n\n"
                "Would you like me to try answering your question using the REST API instead?"
            )
        
        # Try to extract error message from response
        try:
            error_detail = e.response.text
            if "Parse error" in error_detail or "syntax" in error_detail.lower():
                return f"❌ **SPARQL Syntax Error**\n\n{error_detail}\n\n💡 Check your query syntax, especially:\n- Missing or incorrect PREFIX declarations\n- Unclosed brackets or quotes\n- Invalid URI syntax"
            else:
                return f"❌ **Query Error**\n\n{error_detail}"
        except:
            return f"❌ {error_msg}\n\nThe SPARQL endpoint returned an error. Please check your query syntax."
    
    except httpx.RequestError as e:
        error_msg = f"Connection error to SPARQL endpoint: {str(e)}"
        logger.error(error_msg)
        return f"❌ {error_msg}\n\nCould not connect to TED SPARQL endpoint. Please check your internet connection."
    
    except Exception as e:
        error_msg = f"Unexpected error executing SPARQL query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"❌ {error_msg}\n\nPlease verify your SPARQL query syntax or contact support if the issue persists."
