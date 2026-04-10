"""
Supabase Client

Handles database operations and vector search.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from loguru import logger

from app.core.config import settings


class SupabaseClient:
    """Client for Supabase database operations."""
    
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        logger.info("Supabase client initialized")
    
    # ==================== Tender Notices ====================
    
    async def insert_tender(self, tender_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a tender notice."""
        try:
            result = self.client.table("tender_notices").insert(tender_data).execute()
            logger.info(f"Inserted tender: {tender_data.get('notice_id')}")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to insert tender: {str(e)}")
            return None
    
    async def get_tender_by_id(self, notice_id: str) -> Optional[Dict[str, Any]]:
        """Get tender by notice ID."""
        try:
            result = self.client.table("tender_notices")\
                .select("*")\
                .eq("notice_id", notice_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get tender: {str(e)}")
            return None
    
    async def search_tenders(
        self,
        country: Optional[str] = None,
        cpv_code: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search tenders with filters."""
        try:
            query = self.client.table("tender_notices").select("*")
            
            if country:
                query = query.eq("country", country)
            if cpv_code:
                query = query.contains("cpv_codes", [cpv_code])
            
            result = query.order("publication_date", desc=True).limit(limit).execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Failed to search tenders: {str(e)}")
            return []
    
    # ==================== Vector Embeddings ====================
    
    async def insert_embedding(
        self,
        notice_id: str,
        embedding: List[float],
        text_content: str
    ) -> bool:
        """Insert tender embedding for vector search."""
        try:
            data = {
                "notice_id": notice_id,
                "embedding": embedding,
                "text_content": text_content,
            }
            
            self.client.table("tender_embeddings").insert(data).execute()
            logger.info(f"Inserted embedding for: {notice_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to insert embedding: {str(e)}")
            return False
    
    async def vector_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        
        Args:
            query_embedding: Query vector
            limit: Max results
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of matching notices with similarity scores
        """
        try:
            # Call the RPC function for vector search
            result = self.client.rpc(
                "match_tender_embeddings",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": similarity_threshold,
                    "match_count": limit
                }
            ).execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []
    
    # ==================== Subscriptions ====================
    
    async def create_subscription(
        self,
        user_id: str,
        name: str,
        query_params: Dict[str, Any],
        notification_channel: str = "email"
    ) -> Optional[str]:
        """Create notification subscription."""
        try:
            data = {
                "user_id": user_id,
                "subscription_name": name,
                "query_parameters": query_params,
                "notification_channel": notification_channel,
                "is_active": True,
            }
            
            result = self.client.table("notification_subscriptions").insert(data).execute()
            
            if result.data:
                subscription_id = result.data[0]["id"]
                logger.info(f"Created subscription: {subscription_id}")
                return subscription_id
            
            return None
        except Exception as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            return None
    
    async def get_active_subscriptions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active subscriptions."""
        try:
            query = self.client.table("notification_subscriptions")\
                .select("*")\
                .eq("is_active", True)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get subscriptions: {str(e)}")
            return []
    
    # ==================== Query History ====================
    
    async def save_query(
        self,
        user_id: str,
        query_text: str,
        expert_query: str,
        results_count: int
    ) -> bool:
        """Save query to history."""
        try:
            data = {
                "user_id": user_id,
                "query_text": query_text,
                "expert_query": expert_query,
                "results_count": results_count,
            }
            
            self.client.table("query_history").insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to save query: {str(e)}")
            return False
    
    async def get_query_history(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get user's query history."""
        try:
            result = self.client.table("query_history")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("queried_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Failed to get query history: {str(e)}")
            return []


# Singleton instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
