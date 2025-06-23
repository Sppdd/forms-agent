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
    
    Use this tool when you need to modify the basic information of an existing Google Form.
    This tool allows you to update the form's title and description while preserving all
    existing questions and settings.
    
    Args:
        form_id: The Google Form ID to update
        title: New form title (will auto-generate if empty or generic)
        description: New form description (will auto-generate if empty or generic)
        
    Returns:
        A dictionary containing update results with the following structure:
        - status: 'success' or 'error'
        - form_id: The ID of the updated form
        - updated_title: The new title that was applied
        - updated_description: The new description that was applied
        - update_result: The raw API response from Google Forms
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
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
        
        # Store updated info in session state if tool_context is available
        if tool_context:
            tool_context.state["last_form_update"] = {
                "form_id": form_id,
                "title": title,
                "description": description
            }
        
        return {
            "status": "success",
            "form_id": form_id,
            "updated_title": title,
            "updated_description": description,
            "update_result": result,
            "message": f"Successfully updated form {form_id}"
        }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "status": "error",
            "error_message": f"Failed to update form: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to update form info: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def modify_questions(form_id: str, modifications: List[Dict[str, Any]], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Modify questions in the form (add, edit, delete).
    
    Use this tool when you need to make changes to questions in an existing Google Form.
    This tool supports adding new questions, updating existing questions, and deleting
    questions from the form.
    
    Args:
        form_id: The Google Form ID to modify
        modifications: List of modification operations (add, update, delete)
        
    Returns:
        A dictionary containing modification results with the following structure:
        - status: 'success' or 'error'
        - form_id: The ID of the modified form
        - modifications_applied: Number of modifications successfully applied
        - modification_result: The raw API response from Google Forms
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
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
                "status": "error",
                "error_message": "No modifications specified."
            }
        
        # Apply modifications
        batch_request = {"requests": requests}
        result = service.forms().batchUpdate(
            formId=form_id,
            body=batch_request
        ).execute()
        
        # Store modification info in session state if tool_context is available
        if tool_context:
            tool_context.state["last_form_modifications"] = {
                "form_id": form_id,
                "modifications": modifications,
                "result": result
            }
        
        return {
            "status": "success",
            "form_id": form_id,
            "modifications_applied": len(modifications),
            "modification_result": result,
            "message": f"Successfully applied {len(modifications)} modifications to form {form_id}"
        }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "status": "error",
            "error_message": f"Failed to modify questions: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to modify questions: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def delete_form(form_id: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Delete a Google Form and its associated responses.
    
    Use this tool when you need to permanently remove a Google Form and all its data.
    This action cannot be undone, so use with caution.
    
    Args:
        form_id: The Google Form ID to delete
        
    Returns:
        A dictionary containing deletion results with the following structure:
        - status: 'success' or 'error'
        - form_id: The ID of the deleted form
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
    """
    try:
        service = _get_forms_service()
        drive_service = _get_drive_service()
        
        # Delete the form file from Google Drive
        try:
            drive_service.files().delete(fileId=form_id).execute()
            
            # Store deletion info in session state if tool_context is available
            if tool_context:
                tool_context.state["deleted_form_id"] = form_id
                tool_context.state["deletion_timestamp"] = datetime.now().isoformat()
            
            return {
                "status": "success",
                "form_id": form_id,
                "message": f"Successfully deleted form {form_id}"
            }
            
        except HttpError as e:
            if e.resp.status == 404:
                return {
                    "status": "success",
                    "form_id": form_id,
                    "message": f"Form {form_id} was already deleted or does not exist"
                }
            else:
                raise e
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "status": "error",
            "error_message": f"Failed to delete form: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to delete form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def get_form_responses(form_id: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Retrieve responses from a Google Form.
    
    Use this tool when you need to access the responses submitted to a Google Form.
    This tool fetches all responses and provides them in a structured format for analysis.
    
    Args:
        form_id: The Google Form ID to get responses from
        
    Returns:
        A dictionary containing response data with the following structure:
        - status: 'success' or 'error'
        - form_id: The ID of the form
        - responses: List of response objects with answers and metadata
        - response_count: Number of responses retrieved
        - form_info: Basic information about the form
        - error_message: Present only if status is 'error'
    """
    try:
        service = _get_forms_service()
        
        # Get form information
        form_info = service.forms().get(formId=form_id).execute()
        
        # Get responses
        responses_result = service.forms().responses().list(formId=form_id).execute()
        responses = responses_result.get('responses', [])
        
        # Process responses to extract answers
        processed_responses = []
        for response in responses:
            response_data = {
                "response_id": response.get('responseId'),
                "created_time": response.get('createdTime'),
                "last_submitted_time": response.get('lastSubmittedTime'),
                "answers": {}
            }
            
            # Extract answers for each question
            answers = response.get('answers', {})
            for question_id, answer_data in answers.items():
                question_info = form_info.get('items', [])
                question_title = f"Question_{question_id}"
                
                # Find question title
                for item in question_info:
                    if item.get('itemId') == question_id:
                        question_title = item.get('title', f"Question_{question_id}")
                        break
                
                # Extract answer value
                answer_value = None
                if 'textAnswers' in answer_data:
                    answer_value = [ans.get('value', '') for ans in answer_data['textAnswers'].get('answers', [])]
                elif 'choiceAnswers' in answer_data:
                    answer_value = [ans.get('value', '') for ans in answer_data['choiceAnswers'].get('answers', [])]
                elif 'fileUploadAnswers' in answer_data:
                    answer_value = [ans.get('fileId', '') for ans in answer_data['fileUploadAnswers'].get('answers', [])]
                
                response_data["answers"][question_title] = answer_value
            
            processed_responses.append(response_data)
        
        # Store responses in session state if tool_context is available
        if tool_context:
            tool_context.state["form_responses"] = processed_responses
            tool_context.state["response_count"] = len(processed_responses)
        
        return {
            "status": "success",
            "form_id": form_id,
            "responses": processed_responses,
            "response_count": len(processed_responses),
            "form_info": {
                "title": form_info.get('info', {}).get('title'),
                "description": form_info.get('info', {}).get('description'),
                "question_count": len(form_info.get('items', []))
            }
        }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "status": "error",
            "error_message": f"Failed to get responses: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get form responses: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _get_forms_service():
    """Get authenticated Google Forms service."""
    try:
        from google.oauth2 import service_account
        SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'service_account.json')
        
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('forms', 'v1', credentials=credentials)
        return service
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Forms API: {str(e)}")


