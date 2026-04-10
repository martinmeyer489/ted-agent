# Agent Design - Agno Implementation

## Overview

The TED Bot uses the Agno framework to implement a multi-agent system where specialized agents handle different aspects of tender discovery, analysis, and monitoring.

## Agno Framework Architecture

### What is Agno?

Agno is a Python framework for building AI agent applications with:
- **Multi-agent orchestration**: Coordinate multiple specialized agents
- **LLM-agnostic**: Works with any LLM (we use Ollama)
- **Tool integration**: Agents can use tools/functions
- **Memory management**: Conversation history and context
- **Workflow support**: Complex multi-step processes

### Core Concepts

```python
from agno import Agent, Tool, Workflow
from agno.models import OllamaModel

# LLM backend
llm = OllamaModel(model="llama3.1", base_url="http://localhost:11434")

# Agent with tools
agent = Agent(
    name="Search Agent",
    model=llm,
    tools=[search_tenders_tool, filter_results_tool],
    instructions="You help users find relevant tenders...",
    show_tool_calls=True
)

# Execute
response = agent.run("Find IT tenders in Germany")
```

## Agent Architecture

### Agent Hierarchy

```
Main Agent (Orchestrator)
    │
    ├─── Search Agent
    │    ├─ Vector Search Tool
    │    ├─ Keyword Search Tool
    │    └─ Hybrid Search Tool
    │
    ├─── Analysis Agent
    │    ├─ Summarization Tool
    │    ├─ Extraction Tool
    │    └─ Q&A Tool
    │
    ├─── Monitoring Agent
    │    ├─ TED Fetch Tool
    │    ├─ Matcher Tool
    │    └─ Notification Tool
    │
    ├─── Notification Agent
    │    ├─ Subscription Manager
    │    └─ Alert Sender
    │
    └─── Report Agent
         ├─ Aggregation Tool
         ├─ Trend Analysis Tool
         └─ Insight Generator
```

## Agent Specifications

### 1. Main Agent (Orchestrator)

**Purpose**: Route user queries to appropriate specialized agents

**Configuration**:
```python
main_agent = Agent(
    name="TED Bot Orchestrator",
    model=llm,
    instructions="""
    You are TED Bot, an AI assistant for European tender notices.
    Your role is to understand user queries and route them to specialized agents:
    - For searches and filters: use Search Agent
    - For document analysis and summaries: use Analysis Agent
    - For setting up alerts: use Notification Agent
    - For reports and insights: use Report Agent
    
    Always be helpful, precise, and cite sources when providing tender information.
    """,
    tools=[
        delegate_to_search,
        delegate_to_analysis,
        delegate_to_notification,
        delegate_to_report
    ],
    markdown=True
)
```

**Conversation Flow**:
```
User: "Find IT tenders in Germany above 500k EUR"
  ↓
Main Agent analyzes intent → "This is a search query"
  ↓
Delegates to Search Agent with parameters
  ↓
Receives results and formats for user
  ↓
Response: "I found 12 IT tenders in Germany..."
```

### 2. Search Agent

**Purpose**: Execute tender searches using various strategies

**Configuration**:
```python
search_agent = Agent(
    name="Search Agent",
    model=llm,
    instructions="""
    You help users find relevant tenders from the TED database.
    
    Process:
    1. Parse user query to extract search criteria (keywords, countries, CPV codes, values, dates)
    2. Choose appropriate search strategy (keyword, semantic, or hybrid)
    3. Execute search using available tools
    4. Rank and present results clearly
    5. Explain why results are relevant
    
    Always show key details: title, authority, country, value, deadline.
    """,
    tools=[
        keyword_search_tool,
        semantic_search_tool,
        hybrid_search_tool,
        get_tender_details_tool
    ],
    show_tool_calls=True
)
```

**Tools**:

