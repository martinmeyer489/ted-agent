"""
TED Agent - Main conversational agent for tender searches.

An Agno agent that helps users find and analyze EU tender opportunities.
"""

from typing import Optional, Dict, List, AsyncIterator
from agno.agent import Agent, RunEvent
from agno.models.ollama import Ollama
from loguru import logger
from datetime import datetime, timedelta

from app.core.config import settings
from app.agents.tools import search_ted_tenders, get_ted_notice_details, query_ted_sparql


# In-memory conversation history store
# Format: {session_id: [(timestamp, role, message), ...]}
_conversation_history: Dict[str, List[tuple]] = {}
_HISTORY_MAX_MESSAGES = 20  # Keep last 20 messages per session
_HISTORY_EXPIRY_HOURS = 24  # Clear history after 24 hours


def _clean_old_sessions():
    """Remove expired conversation sessions."""
    now = datetime.now()
    expired_sessions = []
    
    for session_id, history in _conversation_history.items():
        if history:
            last_timestamp = history[-1][0]
            if now - last_timestamp > timedelta(hours=_HISTORY_EXPIRY_HOURS):
                expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del _conversation_history[session_id]
        logger.info(f"Cleaned expired session: {session_id}")


def _add_to_history(session_id: str, role: str, message: str):
    """Add a message to conversation history."""
    if session_id not in _conversation_history:
        _conversation_history[session_id] = []
    
    _conversation_history[session_id].append((datetime.now(), role, message))
    
    # Keep only recent messages
    if len(_conversation_history[session_id]) > _HISTORY_MAX_MESSAGES:
        _conversation_history[session_id] = _conversation_history[session_id][-_HISTORY_MAX_MESSAGES:]


def _get_conversation_context(session_id: str) -> str:
    """Get conversation history as context string."""
    if session_id not in _conversation_history:
        return ""
    
    history = _conversation_history[session_id]
    if not history:
        return ""
    
    context_parts = ["Here is our conversation history:\n"]
    for timestamp, role, message in history:
        context_parts.append(f"{role.upper()}: {message}\n")
    
    return "\n".join(context_parts)


