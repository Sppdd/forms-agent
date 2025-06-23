"""
Google Forms Editing Tools

This module provides tools for editing, updating, and deleting Google Forms
using the Google Forms API.
"""

import os
from typing import Any, Dict, List, Optional
import json
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google.adk.tools.tool_context import ToolContext

# Scopes required for Google Forms API
SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/forms.responses.readonly'
]


def update_form_info(form_id: str, title: str, description: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Update form title and/or description.
    
    Args:
        form_id: The Google Form ID
        title: New form title (will auto-generate if empty or generic)
        description: New form description (will auto-generate if empty or generic)
        tool_context: Context for accessing session state
        
    Returns:
        Dict containing update results
    """
    try:
        # Auto-generate title if not provided or too generic
        if not title or title.strip() == "" or title.lower() in ["", "none", "form title"]:
            title = "Updated Form"
        
        # Auto-generate description if not provided or too generic
        if not description or description.strip() == "" or description.lower() in ["", "none", "form description"]:
            description = f"Form updated automatically - {title}"
        
        service = _get_forms_service()
        
        requests = []
        
        requests.append({
            "updateFormInfo": {
                "info": {
                    "title": title,
                    "description": description
                },
                "updateMask": "title,description"
            }
        })
        
        # Apply updates
        batch_request = {"requests": requests}
        result = service.forms().batchUpdate(
            formId=form_id,
            body=batch_request
        ).execute()
        
        # Store updated info in session
        if tool_context:
            tool_context.state["last_form_update"] = {
                "form_id": form_id,
                "title": title,
                "description": description
            }
        
        return {
            "result": "success",
            "form_id": form_id,
            "updated_title": title,
            "updated_description": description,
            "update_result": result,
            "message": f"Successfully updated form {form_id}"
        }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "result": "error",
            "message": f"Failed to update form: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to update form info: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def modify_questions(form_id: str, modifications: List[Dict[str, Any]], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Modify questions in the form (add, edit, delete).
    
    Args:
        form_id: The Google Form ID
        modifications: List of modification operations
        tool_context: Context for accessing session state
        
    Returns:
        Dict containing modification results
    """
    try:
        service = _get_forms_service()
        
        requests = []
        
        for mod in modifications:
            operation = mod.get("operation")
            
            if operation == "add":
                question_data = mod.get("question")
                requests.append({
                    "createItem": {
                        "item": _format_question_for_api(question_data),
                        "location": {
                            "index": mod.get("index", 0)
                        }
                    }
                })
            
            elif operation == "update":
                item_id = mod.get("item_id")
                question_data = mod.get("question")
                requests.append({
                    "updateItem": {
                        "item": {
                            "itemId": item_id,
                            **_format_question_for_api(question_data)
                        },
                        "updateMask": "title,description,questionItem"
                    }
                })
            
            elif operation == "delete":
                item_id = mod.get("item_id")
                requests.append({
                    "deleteItem": {
                        "location": {
                            "index": mod.get("index", 0)
                        }
                    }
                })
        
        if not requests:
            return {
                "result": "error",
                "message": "No modifications specified."
            }
        
        # Apply modifications
        batch_request = {"requests": requests}
        result = service.forms().batchUpdate(
            formId=form_id,
            body=batch_request
        ).execute()
        
        # Store modification info in session
        if tool_context:
            tool_context.state["last_form_modifications"] = {
                "form_id": form_id,
                "modifications": modifications,
                "result": result
            }
        
        return {
            "result": "success",
            "form_id": form_id,
            "modifications_applied": len(modifications),
            "modification_result": result,
            "message": f"Successfully applied {len(modifications)} modifications to form {form_id}"
        }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "result": "error",
            "message": f"Failed to modify questions: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to modify questions: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def delete_form(form_id: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Delete a Google Form permanently.
    
    Args:
        form_id: The Google Form ID to delete
        tool_context: Context for accessing session state
        
    Returns:
        Dict containing deletion results
    """
    try:
        # Note: Google Forms API doesn't have a direct delete method
        # We need to use the Drive API to delete the form file
        from googleapiclient.discovery import build
        
        # Get Drive service (forms are stored as Drive files)
        drive_service = _get_drive_service()
        
        # Delete the form file
        drive_service.files().delete(fileId=form_id).execute()
        
        # Store deletion info in session
        if tool_context:
            tool_context.state["last_form_deletion"] = {
                "form_id": form_id,
                "deleted_at": str(datetime.now())
            }
        
        return {
            "result": "success",
            "form_id": form_id,
            "message": f"Successfully deleted form {form_id}",
            "warning": "This action is permanent and cannot be undone."
        }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "result": "error",
            "message": f"Failed to delete form: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to delete form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def get_form_responses(form_id: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Get responses from a Google Form.
    
    Args:
        form_id: The Google Form ID
        tool_context: Context for accessing session state
        
    Returns:
        Dict containing form responses
    """
    try:
        service = _get_forms_service()
        
        # Get form responses
        result = service.forms().responses().list(formId=form_id).execute()
        
        responses = result.get('responses', [])
        
        # Process responses for easier use
        processed_responses = []
        for response in responses:
            processed_response = {
                "response_id": response.get('responseId'),
                "create_time": response.get('createTime'),
                "last_submitted_time": response.get('lastSubmittedTime'),
                "answers": {}
            }
            
            # Process answers
            answers = response.get('answers', {})
            for question_id, answer_data in answers.items():
                processed_response["answers"][question_id] = answer_data
            
            processed_responses.append(processed_response)
        
        # Store responses in session
        if tool_context:
            tool_context.state["form_responses"] = {
                "form_id": form_id,
                "response_count": len(processed_responses),
                "responses": processed_responses
            }
        
        return {
            "result": "success",
            "form_id": form_id,
            "response_count": len(processed_responses),
            "responses": processed_responses,
            "message": f"Retrieved {len(processed_responses)} responses from form {form_id}"
        }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "result": "error",
            "message": f"Failed to get responses: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to get form responses: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _get_forms_service():
    """Get authenticated Google Forms service."""
    from google.oauth2 import service_account
    
    # Load service account credentials with correct path
    service_account_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'service_account.json')
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path, scopes=SCOPES
    )
    
    service = build('forms', 'v1', credentials=credentials)
    return service