#### keyword_search_tool
```python
@tool
def keyword_search_tool(
    query: str,
    countries: List[str] = None,
    cpv_codes: List[str] = None,
    min_value: float = None,
    max_value: float = None,
    limit: int = 20
) -> List[Dict]:
    """
    Search tenders using keyword matching (PostgreSQL full-text search).
    
    Args:
        query: Search text
        countries: ISO country codes (e.g., ["DE", "FR"])
        cpv_codes: CPV classification codes
        min_value: Minimum tender value
        max_value: Maximum tender value
        limit: Max results
    
    Returns:
        List of matching tenders
    """
    # Implementation uses Supabase client
    results = supabase.from_('tender_notices').\
        text_search('title,description', query).\
        filter('country', 'in', countries if countries else []).\
        filter('value', 'gte', min_value if min_value else 0).\
        limit(limit).\
        execute()
    
    return results.data
```

#### semantic_search_tool
```python
@tool
def semantic_search_tool(
    query: str,
    threshold: float = 0.7,
    limit: int = 20,
    countries: List[str] = None
) -> List[Dict]:
    """
    Search tenders using semantic similarity (vector search).
    
    Args:
        query: Natural language query
        threshold: Similarity threshold (0-1)
        limit: Max results
        countries: Filter by countries
    
    Returns:
        List of matching tenders with similarity scores
    """
    # Generate query embedding
    query_embedding = ollama_client.embeddings(
        model="nomic-embed-text",
        prompt=query
    )["embedding"]
    
    # Vector search in Supabase
    results = supabase.rpc(
        'search_similar_tenders',
        {
            'query_embedding': query_embedding,
            'match_threshold': threshold,
            'match_count': limit
        }
    ).execute()
    
    return results.data
```

#### hybrid_search_tool
```python
@tool
def hybrid_search_tool(
    query: str,
    countries: List[str] = None,
    cpv_codes: List[str] = None,
    limit: int = 20,
    semantic_weight: float = 0.6
) -> List[Dict]:
    """
    Hybrid search combining keyword and semantic search.
    
    Args:
        query: Search query
        countries: Filter countries
        cpv_codes: Filter CPV codes
        limit: Max results
        semantic_weight: Weight for semantic score (0-1), 
                        (1-weight) for keyword score
    
    Returns:
        List of tenders ranked by combined score
    """
    # Get both keyword and semantic results
    keyword_results = keyword_search_tool(query, countries, cpv_codes, limit=limit*2)
    semantic_results = semantic_search_tool(query, countries=countries, limit=limit*2)
    
    # Combine and rerank using weighted scores
    combined = rerank_results(
        keyword_results, 
        semantic_results, 
        semantic_weight
    )
    
    return combined[:limit]
```

### 3. Analysis Agent

**Purpose**: Analyze and summarize tender documents

**Configuration**:
```python
analysis_agent = Agent(
    name="Analysis Agent",
    model=llm,
    instructions="""
    You analyze tender documents and provide insights.
    
    Tasks:
    1. Summarize tender content in clear language
    2. Extract key information: deadlines, requirements, budget
    3. Identify potential risks or challenges
    4. Answer specific questions about tenders
    5. Assess tender suitability based on criteria
    
    Always be objective and cite specific parts of the tender.
    """,
    tools=[
        summarize_tender_tool,
        extract_requirements_tool,
        answer_question_tool,
        assess_suitability_tool
    ],
    markdown=True
)
```

**Tools**:

#### summarize_tender_tool
```python
@tool
def summarize_tender_tool(tender_id: str) -> Dict:
    """
    Generate AI summary of a tender document.
    
    Args:
        tender_id: UUID of tender
    
    Returns:
        Dict with summary and key points
    """
    # Fetch tender
    tender = get_tender_by_id(tender_id)
    
    # Create summarization prompt
    prompt = f"""
    Summarize this tender notice concisely:
    
    Title: {tender['title']}
    Description: {tender['description']}
    Value: {tender['value']} {tender['currency']}
    Deadline: {tender['deadline']}
    
    Provide:
    1. Brief summary (2-3 sentences)
    2. Key requirements
    3. Important dates
    4. Budget information
    """
    
    # Use LLM to summarize
    summary = llm.generate(prompt)
    
    # Cache result
    cache_analysis(tender_id, summary)
    
    return {
        "tender_id": tender_id,
        "summary": summary,
        "generated_at": datetime.now()
    }
```

