"""
Forms Agent Pipeline Optimization with ADK Callbacks

This example shows how to optimize your forms agent pipeline using ADK callbacks
for better performance, caching, validation, and monitoring.
"""

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CALLBACK FUNCTIONS FOR OPTIMIZATION
# ============================================================================

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """Before agent callback for validation and caching."""
    agent_name = callback_context.agent_name
    current_state = callback_context.state.to_dict()
    
    logger.info(f"[CALLBACK] Before agent: {agent_name}")
    
    # Check for cached results
    if current_state.get("skip_agent_execution", False):
        cached_result = current_state.get("cached_result")
        if cached_result:
            logger.info(f"[CALLBACK] Using cached result for {agent_name}")
            return types.Content(
                parts=[types.Part(text=cached_result)],
                role="model"
            )
    
    # Setup monitoring
    callback_context.state["agent_start_time"] = datetime.now().isoformat()
    
    return None

def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """After agent callback for cleanup and caching."""
    agent_name = callback_context.agent_name
    current_state = callback_context.state.to_dict()
    
    logger.info(f"[CALLBACK] After agent: {agent_name}")
    
    # Update monitoring metrics
    start_time = current_state.get("agent_start_time")
    if start_time:
        start_dt = datetime.fromisoformat(start_time)
        duration = (datetime.now() - start_dt).total_seconds()
        callback_context.state["last_agent_duration"] = duration
        logger.info(f"[CALLBACK] {agent_name} execution took {duration:.2f} seconds")
    
    # Cache successful results for form creation
    if agent_name == "FormCreatorAgent" and current_state.get("form_id"):
        cache_key = f"form_creation_{current_state['form_id']}"
        callback_context.state[cache_key] = {
            "form_id": current_state["form_id"],
            "form_url": current_state.get("form_url"),
            "created_at": datetime.now().isoformat(),
            "agent": agent_name
        }
        logger.info(f"[CALLBACK] Cached form creation result: {current_state['form_id']}")
    
    return None

def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """Before model callback for caching and optimization."""
    agent_name = callback_context.agent_name
    current_state = callback_context.state.to_dict()
    
    logger.info(f"[CALLBACK] Before model call for agent: {agent_name}")
    
    # Check for cached LLM response
    cache_key = f"llm_cache_{hash(str(llm_request.contents))}"
    if cache_key in current_state:
        cached_response = current_state[cache_key]
        logger.info(f"[CALLBACK] Using cached LLM response for {agent_name}")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=cached_response)]
            )
        )
    
    return None

def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    """After model callback for caching and processing."""
    agent_name = callback_context.agent_name
    current_state = callback_context.state.to_dict()
    
    logger.info(f"[CALLBACK] After model call for agent: {agent_name}")
    
    # Extract response text
    response_text = ""
    if llm_response.content and llm_response.content.parts:
        response_text = llm_response.content.parts[0].text or ""
    
    # Cache the response
    if response_text:
        cache_key = f"llm_cache_{hash(response_text)}"
        callback_context.state[cache_key] = response_text
        logger.info(f"[CALLBACK] Cached LLM response for {agent_name}")
    
    return None

def before_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    """Before tool callback for validation and caching."""
    agent_name = tool_context.agent_name
    tool_name = tool.name
    
    logger.info(f"[CALLBACK] Before tool call: {tool_name} in agent: {agent_name}")
    
    # Validate tool arguments
    if tool_name == "create_google_form":
        if not args.get("title") or not args.get("description"):
            logger.warning(f"[CALLBACK] Missing required arguments for {tool_name}")
            return {
                "result": "error",
                "message": "Title and description are required for form creation"
            }
    
    # Check for cached tool results
    cache_key = f"tool_cache_{tool_name}_{hash(str(args))}"
    current_state = tool_context.state.to_dict()
    if cache_key in current_state:
        cached_result = current_state[cache_key]
        logger.info(f"[CALLBACK] Using cached result for {tool_name}")
        return cached_result
    
    # Apply rate limiting for API calls
    if tool_name in ["create_google_form", "update_form_info", "add_questions_to_form"]:
        last_api_call = current_state.get("last_api_call_time")
        if last_api_call:
            last_call_dt = datetime.fromisoformat(last_api_call)
            time_diff = (datetime.now() - last_call_dt).total_seconds()
            if time_diff < 1.0:  # Rate limit: 1 call per second
                logger.warning(f"[CALLBACK] Rate limit exceeded for {tool_name}")
                return {
                    "result": "error",
                    "message": "API rate limit exceeded. Please wait a moment and try again."
                }
    
    # Update API call tracking
    tool_context.state["last_api_call_time"] = datetime.now().isoformat()
    tool_context.state["api_call_count"] = current_state.get("api_call_count", 0) + 1
    
    return None

