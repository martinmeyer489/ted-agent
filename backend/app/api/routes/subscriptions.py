"""
Subscription and notification endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import List
import uuid

from app.models.schemas import SubscriptionRequest, SubscriptionResponse
from app.services import TEDQueryBuilder
from app.services.supabase_client import get_supabase_client
from loguru import logger

router = APIRouter()


@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(request: SubscriptionRequest):
    """
    Create a new notification subscription.
    
    Monitors for new tenders matching the query.
    """
    try:
        # Build query parameters
        builder = TEDQueryBuilder()
        
        if request.countries:
            builder.countries(request.countries)
        
        if request.cpv_codes:
            for cpv in request.cpv_codes:
                builder.cpv_code(cpv)
        
        if request.query:
            builder.title_contains(request.query)
        
        expert_query = builder.build()
        
        # Save to database
        db = get_supabase_client()
        
        query_params = {
            "query": request.query,
            "expert_query": expert_query,
            "countries": request.countries,
            "cpv_codes": request.cpv_codes,
            "frequency": request.frequency,
        }
        
        # Use a test user ID for now
        user_id = "test-user"
        
        subscription_id = await db.create_subscription(
            user_id=user_id,
            name=request.name,
            query_params=query_params,
            notification_channel=request.notification_channel
        )
        
        if not subscription_id:
            raise HTTPException(status_code=500, detail="Failed to create subscription")
        
        from datetime import datetime
        return SubscriptionResponse(
            subscription_id=subscription_id,
            name=request.name,
            is_active=True,
            created_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create subscription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions")
async def list_subscriptions():
    """List all active subscriptions for the user."""
    try:
        db = get_supabase_client()
        
        # Use test user for now
        user_id = "test-user"
        
        subscriptions = await db.get_active_subscriptions(user_id)
        
        return {
            "count": len(subscriptions),
            "subscriptions": subscriptions
        }
        
    except Exception as e:
        logger.error(f"List subscriptions failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str):
    """Delete/deactivate a subscription."""
    try:
        # TODO: Implement deactivation in database
        return {
            "status": "success",
            "message": f"Subscription {subscription_id} deactivated"
        }
        
    except Exception as e:
        logger.error(f"Delete subscription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