#### extract_requirements_tool
```python
@tool
def extract_requirements_tool(tender_id: str) -> Dict:
    """
    Extract structured requirements from tender.
    
    Args:
        tender_id: UUID of tender
    
    Returns:
        Dict with categorized requirements
    """
    tender = get_tender_by_id(tender_id)
    
    prompt = f"""
    Extract requirements from this tender:
    {tender['description']}
    
    Categorize into:
    - Technical requirements
    - Financial requirements (certifications, insurance)
    - Administrative requirements (documents needed)
    - Qualification criteria
    
    Format as JSON.
    """
    
    requirements = llm.generate(prompt, response_format="json")
    
    return json.loads(requirements)
```

### 4. Monitoring Agent

**Purpose**: Automated monitoring and matching of new tenders

**Configuration**:
```python
monitoring_agent = Agent(
    name="Monitoring Agent",
    model=llm,
    instructions="""
    You monitor the TED platform for new tenders matching user criteria.
    
    Process:
    1. Fetch new tenders from TED API on schedule
    2. Store and embed new tenders
    3. Check against active notification subscriptions
    4. Trigger notifications for matches
    5. Log activity
    
    Run reliably and handle errors gracefully.
    """,
    tools=[
        fetch_new_tenders_tool,
        match_subscriptions_tool,
        trigger_notification_tool
    ]
)
```

**Scheduled Execution**:
```python
# Run monitoring agent every hour
@scheduler.scheduled_job('interval', hours=1)
def run_monitoring():
    logger.info("Starting scheduled monitoring")
    
    result = monitoring_agent.run(
        "Check for new tenders and match against subscriptions"
    )
    
    logger.info(f"Monitoring complete: {result}")
```

**Tools**:

#### fetch_new_tenders_tool
```python
@tool
def fetch_new_tenders_tool(
    date_from: str = None,
    date_to: str = None
) -> Dict:
    """
    Fetch new tenders from TED API.
    
    Args:
        date_from: Start date (ISO format)
        date_to: End date (ISO format)
    
    Returns:
        Dict with fetch statistics
    """
    # Get last sync timestamp
    last_sync = get_last_sync_timestamp()
    date_from = date_from or last_sync
    
    # Call TED API
    new_tenders = ted_api_client.fetch_notices(
        date_from=date_from,
        date_to=date_to or datetime.now()
    )
    
    # Process and store
    stored = 0
    updated = 0
    
    for tender in new_tenders:
        if tender_exists(tender['ted_id']):
            update_tender(tender)
            updated += 1
        else:
            store_tender(tender)
            generate_embedding(tender)
            stored += 1
    
    # Update sync status
    update_sync_status(stored, updated)
    
    return {
        "fetched": len(new_tenders),
        "new": stored,
        "updated": updated
    }
```

#### match_subscriptions_tool
```python
@tool
def match_subscriptions_tool(tender_id: str) -> List[str]:
    """
    Check if tender matches any active subscriptions.
    
    Args:
        tender_id: UUID of tender to check
    
    Returns:
        List of matching subscription IDs
    """
    tender = get_tender_by_id(tender_id)
    subscriptions = get_active_subscriptions()
    
    matches = []
    
    for sub in subscriptions:
        if matches_criteria(tender, sub['criteria']):
            matches.append(sub['id'])
    
    return matches
```

### 5. Notification Agent

**Purpose**: Manage notification subscriptions and delivery

