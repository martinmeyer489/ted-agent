"""
Tools for Agno agents.

Provides TED API search functionality as agent tools.
"""

from typing import List, Optional, Dict, Any, Tuple
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
        
        # Call TED API using httpx (force IPv4 - TED API IPv6 is unreliable)
        logger.info(f"Calling TED API with query: '{expert_query}'")
        try:
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
            
            transport = httpx.HTTPTransport(local_address="0.0.0.0")
            with httpx.Client(transport=transport, timeout=60.0) as client:
                response = client.post(
                    f"{settings.ted_api_url}/notices/search",
                    json=payload,
                    headers={
                        "accept": "*/*",
                        "Content-Type": "application/json",
                    },
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
        # Note: Users can save tenders by clicking the star (☆) button in the UI
        # Saved items are stored locally in the browser and accessible via the "Saved Items" page
    
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
        
        # Fetch the notice HTML (force IPv4)
        transport = httpx.HTTPTransport(local_address="0.0.0.0")
        with httpx.Client(transport=transport, timeout=30.0, follow_redirects=True) as client:
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


# ==============================================================================
# Workspace Table Tool - COMMENTED OUT (NO LONGER IN USE)
# ==============================================================================
"""
@tool
def update_workspace_table(
    table_id: str,
    title: str,
    columns_json: str,
    rows_json: str,
) -> str:
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
"""


# ==============================================================================
# SPARQL Query Tool
# ==============================================================================


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
        
        # Execute SPARQL query using GET (force IPv4)
        transport = httpx.HTTPTransport(local_address="0.0.0.0")
        with httpx.Client(transport=transport, timeout=120.0, follow_redirects=True) as client:
            response = client.get(
                sparql_endpoint,
                params={"query": sparql_query},
                headers={
                    "Accept": accept_header,
                },
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


@tool
def analyze_buyer_profile(
    buyer_name: str,
    cpv_code: Optional[str] = None,
    months_back: int = 12,
) -> str:
    """
    Analyze a specific buyer's procurement activity and generate a comprehensive profile.
    
    This tool provides competitive intelligence on public sector buyers by aggregating
    their tender history, spending patterns, category preferences, and activity trends.
    Perfect for business development, market research, and opportunity targeting.
    
    Args:
        buyer_name: Name of the contracting authority/buyer to analyze (e.g., "München", "Munich", 
            "Stadtwerke München", "City of Berlin"). Can be partial - will find all matching buyers.
        cpv_code: Optional CPV code to focus analysis (e.g., "72" for IT services, "45" for construction).
            If provided, analysis focuses on this category only.
        months_back: Number of months of historical data to analyze (default: 12, max: 24)
    
    Returns:
        A comprehensive buyer intelligence report including:
        - Total tender volume and estimated values
        - Most active buyer entities matching the search
        - Top procurement categories (CPV codes)
        - Average contract values and value distribution
        - Tender frequency and seasonal patterns
        - Most common procurement procedures
        - Recent tender examples
        - Upcoming opportunities (active tenders)
    
    Example usage:
        - "Analyze buyer profile for Munich" - Get overview of all Munich buyers
        - "What does the City of Berlin procure?" - See Berlin's procurement patterns
        - "Analyze Stadtwerke München for IT services" (with cpv_code="72")
        - "Show me procurement activity for Hamburg in construction" (with cpv_code="45")
        - "Who are the biggest buyers in Germany?" - Use search first, then analyze top buyers
    
    Use cases:
        - **Market Research**: Understand buyer behavior and spending patterns
        - **Lead Qualification**: Identify active buyers in your sector
        - **Business Development**: Target high-value, frequent buyers
        - **Competitive Intelligence**: See what buyers procure and how often
        - **Opportunity Forecasting**: Predict future tenders based on historical patterns
    """
    try:
        logger.info(f"Tool called: analyze_buyer_profile(buyer_name='{buyer_name}', cpv_code={cpv_code}, months_back={months_back})")
        
        # Limit months_back
        months_back = min(months_back, 24)
        
        # Build search query to find buyer tenders
        # Use buyer-name field (alias: AU) for precise buyer matching
        # The ~ operator allows partial matching (e.g., "München" matches "Stadtwerke München GmbH")
        query = f'AU~"{buyer_name}"'
        
        # Add CPV filter if specified
        if cpv_code:
            # Normalize CPV code (remove wildcards if present)
            clean_cpv = cpv_code.replace("*", "").strip()
            query += f' AND CPV={clean_cpv}'
        
        # Request comprehensive fields for analysis
        fields = [
            "publication-date",
            "notice-title",
            "buyer-name",
            "buyer-city",
            "buyer-country",
            "classification-cpv",
            "estimated-value-lot",
            "notice-type",
            "procedure-type",
            "deadline-receipt-tender-date-lot",
            "notice-identifier",
            "publication-number",
        ]
        
        # Fetch data from TED API
        logger.info(f"Fetching buyer data with query: {query}")
        payload = {
            "query": query,
            "fields": fields,
            "page": 1,
            "limit": 100,  # Get more data for better analysis
            "scope": "ACTIVE",
            "paginationMode": "PAGE_NUMBER",
            "onlyLatestVersions": False,
        }
        
        transport = httpx.HTTPTransport(local_address="0.0.0.0")
        with httpx.Client(transport=transport, timeout=60.0) as client:
            response = client.post(
                f"{settings.ted_api_url}/notices/search",
                json=payload,
                headers={
                    "accept": "*/*",
                    "Content-Type": "application/json",
                },
            )
        response.raise_for_status()
        result = response.json()
        
        notices = result.get("notices", [])
        
        if not notices:
            return f"❌ No tender data found for buyer: **{buyer_name}**\n\n💡 **Suggestions:**\n- Try a shorter or partial name (e.g., 'Munich' instead of 'City of Munich')\n- Check spelling\n- Try searching in the buyer's native language (e.g., 'München' for Munich)\n- The buyer may not have recent tenders in the database"
        
        logger.info(f"Analyzing {len(notices)} notices for buyer profile")
        
        # Helper function to safely extract field values (reuse from search_ted_tenders)
        def get_field(notice: Dict, field_name: str, default: str = "N/A") -> str:
            """Safely extract field from notice structure."""
            value = notice.get(field_name)
            if value is None:
                source = notice.get("_source", {})
                value = source.get(field_name, default)
            
            if value == default:
                return default
            
            # Handle multilingual fields
            if isinstance(value, dict):
                for eng_key in ["eng", "en", "ENG", "EN"]:
                    if eng_key in value:
                        val = value[eng_key]
                        if isinstance(val, list) and len(val) > 0:
                            return str(val[0])
                        elif val:
                            return str(val)
                for lang_val in value.values():
                    if isinstance(lang_val, list) and len(lang_val) > 0:
                        return str(lang_val[0])
                    elif lang_val:
                        return str(lang_val)
                return default
            elif isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict):
                    for item in value:
                        for eng_key in ["eng", "en", "ENG", "EN"]:
                            if eng_key in item:
                                return str(item[eng_key])
                        for v in item.values():
                            if v:
                                return str(v)
                else:
                    return str(value[0])
            elif value:
                return str(value)
            return default
        
        # Aggregate data
        buyers = {}  # buyer_name -> count
        cpv_categories = {}  # cpv_code -> count
        notice_types = {}  # notice_type -> count
        procedure_types = {}  # procedure_type -> count
        values = []  # list of estimated values
        pub_dates = []  # list of publication dates
        deadlines = []  # list of upcoming deadlines
        recent_notices = []  # sample recent notices
        
        for notice in notices:
            # Buyer names
            buyer = get_field(notice, "buyer-name")
            if buyer != "N/A":
                buyers[buyer] = buyers.get(buyer, 0) + 1
            
            # CPV codes (main category - first 2 digits)
            cpv = get_field(notice, "classification-cpv")
            if cpv != "N/A" and len(cpv) >= 2:
                cpv_main = cpv[:2]
                cpv_categories[cpv_main] = cpv_categories.get(cpv_main, 0) + 1
            
            # Notice types
            notice_type = get_field(notice, "notice-type")
            if notice_type != "N/A":
                notice_types[notice_type] = notice_types.get(notice_type, 0) + 1
            
            # Procedure types
            proc_type = get_field(notice, "procedure-type")
            if proc_type != "N/A":
                procedure_types[proc_type] = procedure_types.get(proc_type, 0) + 1
            
            # Values
            value_str = get_field(notice, "estimated-value-lot")
            if value_str != "N/A":
                try:
                    value = float(value_str)
                    if value > 0:
                        values.append(value)
                except (ValueError, TypeError):
                    pass
            
            # Publication dates
            pub_date = get_field(notice, "publication-date")
            if pub_date != "N/A":
                pub_dates.append(pub_date[:10])
            
            # Deadlines (for upcoming opportunities)
            deadline = get_field(notice, "deadline-receipt-tender-date-lot")
            if deadline != "N/A":
                try:
                    from datetime import datetime
                    deadline_date = datetime.fromisoformat(deadline[:10])
                    today = datetime.now()
                    if deadline_date > today:
                        deadlines.append({
                            "date": deadline[:10],
                            "title": get_field(notice, "notice-title")[:80],
                            "buyer": buyer,
                            "notice_id": get_field(notice, "publication-number"),
                        })
                except:
                    pass
            
            # Store recent notices (first 5)
            if len(recent_notices) < 5:
                recent_notices.append({
                    "title": get_field(notice, "notice-title"),
                    "buyer": buyer,
                    "cpv": cpv,
                    "pub_date": pub_date[:10] if pub_date != "N/A" else "N/A",
                    "notice_id": get_field(notice, "publication-number"),
                })
        
        # Build comprehensive report
        report_parts = [
            f"# 🏢 Buyer Intelligence Report: {buyer_name}\n",
            f"**Analysis Period:** Last {months_back} months",
            f"**Total Tenders Analyzed:** {len(notices)}",
        ]
        
        if cpv_code:
            report_parts.append(f"**CPV Category Filter:** {cpv_code}*\n")
        else:
            report_parts.append("")
        
        report_parts.append("---\n")
        
        # Section 1: Top Buyers
        report_parts.append("## 📊 Most Active Buyer Entities\n")
        if buyers:
            sorted_buyers = sorted(buyers.items(), key=lambda x: x[1], reverse=True)[:10]
            for i, (buyer, count) in enumerate(sorted_buyers, 1):
                pct = (count / len(notices)) * 100
                report_parts.append(f"{i}. **{buyer}** — {count} tenders ({pct:.1f}%)")
        else:
            report_parts.append("No buyer data available")
        
        # Section 2: Procurement Categories
        report_parts.append("\n## 🎯 Top Procurement Categories (CPV)\n")
        if cpv_categories:
            sorted_cpv = sorted(cpv_categories.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # CPV category names (common ones)
            cpv_names = {
                "03": "Agricultural products",
                "09": "Petroleum/fuel products",
                "15": "Food/beverages",
                "18": "Clothing/footwear",
                "22": "Printed matter",
                "24": "Chemical products",
                "30": "Office/computing machinery",
                "31": "Electrical machinery",
                "32": "Radio/TV equipment",
                "33": "Medical equipment",
                "34": "Transport equipment",
                "35": "Security equipment",
                "37": "Musical instruments",
                "38": "Laboratory equipment",
                "39": "Furniture",
                "42": "Industrial machinery",
                "44": "Construction structures",
                "45": "Construction work",
                "48": "Software packages",
                "50": "Repair/maintenance",
                "51": "Installation services",
                "55": "Hotel/restaurant services",
                "60": "Transport services",
                "63": "Travel/supporting services",
                "64": "Postal/telecommunications",
                "65": "Utility services",
                "66": "Financial services",
                "70": "Real estate services",
                "71": "Architectural/engineering",
                "72": "IT services",
                "73": "Research services",
                "75": "Administration services",
                "76": "Services to oil/gas",
                "77": "Agricultural services",
                "79": "Business services",
                "80": "Education services",
                "85": "Health/social services",
                "90": "Sewage/waste services",
                "92": "Recreational/cultural",
                "98": "Other services",
            }
            
            for i, (cpv, count) in enumerate(sorted_cpv, 1):
                pct = (count / len(notices)) * 100
                category_name = cpv_names.get(cpv, "Other")
                report_parts.append(f"{i}. **CPV {cpv}*** ({category_name}) — {count} tenders ({pct:.1f}%)")
        else:
            report_parts.append("No CPV data available")
        
        # Section 3: Financial Analysis
        report_parts.append("\n## 💰 Financial Overview\n")
        if values:
            total_value = sum(values)
            avg_value = total_value / len(values)
            min_value = min(values)
            max_value = max(values)
            median_value = sorted(values)[len(values) // 2]
            
            report_parts.extend([
                f"- **Total Estimated Value:** €{total_value:,.0f}",
                f"- **Average Contract Value:** €{avg_value:,.0f}",
                f"- **Median Value:** €{median_value:,.0f}",
                f"- **Value Range:** €{min_value:,.0f} - €{max_value:,.0f}",
                f"- **Tenders with Values:** {len(values)} of {len(notices)}",
            ])
            
            # Value distribution
            report_parts.append("\n**Value Distribution:**")
            ranges = [
                (0, 100_000, "€0-100K"),
                (100_000, 500_000, "€100K-500K"),
                (500_000, 1_000_000, "€500K-1M"),
                (1_000_000, 5_000_000, "€1M-5M"),
                (5_000_000, float('inf'), "€5M+"),
            ]
            for min_val, max_val, label in ranges:
                count = len([v for v in values if min_val <= v < max_val])
                if count > 0:
                    pct = (count / len(values)) * 100
                    report_parts.append(f"- {label}: {count} tenders ({pct:.1f}%)")
        else:
            report_parts.append("*No estimated value data available*")
        
        # Section 4: Procurement Activity Patterns
        report_parts.append("\n## 📈 Activity Patterns\n")
        if pub_dates:
            # Calculate tender frequency
            avg_per_month = len(notices) / months_back
            report_parts.append(f"- **Average Frequency:** ~{avg_per_month:.1f} tenders per month")
            
            # Most common notice types
            if notice_types:
                top_notice_type = max(notice_types.items(), key=lambda x: x[1])
                report_parts.append(f"- **Most Common Notice Type:** {top_notice_type[0]} ({top_notice_type[1]} tenders)")
            
            # Most common procedure types
            if procedure_types:
                top_proc_type = max(procedure_types.items(), key=lambda x: x[1])
                report_parts.append(f"- **Most Common Procedure:** {top_proc_type[0]} ({top_proc_type[1]} tenders)")
        
        # Section 5: Upcoming Opportunities
        if deadlines:
            report_parts.append("\n## ⏰ Upcoming Opportunities\n")
            sorted_deadlines = sorted(deadlines, key=lambda x: x["date"])[:5]
            for dl in sorted_deadlines:
                report_parts.append(f"- **{dl['date']}** — {dl['title']} (Notice: `{dl['notice_id']}`)")
        else:
            report_parts.append("\n## ⏰ Upcoming Opportunities\n")
            report_parts.append("*No upcoming open tenders with deadlines found*")
        
        # Section 6: Recent Tender Examples
        report_parts.append("\n## 📋 Recent Tender Examples\n")
        for i, tn in enumerate(recent_notices[:5], 1):
            report_parts.append(
                f"{i}. **{tn['title'][:100]}{'...' if len(tn['title']) > 100 else ''}**\n"
                f"   - Buyer: {tn['buyer']}\n"
                f"   - Published: {tn['pub_date']}\n"
                f"   - CPV: {tn['cpv']}\n"
                f"   - Notice ID: `{tn['notice_id']}`\n"
            )
        
        # Footer with recommendations
        report_parts.extend([
            "\n---\n",
            "## 💡 How to Use This Intelligence\n",
            "- **Target high-value categories** where this buyer is most active",
            "- **Watch for upcoming deadlines** to submit competitive bids",
            "- **Analyze seasonal patterns** to predict future procurement",
            "- **Study procedure preferences** to optimize your approach",
            "- **Track competitors** who frequently win contracts from this buyer\n",
            f"🔗 **Get full details:** Use `get_ted_notice_details(notice_id)` for any tender",
        ])
        
        result = "\n".join(report_parts)
        logger.info(f"Generated buyer profile report ({len(result)} chars)")
        return result
        
    except httpx.HTTPStatusError as e:
        error_msg = f"Error fetching buyer data: HTTP {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        return f"❌ {error_msg}\n\nPlease try again or refine your search criteria."
    except httpx.RequestError as e:
        error_msg = f"Connection error: {str(e)}"
        logger.error(error_msg)
        return f"❌ {error_msg}\n\nPlease check your internet connection and try again."
    except Exception as e:
        error_msg = f"Unexpected error analyzing buyer profile: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"❌ {error_msg}\n\nPlease try again or contact support if the issue persists."


# ==============================================================================
# CPV Enrichment Tool
# ==============================================================================

# CPV division labels (2-digit prefix → human-readable label).
# Used as a fallback when the live SPARQL endpoint is unavailable.
_CPV_STATIC_DIVISIONS: Dict[str, str] = {
    "03": "Agricultural, farming, fishing, forestry and related products",
    "09": "Petroleum products, fuel, electricity and other sources of energy",
    "14": "Mining, basic metals and related products",
    "15": "Food, beverages, tobacco and related products",
    "16": "Farm machinery, equipment and supplies",
    "18": "Clothing, footwear, luggage articles and accessories",
    "19": "Leather and textile fabrics, plastic and rubber materials",
    "22": "Printed matter and related products",
    "24": "Chemical products",
    "30": "Office and computing machinery, equipment and supplies",
    "31": "Electrical machinery, apparatus, equipment and consumables",
    "32": "Radio, television, communication, telecommunication and related equipment",
    "33": "Medical equipments, pharmaceuticals and personal care products",
    "34": "Transport equipment and auxiliary products to transportation",
    "35": "Security, fire-fighting, police and defence equipment",
    "37": "Musical instruments, sport goods, games, toys, handicraft, art materials",
    "38": "Laboratory, optical and precision equipments",
    "39": "Furniture (incl. office furniture), furnishings, domestic appliances",
    "41": "Collected and purified water",
    "42": "Industrial machinery",
    "43": "Machinery for mining, quarrying, construction equipment",
    "44": "Construction structures and materials; auxiliary products to construction",
    "45": "Construction work",
    "48": "Software package and information systems",
    "50": "Repair and maintenance services",
    "51": "Installation services",
    "55": "Hotel, restaurant and retail trade services",
    "60": "Transport services",
    "63": "Supporting and auxiliary transport services; travel agencies services",
    "64": "Postal and telecommunications services",
    "65": "Public utilities",
    "66": "Financial and insurance services",
    "70": "Real estate services",
    "71": "Architectural, construction, engineering and inspection services",
    "72": "IT services: consulting, software development, Internet and support",
    "73": "Research and development services and related consultancy services",
    "75": "Administration, defence and social security services",
    "76": "Services related to the oil and gas industry",
    "77": "Agricultural, forestry, horticultural, aquacultural and apicultural services",
    "79": "Business services: law, marketing, consulting, recruitment, printing and security",
    "80": "Education and training services",
    "85": "Health and social work services",
    "90": "Sewage, refuse, cleaning and environmental services",
    "92": "Recreational, cultural and sporting services",
    "98": "Other community, social and personal services",
}

# Keyword phrases → CPV division prefixes (most relevant first).
# Used as a static fallback for natural-language term lookup.
_KEYWORD_CPV_MAP: List[Tuple[List[str], List[str]]] = [
    (["software", "saas", "application", "platform", "app", "digital solution"], ["48", "72"]),
    (["it service", "ict service", "information technology", "tech support", "helpdesk", "it support"], ["72", "48"]),
    (["cybersecurity", "cyber security", "information security", "infosec", "siem", "soc",
      "firewall", "penetration test", "vulnerability assessment", "endpoint protection"], ["72"]),
    (["cloud service", "cloud hosting", "iaas", "paas", "saas", "datacenter", "data center"], ["72", "48"]),
    (["consulting", "advisory", "consultancy", "management consulting"], ["72", "79", "73"]),
    (["network", "networking", "telecommunication", "telecom", "broadband", "internet provider"], ["32", "64", "72"]),
    (["database", "data processing", "analytics", "business intelligence", "data warehouse", "big data"], ["72", "48"]),
    (["website", "web development", "web design", "e-government", "portal"], ["72", "48"]),
    (["construction", "building work", "civil engineering", "renovation", "refurbishment"], ["45"]),
    (["architecture", "architectural service", "structural engineer", "survey", "inspection"], ["71"]),
    (["road", "highway", "pavement", "asphalt", "bridge", "tunnel", "motorway"], ["45"]),
    (["medical device", "medical equipment", "hospital equipment", "pharmaceutical", "drug", "medicine"], ["33"]),
    (["health service", "healthcare", "social care", "nursing", "care service", "hospital"], ["85"]),
    (["transport service", "logistics", "freight", "shipping", "delivery"], ["60", "63"]),
    (["education", "training", "learning", "e-learning", "vocational training"], ["80"]),
    (["research", "r&d", "research and development", "innovation"], ["73"]),
    (["cleaning", "waste management", "refuse", "environmental service", "sewage", "recycling"], ["90"]),
    (["security service", "guard", "surveillance", "security personnel"], ["79"]),
    (["security equipment", "fire fighting", "defence equipment", "police equipment"], ["35"]),
    (["food", "catering", "meal", "beverage", "drink", "canteen"], ["15", "55"]),
    (["office supply", "furniture", "stationery", "office equipment"], ["39", "30"]),
    (["printing", "printed matter", "document", "publication", "book"], ["22"]),
    (["insurance", "financial service", "banking", "pension"], ["66"]),
    (["real estate", "property", "facility management", "building management"], ["70"]),
    (["energy", "electricity", "natural gas", "solar", "wind energy", "renewable", "fuel"], ["09", "65"]),
    (["water supply", "water service", "utility", "sewage treatment"], ["41", "65"]),
    (["audit", "accounting", "bookkeeping", "legal service", "law firm", "legal advice"], ["79"]),
    (["marketing", "advertising", "communication service", "public relation"], ["79"]),
    (["recruitment", "hr service", "human resource", "staffing", "temporary work"], ["79"]),
    (["electrical installation", "electrical work", "wiring", "electrical equipment"], ["31", "45"]),
    (["repair", "maintenance service", "servicing"], ["50"]),
    (["installation service"], ["51"]),
    (["agricultural", "farming", "horticulture", "forestry", "veterinary"], ["77", "03"]),
    (["chemical", "laboratory chemical"], ["24"]),
]


def _query_cpv_sparql(sparql_query: str, timeout: float = 30.0) -> List[Dict]:
    """Execute a SPARQL query against the EU Publications Office endpoint.

    Returns the raw bindings list from the SPARQL JSON results format.
    Raises on HTTP or connection errors so callers can fall back gracefully.
    """
    sparql_endpoint = "https://publications.europa.eu/webapi/rdf/sparql"
    transport = httpx.HTTPTransport(local_address="0.0.0.0")
    with httpx.Client(transport=transport, timeout=timeout, follow_redirects=True) as client:
        response = client.get(
            sparql_endpoint,
            params={"query": sparql_query},
            headers={"Accept": "application/sparql-results+json"},
        )
    response.raise_for_status()
    return response.json().get("results", {}).get("bindings", [])


def _static_search_term(term: str) -> List[Dict[str, str]]:
    """Match a natural-language term against the static CPV keyword index."""
    term_lower = term.lower()
    seen: set = set()
    results: List[Dict[str, str]] = []
    for keywords, prefixes in _KEYWORD_CPV_MAP:
        if any(kw in term_lower for kw in keywords):
            for prefix in prefixes:
                if prefix not in seen:
                    seen.add(prefix)
                    label = _CPV_STATIC_DIVISIONS.get(prefix, "Unknown category")
                    results.append({"code": f"{prefix}000000", "label": label})
    return results


def _static_lookup_code(cpv_code: str, include_subtree: bool) -> List[Dict[str, str]]:
    """Look up CPV division(s) from the static index for a given code or prefix."""
    clean = cpv_code.strip().replace("*", "")
    prefix = clean.rstrip("0") or clean[:2]
    prefix = prefix[:2]  # at most the 2-digit division prefix

    results: List[Dict[str, str]] = []
    for div, label in sorted(_CPV_STATIC_DIVISIONS.items()):
        if include_subtree:
            if div.startswith(prefix):
                results.append({"code": f"{div}000000", "label": label})
        else:
            if div == prefix:
                results.append({"code": f"{div}000000", "label": label})
    return results


@tool
def get_cpv_enrichment(
    search_term: Optional[str] = None,
    cpv_code: Optional[str] = None,
    include_subtree: bool = False,
    language: str = "EN",
) -> str:
    """
    Translate natural language search terms to CPV codes, or look up / expand CPV codes.

    Use this tool BEFORE calling search_ted_tenders when you need accurate CPV codes
    instead of guessing. It queries the EU Publications Office CPV vocabulary via
    their SPARQL endpoint and falls back to an embedded static index if needed.

    **When to use this tool:**
    - You want to find CPV codes for a topic (e.g., "cybersecurity software", "road construction")
    - You have a partial code and want its label or its full set of sub-codes
    - The user mentions a topic but no CPV code — enrich before searching

    Args:
        search_term: Natural language description of what you're looking for
            (e.g., "cybersecurity software", "road construction", "medical imaging").
            Returns matching CPV codes and labels sorted by code.
        cpv_code: A CPV code or prefix to look up or expand
            (e.g., "72000000" for an exact label lookup, "72" to list the whole
            IT division). When include_subtree=False, returns the label for the
            given code. When include_subtree=True, returns all codes under that prefix.
        include_subtree: If True (requires cpv_code), expand to all descendant codes
            sharing that prefix — e.g. cpv_code="72", include_subtree=True returns
            every 72xxxxxx code. Default: False.
        language: BCP-47 language tag for labels (default: "EN").
            Other EU official languages are supported (e.g., "DE", "FR", "ES").

    Returns:
        A formatted markdown string listing CPV codes with their official labels.
        The codes can be passed directly to search_ted_tenders via cpv_codes=[...].

    Example usage:
        - get_cpv_enrichment(search_term="cybersecurity software")
          → Returns CPV codes for IT security services / software
        - get_cpv_enrichment(cpv_code="72000000")
          → Returns label: "IT services: consulting, software development..."
        - get_cpv_enrichment(cpv_code="72", include_subtree=True)
          → Returns all IT-related CPV sub-codes under the 72* division
        - get_cpv_enrichment(search_term="road construction", include_subtree=True)
          → Finds matching CPV divisions and expands each to child codes
    """
    try:
        logger.info(
            f"Tool called: get_cpv_enrichment("
            f"search_term={search_term!r}, cpv_code={cpv_code!r}, "
            f"include_subtree={include_subtree}, language={language!r})"
        )

        if not search_term and not cpv_code:
            return "❌ Please provide either `search_term` or `cpv_code`."

        lang_tag = language.upper()[:2]
        results: List[Dict[str, str]] = []
        source = "SPARQL"

        # ------------------------------------------------------------------ #
        # Mode A: natural-language term → matching CPV codes                  #
        # ------------------------------------------------------------------ #
        if search_term:
            safe_term = search_term.replace('"', "").replace("\\", "")
            sparql = (
                "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>\n"
                "SELECT DISTINCT ?code ?label WHERE {\n"
                "  ?concept skos:inScheme <http://publications.europa.eu/resource/authority/cpv> ;\n"
                "           skos:notation ?code ;\n"
                "           skos:prefLabel ?label .\n"
                f'  FILTER(LANG(?label) = "{lang_tag}")\n'
                f'  FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{safe_term}")))\n'
                "}\n"
                "ORDER BY ?code\n"
                "LIMIT 30"
            )
            try:
                bindings = _query_cpv_sparql(sparql)
                results = [
                    {
                        "code": b.get("code", {}).get("value", ""),
                        "label": b.get("label", {}).get("value", ""),
                    }
                    for b in bindings
                    if b.get("code", {}).get("value")
                ]
                logger.info(f"SPARQL returned {len(results)} CPV match(es) for term '{search_term}'")
            except Exception as sparql_err:
                logger.warning(f"SPARQL CPV search failed ({sparql_err}); using static index")
                source = "static index (SPARQL unavailable)"
                results = _static_search_term(search_term)

            # SPARQL succeeded but returned nothing — enrich with static index
            if not results and source == "SPARQL":
                logger.info("SPARQL returned 0 results; enriching with static keyword index")
                source = "SPARQL + static index"
                results = _static_search_term(search_term)

            # If include_subtree requested, expand each matched division
            if include_subtree and results:
                expanded: List[Dict[str, str]] = []
                seen_codes: set = set()
                for r in results:
                    prefix = r["code"].rstrip("0") or r["code"][:2]
                    prefix = prefix[:2]
                    sparql_sub = (
                        "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>\n"
                        "SELECT DISTINCT ?code ?label WHERE {\n"
                        "  ?concept skos:inScheme <http://publications.europa.eu/resource/authority/cpv> ;\n"
                        "           skos:notation ?code ;\n"
                        "           skos:prefLabel ?label .\n"
                        f'  FILTER(LANG(?label) = "{lang_tag}")\n'
                        f'  FILTER(STRSTARTS(STR(?code), "{prefix}"))\n'
                        "}\n"
                        "ORDER BY ?code\n"
                        "LIMIT 100"
                    )
                    try:
                        sub_bindings = _query_cpv_sparql(sparql_sub)
                        for b in sub_bindings:
                            code = b.get("code", {}).get("value", "")
                            label = b.get("label", {}).get("value", "")
                            if code and code not in seen_codes:
                                seen_codes.add(code)
                                expanded.append({"code": code, "label": label})
                    except Exception as sub_err:
                        logger.warning(f"Subtree SPARQL failed for prefix '{prefix}' ({sub_err}); skipping expansion")
                        if r["code"] not in seen_codes:
                            seen_codes.add(r["code"])
                            expanded.append(r)
                results = expanded

        # ------------------------------------------------------------------ #
        # Mode B: CPV code → label or subtree expansion                       #
        # ------------------------------------------------------------------ #
        if cpv_code:
            clean_code = cpv_code.strip().replace("*", "")

            if include_subtree:
                prefix = clean_code.rstrip("0") or clean_code[:2]
                sparql = (
                    "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>\n"
                    "SELECT DISTINCT ?code ?label WHERE {\n"
                    "  ?concept skos:inScheme <http://publications.europa.eu/resource/authority/cpv> ;\n"
                    "           skos:notation ?code ;\n"
                    "           skos:prefLabel ?label .\n"
                    f'  FILTER(LANG(?label) = "{lang_tag}")\n'
                    f'  FILTER(STRSTARTS(STR(?code), "{prefix}"))\n'
                    "}\n"
                    "ORDER BY ?code\n"
                    "LIMIT 200"
                )
            else:
                padded = clean_code.ljust(8, "0")[:8]
                sparql = (
                    "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>\n"
                    "SELECT DISTINCT ?code ?label WHERE {\n"
                    "  ?concept skos:inScheme <http://publications.europa.eu/resource/authority/cpv> ;\n"
                    "           skos:notation ?code ;\n"
                    "           skos:prefLabel ?label .\n"
                    f'  FILTER(LANG(?label) = "{lang_tag}")\n'
                    f'  FILTER(STR(?code) = "{padded}")\n'
                    "}\n"
                    "LIMIT 5"
                )

            try:
                bindings = _query_cpv_sparql(sparql)
                code_results = [
                    {
                        "code": b.get("code", {}).get("value", ""),
                        "label": b.get("label", {}).get("value", ""),
                    }
                    for b in bindings
                    if b.get("code", {}).get("value")
                ]
                logger.info(f"SPARQL returned {len(code_results)} CPV entry/entries for code '{cpv_code}'")
                results.extend(code_results)
            except Exception as sparql_err:
                logger.warning(f"SPARQL CPV code lookup failed ({sparql_err}); using static index")
                source = "static index (SPARQL unavailable)"
                results.extend(_static_lookup_code(clean_code, include_subtree))

            if not results and source == "SPARQL":
                logger.info("SPARQL returned 0 results for code lookup; using static index")
                source = "SPARQL + static index"
                results.extend(_static_lookup_code(clean_code, include_subtree))

        # ------------------------------------------------------------------ #
        # Format output                                                        #
        # ------------------------------------------------------------------ #
        # Deduplicate preserving order
        seen_codes: set = set()
        unique: List[Dict[str, str]] = []
        for r in results:
            if r["code"] and r["code"] not in seen_codes:
                seen_codes.add(r["code"])
                unique.append(r)

        if not unique:
            return (
                f"⚠️ No CPV codes found for: **{search_term or cpv_code}**\n\n"
                "**Suggestions:**\n"
                "- Try a different or broader search term\n"
                "- Use a 2-digit CPV division prefix (e.g., '72' for IT, '45' for construction)\n"
                "- Browse the full vocabulary at https://op.europa.eu/en/web/eu-vocabularies/cpv"
            )

        header = [
            "# 🏷️ CPV Code Enrichment\n",
        ]
        if search_term:
            header.append(f"**Search term:** {search_term}")
        if cpv_code:
            header.append(f"**CPV code/prefix:** {cpv_code}")
        if include_subtree:
            header.append("**Mode:** Subtree expansion")
        header.append(f"**Data source:** {source}")
        header.append(f"**Results:** {len(unique)} CPV code(s)\n")
        header.append("---\n")

        table = ["| CPV Code | Label |", "|----------|-------|"]
        for r in unique:
            label_escaped = r["label"].replace("|", "\\|")
            table.append(f"| `{r['code']}` | {label_escaped} |")

        code_list = ", ".join(f'"{r["code"]}"' for r in unique[:10])
        footer = (
            "\n---\n"
            "💡 **Use in search:** Pass these codes to `search_ted_tenders` as:\n"
            f"```\ncpv_codes=[{code_list}]\n```"
        )

        result_text = "\n".join(header + table) + footer
        logger.info(f"get_cpv_enrichment returning {len(unique)} code(s) ({len(result_text)} chars)")
        return result_text

    except Exception as e:
        error_msg = f"Unexpected error in CPV enrichment: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return (
            f"❌ {error_msg}\n\n"
            "Please try again or browse the vocabulary at https://op.europa.eu/en/web/eu-vocabularies/cpv."
        )
