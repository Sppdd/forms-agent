"""
Google Forms Tool - Google ADK Tool Wrapper

This module provides Google ADK tool wrappers for the standalone Google Forms API,
making it easy to integrate into agent pipelines and workflows.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

from google_forms_api import (
    GoogleFormsAPI,
    create_google_form_standalone,
    update_form_standalone,
    add_questions_standalone,
    get_form_info_standalone,
    get_responses_standalone,
    delete_form_standalone
)


def create_form_tool(title: str, description: str = "", tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Create a new Google Form.
    
    Args:
        title: Form title (required)
        description: Form description (optional, will auto-generate if empty)
        tool_context: Google ADK tool context
        
    Returns:
        Dict containing form creation results
    """
    try:
        # Auto-generate description if empty
        if not description or description.strip() == "":
            description = f"Form created automatically - {title}"
        
        result = create_google_form_standalone(title, description)
        
        # Store form info in tool context if available
        if tool_context and result["result"] == "success":
            tool_context.state["last_created_form"] = {
                "form_id": result["form_id"],
                "form_url": result["form_url"],
                "title": title,
                "description": description
            }
        
        return result
        
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to create form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def update_form_tool(form_id: str, title: str = "", description: str = "", tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Update form title and/or description.
    
    Args:
        form_id: The Google Form ID (required)
        title: New form title (optional)
        description: New form description (optional)
        tool_context: Google ADK tool context
        
    Returns:
        Dict containing update results
    """
    try:
        result = update_form_standalone(form_id, title, description)
        
        # Store update info in tool context if available
        if tool_context and result["result"] == "success":
            tool_context.state["last_updated_form"] = {
                "form_id": form_id,
                "title": title,
                "description": description
            }
        
        return result
        
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to update form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def add_questions_tool(form_id: str, questions: List[Dict[str, Any]], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Add questions to a Google Form.
    
    Args:
        form_id: The Google Form ID (required)
        questions: List of question dictionaries (required)
        tool_context: Google ADK tool context
        
    Returns:
        Dict containing question addition results
    """
    try:
        # Validate questions format
        if not questions:
            return {
                "result": "error",
                "message": "No questions provided"
            }
        
        # Auto-complete missing question fields
        for question in questions:
            if not question.get("title"):
                question["title"] = "Question"
            if "required" not in question:
                question["required"] = False
            if not question.get("type"):
                question["type"] = "short_answer"
        
        result = add_questions_standalone(form_id, questions)
        
        # Store questions info in tool context if available
        if tool_context and result["result"] == "success":
            tool_context.state["last_added_questions"] = {
                "form_id": form_id,
                "questions_count": len(questions),
                "questions": questions
            }
        
        return result
        
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to add questions: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def get_form_info_tool(form_id: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Get form information and structure.
    
    Args:
        form_id: The Google Form ID (required)
        tool_context: Google ADK tool context
        
    Returns:
        Dict containing form information
    """
    try:
        result = get_form_info_standalone(form_id)
        
        # Store form info in tool context if available
        if tool_context and result["result"] == "success":
            tool_context.state["last_retrieved_form"] = {
                "form_id": form_id,
                "form_info": result["form_info"],
                "items_count": len(result["items"])
            }
        
        return result
        
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to get form info: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def get_responses_tool(form_id: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Get form responses.
    
    Args:
        form_id: The Google Form ID (required)
        tool_context: Google ADK tool context
        
    Returns:
        Dict containing form responses
    """
    try:
        result = get_responses_standalone(form_id)
        
        # Store responses info in tool context if available
        if tool_context and result["result"] == "success":
            tool_context.state["last_retrieved_responses"] = {
                "form_id": form_id,
                "response_count": result["response_count"]
            }
        
        return result
        
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to get responses: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def delete_form_tool(form_id: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Delete a Google Form permanently.
    
    Args:
        form_id: The Google Form ID to delete (required)
        tool_context: Google ADK tool context
        
    Returns:
        Dict containing deletion results
    """
    try:
        result = delete_form_standalone(form_id)
        
        # Store deletion info in tool context if available
        if tool_context and result["result"] == "success":
            tool_context.state["last_deleted_form"] = {
                "form_id": form_id,
                "deleted_at": str(datetime.now())
            }
        
        return result
        
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to delete form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def configure_form_settings_tool(form_id: str, settings: Dict[str, Any], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Configure form settings.
    
    Args:
        form_id: The Google Form ID (required)
        settings: Dictionary of settings to configure (required)
        tool_context: Google ADK tool context
        
    Returns:
        Dict containing settings configuration results
    """
    try:
        # Validate settings
        if not settings:
            return {
                "result": "error",
                "message": "No settings provided"
            }
        
        # Use the GoogleFormsAPI class for settings configuration
        api = GoogleFormsAPI()
        result = api.configure_settings(form_id, settings)
        
        # Store settings info in tool context if available
        if tool_context and result["result"] == "success":
            tool_context.state["last_configured_settings"] = {
                "form_id": form_id,
                "settings": settings
            }
        
        return result
        
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to configure settings: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def update_questions_tool(form_id: str, question_updates: List[Dict[str, Any]], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Update existing questions in a Google Form.
    
    Args:
        form_id: The Google Form ID (required)
        question_updates: List of question update dictionaries with item_id (required)
        tool_context: Google ADK tool context
        
    Returns:
        Dict containing update results
    """
    try:
        # Validate question updates
        if not question_updates:
            return {
                "result": "error",
                "message": "No question updates provided"
            }
        
        # Use the GoogleFormsAPI class for question updates
        api = GoogleFormsAPI()
        result = api.update_questions(form_id, question_updates)
        
        # Store update info in tool context if available
        if tool_context and result["result"] == "success":
            tool_context.state["last_updated_questions"] = {
                "form_id": form_id,
                "questions_updated": result["questions_updated"]
            }
        
        return result
        
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to update questions: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def delete_questions_tool(form_id: str, question_indices: List[int], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Delete questions from a Google Form by index.
    
    Args:
        form_id: The Google Form ID (required)
        question_indices: List of question indices to delete (required)
        tool_context: Google ADK tool context
        
    Returns:
        Dict containing deletion results
    """
    try:
        # Validate question indices
        if not question_indices:
            return {
                "result": "error",
                "message": "No question indices provided"
            }
        
        # Use the GoogleFormsAPI class for question deletion
        api = GoogleFormsAPI()
        result = api.delete_questions(form_id, question_indices)
        
        # Store deletion info in tool context if available
        if tool_context and result["result"] == "success":
            tool_context.state["last_deleted_questions"] = {
                "form_id": form_id,
                "questions_deleted": result["questions_deleted"]
            }
        
        return result
        
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to delete questions: {str(e)}",
            "error_type": str(type(e).__name__)
        }


# Create Google ADK Tool instances
create_form = FunctionTool(
    name="create_google_form",
    description="Create a new Google Form with title and optional description",
    function=create_form_tool
)

update_form = FunctionTool(
    name="update_google_form",
    description="Update form title and/or description",
    function=update_form_tool
)

add_questions = FunctionTool(
    name="add_questions_to_form",
    description="Add questions to a Google Form",
    function=add_questions_tool
)

get_form_info = FunctionTool(
    name="get_form_info",
    description="Get form information and structure",
    function=get_form_info_tool
)

get_responses = FunctionTool(
    name="get_form_responses",
    description="Get form responses",
    function=get_responses_tool
)

delete_form = FunctionTool(
    name="delete_google_form",
    description="Delete a Google Form permanently",
    function=delete_form_tool
)

configure_settings = FunctionTool(
    name="configure_form_settings",
    description="Configure form settings (quiz mode, response collection, etc.)",
    function=configure_form_settings_tool
)

update_questions = FunctionTool(
    name="update_questions",
    description="Update existing questions in a Google Form",
    function=update_questions_tool
)

delete_questions = FunctionTool(
    name="delete_questions",
    description="Delete questions from a Google Form by index",
    function=delete_questions_tool
)


# Export all tools
__all__ = [
    "create_form",
    "update_form", 
    "add_questions",
    "get_form_info",
    "get_responses",
    "delete_form",
    "configure_settings",
    "update_questions",
    "delete_questions"
] 