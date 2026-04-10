"""
TED API Client

Handles communication with the TED Public API v3.
"""

from typing import List, Dict, Optional, Any
import httpx
from loguru import logger

from app.core.config import settings


class TEDAPIClient:
    """Client for TED Public API."""
    
    def __init__(self):
        self.base_url = settings.ted_api_url
        self.timeout = 30.0
        
    async def search_notices(
        self, 
        query: str, 
        fields: List[str],
        page: int = 1,
        limit: int = 10,
        scope: str = "ACTIVE",
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Search TED notices using expert query.
        
        Args:
            query: Expert search query with SORT BY clause
            fields: List of fields to return
            page: Page number for pagination
            limit: Number of results per page
            scope: "ACTIVE", "ALL", or other scope
            timeout: Request timeout in seconds
            
        Returns:
            API response dict with 'notices' array
        """
        endpoint = f"{self.base_url}/notices/search"
        
        headers = {
            "accept": "*/*",
            "Content-Type": "application/json",
        }
        
        payload = {
            "query": query,
            "fields": fields,
            "page": page,
            "limit": limit,
            "scope": scope,
            "checkQuerySyntax": False,
            "paginationMode": "PAGE_NUMBER",
            "onlyLatestVersions": False,
        }
        
        logger.debug(f"TED API Request: query='{query}', page={page}, limit={limit}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=timeout or self.timeout
                )
                
                response.raise_for_status()
                data = response.json()
                
                notices = data.get('notices', [])
                logger.info(f"TED API Success: {len(notices)} notices returned (page {page})")
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"TED API HTTP Error: {e.response.status_code} - {e.response.text}")
            return {
                "error": {
                    "type": "HTTP_ERROR",
                    "status_code": e.response.status_code,
                    "message": e.response.text
                },
                "notices": []
            }
        except httpx.RequestError as e:
            logger.error(f"TED API Request Error: {str(e)}")
            return {
                "error": {
                    "type": "REQUEST_ERROR",
                    "message": str(e)
                },
                "notices": []
            }
        except Exception as e:
            logger.error(f"TED API Unexpected Error: {str(e)}")
            return {
                "error": {
                    "type": "UNKNOWN_ERROR",
                    "message": str(e)
                },
                "notices": []
            }
    
    async def get_notice_by_id(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single notice by ID.
        
        Args:
            notice_id: Notice document number (ND field)
            
        Returns:
            Notice data or None if not found
        """
        query = f"ND={notice_id} SORT BY publication-date DESC"
        
        fields = [
            "ND", "notice-identifier", "notice-title", "notice-type",
            "publication-date", "classification-cpv", "country-origin",
            "buyer-name", "deadline-date-lot", "estimated-value-lot",
            "description-lot", "description-proc", "links"
        ]
        
        result = await self.search_notices(query, fields, limit=1)
        
        if result.get("notices"):
            return result["notices"][0]
        
        return None


# Singleton instance
_ted_client: Optional[TEDAPIClient] = None


def get_ted_client() -> TEDAPIClient:
    """Get or create TED API client instance."""
    global _ted_client
    if _ted_client is None:
        _ted_client = TEDAPIClient()
    return _ted_client