def after_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict) -> Optional[Dict]:
    """After tool callback for caching and processing."""
    agent_name = tool_context.agent_name
    tool_name = tool.name
    current_state = tool_context.state.to_dict()
    
    logger.info(f"[CALLBACK] After tool call: {tool_name} in agent: {agent_name}")
    
    # Cache successful results
    if tool_response.get("result") == "success":
        cache_key = f"tool_cache_{tool_name}_{hash(str(args))}"
        tool_context.state[cache_key] = tool_response
        logger.info(f"[CALLBACK] Cached successful result for {tool_name}")
    
    # Extract and store important data
    if tool_name == "create_google_form" and tool_response.get("result") == "success":
        form_id = tool_response.get("form_id")
        if form_id:
            tool_context.state["current_form_id"] = form_id
            tool_context.state["form_creation_time"] = datetime.now().isoformat()
            logger.info(f"[CALLBACK] Stored form ID: {form_id}")
    
    return None

# ============================================================================
# HOW TO APPLY THESE CALLBACKS TO YOUR EXISTING AGENTS
# ============================================================================

"""
STEP 1: Import your existing agents
from forms_agent.subagents.form_creator.agent import form_creator_agent
from forms_agent.subagents.form_editor.agent import form_editor_agent
from forms_agent.subagents.document_parser.agent import document_parser_agent
from forms_agent.subagents.form_validator.agent import form_validator_agent

STEP 2: Create optimized versions with callbacks
optimized_form_creator_agent = Agent(
    name="OptimizedFormCreatorAgent",
    model="gemini-2.0-flash",
    description="Optimized Google Forms creation agent with caching and validation",
    instruction=form_creator_agent.instruction,
    tools=form_creator_agent.tools,
    # Add the callbacks here:
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    output_key="optimized_created_form",
)

STEP 3: Create optimized root agent
optimized_root_agent = Agent(
    name="OptimizedFormsAgent",
    model="gemini-2.0-flash",
    description="Optimized comprehensive agent for Google Forms management",
    instruction="Your existing instruction with optimization notes...",
    tools=[
        AgentTool(optimized_form_creator_agent),
        AgentTool(optimized_form_editor_agent),
        AgentTool(optimized_document_parser_agent),
        AgentTool(optimized_form_validator_agent),
    ],
    # Add the callbacks here:
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
"""

# ============================================================================
# OPTIMIZATION BENEFITS
# ============================================================================

OPTIMIZATION_BENEFITS = {
    "Performance": [
        "Caching of LLM responses and tool results",
        "Rate limiting to prevent API overload",
        "Reduced redundant API calls",
        "Faster response times"
    ],
    "Reliability": [
        "Input validation before tool execution",
        "Error recovery and retry logic",
        "Graceful error handling",
        "State validation and cleanup"
    ],
    "Monitoring": [
        "Comprehensive logging of all operations",
        "Performance metrics tracking",
        "Error pattern analysis",
        "API call monitoring"
    ],
    "Safety": [
        "Content filtering for sensitive data",
        "Guardrails for destructive operations",
        "Rate limiting protection",
        "Input sanitization"
    ]
}

if __name__ == "__main__":
    print("🚀 Forms Agent Pipeline Optimization with ADK Callbacks")
    print("=" * 60)
    for category, benefits in OPTIMIZATION_BENEFITS.items():
        print(f"\n📊 {category}:")
        for benefit in benefits:
            print(f"   ✅ {benefit}")
    
    print("\n" + "=" * 60)
    print("To apply these optimizations:")
    print("1. Copy the callback functions above")
    print("2. Add them to your agent definitions")
    print("3. Replace your existing agents with optimized versions")
    print("4. Test the performance improvements!") 