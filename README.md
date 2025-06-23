# 📝 Google Forms Agent

A powerful Streamlit web application for managing Google Forms with OAuth authentication. Create, edit, organize, and manage your Google Forms through an intuitive web interface.

## ✨ Features

- 🔐 **OAuth Authentication**: Secure authentication with your Google account
- 📝 **Form Creation**: Create new forms with various question types
- 📋 **Form Management**: List, view, and edit your existing forms
- 📁 **Organization**: Organize forms in folders (coming soon)
- 📊 **Analytics**: View form responses and analytics (coming soon)
- 🎨 **Modern UI**: Beautiful and intuitive user interface with glassmorphism design
- ☁️ **Cloud Ready**: Deploy to Streamlit Cloud for public access
- 🤖 **AI-Powered**: Convert documents into forms using advanced AI

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/forms-agent.git
cd forms-agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up OAuth Credentials

#### A. Google Cloud Console Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Required APIs**
   - Go to "APIs & Services" > "Library"
   - Enable these APIs:
     - Google Forms API
     - Google Drive API
     - Google People API

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - For local development: `http://localhost:8501/`
     - For production: `https://your-app-name.streamlit.app/`

4. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" user type
   - Fill in required information
   - Add required scopes
   - Add test users if needed

#### B. Local Configuration

1. **Copy the example configuration:**
   ```bash
   cp config.example.toml .streamlit/secrets.toml
   ```

2. **Edit `.streamlit/secrets.toml`** with your real credentials:
   ```toml
   [auth]
   redirect_uri = "http://localhost:8501/"
   client_id = "your-actual-client-id.apps.googleusercontent.com"
   client_secret = "your-actual-client-secret"
   cookie_secret = "your-secure-random-string"
   ```

### 4. Run the Application

```bash
streamlit run app.py
```

Visit `http://localhost:8501` to use the application.

## 🔒 Security Best Practices

- ✅ **Never commit credentials to git**
- ✅ **Use `.streamlit/secrets.toml` for local development**
- ✅ **Use Streamlit Cloud secrets for production**
- ✅ **Rotate credentials regularly**
- ✅ **Use environment variables in production**

## 🎨 UI Features

The application features a modern, beautiful interface with:

- **Glassmorphism Design**: Semi-transparent cards with blur effects
- **Gradient Backgrounds**: Beautiful purple-to-blue gradients
- **Smooth Animations**: Hover effects and transitions
- **Responsive Layout**: Works on desktop and mobile
- **Modern Typography**: Clean, readable fonts
- **Interactive Elements**: Animated buttons and cards

## 📁 Project Structure

```
forms-agent/
├── app.py                      # Main Streamlit application
├── config.example.toml         # Example configuration (safe to commit)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── oauth_troubleshoot.py       # OAuth debugging tool
├── fix_oauth_403.md           # OAuth troubleshooting guide
├── .streamlit/
│   ├── secrets.toml           # Your actual credentials (DO NOT COMMIT)
│   └── config.toml            # Streamlit configuration
└── forms_agent/               # Core forms agent modules
    ├── __init__.py
    ├── agent.py               # Main agent
    └── subagents/             # Specialized subagents
        ├── form_creator/      # Form creation tools
        ├── form_editor/       # Form editing tools
        ├── form_validator/    # Form validation tools
        └── document_parser/   # Document parsing tools
```

## 🛠️ Development

### Adding New Features

1. Create new subagents in `forms_agent/subagents/`
2. Update the main agent in `forms_agent/agent.py`
3. Add new UI components in `app.py`

### Testing OAuth

Run the troubleshooting script:
```bash
python oauth_troubleshoot.py
```

## ☁️ Deployment

### Streamlit Cloud Deployment

1. **Push your code to GitHub** (without secrets!)
2. **Connect to Streamlit Cloud**
3. **Add secrets in Streamlit Cloud dashboard:**
   - Go to your app settings
   - Add secrets in TOML format
   - Use production redirect URI

### Environment Variables

For other platforms, set these environment variables:
```bash
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
STREAMLIT_REDIRECT_URI=your-redirect-uri
```

## 🐛 Troubleshooting

### OAuth 403 Errors

1. **Check API enablement** in Google Cloud Console
2. **Verify redirect URIs** match exactly
3. **Run the troubleshooter**: `python oauth_troubleshoot.py`
4. **See the detailed guide**: `fix_oauth_403.md`

### Common Issues

- **Redirect URI mismatch**: Ensure exact match including trailing slash
- **APIs not enabled**: Enable Google Forms API and Drive API
- **Consent screen not configured**: Complete OAuth consent screen setup
- **Invalid credentials**: Double-check client_id and client_secret

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- 📚 [Documentation](https://github.com/your-repo/forms-agent/wiki)
- 🐛 [Report Issues](https://github.com/your-repo/forms-agent/issues)
- 💬 [Discussions](https://github.com/your-repo/forms-agent/discussions)

---

**⚠️ Security Notice**: Never commit OAuth credentials or API keys to version control. Always use environment variables or secure secret management. 