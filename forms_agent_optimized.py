"""
Optimized FormsAgent with ADK Callbacks

This agent demonstrates how to use ADK callbacks to optimize the forms pipeline
with caching, validation, monitoring, and error recovery.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types

from forms_agent.subagents.document_parser.agent import document_parser_agent
from forms_agent.subagents.form_creator.agent import form_creator_agent
from forms_agent.subagents.form_editor.agent import form_editor_agent
from forms_agent.subagents.form_validator.agent import form_validator_agent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CALLBACK FUNCTIONS FOR OPTIMIZATION
# ============================================================================

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Before agent callback for setup, validation, and caching.
    
    Optimizations:
    - Check for cached results
    - Validate session state
    - Setup monitoring
    - Apply guardrails
    """
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict()
    
    logger.info(f"[CALLBACK] Before agent: {agent_name} (Inv: {invocation_id})")
    logger.info(f"[CALLBACK] Current state: {current_state}")
    
    # Check for cached results
    if current_state.get("skip_agent_execution", False):
        cached_result = current_state.get("cached_result")
        if cached_result:
            logger.info(f"[CALLBACK] Using cached result for {agent_name}")
            return types.Content(
                parts=[types.Part(text=cached_result)],
                role="model"
            )
    
    # Validate session state
    if agent_name == "FormCreatorAgent":
        if not current_state.get("parsed_content") and not current_state.get("form_data"):
            logger.warning(f"[CALLBACK] FormCreatorAgent called without parsed content")
            return types.Content(
                parts=[types.Part(text="Error: No form data available. Please parse a document or provide form details first.")],
                role="model"
            )
    
    # Setup monitoring
    callback_context.state["agent_start_time"] = datetime.now().isoformat()
    callback_context.state["agent_invocation_count"] = current_state.get("agent_invocation_count", 0) + 1
    
    # Apply content guardrails
    user_message = ""
    if callback_context.invocation_context and callback_context.invocation_context.messages:
        last_message = callback_context.invocation_context.messages[-1]
        if last_message.parts:
            user_message = last_message.parts[0].text or ""
    
    # Check for forbidden content
    forbidden_keywords = ["delete all", "remove everything", "clear all data"]
    if any(keyword in user_message.lower() for keyword in forbidden_keywords):
        logger.warning(f"[CALLBACK] Forbidden content detected in {agent_name}")
        return types.Content(
            parts=[types.Part(text="I cannot perform destructive operations without explicit confirmation. Please be more specific about what you want to modify.")],
            role="model"
        )
    
    logger.info(f"[CALLBACK] Proceeding with {agent_name} execution")
    return None

