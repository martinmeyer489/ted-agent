"""
AgentOS API endpoints for agent-ui compatibility.

Provides the standard AgentOS API interface for the agent-ui frontend.
"""

from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json
from loguru import logger
from sse_starlette.sse import EventSourceResponse
import asyncio
import time as time_module

from app.agents.ted_agent import get_ted_agent


router = APIRouter()


# ============================================================================
# Helpers
# ============================================================================

def _format_tool_call(tc: Dict[str, Any], started: bool = True) -> Dict[str, Any]:
    """Format a tool call dict from Agno into the agent-ui ToolCall format."""
    tool_name = tc.get("tool_name", "unknown")
    tool_args = tc.get("tool_args", {})
    if isinstance(tool_args, str):
        try:
            tool_args = json.loads(tool_args)
        except (json.JSONDecodeError, TypeError):
            tool_args = {"raw": tool_args}
    
    # Get execution time from metrics if available
    metrics = tc.get("metrics", {})
    exec_time = 0
    if isinstance(metrics, dict):
        exec_time = metrics.get("time", 0) or 0
    
    tc_id = tc.get("tool_call_id") or f"{tool_name}-{tc.get('created_at', int(time_module.time()))}"
    
    return {
        "role": "tool",
        "content": tc.get("content") if not started else None,
        "tool_call_id": tc_id,
        "tool_name": tool_name,
        "tool_args": tool_args if isinstance(tool_args, dict) else {},
        "tool_call_error": bool(tc.get("tool_call_error", False)),
        "metrics": {"time": exec_time},
        "created_at": tc.get("created_at", int(time_module.time())),
    }


# ============================================================================
# Models
# ============================================================================

class Agent(BaseModel):
    """Agent model for listing available agents."""
    agent_id: str
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[str]] = None


