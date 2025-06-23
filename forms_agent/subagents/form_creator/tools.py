"""
Google Forms Creation Tools

This module provides tools for interacting with the Google Forms API
to create and configure powerful forms with advanced features.
"""

import os
from typing import Any, Dict, List, Optional
import json
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google.adk.tools.tool_context import ToolContext

# Try to import the standalone API client
try:
    from google_forms_api import GoogleFormsAPI
    USE_STANDALONE_API = True
except ImportError:
    USE_STANDALONE_API = False

# Scopes required for Google Forms API
SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

# Service account file path
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'service_account.json')


def create_google_form(title: str, description: Optional[str] = None, form_type: str = "form", tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Create a new Google Form with advanced configuration options.
    
    Use this tool when you need to create a new Google Form from scratch. This tool
    creates the form with the specified title and description, and returns the form
    ID and URLs for further configuration. Supports both regular forms and quizzes.
    
    Args:
        title: The title for the new Google Form
        description: The description for the form (will auto-generate if None or empty)
        form_type: Type of form to create ("form" or "quiz")
        
    Returns:
        A dictionary containing form creation results with the following structure:
        - status: 'success' or 'error'
        - form_id: The unique identifier for the created form
        - form_url: The URL to edit the form
        - responder_url: The URL for form responders
        - form_info: Dictionary containing form metadata
        - form_type: The type of form created
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
    """
    try:
        # Auto-generate description if not provided
        if not description or description.strip() == "":
            description = f"{form_type.title()} created automatically - {title}"
        
        # Use standalone API if available, otherwise use direct API calls
        if USE_STANDALONE_API:
            return _create_form_with_standalone_api(title, description, form_type, tool_context)
        else:
            return _create_form_with_direct_api(title, description, form_type, tool_context)
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to create form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _create_form_with_standalone_api(title: str, description: str, form_type: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """Create form using the standalone Google Forms API client."""
    try:
        api = GoogleFormsAPI(SERVICE_ACCOUNT_FILE)
        result = api.create_form(title, description, form_type)
        
        # Convert result format to match our expected structure
        if result["result"] == "success":
            # Store form info in session state if tool_context is available
            if tool_context:
                tool_context.state["form_id"] = result["form_id"]
                tool_context.state["form_url"] = result["form_url"]
                tool_context.state["responder_url"] = result["responder_url"]
                tool_context.state["created_form"] = result["form_info"]
                tool_context.state["form_type"] = form_type
            
            return {
                "status": "success",
                "form_id": result["form_id"],
                "form_url": result["form_url"],
                "responder_url": result["responder_url"],
                "form_info": result["form_info"],
                "form_type": form_type,
                "message": result["message"]
            }
        else:
            return {
                "status": "error",
                "error_message": result["message"],
                "error_code": result.get("error_code"),
                "error_type": "APIError"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Standalone API error: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _create_form_with_direct_api(title: str, description: str, form_type: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """Create form using direct Google Forms API calls with advanced features."""
    try:
        # Get authenticated service
        service = _get_forms_service()
        
        # Create form request with only title (API limitation)
        form_request = {
            "info": {
                "title": title
            }
        }
        
        # Create the form
        result = service.forms().create(body=form_request).execute()
        
        form_id = result.get('formId')
        form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
        responder_url = result.get('responderUri')
        
        # Use batchUpdate to add description and configure as quiz if needed
        update_requests = []
        
        # Add description if provided
        if description and description.strip():
            update_requests.append({
                "updateFormInfo": {
                    "info": {
                        "description": description
                    },
                    "updateMask": "description"
                }
            })
        
        # Configure as quiz if specified
        if form_type.lower() == "quiz":
            update_requests.append({
                "updateSettings": {
                    "settings": {
                        "quizSettings": {
                            "isQuiz": True
                        }
                    },
                    "updateMask": "quizSettings.isQuiz"
                }
            })
        
        # Apply updates if any
        if update_requests:
            batch_request = {"requests": update_requests}
            service.forms().batchUpdate(
                formId=form_id,
                body=batch_request
            ).execute()
        
        # Store form info in session state if tool_context is available
        if tool_context:
            tool_context.state["form_id"] = form_id
            tool_context.state["form_url"] = form_url
            tool_context.state["responder_url"] = responder_url
            tool_context.state["created_form"] = result
            tool_context.state["form_type"] = form_type
        
        return {
            "status": "success",
            "form_id": form_id,
            "form_url": form_url,
            "responder_url": responder_url,
            "form_info": result.get('info', {}),
            "form_type": form_type,
            "message": f"Successfully created {form_type}: {title}"
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
    Configure advanced form settings including quiz mode, response collection, and publishing.
    
    Use this tool when you have created a Google Form and need to configure its settings
    like quiz mode, email collection, response editing permissions, confirmation messages,
    and publishing settings.
    
    Args:
        form_id: The Google Form ID to configure
        settings: Dictionary of settings to configure including:
            - is_quiz: Enable quiz mode with grading
            - collect_email: Collect respondent email addresses
            - allow_response_editing: Allow respondents to edit responses
            - confirmation_message: Custom confirmation message
            - is_published: Publish the form for responses
            - is_accepting_responses: Enable/disable response collection
            - quiz_settings: Advanced quiz configuration
            - general_settings: Other general form settings
        
    Returns:
        A dictionary containing settings configuration results with the following structure:
        - status: 'success' or 'error'
        - applied_settings: Dictionary of settings that were successfully applied
        - update_result: The raw API response from Google Forms
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
    """
    try:
        # Use standalone API if available
        if USE_STANDALONE_API:
            api = GoogleFormsAPI(SERVICE_ACCOUNT_FILE)
            result = api.configure_settings(form_id, settings)
            
            # Convert result format
            if result["result"] == "success":
                if tool_context:
                    tool_context.state["form_settings"] = settings
                
                return {
                    "status": "success",
                    "applied_settings": result["applied_settings"],
                    "update_result": result["update_result"],
                    "message": result["message"]
                }
            else:
                return {
                    "status": "error",
                    "error_message": result["message"],
                    "error_code": result.get("error_code"),
                    "error_type": "APIError"
                }
        else:
            # Use original implementation
            return _setup_form_settings_direct(form_id, settings, tool_context)
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to configure form settings: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _setup_form_settings_direct(form_id: str, settings: Dict[str, Any], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """Configure form settings using direct API calls (strict, valid structure)."""
    try:
        service = _get_forms_service()
        requests = []
        
        # Quiz settings - this is the only supported setting in the API
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
        
        # Note: The Google Forms API only supports quizSettings
        # Other settings like collectEmail, allowResponseEditing, etc. are not supported
        # in the current API version
        
        # Apply settings if any
        if requests:
            batch_request = {"requests": requests}
            result = service.forms().batchUpdate(
                formId=form_id,
                body=batch_request
            ).execute()
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
                "message": "No supported settings to update",
                "applied_settings": {},
                "note": "Only quiz settings are currently supported by the Google Forms API"
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
    Add advanced questions to an existing Google Form with full API support.
    
    Use this tool when you have a Google Form created and want to add questions to it.
    This tool converts question data into the proper Google Forms API format and adds
    them to the specified form. Supports all question types including quizzes, images,
    videos, and sections.
    
    Args:
        form_id: The Google Form ID to add questions to
        questions: List of question dictionaries with advanced configuration including:
            - type: Question type (multiple_choice, checkbox, dropdown, short_answer, long_answer, linear_scale, multiple_choice_grid, checkbox_grid, date, time, file_upload, image, video, section)
            - question: Question text
            - options: List of options for choice questions
            - required: Whether the question is required
            - grading: Quiz grading configuration (for quizzes)
            - image: Image configuration for image questions
            - video: Video configuration for video questions
            - section: Section configuration for page breaks
        
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
        # Use standalone API if available
        if USE_STANDALONE_API:
            api = GoogleFormsAPI(SERVICE_ACCOUNT_FILE)
            result = api.add_questions(form_id, questions)
            
            # Convert result format
            if result["result"] == "success":
                if tool_context:
                    tool_context.state["added_questions"] = questions
                    tool_context.state["total_questions"] = result["questions_added"]
                
                return {
                    "status": "success",
                    "added_questions": questions,
                    "question_count": result["questions_added"],
                    "update_result": result["batch_result"],
                    "message": result["message"]
                }
            else:
                return {
                    "status": "error",
                    "error_message": result["message"],
                    "error_code": result.get("error_code"),
                    "error_type": "APIError"
                }
        else:
            # Use original implementation
            return _add_questions_direct(form_id, questions, tool_context)
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to add questions to form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _add_questions_direct(form_id: str, questions: List[Dict[str, Any]], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """Add questions using direct API calls with advanced question types."""
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


def add_media_to_form(form_id: str, media_items: List[Dict[str, Any]], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Add images, videos, and other media to a Google Form.
    
    Use this tool when you want to add visual content to your form including images,
    videos, and other media elements to enhance the form experience.
    
    Args:
        form_id: The Google Form ID to add media to
        media_items: List of media item dictionaries with:
            - type: Media type ("image" or "video")
            - title: Title for the media item
            - description: Description for the media item
            - content_uri: URI for image content or YouTube URI for videos
            - alignment: Image alignment ("LEFT", "CENTER", "RIGHT")
            - width: Image width in pixels
            - height: Image height in pixels
        
    Returns:
        A dictionary containing media addition results
    """
    try:
        service = _get_forms_service()
        
        requests = []
        added_media = []
        
        for i, media_item in enumerate(media_items):
            try:
                formatted_media = _format_media_for_api(media_item)
                requests.append({
                    "createItem": {
                        "item": formatted_media,
                        "location": {
                            "index": i
                        }
                    }
                })
                added_media.append(media_item)
            except Exception as e:
                print(f"Warning: Skipping media item {i+1} due to error: {str(e)}")
                continue
        
        if not requests:
            return {
                "status": "error",
                "error_message": "No valid media items to add to the form"
            }
        
        # Execute batch update
        batch_request = {"requests": requests}
        result = service.forms().batchUpdate(
            formId=form_id,
            body=batch_request
        ).execute()
        
        if tool_context:
            tool_context.state["added_media"] = added_media
        
        return {
            "status": "success",
            "added_media": added_media,
            "media_count": len(added_media),
            "update_result": result,
            "message": f"Successfully added {len(added_media)} media items to form {form_id}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to add media to form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def create_form_sections(form_id: str, sections: List[Dict[str, Any]], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Create sections and page breaks in a Google Form for better organization.
    
    Use this tool when you want to organize your form into multiple pages or sections
    for better user experience and logical flow.
    
    Args:
        form_id: The Google Form ID to add sections to
        sections: List of section dictionaries with:
            - title: Section title
            - description: Section description
            - navigation_type: Navigation type ("CONTINUE" or "GO_TO_PAGE")
            - condition: Conditional logic for section display
        
    Returns:
        A dictionary containing section creation results
    """
    try:
        service = _get_forms_service()
        
        requests = []
        added_sections = []
        
        for i, section in enumerate(sections):
            try:
                formatted_section = _format_section_for_api(section)
                requests.append({
                    "createItem": {
                        "item": formatted_section,
                        "location": {
                            "index": i
                        }
                    }
                })
                added_sections.append(section)
            except Exception as e:
                print(f"Warning: Skipping section {i+1} due to error: {str(e)}")
                continue
        
        if not requests:
            return {
                "status": "error",
                "error_message": "No valid sections to add to the form"
            }
        
        # Execute batch update
        batch_request = {"requests": requests}
        result = service.forms().batchUpdate(
            formId=form_id,
            body=batch_request
        ).execute()
        
        if tool_context:
            tool_context.state["added_sections"] = added_sections
        
        return {
            "status": "success",
            "added_sections": added_sections,
            "section_count": len(added_sections),
            "update_result": result,
            "message": f"Successfully added {len(added_sections)} sections to form {form_id}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to create form sections: {str(e)}",
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
    """Convert question data to Google Forms API format (strict, valid structure)."""
    question_type = question.get("type", "").lower()
    question_text = question.get("question", "")
    required = question.get("required", False)
    
    # Base item structure
    item = {
        "title": question_text
    }

    # Supported question types - all must be nested under questionItem
    if question_type in ["multiple_choice", "checkbox", "dropdown", "short_answer", "long_answer", "linear_scale", "multiple_choice_grid", "checkbox_grid", "date", "time", "file_upload"]:
        question_item = {}
        
        # Choice questions
        if question_type == "multiple_choice":
            options = question.get("options", [])
            question_item = {
                "question": {
                    "required": required,
                    "choiceQuestion": {
                        "type": "RADIO",
                        "options": [{"value": str(option)} for option in options],
                        "shuffle": question.get("shuffle", False)
                    }
                }
            }
            # Add grading if provided (for quizzes)
            if "grading" in question:
                question_item["question"]["grading"] = question["grading"]
                
        elif question_type == "checkbox":
            options = question.get("options", [])
            question_item = {
                "question": {
                    "required": required,
                    "choiceQuestion": {
                        "type": "CHECKBOX",
                        "options": [{"value": str(option)} for option in options],
                        "shuffle": question.get("shuffle", False)
                    }
                }
            }
            if "grading" in question:
                question_item["question"]["grading"] = question["grading"]
                
        elif question_type == "dropdown":
            options = question.get("options", [])
            question_item = {
                "question": {
                    "required": required,
                    "choiceQuestion": {
                        "type": "DROP_DOWN",
                        "options": [{"value": str(option)} for option in options]
                    }
                }
            }
            if "grading" in question:
                question_item["question"]["grading"] = question["grading"]
                
        elif question_type == "short_answer":
            question_item = {
                "question": {
                    "required": required,
                    "textQuestion": {}
                }
            }
            if "grading" in question:
                question_item["question"]["grading"] = question["grading"]
                
        elif question_type == "long_answer":
            question_item = {
                "question": {
                    "required": required,
                    "textQuestion": {"paragraph": True}
                }
            }
            if "grading" in question:
                question_item["question"]["grading"] = question["grading"]
                
        elif question_type == "linear_scale":
            question_item = {
                "question": {
                    "required": required,
                    "scaleQuestion": {
                        "low": question.get("min_value", 1),
                        "high": question.get("max_value", 5),
                        "lowLabel": question.get("min_label", ""),
                        "highLabel": question.get("max_label", "")
                    }
                }
            }
            
        elif question_type in ["multiple_choice_grid", "checkbox_grid"]:
            grid_type = "RADIO" if question_type == "multiple_choice_grid" else "CHECKBOX"
            question_item = {
                "question": {
                    "required": required,
                    "gridQuestion": {
                        "columns": {"options": [{"value": str(col)} for col in question.get("columns", [])]},
                        "rows": {"options": [{"value": str(row)} for row in question.get("rows", [])]},
                        "type": grid_type
                    }
                }
            }
            
        elif question_type == "date":
            question_item = {
                "question": {
                    "required": required,
                    "dateQuestion": {
                        "includeTime": question.get("include_time", False),
                        "includeYear": question.get("include_year", True)
                    }
                }
            }
            
        elif question_type == "time":
            question_item = {
                "question": {
                    "required": required,
                    "timeQuestion": {
                        "duration": question.get("duration", False)
                    }
                }
            }
            
        elif question_type == "file_upload":
            question_item = {
                "question": {
                    "required": required,
                    "fileUploadQuestion": {
                        "maxFiles": question.get("max_files", 1),
                        "maxFileSize": question.get("max_file_size", 10485760),
                        "allowedFileTypes": question.get("allowed_file_types", [])
                    }
                }
            }
        
        # Always nest under questionItem
        item["questionItem"] = question_item
        
    # Media items (images and videos) - these are separate item types
    elif question_type == "image":
        content_uri = question.get("content_uri", "")
        alignment = question.get("alignment", "LEFT")
        item["imageItem"] = {
            "image": {
                "contentUri": content_uri,
                "properties": {
                    "alignment": alignment
                }
            }
        }
        
    elif question_type == "video":
        youtube_uri = question.get("youtube_uri", "")
        item["videoItem"] = {
            "video": {
                "youtubeUri": youtube_uri
            }
        }
        
    # Section/page break items
    elif question_type == "section":
        navigation_type = question.get("navigation_type", "CONTINUE")
        item["pageBreakItem"] = {
            "navigationType": navigation_type
        }
    
    return item


def _format_media_for_api(media_item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert media item data to Google Forms API format (strict, valid structure)."""
    media_type = media_item.get("type", "").lower()
    title = media_item.get("title", "")
    description = media_item.get("description", "")
    
    formatted_media = {
        "title": title
    }
    
    # Add description if provided
    if description:
        formatted_media["description"] = description
    
    if media_type == "image":
        content_uri = media_item.get("content_uri", "")
        alignment = media_item.get("alignment", "LEFT")
        formatted_media["imageItem"] = {
            "image": {
                "contentUri": content_uri,
                "properties": {
                    "alignment": alignment
                }
            }
        }
    elif media_type == "video":
        youtube_uri = media_item.get("youtube_uri", "")
        formatted_media["videoItem"] = {
            "video": {
                "youtubeUri": youtube_uri
            }
        }
    
    return formatted_media


def _format_section_for_api(section: Dict[str, Any]) -> Dict[str, Any]:
    """Convert section data to Google Forms API format (strict, valid structure)."""
    title = section.get("title", "")
    description = section.get("description", "")
    
    formatted_section = {
        "title": title
    }
    
    # Add description if provided
    if description:
        formatted_section["description"] = description
    
    # Add page break for section
    formatted_section["pageBreakItem"] = {
        "navigationType": section.get("navigation_type", "CONTINUE")
    }
    
    return formatted_section


def list_my_forms(tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    List all Google Forms that you have access to.
    
    Use this tool when you need to see all the forms you've created or have access to.
    This tool provides a comprehensive list with form details including titles, IDs,
    creation dates, and URLs.
    
    Returns:
        A dictionary containing form listing results with the following structure:
        - status: 'success' or 'error'
        - forms: List of form objects with details
        - total_count: Total number of forms found
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
    """
    try:
        drive_service = _get_drive_service()
        
        # Search for Google Forms files
        query = "mimeType='application/vnd.google-apps.form'"
        results = drive_service.files().list(
            q=query,
            pageSize=100,
            fields="files(id,name,createdTime,modifiedTime,owners,webViewLink,webContentLink)"
        ).execute()
        
        forms = results.get('files', [])
        
        # Get additional form details using Forms API
        forms_service = _get_forms_service()
        detailed_forms = []
        
        for form in forms:
            try:
                form_details = forms_service.forms().get(formId=form['id']).execute()
                detailed_form = {
                    "form_id": form['id'],
                    "title": form['name'],
                    "created_time": form['createdTime'],
                    "modified_time": form['modifiedTime'],
                    "owners": [owner.get('emailAddress', '') for owner in form.get('owners', [])],
                    "edit_url": f"https://docs.google.com/forms/d/{form['id']}/edit",
                    "responder_url": form_details.get('responderUri', ''),
                    "description": form_details.get('info', {}).get('description', ''),
                    "is_quiz": form_details.get('settings', {}).get('quizSettings', {}).get('isQuiz', False),
                    "item_count": len(form_details.get('items', [])),
                    "web_view_link": form.get('webViewLink', '')
                }
                detailed_forms.append(detailed_form)
            except Exception as e:
                # If we can't get details for a specific form, include basic info
                detailed_form = {
                    "form_id": form['id'],
                    "title": form['name'],
                    "created_time": form['createdTime'],
                    "modified_time": form['modifiedTime'],
                    "owners": [owner.get('emailAddress', '') for owner in form.get('owners', [])],
                    "edit_url": f"https://docs.google.com/forms/d/{form['id']}/edit",
                    "note": f"Could not retrieve full details: {str(e)}"
                }
                detailed_forms.append(detailed_form)
        
        # Store forms list in session state if tool_context is available
        if tool_context:
            tool_context.state["my_forms"] = detailed_forms
            tool_context.state["forms_count"] = len(detailed_forms)
        
        return {
            "status": "success",
            "forms": detailed_forms,
            "total_count": len(detailed_forms),
            "message": f"Found {len(detailed_forms)} forms"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to list forms: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def move_form_to_folder(form_id: str, folder_id: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Move a Google Form to a specific folder in Google Drive.
    
    Use this tool when you want to organize your forms by moving them to specific
    folders in Google Drive. This helps keep your forms organized and easily accessible.
    
    Args:
        form_id: The Google Form ID to move
        folder_id: The Google Drive folder ID to move the form to
        
    Returns:
        A dictionary containing move results with the following structure:
        - status: 'success' or 'error'
        - form_id: The ID of the moved form
        - folder_id: The ID of the destination folder
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
    """
    try:
        drive_service = _get_drive_service()
        
        # Move the form to the specified folder
        file = drive_service.files().update(
            fileId=form_id,
            addParents=folder_id,
            removeParents='root',  # Remove from root folder
            fields='id, parents'
        ).execute()
        
        # Store move info in session state if tool_context is available
        if tool_context:
            tool_context.state["moved_form_id"] = form_id
            tool_context.state["destination_folder_id"] = folder_id
            tool_context.state["move_timestamp"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "form_id": form_id,
            "folder_id": folder_id,
            "message": f"Successfully moved form {form_id} to folder {folder_id}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to move form: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def create_forms_folder(folder_name: str, parent_folder_id: Optional[str] = None, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Create a new folder in Google Drive for organizing forms.
    
    Use this tool when you want to create a dedicated folder to organize your
    Google Forms. This helps keep your forms organized and easily accessible.
    
    Args:
        folder_name: The name for the new folder
        parent_folder_id: The ID of the parent folder (optional, defaults to root)
        
    Returns:
        A dictionary containing folder creation results with the following structure:
        - status: 'success' or 'error'
        - folder_id: The ID of the created folder
        - folder_name: The name of the created folder
        - folder_url: The URL to access the folder
        - message: Human-readable success message
        - error_message: Present only if status is 'error'
    """
    try:
        drive_service = _get_drive_service()
        
        # Prepare folder metadata
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        # Add parent folder if specified
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]
        
        # Create the folder
        folder = drive_service.files().create(
            body=folder_metadata,
            fields='id,name,webViewLink'
        ).execute()
        
        folder_id = folder.get('id')
        folder_url = folder.get('webViewLink')
        
        # Store folder info in session state if tool_context is available
        if tool_context:
            tool_context.state["created_folder_id"] = folder_id
            tool_context.state["created_folder_name"] = folder_name
            tool_context.state["folder_creation_time"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "folder_id": folder_id,
            "folder_name": folder_name,
            "folder_url": folder_url,
            "message": f"Successfully created folder '{folder_name}' with ID {folder_id}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to create folder: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def get_form_details(form_id: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific Google Form.
    
    Use this tool when you need comprehensive information about a specific form
    including its structure, questions, settings, and metadata.
    
    Args:
        form_id: The Google Form ID to get details for
        
    Returns:
        A dictionary containing form details with the following structure:
        - status: 'success' or 'error'
        - form_id: The ID of the form
        - form_info: Complete form information including title, description, settings
        - questions: List of all questions in the form
        - item_count: Number of items in the form
        - is_quiz: Whether the form is a quiz
        - created_time: When the form was created
        - modified_time: When the form was last modified
        - edit_url: URL to edit the form
        - responder_url: URL for form responders
        - error_message: Present only if status is 'error'
    """
    try:
        forms_service = _get_forms_service()
        drive_service = _get_drive_service()
        
        # Get form details from Forms API
        form_details = forms_service.forms().get(formId=form_id).execute()
        
        # Get file metadata from Drive API
        file_metadata = drive_service.files().get(
            fileId=form_id,
            fields='id,name,createdTime,modifiedTime,owners,webViewLink'
        ).execute()
        
        # Process questions/items
        items = form_details.get('items', [])
        questions = []
        
        for item in items:
            question_info = {
                "item_id": item.get('itemId'),
                "title": item.get('title'),
                "type": None
            }
            
            # Determine item type
            if 'questionItem' in item:
                question = item['questionItem'].get('question', {})
                if 'choiceQuestion' in question:
                    choice_type = question['choiceQuestion'].get('type', '')
                    if choice_type == 'RADIO':
                        question_info["type"] = "multiple_choice"
                    elif choice_type == 'CHECKBOX':
                        question_info["type"] = "checkbox"
                elif 'textQuestion' in question:
                    question_info["type"] = "text"
                elif 'dateQuestion' in question:
                    question_info["type"] = "date"
                elif 'timeQuestion' in question:
                    question_info["type"] = "time"
                elif 'fileUploadQuestion' in question:
                    question_info["type"] = "file_upload"
                elif 'scaleQuestion' in question:
                    question_info["type"] = "linear_scale"
                elif 'gridQuestion' in question:
                    question_info["type"] = "grid"
            elif 'imageItem' in item:
                question_info["type"] = "image"
            elif 'videoItem' in item:
                question_info["type"] = "video"
            elif 'pageBreakItem' in item:
                question_info["type"] = "page_break"
            elif 'sectionHeaderItem' in item:
                question_info["type"] = "section_header"
            
            questions.append(question_info)
        
        # Store form details in session state if tool_context is available
        if tool_context:
            tool_context.state["current_form_details"] = form_details
            tool_context.state["current_form_questions"] = questions
        
        return {
            "status": "success",
            "form_id": form_id,
            "form_info": form_details.get('info', {}),
            "questions": questions,
            "item_count": len(items),
            "is_quiz": form_details.get('settings', {}).get('quizSettings', {}).get('isQuiz', False),
            "created_time": file_metadata.get('createdTime'),
            "modified_time": file_metadata.get('modifiedTime'),
            "edit_url": f"https://docs.google.com/forms/d/{form_id}/edit",
            "responder_url": form_details.get('responderUri', ''),
            "owners": [owner.get('emailAddress', '') for owner in file_metadata.get('owners', [])],
            "message": f"Retrieved details for form: {form_details.get('info', {}).get('title', 'Untitled')}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get form details: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _get_drive_service():
    """Get authenticated Google Drive service."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Drive API: {str(e)}") 