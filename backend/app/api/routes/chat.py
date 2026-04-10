"""
Chat endpoints for conversational interface with TED agent.

Uses Agno agent with TED API search tool for intelligent tender discovery.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger
import json

from app.agents.ted_agent import get_ted_agent


router = APIRouter()


class ChatMessage(BaseModel):
    """Simple chat message for the new streamlined interface."""
    message: str = Field(..., description="User's message", min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    stream: bool = Field(False, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="Agent's response")
    session_id: Optional[str] = Field(None, description="Session ID")


@router.post("/chat")
async def chat(request: ChatMessage):
    """
    Chat with the TED agent - ask questions in natural language.
    
    The agent uses the TED API search tool to find tender notices based on your query.
    
    Set `stream=true` in the request to get a streaming response (Server-Sent Events).
    
    Example queries:
    - "Find software development contracts in Germany"
    - "Show me IT services tenders in France"
    - "Any construction projects in Spain?"
    - "Search for tenders with CPV code 72000000"
    - "What tender opportunities are available for consulting services?"
    
    The agent will:
    1. Understand your natural language request
    2. Extract search parameters (keywords, countries, CPV codes)
    3. Call the TED API search tool
    4. Return formatted results with tender details
    """
    try:
        logger.info(f"Chat request: '{request.message[:100]}...' (session: {request.session_id or 'new'}, stream: {request.stream})")
        
        # Get agent instance
        agent = get_ted_agent()
        
        # Return streaming response if requested
        if request.stream:
            async def event_generator():
                """Generate Server-Sent Events for streaming response."""
                try:
                    async for chunk in agent.run_stream(
                        message=request.message,
                        session_id=request.session_id
                    ):
                        # Format as Server-Sent Event
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    
                    # Send completion event
                    yield f"data: {json.dumps({'event': 'done'})}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error in stream generator: {str(e)}", exc_info=True)
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable buffering in nginx
                }
            )
        
        # Non-streaming response
        response = await agent.run(
            message=request.message,
            session_id=request.session_id
        )
        
        return ChatResponse(
            response=response,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """Health check for chat service."""
    try:
        agent = get_ted_agent()
        return {
            "status": "healthy",
            "service": "chat",
            "agent": "TED Tender Search Agent",
            "model": agent.agent.model.id if hasattr(agent.agent, 'model') else "unknown"
        }
    except Exception as e:
        logger.error(f"Chat health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Chat service unhealthy: {str(e)}"
        )