**Configuration**:
```python
notification_agent = Agent(
    name="Notification Agent",
    model=llm,
    instructions="""
    You manage user notification preferences and deliver alerts.
    
    Responsibilities:
    1. Create/update/delete notification subscriptions
    2. Validate subscription criteria
    3. Send notifications when matches found
    4. Track notification history
    
    Be precise about criteria and confirm user preferences.
    """,
    tools=[
        create_subscription_tool,
        update_subscription_tool,
        delete_subscription_tool,
        send_notification_tool
    ]
)
```

### 6. Report Agent

**Purpose**: Generate insights and reports

**Configuration**:
```python
report_agent = Agent(
    name="Report Agent",
    model=llm,
    instructions="""
    You generate reports and insights about tender activity.
    
    Capabilities:
    1. Aggregate tender statistics
    2. Identify trends over time
    3. Analyze by sector, country, value
    4. Provide actionable insights
    
    Present data clearly with key takeaways.
    """,
    tools=[
        aggregate_statistics_tool,
        trend_analysis_tool,
        sector_analysis_tool,
        generate_insights_tool
    ],
    markdown=True
)
```

## Agent Workflows

### Workflow 1: User Search Query

```python
from agno import Workflow

search_workflow = Workflow(
    name="Tender Search Workflow",
    agents=[main_agent, search_agent]
)

@search_workflow.step
def parse_query(user_input: str):
    """Main agent parses intent"""
    return main_agent.run(user_input)

@search_workflow.step
def execute_search(parsed_query):
    """Search agent executes search"""
    return search_agent.run(parsed_query)

@search_workflow.step 
def format_response(results):
    """Format results for user"""
    return main_agent.run(f"Format these results: {results}")
```

### Workflow 2: Scheduled Monitoring

```python
monitoring_workflow = Workflow(
    name="Tender Monitoring Workflow",
    agents=[monitoring_agent, notification_agent]
)

@monitoring_workflow.step
def fetch_new():
    """Fetch new tenders"""
    return monitoring_agent.run("Fetch new tenders from TED API")

@monitoring_workflow.step
def match_and_notify(new_tenders):
    """Match against subscriptions and notify"""
    for tender in new_tenders:
        matches = match_subscriptions_tool(tender['id'])
        for subscription_id in matches:
            notification_agent.run(
                f"Send notification for tender {tender['id']} to subscription {subscription_id}"
            )
```

## Memory Management

### Conversation Memory

```python
from agno.memory import ConversationMemory

# Each chat session has memory
memory = ConversationMemory(
    session_id="user_session_123",
    max_messages=50  # Keep last 50 messages
)

agent = Agent(
    name="Search Agent",
    model=llm,
    memory=memory,
    tools=[...]
)

# Memory persists across turns
response1 = agent.run("Find IT tenders in Germany")
response2 = agent.run("Show me the ones above 1M EUR")  # Agent remembers previous context
```

### Knowledge Base (RAG)

```python
from agno.knowledge import VectorKnowledge

# Knowledge base of tender data
tender_knowledge = VectorKnowledge(
    embedder=OllamaEmbedder(model="nomic-embed-text"),
    vector_db=SupabaseVectorDB(
        table="tender_embeddings",
        embedding_column="embedding"
    )
)

analysis_agent = Agent(
    name="Analysis Agent",
    model=llm,
    knowledge_base=tender_knowledge,  # Agent can query tender data
    tools=[...]
)
```

## Error Handling

### Agent-Level Error Handling

```python
from agno.exceptions import ToolException, AgentException

agent = Agent(
    name="Search Agent",
    model=llm,
    tools=[search_tool],
    max_retries=3,
    retry_delay=1.0,
    on_error=handle_agent_error
)

def handle_agent_error(error: Exception, context: dict):
    """Custom error handler"""
    logger.error(f"Agent error: {error}", extra=context)
    
    if isinstance(error, ToolException):
        return "I encountered an error searching the database. Please try again."
    elif isinstance(error, AgentException):
        return "I'm having trouble processing your request. Could you rephrase?"
    else:
        return "An unexpected error occurred. Please contact support."
```

