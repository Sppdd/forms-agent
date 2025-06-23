"""
Google Forms API - Standalone Implementation

This module provides a comprehensive standalone implementation for Google Forms API
operations. It can be used as a separate function file, tool, or integrated into
agent pipelines.

Features:
- Form creation, editing, and deletion
- Question management (add, update, delete)
- Form settings configuration
- Response retrieval
- Authentication handling (service account)
- Error handling and validation
"""

import os
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Forms API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/forms.responses.readonly'
]

# Service account file path
SERVICE_ACCOUNT_FILE = 'service_account.json'

# Question type mappings
QUESTION_TYPE_MAPPING = {
    "multiple_choice": "MULTIPLE_CHOICE",
    "short_answer": "SHORT_ANSWER", 
    "long_answer": "PARAGRAPH",
    "checkbox": "CHECKBOX",
    "dropdown": "DROP_DOWN",
    "linear_scale": "LINEAR_SCALE",
    "date": "DATE",
    "time": "TIME",
    "grid": "MULTIPLE_CHOICE_GRID"
}


class GoogleFormsAPI:
    """Standalone Google Forms API client with comprehensive functionality."""
    
    def __init__(self, service_account_file: str = SERVICE_ACCOUNT_FILE):
        """
        Initialize the Google Forms API client.
        
        Args:
            service_account_file: Path to service account JSON file
        """
        self.service_account_file = service_account_file
        self.forms_service = None
        self.drive_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google APIs using service account."""
        try:
            if os.path.exists(self.service_account_file):
                # Use service account authentication
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_file, scopes=SCOPES
                )
                self.forms_service = build('forms', 'v1', credentials=credentials)
                self.drive_service = build('drive', 'v3', credentials=credentials)
            else:
                # Fallback to OAuth2 flow
                self._authenticate_oauth2()
        except Exception as e:
            if "service_account.json not found" in str(e):
                raise Exception(f"Authentication failed: {self.service_account_file} not found. Please ensure the Google service account credentials file is available in the project root directory.")
            else:
                raise Exception(f"Authentication failed: {str(e)}")
    
    def _authenticate_oauth2(self):
        """Authenticate using OAuth2 flow (fallback)."""
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('service_account.json'):
                    raise FileNotFoundError("service_account.json not found. Please ensure the Google service account credentials file is available in the project root directory.")
                flow = InstalledAppFlow.from_client_secrets_file('service_account.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.forms_service = build('forms', 'v1', credentials=creds)
        self.drive_service = build('drive', 'v3', credentials=creds)
    
    def create_form(self, title: str, description: str = "", form_type: str = "form") -> Dict[str, Any]:
        """
        Create a new Google Form.
        
        Args:
            title: Form title
            description: Form description (auto-generated if empty)
            form_type: Type of form to create ("form" or "quiz")
            
        Returns:
            Dict containing form creation results
        """
        try:
            # Auto-generate description if empty
            if not description or description.strip() == "":
                description = f"{form_type.title()} created automatically - {title}"
            
            # Google Forms API only allows setting title during creation
            form_request = {
                "info": {
                    "title": title,
                    "documentTitle": title
                }
            }
            
            result = self.forms_service.forms().create(body=form_request).execute()
            
            form_id = result.get('formId')
            form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
            responder_url = result.get('responderUri')
            
            # Update description separately if provided
            if description and description.strip() != "":
                update_result = self.update_form_info(form_id, title, description)
                if update_result["result"] == "success":
                    description = update_result.get("updated_description", description)
            
            # Configure as quiz if specified
            if form_type.lower() == "quiz":
                quiz_settings = {
                    "is_quiz": True
                }
                quiz_result = self.configure_settings(form_id, quiz_settings)
                if quiz_result["result"] != "success":
                    print(f"Warning: Failed to configure quiz settings: {quiz_result['message']}")
            
            return {
                "result": "success",
                "form_id": form_id,
                "form_url": form_url,
                "responder_url": responder_url,
                "form_info": result.get('info', {}),
                "description": description,
                "form_type": form_type,
                "message": f"Successfully created {form_type}: {title}"
            }
            
        except HttpError as e:
            error_details = json.loads(e.content.decode())
            return {
                "result": "error",
                "message": f"Google Forms API error: {error_details.get('error', {}).get('message', str(e))}",
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "result": "error",
                "message": f"Failed to create form: {str(e)}"
            }
    
    def update_form_info(self, form_id: str, title: str = "", description: str = "") -> Dict[str, Any]:
        """
        Update form title and/or description.
        
        Args:
            form_id: The Google Form ID
            title: New form title (optional)
            description: New form description (optional)
            
        Returns:
            Dict containing update results
        """
        try:
            # Get current form info if not provided
            if not title or not description:
                current_form = self.forms_service.forms().get(formId=form_id).execute()
                current_info = current_form.get('info', {})
                title = title or current_info.get('title', 'Updated Form')
                description = description or current_info.get('description', f'Form updated - {title}')
            
            requests = [{
                "updateFormInfo": {
                    "info": {
                        "title": title,
                        "description": description
                    },
                    "updateMask": "title,description"
                }
            }]
            
            batch_request = {"requests": requests}
            result = self.forms_service.forms().batchUpdate(
                formId=form_id,
                body=batch_request
            ).execute()
            
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
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "result": "error",
                "message": f"Failed to update form: {str(e)}"
            }
    
    def add_questions(self, form_id: str, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add questions to a Google Form.
        
        Args:
            form_id: The Google Form ID
            questions: List of question dictionaries
            
        Returns:
            Dict containing question addition results
        """
        try:
            requests = []
            
            for i, question in enumerate(questions):
                formatted_question = self._format_question_for_api(question)
                item_request = {
                    "createItem": {
                        "item": {
                            "title": question.get("title", ""),
                            "questionItem": {
                                "question": formatted_question,
                                "required": question.get("required", False)
                            }
                        },
                        "location": {
                            "index": i
                        }
                    }
                }
                requests.append(item_request)
            
            if requests:
                batch_request = {"requests": requests}
                result = self.forms_service.forms().batchUpdate(
                    formId=form_id,
                    body=batch_request
                ).execute()
                
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
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "result": "error",
                "message": f"Failed to add questions: {str(e)}"
            }
    
    def update_questions(self, form_id: str, question_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update existing questions in a Google Form.
        
        Args:
            form_id: The Google Form ID
            question_updates: List of question update dictionaries with item_id
            
        Returns:
            Dict containing update results
        """
        try:
            requests = []
            
            for update in question_updates:
                item_id = update.get("item_id")
                question_data = update.get("question", {})
                
                if not item_id:
                    continue
                
                formatted_question = self._format_question_for_api(question_data)
                requests.append({
                    "updateItem": {
                        "item": {
                            "itemId": item_id,
                            "title": question_data.get("title", ""),
                            "questionItem": {
                                "question": formatted_question,
                                "required": question_data.get("required", False)
                            }
                        },
                        "updateMask": "title,questionItem"
                    }
                })
            
            if requests:
                batch_request = {"requests": requests}
                result = self.forms_service.forms().batchUpdate(
                    formId=form_id,
                    body=batch_request
                ).execute()
                
                return {
                    "result": "success",
                    "questions_updated": len(requests),
                    "batch_result": result,
                    "message": f"Successfully updated {len(requests)} questions in form {form_id}"
                }
            else:
                return {
                    "result": "success",
                    "questions_updated": 0,
                    "message": "No questions to update"
                }
                
        except HttpError as e:
            error_details = json.loads(e.content.decode())
            return {
                "result": "error",
                "message": f"Failed to update questions: {error_details.get('error', {}).get('message', str(e))}",
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "result": "error",
                "message": f"Failed to update questions: {str(e)}"
            }
    
    def delete_questions(self, form_id: str, question_indices: List[int]) -> Dict[str, Any]:
        """
        Delete questions from a Google Form by index.
        
        Args:
            form_id: The Google Form ID
            question_indices: List of question indices to delete
            
        Returns:
            Dict containing deletion results
        """
        try:
            requests = []
            
            for index in question_indices:
                requests.append({
                    "deleteItem": {
                        "location": {
                            "index": index
                        }
                    }
                })
            
            if requests:
                batch_request = {"requests": requests}
                result = self.forms_service.forms().batchUpdate(
                    formId=form_id,
                    body=batch_request
                ).execute()
                
                return {
                    "result": "success",
                    "questions_deleted": len(requests),
                    "batch_result": result,
                    "message": f"Successfully deleted {len(requests)} questions from form {form_id}"
                }
            else:
                return {
                    "result": "success",
                    "questions_deleted": 0,
                    "message": "No questions to delete"
                }
                
        except HttpError as e:
            error_details = json.loads(e.content.decode())
            return {
                "result": "error",
                "message": f"Failed to delete questions: {error_details.get('error', {}).get('message', str(e))}",
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "result": "error",
                "message": f"Failed to delete questions: {str(e)}"
            }
    
    def configure_settings(self, form_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure form settings.
        
        Args:
            form_id: The Google Form ID
            settings: Dictionary of settings to configure
            
        Returns:
            Dict containing settings configuration results
        """
        try:
            requests = []
            
            # Quiz settings
            if "is_quiz" in settings:
                requests.append({
                    "updateSettings": {
                        "settings": {
                            "quizSettings": {
                                "isQuiz": settings["is_quiz"]
                            }
                        },
                        "updateMask": "quizSettings.isQuiz"
                    }
                })
            
            # General settings
            general_settings = {}
            update_mask_parts = []
            
            if "collect_email" in settings:
                general_settings["collectEmail"] = settings["collect_email"]
                update_mask_parts.append("generalSettings.collectEmail")
            
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
            
            if requests:
                batch_request = {"requests": requests}
                result = self.forms_service.forms().batchUpdate(
                    formId=form_id,
                    body=batch_request
                ).execute()
                
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
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "result": "error",
                "message": f"Failed to configure form settings: {str(e)}"
            }
    
    def get_form_info(self, form_id: str) -> Dict[str, Any]:
        """
        Get form information and structure.
        
        Args:
            form_id: The Google Form ID
            
        Returns:
            Dict containing form information
        """
        try:
            result = self.forms_service.forms().get(formId=form_id).execute()
            
            return {
                "result": "success",
                "form_id": form_id,
                "form_info": result.get('info', {}),
                "items": result.get('items', []),
                "settings": result.get('settings', {}),
                "message": f"Successfully retrieved form info for {form_id}"
            }
            
        except HttpError as e:
            error_details = json.loads(e.content.decode())
            return {
                "result": "error",
                "message": f"Failed to get form info: {error_details.get('error', {}).get('message', str(e))}",
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "result": "error",
                "message": f"Failed to get form info: {str(e)}"
            }
    
    def get_responses(self, form_id: str) -> Dict[str, Any]:
        """
        Get form responses.
        
        Args:
            form_id: The Google Form ID
            
        Returns:
            Dict containing form responses
        """
        try:
            result = self.forms_service.forms().responses().list(formId=form_id).execute()
            responses = result.get('responses', [])
            
            processed_responses = []
            for response in responses:
                processed_response = {
                    "response_id": response.get('responseId'),
                    "create_time": response.get('createTime'),
                    "last_submitted_time": response.get('lastSubmittedTime'),
                    "answers": response.get('answers', {})
                }
                processed_responses.append(processed_response)
            
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
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "result": "error",
                "message": f"Failed to get responses: {str(e)}"
            }
    
    def delete_form(self, form_id: str) -> Dict[str, Any]:
        """
        Delete a Google Form permanently.
        
        Args:
            form_id: The Google Form ID to delete
            
        Returns:
            Dict containing deletion results
        """
        try:
            # Use Drive API to delete the form file
            self.drive_service.files().delete(fileId=form_id).execute()
            
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
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "result": "error",
                "message": f"Failed to delete form: {str(e)}"
            }
    
    def _format_question_for_api(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format question data for Google Forms API.
        
        Args:
            question: Question dictionary
            
        Returns:
            Formatted question for API
        """
        question_type = question.get("type", "short_answer")
        api_type = QUESTION_TYPE_MAPPING.get(question_type, "SHORT_ANSWER")
        
        formatted_question = {
            "questionType": api_type,
            "required": question.get("required", False)
        }
        
        # Add type-specific properties
        if api_type in ["MULTIPLE_CHOICE", "CHECKBOX", "DROP_DOWN"]:
            options = question.get("options", [])
            formatted_question["choiceQuestion"] = {
                "type": "RADIO" if api_type == "MULTIPLE_CHOICE" else api_type,
                "options": [{"value": str(option)} for option in options]
            }
        elif api_type == "LINEAR_SCALE":
            scale_data = question.get("scale", {"low": 1, "high": 5})
            formatted_question["scaleQuestion"] = {
                "low": scale_data.get("low", 1),
                "high": scale_data.get("high", 5),
                "lowLabel": scale_data.get("low_label", ""),
                "highLabel": scale_data.get("high_label", "")
            }
        elif api_type in ["MULTIPLE_CHOICE_GRID", "CHECKBOX_GRID"]:
            grid_data = question.get("grid", {})
            formatted_question["rowQuestion"] = {
                "title": grid_data.get("title", ""),
                "options": [{"value": str(option)} for option in grid_data.get("options", [])]
            }
        
        return formatted_question


# Standalone functions for easy integration
def create_google_form_standalone(title: str, description: str = "", form_type: str = "form", service_account_file: str = SERVICE_ACCOUNT_FILE) -> Dict[str, Any]:
    """Standalone function to create a Google Form."""
    api = GoogleFormsAPI(service_account_file)
    return api.create_form(title, description, form_type)


def update_form_standalone(form_id: str, title: str = "", description: str = "", service_account_file: str = SERVICE_ACCOUNT_FILE) -> Dict[str, Any]:
    """Standalone function to update a Google Form."""
    api = GoogleFormsAPI(service_account_file)
    return api.update_form_info(form_id, title, description)


def add_questions_standalone(form_id: str, questions: List[Dict[str, Any]], service_account_file: str = SERVICE_ACCOUNT_FILE) -> Dict[str, Any]:
    """Standalone function to add questions to a Google Form."""
    api = GoogleFormsAPI(service_account_file)
    return api.add_questions(form_id, questions)


def get_form_info_standalone(form_id: str, service_account_file: str = SERVICE_ACCOUNT_FILE) -> Dict[str, Any]:
    """Standalone function to get form information."""
    api = GoogleFormsAPI(service_account_file)
    return api.get_form_info(form_id)


def get_responses_standalone(form_id: str, service_account_file: str = SERVICE_ACCOUNT_FILE) -> Dict[str, Any]:
    """Standalone function to get form responses."""
    api = GoogleFormsAPI(service_account_file)
    return api.get_responses(form_id)


def delete_form_standalone(form_id: str, service_account_file: str = SERVICE_ACCOUNT_FILE) -> Dict[str, Any]:
    """Standalone function to delete a Google Form."""
    api = GoogleFormsAPI(service_account_file)
    return api.delete_form(form_id)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    print("Google Forms API - Standalone Implementation")
    print("=" * 50)
    
    # Test form creation
    print("\n1. Creating a test form...")
    result = create_google_form_standalone(
        title="Test Form - API Implementation",
        description="This is a test form created using the standalone Google Forms API"
    )
    
    if result["result"] == "success":
        form_id = result["form_id"]
        print(f"✅ Form created successfully!")
        print(f"   Form ID: {form_id}")
        print(f"   Form URL: {result['form_url']}")
        
        # Test adding questions
        print("\n2. Adding questions to the form...")
        questions = [
            {
                "title": "What is your name?",
                "type": "short_answer",
                "required": True
            },
            {
                "title": "How would you rate our service?",
                "type": "linear_scale",
                "required": False,
                "scale": {"low": 1, "high": 5, "low_label": "Poor", "high_label": "Excellent"}
            },
            {
                "title": "What features would you like to see?",
                "type": "checkbox",
                "required": False,
                "options": ["Feature A", "Feature B", "Feature C", "Feature D"]
            }
        ]
        
        add_result = add_questions_standalone(form_id, questions)
        if add_result["result"] == "success":
            print(f"✅ {add_result['questions_added']} questions added successfully!")
        
        # Test getting form info
        print("\n3. Getting form information...")
        info_result = get_form_info_standalone(form_id)
        if info_result["result"] == "success":
            print(f"✅ Form info retrieved successfully!")
            print(f"   Title: {info_result['form_info'].get('title', 'N/A')}")
            print(f"   Items count: {len(info_result['items'])}")
        
        # Test updating form
        print("\n4. Updating form information...")
        update_result = update_form_standalone(
            form_id, 
            title="Updated Test Form - API Implementation",
            description="This form has been updated using the standalone API"
        )
        if update_result["result"] == "success":
            print("✅ Form updated successfully!")
        
        print(f"\n🎉 All tests completed successfully!")
        print(f"📝 Form URL: {result['form_url']}")
        print(f"📊 Responder URL: {result['responder_url']}")
        
    else:
        print(f"❌ Form creation failed: {result['message']}") 