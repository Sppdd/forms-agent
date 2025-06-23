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
    
    Use this tool when you need to create a new Google Form from scratch. This tool
    creates the form with the specified title and description, and returns the form
    ID and URLs for further configuration.
    
    Args:
        title: The title for the new Google Form
        description: The description for the form (will auto-generate if empty or generic)
        
    Returns:
        A dictionary containing form creation results with the following structure:
        - status: 'success' or 'error'
        - form_id: The unique identifier for the created form
        - form_url: The URL to edit the form
        - responder_url: The URL for form responders
        - form_info: Dictionary containing form metadata
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
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
        
        # Store form info in session state if tool_context is available
        if tool_context:
            tool_context.state["form_id"] = form_id
            tool_context.state["form_url"] = form_url
            tool_context.state["responder_url"] = responder_url
            tool_context.state["created_form"] = result
        
        return {
            "status": "success",
            "form_id": form_id,
            "form_url": form_url,
            "responder_url": responder_url,
            "form_info": result.get('info', {}),
            "message": f"Successfully created form: {title}"
        }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "status": "error",
            "error_message": f"Google Forms API error: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to create form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def setup_form_settings(form_id: str, settings: Dict[str, Any], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Configure form settings such as response collection, quiz mode, and other preferences.
    
    Use this tool when you have created a Google Form and need to configure its settings
    like quiz mode, email collection, response editing permissions, and confirmation messages.
    
    Args:
        form_id: The Google Form ID to configure
        settings: Dictionary of settings to configure (is_quiz, collect_email, allow_response_editing, confirmation_message)
        
    Returns:
        A dictionary containing settings configuration results with the following structure:
        - status: 'success' or 'error'
        - applied_settings: Dictionary of settings that were successfully applied
        - update_result: The raw API response from Google Forms
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
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
            
            # Store updated settings in session state if tool_context is available
            if tool_context:
                tool_context.state["form_settings"] = settings
            
            return {
                "status": "success",
                "applied_settings": settings,
                "update_result": result,
                "message": f"Successfully configured form settings for {form_id}"
            }
        else:
            return {
                "status": "success",
                "message": "No settings to update",
                "applied_settings": {}
            }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "status": "error",
            "error_message": f"Failed to update settings: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to configure form settings: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def add_questions_to_form(form_id: str, questions: List[Dict[str, Any]], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Add questions to an existing Google Form.
    
    Use this tool when you have a Google Form created and want to add questions to it.
    This tool converts question data into the proper Google Forms API format and adds
    them to the specified form.
    
    Args:
        form_id: The Google Form ID to add questions to
        questions: List of question dictionaries with type, question text, and options
        
    Returns:
        A dictionary containing question addition results with the following structure:
        - status: 'success' or 'error'
        - added_questions: List of questions that were successfully added
        - question_count: Number of questions added
        - update_result: The raw API response from Google Forms
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
    """
    try:
        service = _get_forms_service()
        
        # Prepare batch update request
        requests = []
        added_questions = []
        
        for i, question in enumerate(questions):
            try:
                formatted_question = _format_question_for_api(question)
                requests.append({
                    "createItem": {
                        "item": formatted_question,
                        "location": {
                            "index": i
                        }
                    }
                })
                added_questions.append(question)
            except Exception as e:
                # Skip invalid questions but continue with others
                print(f"Warning: Skipping question {i+1} due to error: {str(e)}")
                continue
        
        if not requests:
            return {
                "status": "error",
                "error_message": "No valid questions to add to the form"
            }
        
        # Execute batch update
        batch_request = {"requests": requests}
        result = service.forms().batchUpdate(
            formId=form_id,
            body=batch_request
        ).execute()
        
        # Store added questions in session state if tool_context is available
        if tool_context:
            tool_context.state["added_questions"] = added_questions
            tool_context.state["total_questions"] = len(added_questions)
        
        return {
            "status": "success",
            "added_questions": added_questions,
            "question_count": len(added_questions),
            "update_result": result,
            "message": f"Successfully added {len(added_questions)} questions to form {form_id}"
        }
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        return {
            "status": "error",
            "error_message": f"Failed to add questions: {error_details.get('error', {}).get('message', str(e))}",
            "error_code": e.resp.status,
            "error_type": "HttpError"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to add questions to form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _get_forms_service():
    """Get authenticated Google Forms service using service account."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('forms', 'v1', credentials=credentials)
        return service
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Forms API: {str(e)}")


def _get_forms_service_oauth2():
    """Get authenticated Google Forms service using OAuth2 (alternative method)."""
    creds = None
    
    # Load existing credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    service = build('forms', 'v1', credentials=creds)
    return service


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