### Tool-Level Error Handling

```python
@tool
def semantic_search_tool(query: str, limit: int = 20):
    """Search with error handling"""
    try:
        # Generate embedding
        embedding = ollama_client.embeddings(model="nomic-embed-text", prompt=query)
        
        # Search
        results = supabase.rpc('search_similar_tenders', {...}).execute()
        
        return results.data
        
    except OllamaError as e:
        logger.error(f"Ollama error: {e}")
        raise ToolException("Embedding generation failed")
        
    except SupabaseError as e:
        logger.error(f"Database error: {e}")
        raise ToolException("Database search failed")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise ToolException("Search failed unexpectedly")
```

## Testing Agents

### Unit Testing Individual Agents

```python
import pytest
from unittest.mock import Mock, patch

def test_search_agent():
    """Test search agent with mocked tools"""
    
    # Mock LLM
    mock_llm = Mock()
    mock_llm.generate.return_value = "Search results..."
    
    # Mock tools
    with patch('app.agents.tools.keyword_search_tool') as mock_search:
        mock_search.return_value = [
            {"id": "t1", "title": "Test Tender"}
        ]
        
        agent = Agent(
            name="Search Agent",
            model=mock_llm,
            tools=[keyword_search_tool]
        )
        
        response = agent.run("Find IT tenders")
        
        assert mock_search.called
        assert "Test Tender" in response
```

### Integration Testing Workflows

```python
def test_search_workflow_integration():
    """Test full search workflow"""
    
    workflow = create_search_workflow()
    
    result = workflow.run("Find construction tenders in Germany")
    
    assert len(result['results']) > 0
    assert all(t['country'] == 'DE' for t in result['results'])
```

## Performance Optimization

### Caching Results

```python
from agno.cache import RedisCache

cache = RedisCache(url="redis://localhost:6379")

@tool(cache=cache, cache_ttl=3600)  # Cache for 1 hour
def semantic_search_tool(query: str):
    """Cached semantic search"""
    # Expensive operation
    ...
```

### Parallel Tool Execution

```python
agent = Agent(
    name="Search Agent",
    model=llm,
    tools=[keyword_search, semantic_search, cpv_search],
    parallel_tool_calls=True  # Execute tools in parallel when possible
)
```

## Monitoring and Logging

### Agent Telemetry

```python
from agno.telemetry import AgentTelemetry

telemetry = AgentTelemetry(
    backend="console",  # or "opentelemetry", "datadog"
    log_level="INFO"
)

agent = Agent(
    name="Search Agent",
    model=llm,
    tools=[...],
    telemetry=telemetry
)

# Automatic logging of:
# - Tool calls and results
# - LLM prompts and responses
# - Execution time
# - Errors
```

## Configuration

### Agent Configuration File

```yaml
# config/agents.yaml

agents:
  main_agent:
    name: "TED Bot Orchestrator"
    model: "llama3.1"
    temperature: 0.7
    max_tokens: 2000
    
  search_agent:
    name: "Search Agent"
    model: "llama3.1"
    temperature: 0.3  # Lower for more precise searches
    max_tokens: 1500
    show_tool_calls: true
    
  analysis_agent:
    name: "Analysis Agent"
    model: "llama3.1"
    temperature: 0.5
    max_tokens: 3000
    markdown: true
```

### Loading Configuration

```python
import yaml
from agno import Agent, OllamaModel

def create_agent_from_config(config_path: str, agent_name: str):
    """Create agent from YAML config"""
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    agent_config = config['agents'][agent_name]
    
    llm = OllamaModel(
        model=agent_config['model'],
        temperature=agent_config.get('temperature', 0.7),
        max_tokens=agent_config.get('max_tokens', 2000)
    )
    
    return Agent(
        name=agent_config['name'],
        model=llm,
        **{k: v for k, v in agent_config.items() 
           if k not in ['name', 'model', 'temperature', 'max_tokens']}
    )
```
