# Google Forms Manager

A comprehensive Google Forms management system with AI-powered agents and a modern web interface. Create, edit, organize, and manage Google Forms with advanced automation capabilities.

## 🌟 Features

### 🤖 AI-Powered Agents
- **Document Parser Agent**: Extract form requirements from documents
- **Form Creator Agent**: Automatically generate forms from specifications
- **Form Editor Agent**: Modify existing forms with intelligent suggestions
- **Form Validator Agent**: Validate forms for completeness and best practices

### 🌐 Web Interface
- **Modern Streamlit UI**: Beautiful, responsive web application
- **Google OAuth Authentication**: Secure login with Google accounts
- **Real-time Form Management**: Create, edit, and organize forms
- **Analytics Dashboard**: View form statistics and usage metrics
- **Folder Organization**: Organize forms in Google Drive folders

### 🔧 Advanced Capabilities
- **Service Account Integration**: Automated form operations
- **Google Drive Integration**: Seamless file management
- **Batch Operations**: Process multiple forms efficiently
- **Response Analysis**: View and analyze form responses
- **Custom Question Types**: Support for all Google Forms question types

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Cloud Project with Forms API enabled
- Google OAuth credentials (for web app)
- Service account key (for automated operations)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sppdd/forms-agent.git
   cd forms-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_streamlit.txt
   ```

3. **Set up Google Cloud credentials**
   - Place your service account JSON file in `forms_agent/service-account-key.json`
   - Configure OAuth credentials for the web app (see deployment guide)

4. **Configure Streamlit secrets**
   ```bash
   # Create .streamlit/secrets.toml
   [auth]
   redirect_uri = "http://localhost:8501/oauth2callback"
   cookie_secret = "your-secure-cookie-secret"
   client_id = "your-google-client-id"
   client_secret = "your-google-client-secret"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

   [forms_agent]
   service_account_path = "forms_agent/service-account-key.json"
   ```

### Running the Application

#### Web Interface (Recommended)
```bash
streamlit run streamlit_app.py
```
Visit `http://localhost:8501` and log in with your Google account.

#### Command Line Interface
```bash
# Test service account
python quick_form_access.py

# Run forms management example
python forms_drive_management_example.py
```

## 📖 Usage Guide

### Web Interface

1. **Authentication**: Log in with your Google account
2. **My Forms**: View and manage all your forms
3. **Create Form**: Build new forms with an intuitive interface
4. **Organize**: Create folders and organize your forms
5. **Analytics**: View form statistics and usage data

### Programmatic Usage

```python
from forms_agent.subagents.form_creator.tools import create_google_form, list_my_forms
from forms_agent.subagents.form_editor.tools import update_form_info, get_form_responses

# Create a new form
result = create_google_form(
    title="Customer Feedback Survey",
    description="Help us improve our services",
    form_type="form"
)

# List all forms
forms = list_my_forms()

# Get form responses
responses = get_form_responses("form_id_here")
```

## 🏗️ Architecture

### Agent System
```
forms_agent/
├── agent.py                 # Main orchestrator agent
├── optimized_agent.py       # Performance-optimized version
└── subagents/
    ├── document_parser/     # Extract requirements from docs
    ├── form_creator/        # Generate new forms
    ├── form_editor/         # Modify existing forms
    └── form_validator/      # Validate form completeness
```

### Web Application
```
├── streamlit_app.py         # Main web application
├── .streamlit/secrets.toml  # OAuth configuration
├── Dockerfile              # Container configuration
└── docker-compose.yml      # Multi-service deployment
```

## 🚀 Deployment

### Streamlit Community Cloud
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Configure secrets in Streamlit Cloud dashboard
4. Deploy

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t forms-manager .
docker run -p 8501:8080 forms-manager
```

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/forms-manager
gcloud run deploy forms-manager --image gcr.io/YOUR_PROJECT_ID/forms-manager
```

For detailed deployment instructions, see [deploy_guide.md](deploy_guide.md).

## 🔐 Security

- **OAuth 2.0 Authentication**: Secure Google account login
- **Service Account Security**: Isolated credentials for automated operations
- **HTTPS Enforcement**: All production deployments use SSL
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Sanitized user inputs

## 📊 API Reference

### Form Creation
```python
create_google_form(title, description, form_type="form")
add_questions_to_form(form_id, questions)
setup_form_settings(form_id, settings)
```

### Form Management
```python
list_my_forms()
get_form_details(form_id)
update_form_info(form_id, updates)
delete_form(form_id)
```

### Organization
```python
create_forms_folder(name, parent_folder_id=None)
move_form_to_folder(form_id, folder_id)
```

### Responses
```python
get_form_responses(form_id)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the guides in this repository
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join GitHub Discussions for questions

## 🔄 Changelog

### v2.0.0 - Web Interface Release
- ✨ Added Streamlit web application with OAuth
- 🔐 Google OAuth authentication
- 📱 Responsive web interface
- 📊 Analytics dashboard
- 🗂️ Folder organization features

### v1.0.0 - Initial Release
- 🤖 AI-powered form agents
- 🔧 Service account integration
- 📝 Form creation and editing
- ✅ Form validation
- 📄 Document parsing

## 🙏 Acknowledgments

- Google Forms API for form management capabilities
- Streamlit for the web framework
- Google Cloud Platform for hosting and authentication
- The open-source community for various dependencies 