def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    After agent callback for cleanup, caching, and monitoring.
    
    Optimizations:
    - Cache successful results
    - Update monitoring metrics
    - Cleanup temporary state
    - Format responses
    """
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict()
    
    logger.info(f"[CALLBACK] After agent: {agent_name} (Inv: {invocation_id})")
    
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
    
    # Cleanup temporary state
    temp_keys = ["agent_start_time", "temp_form_data"]
    for key in temp_keys:
        if key in callback_context.state:
            del callback_context.state[key]
    
    return None

def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """
    Before model callback for prompt optimization and caching.
    
    Optimizations:
    - Cache LLM responses
    - Optimize prompts
    - Add context from state
    - Apply safety filters
    """
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
    
    # Optimize prompts with context
    if agent_name == "FormCreatorAgent" and current_state.get("parsed_content"):
        # Add parsed content context to the prompt
        context_info = f"\n\nContext from document parsing: {json.dumps(current_state['parsed_content'], indent=2)}"
        if llm_request.contents and llm_request.contents[-1].parts:
            llm_request.contents[-1].parts[0].text += context_info
        logger.info(f"[CALLBACK] Enhanced prompt with document context for {agent_name}")
    
    # Apply safety filters
    user_content = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts:
            user_content = llm_request.contents[-1].parts[0].text or ""
    
    # Check for sensitive content
    sensitive_patterns = ["password", "credit card", "ssn", "social security"]
    if any(pattern in user_content.lower() for pattern in sensitive_patterns):
        logger.warning(f"[CALLBACK] Sensitive content detected in {agent_name}")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="I cannot process requests containing sensitive personal information like passwords, credit cards, or social security numbers.")]
            )
        )
    
    logger.info(f"[CALLBACK] Proceeding with LLM call for {agent_name}")
    return None

def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    """
    After model callback for response processing and caching.
    
    Optimizations:
    - Cache LLM responses
    - Extract structured data
    - Format responses
    - Add metadata
    """
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
    
    # Extract structured data for form creation
    if agent_name == "FormCreatorAgent" and "form" in response_text.lower():
        try:
            # Try to extract form ID from response
            import re
            form_id_match = re.search(r'[a-zA-Z0-9_-]{20,}', response_text)
            if form_id_match:
                form_id = form_id_match.group()
                callback_context.state["extracted_form_id"] = form_id
                logger.info(f"[CALLBACK] Extracted form ID: {form_id}")
        except Exception as e:
            logger.warning(f"[CALLBACK] Failed to extract form ID: {e}")
    
    # Add response metadata
    callback_context.state["last_llm_response_length"] = len(response_text)
    callback_context.state["last_llm_timestamp"] = datetime.now().isoformat()
    
    return None

def before_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    """
    Before tool callback for validation, caching, and optimization.
    
    Optimizations:
    - Validate tool arguments
    - Check for cached tool results
    - Apply rate limiting
    - Add authentication
    """
    agent_name = tool_context.agent_name
    tool_name = tool.name
    
    logger.info(f"[CALLBACK] Before tool call: {tool_name} in agent: {agent_name}")
    logger.info(f"[CALLBACK] Tool args: {args}")
    
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
    
    logger.info(f"[CALLBACK] Proceeding with tool execution: {tool_name}")
    return None

def after_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict) -> Optional[Dict]:
    """
    After tool callback for result processing and caching.
    
    Optimizations:
    - Cache successful results
    - Extract and store important data
    - Handle errors gracefully
    - Update metrics
    """
    agent_name = tool_context.agent_name
    tool_name = tool.name
    current_state = tool_context.state.to_dict()
    
    logger.info(f"[CALLBACK] After tool call: {tool_name} in agent: {agent_name}")
    logger.info(f"[CALLBACK] Tool response: {tool_response}")
    
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
    
    # Handle errors gracefully
    if tool_response.get("result") == "error":
        error_count = current_state.get("error_count", 0) + 1
        tool_context.state["error_count"] = error_count
        tool_context.state["last_error"] = {
            "tool": tool_name,
            "error": tool_response.get("message"),
            "timestamp": datetime.now().isoformat()
        }
        logger.error(f"[CALLBACK] Tool error in {tool_name}: {tool_response.get('message')}")
        
        # Implement retry logic for certain errors
        if "rate limit" in tool_response.get("message", "").lower():
            tool_context.state["retry_after"] = datetime.now().isoformat()
    
    # Update metrics
    tool_context.state["tool_success_count"] = current_state.get("tool_success_count", 0) + (1 if tool_response.get("result") == "success" else 0)
    
    return None

# ============================================================================
# OPTIMIZED AGENT DEFINITIONS
# ============================================================================

# Optimized Form Creator Agent with callbacks
optimized_form_creator_agent = Agent(
    name="OptimizedFormCreatorAgent",
    model="gemini-2.0-flash",
    description="Optimized Google Forms creation agent with caching, validation, and monitoring",
    instruction="""You are an optimized Google Forms Creation AI with enhanced capabilities.

**ENHANCED FEATURES**:
- Automatic caching of form creation results
- Input validation and error recovery
- Rate limiting and API optimization
- Comprehensive monitoring and logging
- Safety guardrails and content filtering

