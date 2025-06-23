# Google Forms API - Standalone Implementation

A comprehensive standalone implementation of Google Forms API that can be used as separate functions, tools, or integrated into Google ADK agent pipelines.

## 🚀 Features

- **Standalone Functions**: Direct API calls without dependencies
- **Google ADK Tools**: Wrapped tools for agent pipelines
- **Google ADK Agent**: Complete agent with all capabilities
- **Comprehensive API**: Full CRUD operations for Google Forms
- **Auto-completion**: Intelligent filling of missing data
- **Error Handling**: Robust error handling and validation
- **Authentication**: Service account and OAuth2 support

## 📁 File Structure

```
├── google_forms_api.py          # Standalone API implementation
├── google_forms_tool.py         # Google ADK tool wrappers
├── google_forms_agent.py        # Google ADK agent
├── test_standalone_forms.py     # Test script
├── README_standalone_forms.md   # This documentation
└── service_account.json         # Google service account credentials
```

## 🛠️ Installation

1. **Install Dependencies**:
```bash
pip install google-adk google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

2. **Set up Google Service Account**:
   - Create a Google Cloud Project
   - Enable Google Forms API
   - Create a service account
   - Download the JSON credentials file as `service_account.json`

3. **Configure Scopes**:
   The implementation uses these Google API scopes:
   - `https://www.googleapis.com/auth/forms.body`
   - `https://www.googleapis.com/auth/drive.file`
   - `https://www.googleapis.com/auth/forms.responses.readonly`

## 🎯 Usage Examples

### 1. Standalone Functions

Use the API directly without any framework dependencies:

```python
from google_forms_api import create_google_form_standalone, add_questions_standalone

# Create a form
result = create_google_form_standalone(
    title="My Survey Form",
    description="A comprehensive survey about user experience"
)

if result["result"] == "success":
    form_id = result["form_id"]
    print(f"Form created: {result['form_url']}")
    
    # Add questions
    questions = [
        {
            "title": "What is your name?",
            "type": "short_answer",
            "required": True
        },
        {
            "title": "Rate our service",
            "type": "linear_scale",
            "required": False,
            "scale": {"low": 1, "high": 5, "low_label": "Poor", "high_label": "Excellent"}
        }
    ]
    
    add_result = add_questions_standalone(form_id, questions)
    print(f"Added {add_result['questions_added']} questions")
```

### 2. Google ADK Tools

Use the tools in your Google ADK agent pipelines:

```python
from google_forms_tool import create_form, add_questions, configure_settings

# Create a form using ADK tool
result = create_form_tool(
    title="Employee Feedback Form",
    description="Collect feedback from employees"
)

if result["result"] == "success":
    form_id = result["form_id"]
    
    # Add questions
    questions = [
        {
            "title": "Employee ID",
            "type": "short_answer",
            "required": True
        },
        {
            "title": "Department",
            "type": "dropdown",
            "required": True,
            "options": ["Engineering", "Marketing", "Sales", "HR", "Finance"]
        }
    ]
    
    add_questions_tool(form_id, questions)
    
    # Configure settings
    settings = {
        "collect_email": True,
        "allow_response_editing": False,
        "confirmation_message": "Thank you for your feedback!"
    }
    
    configure_settings_tool(form_id, settings)
```

### 3. Google ADK Agent

Use the complete agent for comprehensive form management:

```python
from google_forms_agent import google_forms_agent

# The agent can handle natural language requests
# Example: "Create a customer satisfaction survey with 5 questions"
# The agent will automatically:
# - Generate appropriate title and description
# - Create relevant questions
# - Configure appropriate settings
# - Provide form URLs and IDs
```

### 4. GoogleFormsAPI Class

Use the class for more control and batch operations:

```python
from google_forms_api import GoogleFormsAPI

# Initialize the API
api = GoogleFormsAPI()

# Create a form
result = api.create_form("Quiz Form", "A test quiz")

if result["result"] == "success":
    form_id = result["form_id"]
    
    # Add multiple questions
    questions = [
        {
            "title": "What is 2 + 2?",
            "type": "multiple_choice",
            "required": True,
            "options": ["3", "4", "5", "6"]
        },
        {
            "title": "Explain your reasoning",
            "type": "long_answer",
            "required": False
        }
    ]
    
    api.add_questions(form_id, questions)
    
    # Configure as quiz
    api.configure_settings(form_id, {"is_quiz": True})
    
    # Get form info
    info = api.get_form_info(form_id)
    print(f"Form has {len(info['items'])} questions")
```

