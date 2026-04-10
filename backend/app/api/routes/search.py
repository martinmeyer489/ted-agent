"""
Search endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import SearchRequest, SearchResponse, TenderNotice
from app.services import get_ted_client, TEDQueryBuilder, DEFAULT_NOTICE_FIELDS
from app.services.supabase_client import get_supabase_client
from loguru import logger

router = APIRouter()


@router.post("/tenders/search", response_model=SearchResponse)
async def search_tenders(request: SearchRequest) -> SearchResponse:
    """
    Search for tender notices.
    
    Accepts natural language or structured query parameters.
    """
    try:
        # Build expert query
        builder = TEDQueryBuilder()
        
        # Add filters from request
        if request.countries:
            builder.countries(request.countries)
        
        if request.cpv_codes:
            for cpv in request.cpv_codes:
                builder.cpv_code(cpv)
        
        if request.published_after:
            builder.published_after(request.published_after)
        
        if request.published_before:
            builder.published_before(request.published_before)
        
        # If query contains words, add title search
        if request.query and not request.query.startswith("ND="):
            builder.title_contains(request.query)
        
        expert_query = builder.build(sort_by="publication-date DESC")
        logger.info(f"Expert query: {expert_query}")
        
        # Execute TED API search
        ted_client = get_ted_client()
        result = await ted_client.search_notices(
            query=expert_query,
            fields=DEFAULT_NOTICE_FIELDS,
            limit=min(request.max_results, 100),
            scope="ACTIVE"
        )
        
        # Parse notices
        notices: List[TenderNotice] = []
        raw_notices = result.get("notices", [])
        logger.debug(f"Parsing {len(raw_notices)} notices")
        
        for idx, notice_data in enumerate(raw_notices):
            try:
                # Helper to extract multilingual text (prefer English)
                def get_multilang(field, default=""):
                    val = notice_data.get(field)
                    if val is None:
                        return default
                    
                    # Handle dict with language keys
                    if isinstance(val, dict):
                        result = val.get('eng', val.get('ENG'))
                        if result is None:
                            # Get first available language
                            result = next(iter(val.values()), default) if val else default
                        # If result is still a list, get first item
                        if isinstance(result, list):
                            return result[0] if result else default
                        return str(result) if result else default
                    
                    # Handle list
                    elif isinstance(val, list):
                        if not val:
                            return default
                        item = val[0]
                        # If list item is dict, recurse
                        if isinstance(item, dict):
                            result = item.get('eng', item.get('ENG'))
                            if result is None:
                                result = next(iter(item.values()), default) if item else default
                            if isinstance(result, list):
                                return result[0] if result else default
                            return str(result) if result else default
                        return str(item)
                    
                    # Handle string
                    return str(val)
                
                # Extract title
                title = get_multilang("notice-title", notice_data.get("ND", "Untitled"))
                
                # Extract description (try multiple fields)
                description = (
                    get_multilang("description-lot") or 
                    get_multilang("description-glo") or 
                    get_multilang("description-part") or
                    None
                )
                
                # Extract buyer name
                buyer = (
                    get_multilang("organisation-name-buyer") or
                    get_multilang("buyer-name") or
                    None
                )
                
                # Extract simple fields
                notice_id = notice_data.get("ND", f"notice-{idx}")
                pub_date = notice_data.get("publication-date", "")
                cpv_codes = notice_data.get("classification-cpv", [])
                
                # Extract country (from various fields or title)
                country = None
                
                # Try various country fields
                if notice_data.get("place-of-performance-country-part"):
                    val = notice_data["place-of-performance-country-part"]
                    country = val[0] if isinstance(val, list) and val else val
                
                # If no country field, try to extract from title
                if not country or country == "EU":
                    title_str = str(title)
                    # Title format is usually "Country – Title"
                    if '–' in title_str:
                        country_part = title_str.split('–')[0].strip()
                        # Keep first word as country
                        country = country_part.split()[0] if country_part else "EU"
                
                if not country:
                    country = "EU"
                
                # Links - not in the new field list
                links = []
                
                notice = TenderNotice(
                    notice_id=notice_id,
                    title=title,
                    description=description,
                    country=country,
                    publication_date=pub_date,
                    deadline=None,  # Not in default fields
                    cpv_codes=cpv_codes if isinstance(cpv_codes, list) else [],
                    buyer_name=buyer,
                    estimated_value=None,
                    links=links,
                    raw_data=notice_data
                )
                notices.append(notice)
                logger.debug(f"Parsed notice {idx}: {title[:50]}")
            except Exception as e:
                logger.error(f"Failed to parse notice {idx}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Successfully parsed {len(notices)} out of {len(raw_notices)} notices")
        
        # Filter by country if specified (client-side filtering since API doesn't support it)
        if request.countries:
            country_codes = [c.upper() for c in request.countries]
            country_names = [c.lower() for c in request.countries]
            
            filtered_notices = []
            for notice in notices:
                notice_country = notice.country.upper() if notice.country else ""
                # Check if country matches (by code or name)
                if any(c in notice_country.upper() or c.upper() in notice_country for c in country_codes + country_names):
                    filtered_notices.append(notice)
            
            logger.info(f"Country filter applied: {len(filtered_notices)} out of {len(notices)} notices match {request.countries}")
            notices = filtered_notices
        
        # Save to database
        db = get_supabase_client()
        for notice in notices[:10]:  # Save first 10
            tender_data = {
                "notice_id": notice.notice_id,
                "title": notice.title,
                "description": notice.description,
                "country": notice.country,
                "publication_date": notice.publication_date,
                "deadline": notice.deadline,
                "cpv_codes": notice.cpv_codes,
                "buyer_name": notice.buyer_name,
                "raw_data": notice.raw_data,
            }
            await db.insert_tender(tender_data)
        
        return SearchResponse(
            query=request.query,
            expert_query=expert_query,
            notices=notices[:request.max_results],
            count=len(notices),
            error=result.get("error", {}).get("message") if "error" in result else None
        )
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenders/{notice_id}", response_model=TenderNotice)
async def get_tender(notice_id: str) -> TenderNotice:
    """Get a specific tender by ID."""
    try:
        # Try database first
        db = get_supabase_client()
        tender = await db.get_tender_by_id(notice_id)
        
        if tender:
            return TenderNotice(
                notice_id=tender["notice_id"],
                title=tender["title"],
                description=tender.get("description"),
                country=tender["country"],
                publication_date=tender["publication_date"],
                deadline=tender.get("deadline"),
                cpv_codes=tender.get("cpv_codes", []),
                buyer_name=tender.get("buyer_name"),
                raw_data=tender.get("raw_data")
            )
        
        # Fallback to TED API
        ted_client = get_ted_client()
        notice_data = await ted_client.get_notice_by_id(notice_id)
        
        if not notice_data:
            raise HTTPException(status_code=404, detail="Notice not found")
        
        return TenderNotice(
            notice_id=notice_data.get("ND", ""),
            title=notice_data.get("notice-title", ["N/A"])[0],
            description=notice_data.get("description-lot", [""])[0] if notice_data.get("description-lot") else None,
            country=notice_data.get("country-origin", [""])[0],
            publication_date=notice_data.get("publication-date", [""])[0],
            deadline=notice_data.get("deadline-date-lot", [""])[0] if notice_data.get("deadline-date-lot") else None,
            cpv_codes=notice_data.get("classification-cpv", []),
            buyer_name=notice_data.get("buyer-name", [""])[0] if notice_data.get("buyer-name") else None,
            raw_data=notice_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get tender failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