class TEDAgent:
    """
    TED Agent for searching and analyzing EU tender notices.
    
    This agent can:
    - Search TED database using natural language
    - Filter by countries and CPV codes
    - Provide formatted tender information
    - Answer questions about tender opportunities
    """
    
    def __init__(self):
        """Initialize the TED agent with Ollama model and TED search tool."""
        
        # Configure Ollama model
        # Note: For Ollama Cloud, the API key should be in the Authorization header
        # which is handled via client_params
        model = Ollama(
            id=settings.ollama_chat_model,
            host=settings.ollama_api_url,
            client_params={
                "headers": {
                    "Authorization": f"Bearer {settings.ollama_api_key}"
                }
            } if settings.ollama_api_key else None,
        )
        
        # Create agent with instructions and tools
        self.agent = Agent(
            name="TED Tender Search Agent",
            model=model,
            tools=[search_ted_tenders, get_ted_notice_details],  # SPARQL temporarily disabled for debugging
            instructions=[
                "You are a helpful assistant specialized in finding EU public procurement opportunities.",
                "You help users search the TED (Tenders Electronic Daily) database for tender notices.",
                "",
                "## CRITICAL: Tool Output Rules",
                "⚠️ When a tool returns results, you MUST:",
                "1. Show the COMPLETE tool output to the user",
                "2. Do NOT summarize or truncate the results",
                "3. Include ALL markdown tables, data, and formatting from the tool",
                "4. If a tool returns formatted markdown (tables/headings), show it exactly as returned",
                "",
                "## Available Tools:",
                "1. **search_ted_tenders** - Search for tenders by keywords, countries, CPV codes, and notice types",
                "2. **get_ted_notice_details** - Get complete details for a specific notice by ID",
                "",
                "## Tool Selection Guide:",
                "",
                "**Use search_ted_tenders when:**",
                "- User wants to find tenders by keywords (e.g., 'software', 'construction')",
                "- Filtering by country, CPV code, or notice type",
                "- Browsing recent notices",
                "- Any general searches including award winners",
                "",
                "**Use get_ted_notice_details when:**",
                "- User wants full details of a specific tender by ID",
                "- Following up on a search result to see more information",
                "",
                "## Your Capabilities:",
                "",
                "When users ask about tenders, contracts, or procurement opportunities:",
                "1. Extract the key search terms (e.g., 'software', 'IT services', 'construction')",
                "2. Identify any countries mentioned (e.g., 'Germany', 'France', 'Poland')",
                "3. Identify any CPV codes if mentioned (e.g., '72000000' for IT services)",
                "4. Identify any notice types (e.g., 'award notices', 'contract notices', 'design contests')",
                "5. Use the search_ted_tenders tool to search the TED database",
                "6. Present the results in a clear, user-friendly format",
                "",
                "## Notice Type Filtering:",
                "Users can filter by specific notice types. Common types include:",
                "- **Contract Notices (cn-standard)**: New procurement opportunities (open tenders)",
                "- **Award Notices (can-standard)**: Contracts that have been awarded",
                "- **Modification Notices (can-modif)**: Changes to existing contracts",
                "- **Design Contest Notices (cn-desg)**: Design competitions",
                "- **Prior Information Notices (pin-only)**: Advance notice of future procurement",
                "",
                "When users mention:",
                "- 'award notices', 'awarded contracts', 'winners' → use notice_types=['can-standard']",
                "- 'new tenders', 'open opportunities', 'contract notices' → use notice_types=['cn-standard']",
                "- 'design contests', 'design competitions' → use notice_types=['cn-desg']",
                "- 'modifications', 'changes to contracts' → use notice_types=['can-modif']",
                "",
                "## Result Display Behavior:",
                "- For searches with MORE than 5 results: Shows a compact table with summary information",
                "- For searches with 5 or FEWER results: Shows full details for each tender",
                "- When compact view is shown: Tell the user they can ask for details on specific tenders by number",
                "",
                "## When Users Want More Details:",
                "If a user asks for details on a specific tender from the list:",
                "- If they reference a tender by number (e.g., 'Show me #3'), extract the Notice ID from the results",
                "- Use the get_ted_notice_details tool with that Notice ID",
                "- Present the full HTML-converted details",
                "",
                "CPV Code Reference:",
                "- 45000000: Construction work",
                "- 71000000: Architectural and engineering services",
                "- 72000000: IT services: consulting, software development, Internet and support",
                "- 73000000: Research and development services",
                "- 75000000: Administration, defence and social security services",
                "- 80000000: Education and training services",
                "- 85000000: Health and social work services",
                "- 90000000: Sewage, refuse, cleaning and environmental services",
                "",
                "Be conversational and helpful. If the search returns no results, suggest alternative search terms.",
                "Always use the tool to get real data - never make up tender information.",
                "Present search results in a clear, well-formatted manner using the markdown tables provided.",
                "",
                "Example interactions:",
                "User: 'Find software development contracts in Germany'",
                "→ Search with query='software development', countries=['Germany']",
                "",
                "User: 'Show me IT services tenders'",
                "→ Search with query='IT services' or cpv_codes=['72000000']",
                "",
                "User: 'Any construction projects in France and Spain?'",
                "→ Search with query='construction', countries=['France', 'Spain']",
                "",
                "User: 'Show me awarded IT contracts in Poland'",
                "→ Search with query='IT', countries=['Poland'], notice_types=['can-standard']",
                "",
                "User: 'Find design contest notices'",
                "→ Search with notice_types=['cn-desg']",
                "",
                "User: 'Get details for notice 123456-2024'",
                "→ Use get_ted_notice_details with notice_id='123456-2024'",
            ],
            markdown=True,
            show_tool_calls=False,  # Don't show tool calls, just results
            debug_mode=False,
        )
        
        logger.info(f"TED Agent initialized with model: {settings.ollama_chat_model}")
    
    async def run(self, message: str, session_id: Optional[str] = None) -> str:
        """
        Run the agent with a user message.
        
        Args:
            message: User's message/question
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Agent's response as a string
        """
        try:
            logger.info(f"Agent received message: '{message}' (session: {session_id or 'new'})")
            
            # Clean old sessions periodically
            _clean_old_sessions()
            
            # Build message with conversation context if session exists
            if session_id:
                context = _get_conversation_context(session_id)
                if context:
                    # Prepend context to the message
                    full_message = f"{context}\n\nUser's current message: {message}"
                    logger.info(f"Added conversation context ({len(context)} chars)")
                else:
                    full_message = message
                
                # Store user message in history
                _add_to_history(session_id, "user", message)
            else:
                full_message = message
            
            # Run agent with message
            response = await self.agent.arun(
                full_message, 
                stream=False
            )
            
            # Extract response content - handle different response types
            if hasattr(response, 'content'):
                result = response.content
            elif hasattr(response, 'messages') and response.messages:
                # If response has messages, concatenate all assistant messages
                result = "\n\n".join(
                    msg.content for msg in response.messages 
                    if hasattr(msg, 'role') and msg.role == 'assistant' and hasattr(msg, 'content')
                )
            else:
                result = str(response)
            
            # Store assistant response in history
            if session_id:
                _add_to_history(session_id, "assistant", result)
            
            logger.info(f"Agent response length: {len(result)} characters")
            logger.debug(f"Agent response preview: {result[:500]}")
            return result
            
        except Exception as e:
            logger.error(f"Error running TED agent: {str(e)}", exc_info=True)
            return f"I apologize, but I encountered an error while processing your request: {str(e)}\n\nPlease try rephrasing your question or contact support if the issue persists."
    
    async def run_stream(self, message: str, session_id: Optional[str] = None) -> AsyncIterator[str]:
        """
        Run the agent with streaming response.
        
        Args:
            message: User's message/question
            session_id: Optional session ID for conversation continuity
            
        Yields:
            Chunks of the agent's response as they are generated
        """
        try:
            logger.info(f"Agent received streaming request: '{message}' (session: {session_id or 'new'})")
            
            # Clean old sessions periodically
            _clean_old_sessions()
            
            # Build message with conversation context if session exists
            if session_id:
                context = _get_conversation_context(session_id)
                if context:
                    full_message = f"{context}\n\nUser's current message: {message}"
                    logger.info(f"Added conversation context ({len(context)} chars)")
                else:
                    full_message = message
                
                # Store user message in history
                _add_to_history(session_id, "user", message)
            else:
                full_message = message
            
            # Run agent with streaming enabled
            complete_response = []
            
            stream = await self.agent.arun(
                full_message, 
                stream=True
            )
            
            # Process each chunk from the stream
            async for chunk in stream:
                # Extract content from the chunk based on event type
                if chunk.event == RunEvent.run_content:
                    content = chunk.content
                    if content:
                        complete_response.append(content)
                        yield content
                        
            # Store complete assistant response in history
            if session_id and complete_response:
                full_response = "".join(complete_response)
                _add_to_history(session_id, "assistant", full_response)
                logger.info(f"Streaming complete. Total response length: {len(full_response)} characters")
                
        except Exception as e:
            logger.error(f"Error in streaming TED agent: {str(e)}", exc_info=True)
            error_msg = f"I apologize, but I encountered an error while processing your request: {str(e)}\n\nPlease try rephrasing your question or contact support if the issue persists."
            yield error_msg
    
    def run_sync(self, message: str, session_id: Optional[str] = None) -> str:
        """
        Synchronous wrapper for run method.
        
        Args:
            message: User's message/question
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Agent's response as a string
        """
        import asyncio
        return asyncio.run(self.run(message, session_id))


# Global agent instance
_agent_instance: Optional[TEDAgent] = None


def get_ted_agent() -> TEDAgent:
    """Get or create the global TED agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = TEDAgent()
    return _agent_instance