def _get_drive_service():
    """Get authenticated Google Drive service."""
    try:
        from google.oauth2 import service_account
        SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'service_account.json')
        
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Drive API: {str(e)}")


def _format_question_for_api(question: Dict[str, Any]) -> Dict[str, Any]:
    """Convert question data to Google Forms API format."""
    question_type = question.get("type", "").lower()
    question_text = question.get("question", "")
    required = question.get("required", False)
    
    # Base question structure
    formatted_question = {
        "title": question_text,
        "questionId": f"question_{hash(question_text) % 1000000}"
    }
    
    # Add question type-specific configuration
    if question_type == "multiple_choice":
        options = question.get("options", [])
        formatted_question["question"] = {
            "questionId": formatted_question["questionId"],
            "required": required,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [{"value": str(option)} for option in options],
                "shuffle": False
            }
        }
    
    elif question_type == "checkbox":
        options = question.get("options", [])
        formatted_question["question"] = {
            "questionId": formatted_question["questionId"],
            "required": required,
            "choiceQuestion": {
                "type": "CHECKBOX",
                "options": [{"value": str(option)} for option in options],
                "shuffle": False
            }
        }
    
    elif question_type == "dropdown":
        options = question.get("options", [])
        formatted_question["question"] = {
            "questionId": formatted_question["questionId"],
            "required": required,
            "choiceQuestion": {
                "type": "DROP_DOWN",
                "options": [{"value": str(option)} for option in options]
            }
        }
    
    elif question_type == "short_answer":
        formatted_question["question"] = {
            "questionId": formatted_question["questionId"],
            "required": required,
            "textQuestion": {
                "type": "SHORT_ANSWER"
            }
        }
    
    elif question_type == "long_answer":
        formatted_question["question"] = {
            "questionId": formatted_question["questionId"],
            "required": required,
            "textQuestion": {
                "type": "PARAGRAPH"
            }
        }
    
    elif question_type == "linear_scale":
        min_value = question.get("min_value", 1)
        max_value = question.get("max_value", 5)
        min_label = question.get("min_label", "")
        max_label = question.get("max_label", "")
        
        formatted_question["question"] = {
            "questionId": formatted_question["questionId"],
            "required": required,
            "scaleQuestion": {
                "low": min_value,
                "high": max_value,
                "lowLabel": min_label,
                "highLabel": max_label
            }
        }
    
    else:
        # Default to short answer for unknown types
        formatted_question["question"] = {
            "questionId": formatted_question["questionId"],
            "required": required,
            "textQuestion": {
                "type": "SHORT_ANSWER"
            }
        }
    
    return formatted_question 