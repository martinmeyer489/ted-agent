"""
Pydantic models for API requests and responses.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request for tender search."""
    query: str = Field(..., description="Natural language or expert search query")
    countries: Optional[List[str]] = Field(None, description="Country codes or names")
    cpv_codes: Optional[List[str]] = Field(None, description="CPV classification codes")
    published_after: Optional[str] = Field(None, description="Publication date filter (YYYY-MM-DD)")
    published_before: Optional[str] = Field(None, description="Publication date filter (YYYY-MM-DD)")
    max_results: int = Field(50, description="Maximum number of results", gt=0, le=500)


class TenderNotice(BaseModel):
    """Tender notice data."""
    notice_id: str
    title: str
    description: Optional[str] = None
    country: str
    publication_date: str
    deadline: Optional[str] = None
    cpv_codes: List[str] = []
    buyer_name: Optional[str] = None
    estimated_value: Optional[float] = None
    links: Optional[List[str]] = None
    raw_data: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Response for tender search."""
    query: str
    expert_query: str
    notices: List[TenderNotice]
    count: int
    error: Optional[str] = None


class ChatMessage(BaseModel):
    """Chat message."""
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: List[ChatMessage]
    stream: bool = Field(False, description="Whether to stream response")


class SubscriptionRequest(BaseModel):
    """Request to create notification subscription."""
    name: str = Field(..., description="Subscription name")
    query: str = Field(..., description="Search query for monitoring")
    countries: Optional[List[str]] = None
    cpv_codes: Optional[List[str]] = None
    notification_channel: str = Field("email", description="Notification channel")
    frequency: str = Field("daily", description="Check frequency: hourly, daily, weekly")


class SubscriptionResponse(BaseModel):
    """Response for subscription creation."""
    subscription_id: str
    name: str
    is_active: bool
    created_at: datetime


class ReportRequest(BaseModel):
    """Request to generate report."""
    report_type: str = Field(..., description="Type: summary, comparison, trend")
    query: Optional[str] = None
    countries: Optional[List[str]] = None
    cpv_codes: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response for tender analysis."""
    notice_id: str
    analysis: Dict[str, Any] = Field(..., description="Analysis results")
    insights: List[str] = Field(..., description="Key insights")
    recommendations: List[str] = Field(..., description="Recommended actions")