class RunRequest(BaseModel):
    """Request to run an agent."""
    message: str = Field(..., description="User's message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    stream: bool = Field(default=True, description="Whether to stream the response")


class RunResponse(BaseModel):
    """Response from agent run."""
    run_id: str
    agent_id: str
    session_id: Optional[str] = None
    content: str
    created_at: datetime


class Session(BaseModel):
    """Session model."""
    session_id: str
    agent_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class SessionRun(BaseModel):
    """Run within a session."""
    run_id: str
    role: str  # 'user' or 'assistant'
    content: str
    created_at: datetime


# ============================================================================
# In-memory storage (for simplicity)
# ============================================================================

_sessions: Dict[str, Dict[str, Any]] = {}
_runs: Dict[str, List[SessionRun]] = {}


# ============================================================================
# Agent Endpoints
# ============================================================================

@router.get("/agents", response_model=List[Agent])
async def list_agents():
    """
    List all available agents.
    
    For the TED Bot, we have one main agent.
    """
    agent = get_ted_agent()
    
    return [
        Agent(
            agent_id="ted-agent",
            name="TED Tender Search Agent",
            description="AI-powered agent for discovering and analyzing EU tender opportunities from the TED database",
            model=agent.agent.model.id if hasattr(agent.agent, 'model') else "llama3.1",
            tools=["search_ted_tenders", "get_ted_notice_details"]
        )
    ]


@router.get("/teams")
async def list_teams():
    """
    List all teams.
    
    For this implementation, we don't use teams - just individual agents.
    Returns empty list to satisfy agent-ui requirements.
    """
    return []


@router.post("/agents/{agent_id}/runs")
async def run_agent(
    agent_id: str, 
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    stream: bool = Form(True)
):
    """
    Run an agent with a message.
    
    Supports both streaming and non-streaming responses.
    Accepts form data (for frontend compatibility) or JSON.
    """
    try:
        # Get or create session
        session_id_value = session_id or str(uuid.uuid4())
        if session_id_value not in _sessions:
            _sessions[session_id_value] = {
                "session_id": session_id_value,
                "agent_id": agent_id,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "message_count": 0
            }
            _runs[session_id_value] = []
        
        # Update session
        _sessions[session_id_value]["updated_at"] = datetime.now()
        _sessions[session_id_value]["message_count"] += 1
        
        # Add user message to runs
        user_run = SessionRun(
            run_id=str(uuid.uuid4()),
            role="user",
            content=message,
            created_at=datetime.now()
        )
        _runs[session_id_value].append(user_run)
        
        logger.info(f"Running agent {agent_id} with message: '{message[:100]}...'")
        
        # Get agent
        agent = get_ted_agent()
        
        if stream:
            # Stream response using Agno's native streaming
            async def event_generator():
                try:
                    run_id = str(uuid.uuid4())
                    now = int(time_module.time())
                    
                    # Send RunStarted event
                    yield json.dumps({
                        "event": "RunStarted",
                        "session_id": session_id_value,
                        "agent_id": agent_id,
                        "run_id": run_id,
                        "created_at": now,
                    })
                    
                    accumulated_content = ""
                    seen_tool_ids = set()
                    
                    async for run_response in agent.run_stream(
                        message=message,
                        session_id=session_id_value,
                    ):
                        event_type = getattr(run_response, 'event', None)
                        
                        if event_type == "ToolCallStarted":
                            # Extract new tool calls and send ToolCallStarted events
                            tools = getattr(run_response, 'tools', None) or []
                            for tc in tools:
                                tc_name = tc.get("tool_name", "unknown")
                                tc_id = tc.get("tool_call_id") or f"{tc_name}-{tc.get('created_at', int(time_module.time()))}"
                                if tc_id not in seen_tool_ids:
                                    seen_tool_ids.add(tc_id)
                                    yield json.dumps({
                                        "event": "ToolCallStarted",
                                        "session_id": session_id_value,
                                        "run_id": run_id,
                                        "tool": _format_tool_call(tc, started=True),
                                        "created_at": int(time_module.time()),
                                    })
                        
                        elif event_type == "ToolCallCompleted":
                            # Send ToolCallCompleted for tools that have results
                            tools = getattr(run_response, 'tools', None) or []
                            for tc in tools:
                                yield json.dumps({
                                    "event": "ToolCallCompleted",
                                    "session_id": session_id_value,
                                    "run_id": run_id,
                                    "tool": _format_tool_call(tc, started=False),
                                    "created_at": int(time_module.time()),
                                })
                        
                        elif event_type == "RunResponse":
                            # Content delta from the model
                            delta = getattr(run_response, 'content', None)
                            if delta:
                                accumulated_content += str(delta)
                                yield json.dumps({
                                    "event": "RunContent",
                                    "content": accumulated_content,
                                    "session_id": session_id_value,
                                    "run_id": run_id,
                                    "created_at": int(time_module.time()),
                                })
                        
                        elif event_type == "RunCompleted":
                            # RunCompleted may have final content
                            final_content = getattr(run_response, 'content', None)
                            if final_content:
                                accumulated_content = str(final_content)
                    
                    # Store conversation in history
                    if accumulated_content:
                        from app.agents.ted_agent import _add_to_history
                        _add_to_history(session_id_value, "assistant", accumulated_content)
                    
                    # Add runs to in-memory storage
                    assistant_run = SessionRun(
                        run_id=run_id,
                        role="assistant",
                        content=accumulated_content,
                        created_at=datetime.now()
                    )
                    _runs[session_id_value].append(assistant_run)
                    
                    # Send RunCompleted with final content
                    yield json.dumps({
                        "event": "RunCompleted",
                        "content": accumulated_content,
                        "session_id": session_id_value,
                        "run_id": run_id,
                        "created_at": int(time_module.time()),
                    })
                    
                except Exception as e:
                    logger.error(f"Error in event generator: {str(e)}", exc_info=True)
                    yield json.dumps({
                        "event": "RunError",
                        "error": str(e)
                    })
            
            return EventSourceResponse(event_generator())
        
        else:
            # Non-streaming response
            response = await agent.run(
                message=message,
                session_id=session_id_value
            )
            
            run_id = str(uuid.uuid4())
            assistant_run = SessionRun(
                run_id=run_id,
                role="assistant",
                content=response,
                created_at=datetime.now()
            )
            _runs[session_id_value].append(assistant_run)
            
            return RunResponse(
                run_id=run_id,
                agent_id=agent_id,
                session_id=session_id_value,
                content=response,
                created_at=datetime.now()
            )
    
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error running agent: {str(e)}"
        )


# ============================================================================
# Session Endpoints
# ============================================================================

@router.get("/sessions", response_model=List[Session])
async def list_sessions():
    """List all sessions."""
    sessions = []
    for session_data in _sessions.values():
        sessions.append(Session(**session_data))
    
    # Sort by updated_at descending
    sessions.sort(key=lambda x: x.updated_at, reverse=True)
    return sessions


@router.get("/sessions/{session_id}/runs", response_model=List[SessionRun])
async def get_session_runs(session_id: str):
    """Get all runs for a session."""
    if session_id not in _runs:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return _runs[session_id]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    del _sessions[session_id]
    if session_id in _runs:
        del _runs[session_id]
    
    return {"message": f"Session {session_id} deleted"}


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health():
    """Health check endpoint."""
    try:
        agent = get_ted_agent()
        return {
            "status": "healthy",
            "service": "agentos",
            "agents": 1,
            "sessions": len(_sessions),
            "model": agent.agent.model.id if hasattr(agent.agent, 'model') else "unknown"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