def _get_drive_service():
    """Get authenticated Google Drive service."""
    from google.oauth2 import service_account
    
    # Load service account credentials with correct path
    service_account_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'service_account.json')
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path, scopes=['https://www.googleapis.com/auth/drive.file']
    )
    
    service = build('drive', 'v3', credentials=credentials)
    return service


def _format_question_for_api(question: Dict[str, Any]) -> Dict[str, Any]:
    """Format question data for Google Forms API."""
    question_type = question.get("type", "short_answer")
    question_text = question.get("question", "")
    required = question.get("required", False)
    
    # Map question types to Google Forms API format
    type_mapping = {
        "multiple_choice": "MULTIPLE_CHOICE",
        "short_answer": "SHORT_ANSWER",
        "long_answer": "PARAGRAPH",
        "checkbox": "CHECKBOX",
        "dropdown": "DROP_DOWN",
        "linear_scale": "LINEAR_SCALE",
        "date": "DATE",
        "time": "TIME"
    }
    
    api_type = type_mapping.get(question_type, "SHORT_ANSWER")
    
    formatted_question = {
        "title": question_text,
        "questionItem": {
            "question": {
                "required": required
            }
        }
    }
    
    # Add question-specific formatting
    if api_type == "MULTIPLE_CHOICE":
        options = question.get("options", [])
        formatted_question["questionItem"]["question"]["choiceQuestion"] = {
            "type": "RADIO",
            "options": [{"value": option} for option in options]
        }
    elif api_type == "CHECKBOX":
        options = question.get("options", [])
        formatted_question["questionItem"]["question"]["choiceQuestion"] = {
            "type": "CHECKBOX",
            "options": [{"value": option} for option in options]
        }
    elif api_type == "SHORT_ANSWER":
        formatted_question["questionItem"]["question"]["textQuestion"] = {}
    elif api_type == "PARAGRAPH":
        formatted_question["questionItem"]["question"]["textQuestion"] = {
            "paragraph": True
        }
    elif api_type == "LINEAR_SCALE":
        scale_data = question.get("scale", {"low": 1, "high": 5})
        formatted_question["questionItem"]["question"]["scaleQuestion"] = {
            "low": scale_data.get("low", 1),
            "high": scale_data.get("high", 5)
        }
    
    return formatted_question 