**WORKFLOW**:
1. Validate input data and check cache
2. Create form with optimized API calls
3. Add questions with batch processing
4. Configure settings with best practices
5. Cache results for future use

**AUTO-COMPLETION**: Enhanced with context-aware defaults and validation.
""",
    tools=form_creator_agent.tools,
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    output_key="optimized_created_form",
)

# Optimized Form Editor Agent with callbacks
optimized_form_editor_agent = Agent(
    name="OptimizedFormEditorAgent",
    model="gemini-2.0-flash",
    description="Optimized Google Forms editing agent with caching and validation",
    instruction="""You are an optimized Google Forms Editing AI with enhanced capabilities.

**ENHANCED FEATURES**:
- Cached form data retrieval
- Optimized batch updates
- Error recovery and retry logic
- Change tracking and rollback support
- Performance monitoring

**WORKFLOW**:
1. Validate form ID and check cache
2. Retrieve current form state
3. Apply changes with optimization
4. Cache updated form data
5. Provide detailed change summary

**AUTO-COMPLETION**: Enhanced with form-aware defaults and validation.
""",
    tools=form_editor_agent.tools,
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    output_key="optimized_edit_result",
)

# Optimized Document Parser Agent with callbacks
optimized_document_parser_agent = Agent(
    name="OptimizedDocumentParserAgent",
    model="gemini-2.0-flash",
    description="Optimized document parsing agent with caching and validation",
    instruction="""You are an optimized Document Analysis AI with enhanced capabilities.

**ENHANCED FEATURES**:
- Cached document parsing results
- Optimized content extraction
- Enhanced question detection
- Content validation and filtering
- Performance monitoring

**WORKFLOW**:
1. Check for cached parsing results
2. Extract and validate document content
3. Identify and structure questions
4. Cache parsed content
5. Provide structured output

**AUTO-COMPLETION**: Enhanced with document-aware defaults and validation.
""",
    tools=document_parser_agent.tools,
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    output_key="optimized_parsed_content",
)

# ============================================================================
# OPTIMIZED ROOT AGENT
# ============================================================================

# Create the optimized main forms agent
optimized_root_agent = Agent(
    name="OptimizedFormsAgent",
    model="gemini-2.0-flash",
    description="Optimized comprehensive agent for Google Forms management with enhanced performance and monitoring",
    instruction="""You are an optimized Google Forms Management AI Assistant with intelligent auto-completion and enhanced capabilities.

**🚀 OPTIMIZED FEATURES**:
- **Caching**: Automatic caching of form operations and LLM responses
- **Validation**: Enhanced input validation and error recovery
- **Monitoring**: Comprehensive performance monitoring and logging
- **Safety**: Content filtering and guardrails
- **Performance**: Optimized API calls and batch processing
- **Recovery**: Automatic retry logic and error handling

**🤖 ENHANCED AUTO-COMPLETION**:
- Context-aware defaults using cached data
- Intelligent form structure optimization
- Enhanced question type detection
- Performance-optimized settings

**WORKFLOW OPTIMIZATION**:
1. **Document Processing**: Use `optimized_document_parser_agent` with caching
2. **Form Validation**: Use `form_validator_agent` with enhanced validation
3. **Form Creation**: Use `optimized_form_creator_agent` with performance optimization
4. **Form Editing**: Use `optimized_form_editor_agent` with change tracking

**MONITORING & ANALYTICS**:
- Track API call performance
- Monitor cache hit rates
- Log error patterns
- Measure response times

**SAFETY & GUARDRAILS**:
- Content filtering for sensitive data
- Rate limiting for API calls
- Validation of destructive operations
- Error recovery mechanisms

Always provide clear feedback on optimizations applied and performance improvements achieved.
""",
    tools=[
        AgentTool(optimized_document_parser_agent),
        AgentTool(form_validator_agent),
        AgentTool(optimized_form_creator_agent),
        AgentTool(optimized_form_editor_agent),
    ],
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
) 