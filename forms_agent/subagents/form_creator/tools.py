"""
Google Forms Creation Tools

This module provides tools for interacting with the Google Forms API
to create and configure forms.
"""

import os
from typing import Any, Dict, List, Optional
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google.adk.tools.tool_context import ToolContext

# Scopes required for Google Forms API
SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/drive.file'
]

# Service account file path
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'service_account.json')


def create_google_form(title: str, description: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Create a new Google Form with basic information.
    
    Args:
        title: Form title
        description: Form description (will auto-generate if empty or generic)
        tool_context: Context for accessing session state
        
    Returns:
        Dict containing form creation results
    """
    try:
        # Auto-generate description if not provided or too generic
        if not description or description.strip() == "" or description.lower() in ["", "none", "form description"]:
            description = f"Form created automatically - {title}"
        
        # Get authenticated service
        service = _get_forms_service()
        
        # Create form request
        form_request = {
            "info": {
                "title": title,
                "description": description,
                "documentTitle": title
            }
        }
        
        # Create the form
        result = service.forms().create(body=form_request).execute()
        
        form_id = result.get('formId')
        form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
        responder_url = result.get('responderUri')
        
        # Store form info in session
        if tool_context:
            tool_context.state["form_id"] = form_id
            tool_context.state["form_url"] = form_url
            tool_context.state["responder_url"] = responder_url
            tool_context.state["created_form"] = result
        
        return {
            "result": "success",
            "form_id": form_id,
            "form_url": form_url,
            "responder_url": responder_url,
            "form_info": result.get('info', {}),
            "message": f"Successfully created form: {title}"
        }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "result": "error",
            "message": f"Google Forms API error: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to create form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def setup_form_settings(form_id: str, settings: Dict[str, Any], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Configure form settings such as response collection, quiz mode, etc.
    
    Args:
        form_id: The Google Form ID
        settings: Dictionary of settings to configure
        tool_context: Context for accessing session state
        
    Returns:
        Dict containing settings configuration results
    """
    try:
        service = _get_forms_service()
        
        # Prepare settings update request
        requests = []
        
        # Configure as quiz if specified
        if settings.get("is_quiz", False):
            requests.append({
                "updateSettings": {
                    "settings": {
                        "quizSettings": {
                            "isQuiz": True
                        }
                    },
                    "updateMask": "quizSettings.isQuiz"
                }
            })
        
        # Configure response settings
        if "collect_email" in settings:
            requests.append({
                "updateSettings": {
                    "settings": {
                        "generalSettings": {
                            "collectEmail": settings["collect_email"]
                        }
                    },
                    "updateMask": "generalSettings.collectEmail"
                }
            })
        
        # Configure other settings
        general_settings = {}
        update_mask_parts = []
        
        if "allow_response_editing" in settings:
            general_settings["allowResponseEditing"] = settings["allow_response_editing"]
            update_mask_parts.append("generalSettings.allowResponseEditing")
            
        if "confirmation_message" in settings:
            general_settings["confirmationMessage"] = settings["confirmation_message"]
            update_mask_parts.append("generalSettings.confirmationMessage")
            
        if general_settings:
            requests.append({
                "updateSettings": {
                    "settings": {
                        "generalSettings": general_settings
                    },
                    "updateMask": ",".join(update_mask_parts)
                }
            })
        
        # Apply settings if any
        if requests:
            batch_request = {"requests": requests}
            result = service.forms().batchUpdate(
                formId=form_id,
                body=batch_request
            ).execute()
            
            # Store updated settings in session
            if tool_context:
                tool_context.state["form_settings"] = settings
            
            return {
                "result": "success",
                "applied_settings": settings,
                "update_result": result,
                "message": f"Successfully configured form settings for {form_id}"
            }
        else:
            return {
                "result": "success",
                "message": "No settings to update",
                "applied_settings": {}
            }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "result": "error",
            "message": f"Failed to update settings: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to configure form settings: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def add_questions_to_form(form_id: str, questions: List[Dict[str, Any]], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Add questions to the Google Form.
    
    Args:
        form_id: The Google Form ID
        questions: List of question dictionaries in Google Forms format
        tool_context: Context for accessing session state
        
    Returns:
        Dict containing question addition results
    """
    try:
        service = _get_forms_service()
        
        # Prepare batch request for adding questions
        requests = []
        
        for i, question in enumerate(questions):
            # Create item for each question
            item_request = {
                "createItem": {
                    "item": {
                        "title": question.get("title", ""),
                        "questionItem": {
                            "question": _format_question_for_api(question),
                            "required": question.get("required", False)
                        }
                    },
                    "location": {
                        "index": i
                    }
                }
            }
            requests.append(item_request)
        
        # Execute batch request
        if requests:
            batch_request = {"requests": requests}
            result = service.forms().batchUpdate(
                formId=form_id,
                body=batch_request
            ).execute()
            
            # Store question addition result in session
            if tool_context:
                tool_context.state["questions_added"] = len(questions)
                tool_context.state["add_questions_result"] = result
            
            return {
                "result": "success",
                "questions_added": len(questions),
                "batch_result": result,
                "message": f"Successfully added {len(questions)} questions to form {form_id}"
            }
        else:
            return {
                "result": "success",
                "questions_added": 0,
                "message": "No questions to add"
            }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "result": "error",
            "message": f"Failed to add questions: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "result": "error",
            "message": f"Failed to add questions to form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _get_forms_service():
    """Get authenticated Google Forms service using service account."""
    try:
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            # Use service account authentication
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            return build('forms', 'v1', credentials=credentials)
        else:
            # Fallback to OAuth2 flow
            return _get_forms_service_oauth2()
    except Exception as e:
        raise Exception(f"Authentication failed: {SERVICE_ACCOUNT_FILE} not found. Please ensure the Google service account credentials file is available in the project root directory.")


def _get_forms_service_oauth2():
    """Get authenticated Google Forms service using OAuth2 (fallback)."""
    creds = None
    
    # Check for existing token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                raise FileNotFoundError(
                    f"{SERVICE_ACCOUNT_FILE} not found. Please ensure the Google service account credentials file is available in the project root directory."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                SERVICE_ACCOUNT_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('forms', 'v1', credentials=creds)


def _format_question_for_api(question: Dict[str, Any]) -> Dict[str, Any]:
    """Format question data for Google Forms API."""
    question_type = question.get("questionType", "SHORT_ANSWER")
    formatted_question = {"questionType": question_type}
    
    if question_type in ["MULTIPLE_CHOICE", "CHECKBOX", "DROP_DOWN"]:
        choice_question = question.get("choiceQuestion", {})
        formatted_question["choiceQuestion"] = {
            "type": choice_question.get("type", "RADIO" if question_type == "MULTIPLE_CHOICE" else question_type),
            "options": choice_question.get("options", [])
        }
    elif question_type == "LINEAR_SCALE":
        scale_question = question.get("scaleQuestion", {})
        formatted_question["scaleQuestion"] = {
            "low": scale_question.get("low", 1),
            "high": scale_question.get("high", 5),
            "lowLabel": scale_question.get("lowLabel", ""),
            "highLabel": scale_question.get("highLabel", "")
        }
    elif question_type in ["MULTIPLE_CHOICE_GRID", "CHECKBOX_GRID"]:
        grid_question = question.get("rowQuestion", {})
        formatted_question["rowQuestion"] = grid_question
    
    return formatted_question 