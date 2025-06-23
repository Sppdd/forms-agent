# 📝 Google Forms Manager

A powerful Streamlit web application for managing Google Forms with OAuth authentication. Create, edit, organize, and manage your Google Forms through an intuitive web interface.

## ✨ Features

- 🔐 **OAuth Authentication**: Secure authentication with your Google account
- 📝 **Form Creation**: Create new forms with various question types
- 📋 **Form Management**: List, view, and edit your existing forms
- 📁 **Organization**: Organize forms in folders (coming soon)
- 📊 **Analytics**: View form responses and analytics (coming soon)
- 🎨 **Modern UI**: Beautiful and intuitive user interface
- ☁️ **Cloud Ready**: Deploy to Streamlit Cloud for public access

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/forms-agent.git
   cd forms-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements_streamlit.txt
   ```

3. **Set up OAuth credentials**
   - Follow the [Google Cloud Setup Guide](STREAMLIT_CLOUD_DEPLOYMENT.md#step-1-google-cloud-setup)
   - Set environment variables:
     ```bash
     export GOOGLE_CLIENT_ID="your-client-id"
     export GOOGLE_CLIENT_SECRET="your-client-secret"
     ```

4. **Run the application**
   ```bash
   streamlit run streamlit_app_oauth.py
   ```

### Streamlit Cloud Deployment

For public deployment, follow the complete [Streamlit Cloud Deployment Guide](STREAMLIT_CLOUD_DEPLOYMENT.md).

## 📁 Project Structure

```
forms-agent/
├── streamlit_app_oauth.py      # Main OAuth-enabled Streamlit app
├── streamlit_app.py            # Service account version (legacy)
├── streamlit_app_simple.py     # Simple version
├── requirements_streamlit.txt   # Dependencies for Streamlit
├── requirements.txt            # Full dependencies
├── README.md                   # This file
├── STREAMLIT_CLOUD_DEPLOYMENT.md # Deployment guide
└── forms_agent/               # Core forms agent modules
    ├── __init__.py
    ├── agent.py               # Main agent
    └── subagents/             # Specialized subagents
        ├── form_creator/      # Form creation tools
        ├── form_editor/       # Form editing tools
        ├── form_validator/    # Form validation tools
        └── document_parser/   # Document parsing tools
```

## 🔧 Configuration

### OAuth Setup

The application uses OAuth 2.0 for secure authentication. You need to:

1. **Create a Google Cloud Project**
2. **Enable Required APIs**:
   - Google Forms API
   - Google Drive API
3. **Create OAuth 2.0 Credentials**
4. **Configure Environment Variables**

See [STREAMLIT_CLOUD_DEPLOYMENT.md](STREAMLIT_CLOUD_DEPLOYMENT.md) for detailed instructions.

### Environment Variables

For local development:
```bash
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-client-secret
```

For Streamlit Cloud, add these as secrets in your app settings.

## 🎯 Usage

### Authentication

1. Visit the application
2. Click "Authorize" to authenticate with Google
3. Grant necessary permissions
4. Enter the authorization code
5. Start managing your forms!

### Creating Forms

1. Navigate to "Create Form"
2. Enter form title and description
3. Click "Create Form"
4. Your form will be created and you'll get the links

### Managing Forms

1. Go to "My Forms" to see all your forms
2. Click "View" to see form details
3. Click "Edit" to modify forms
4. Use "Refresh" to update the list

## 🔐 Security

- ✅ OAuth 2.0 authentication
- ✅ Secure token handling
- ✅ Session-based authentication
- ✅ No service account files needed
- ✅ Environment variable protection

## 🛠️ Development

### Adding New Features

1. **Backend**: Add new functions in the appropriate subagent
2. **Frontend**: Update the Streamlit app interface
3. **Testing**: Test locally before deploying

### Code Structure

- **`streamlit_app_oauth.py`**: Main application with OAuth
- **`forms_agent/`**: Core business logic and API interactions
- **`subagents/`**: Specialized modules for different tasks

## 📊 API Usage

The application uses these Google APIs:
- **Google Forms API**: Form creation and management
- **Google Drive API**: File organization and access
- **Google Drive File API**: File-specific operations

## 🚀 Deployment

### Streamlit Cloud (Recommended)

1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Configure OAuth secrets
4. Deploy!

See [STREAMLIT_CLOUD_DEPLOYMENT.md](STREAMLIT_CLOUD_DEPLOYMENT.md) for complete instructions.

### Other Platforms

The application can be deployed to any platform that supports Streamlit:
- Heroku
- AWS
- Google Cloud Platform
- Azure

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:

1. Check the [troubleshooting guide](STREAMLIT_CLOUD_DEPLOYMENT.md#troubleshooting)
2. Review the deployment documentation
3. Check Google Cloud Console for API errors
4. Create an issue in the repository

## 🔄 Changelog

### Version 1.0.0
- ✅ OAuth authentication implementation
- ✅ Form creation and management
- ✅ Streamlit Cloud deployment support
- ✅ Clean codebase structure
- ✅ Comprehensive documentation

---

**Happy Form Managing! 📝✨** 