## 📋 Supported Question Types

| Type | Description | Example |
|------|-------------|---------|
| `short_answer` | Single line text input | Name, email, phone |
| `long_answer` | Multi-line text input | Comments, feedback |
| `multiple_choice` | Radio button selection | Yes/No, single choice |
| `checkbox` | Multiple selection | "Select all that apply" |
| `dropdown` | Dropdown menu | Department, country |
| `linear_scale` | Rating scale | 1-5, 1-10 ratings |
| `date` | Date picker | Birth date, event date |
| `time` | Time picker | Meeting time |
| `grid` | Multiple choice grid | Matrix questions |

## ⚙️ Form Settings

Configure various form settings:

```python
settings = {
    "is_quiz": True,                    # Enable quiz mode
    "collect_email": True,              # Collect respondent emails
    "allow_response_editing": False,    # Allow editing responses
    "confirmation_message": "Thanks!"   # Custom confirmation
}
```

## 🔧 Available Functions

### Standalone Functions
- `create_google_form_standalone(title, description)`
- `update_form_standalone(form_id, title, description)`
- `add_questions_standalone(form_id, questions)`
- `get_form_info_standalone(form_id)`
- `get_responses_standalone(form_id)`
- `delete_form_standalone(form_id)`

### Google ADK Tools
- `create_form` - Create new forms
- `update_form` - Update form metadata
- `add_questions` - Add questions to forms
- `get_form_info` - Get form information
- `get_responses` - Get form responses
- `delete_form` - Delete forms
- `configure_settings` - Configure form settings
- `update_questions` - Update existing questions
- `delete_questions` - Delete questions by index

### GoogleFormsAPI Class Methods
- `create_form(title, description)`
- `update_form_info(form_id, title, description)`
- `add_questions(form_id, questions)`
- `update_questions(form_id, question_updates)`
- `delete_questions(form_id, question_indices)`
- `configure_settings(form_id, settings)`
- `get_form_info(form_id)`
- `get_responses(form_id)`
- `delete_form(form_id)`

## 🧪 Testing

Run the comprehensive test script:

```bash
python test_standalone_forms.py
```

This will test:
- Standalone functions
- Google ADK tools
- Google ADK agent
- GoogleFormsAPI class

## 🔐 Authentication

### Service Account (Recommended)
1. Place `service_account.json` in the project root
2. The API will automatically use service account authentication

### OAuth2 (Fallback)
1. Place `service_account.json` in the project root
2. The API will use OAuth2 flow for user authentication

## 🚨 Error Handling

All functions return consistent error responses:

```python
{
    "result": "error",
    "message": "Detailed error message",
    "error_code": 400,  # HTTP status code
    "error_type": "HttpError"
}
```

## 🔄 Integration with Existing Agent Pipeline

To integrate with your existing forms agent pipeline:

```python
# In your main agent
from google_forms_tool import create_form, add_questions

# Add the tools to your agent
my_agent = Agent(
    name="MyAgent",
    tools=[create_form, add_questions, ...],
    # ... other configuration
)
```

## 📝 Response Format

All successful operations return:

```python
{
    "result": "success",
    "form_id": "1FAIpQLS...",
    "form_url": "https://docs.google.com/forms/d/...",
    "message": "Operation completed successfully",
    # ... additional data specific to operation
}
```

## 🎯 Best Practices

1. **Always validate responses**: Check `result` field before proceeding
2. **Use auto-completion**: Let the API fill missing data intelligently
3. **Handle errors gracefully**: Provide fallback options
4. **Store form IDs**: Keep track of created forms for later operations
5. **Use batch operations**: When possible, use batch updates for efficiency
6. **Test thoroughly**: Use the test script to verify functionality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the error messages for guidance
2. Review the test script for examples
3. Ensure your service account has proper permissions
4. Verify Google Forms API is enabled in your project

## 🔗 Related Links

- [Google Forms API Documentation](https://developers.google.com/forms/api)
- [Google ADK Documentation](https://developers.google.com/adk)
- [Google Cloud Console](https://console.cloud.google.com/) 