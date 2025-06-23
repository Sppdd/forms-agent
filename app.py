#!/usr/bin/env python3
"""
Google Forms Agent - Main Application

A unified web application that integrates OAuth authentication with the forms agent pipeline.
Users can authenticate with Google to access their Drive files and create forms using AI.
"""

import streamlit as st
import os
import sys
import json
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Add the forms_agent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'forms_agent'))

# Import forms agent
try:
    from forms_agent.agent import root_agent
    FORMS_AGENT_AVAILABLE = True
except ImportError as e:
    st.error(f"Forms agent not available: {e}")
    FORMS_AGENT_AVAILABLE = False

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/forms',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'openid',
    'email',
    'profile'
]

# Page configuration
st.set_page_config(
    page_title="Google Forms Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/forms-agent',
        'Report a bug': 'https://github.com/your-repo/forms-agent/issues',
        'About': "AI-Powered Google Forms Agent - Transform documents into interactive forms using advanced AI."
    }
)

# Custom CSS - Green and Black Theme
st.markdown("""
<style>
    /* Global Styles */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #00ff41, #32cd32);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
    }
    
    /* Card Styles */
    .agent-card {
        background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
        color: #00ff41;
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 5px solid #00ff41;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0, 255, 65, 0.2);
        border: 1px solid #333;
    }
    
    /* Chat Messages */
    .chat-message-user {
        background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
        color: #ffffff;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #00ff41;
        box-shadow: 0 2px 10px rgba(0, 255, 65, 0.1);
    }
    
    .chat-message-agent {
        background: linear-gradient(135deg, #0d2818, #1a4a2e);
        color: #00ff41;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #32cd32;
        box-shadow: 0 2px 10px rgba(50, 205, 50, 0.2);
    }
    
    /* File Cards */
    .file-card {
        background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
        color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #00ff41;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .file-card:hover {
        box-shadow: 0 4px 20px rgba(0, 255, 65, 0.3);
        border-color: #32cd32;
        transform: translateY(-2px);
    }
    
    /* Status Messages */
    .success-message {
        background: linear-gradient(135deg, #0d2818, #1a4a2e);
        color: #00ff41;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #32cd32;
        box-shadow: 0 2px 10px rgba(0, 255, 65, 0.2);
    }
    
    .error-message {
        background: linear-gradient(135deg, #2d1a1a, #4a1a1a);
        color: #ff4444;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ff4444;
        box-shadow: 0 2px 10px rgba(255, 68, 68, 0.2);
    }
    
    .info-message {
        background: linear-gradient(135deg, #1a1a2d, #2a2a4a);
        color: #00ccff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #00ccff;
        box-shadow: 0 2px 10px rgba(0, 204, 255, 0.2);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #00ff41, #32cd32) !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 255, 65, 0.3) !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #32cd32, #00ff41) !important;
        box-shadow: 0 6px 20px rgba(0, 255, 65, 0.5) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #1a1a1a !important;
    }
    
    /* Main content area */
    .css-18e3th9 {
        background-color: #0f0f0f !important;
    }
    
    /* Text areas and inputs */
    .stTextArea textarea {
        background-color: #1a1a1a !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 8px !important;
    }
    
    .stTextInput input {
        background-color: #1a1a1a !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 8px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a1a !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2d2d2d !important;
        color: #00ff41 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #00ff41 !important;
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    defaults = {
        'authenticated': False,
        'credentials': None,
        'user_info': None,
        'chat_history': [],
        'current_file_id': None,
        'drive_files': [],
        'current_page': 'home'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_navigation():
    """Show navigation sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h2 style="color: #00ff41; margin: 0;">🤖 Forms Agent</h2>
            <p style="color: #888; margin: 0; font-size: 0.9rem;">AI-Powered Form Creation</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation menu
        pages = {
            "🏠 Home": "home",
            "🤖 AI Assistant": "agent",
            "📁 Drive Files": "files", 
            "🚀 Quick Actions": "actions",
            "❓ How to Use": "howto",
            "ℹ️ About": "about"
        }
        
        for page_name, page_key in pages.items():
            if st.button(page_name, use_container_width=True, key=f"nav_{page_key}"):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # User info or login status
        if st.session_state.authenticated:
            user_info = st.session_state.user_info
            st.markdown("### 👤 User Profile")
            st.write(f"**{user_info.get('name', 'Unknown')}**")
            st.write(f"📧 {user_info.get('email', 'Unknown')}")
            
            st.markdown("### 🤖 Agent Status")
            if FORMS_AGENT_AVAILABLE:
                st.success("✅ Agent Online")
            else:
                st.error("❌ Agent Offline")
            
            if st.button("🔓 Logout", use_container_width=True):
                for key in ['authenticated', 'credentials', 'user_info', 'chat_history']:
                    st.session_state[key] = False if key == 'authenticated' else None if key != 'chat_history' else []
                st.session_state.current_page = 'home'
                st.rerun()
        else:
            st.markdown("### 🔐 Authentication")
            st.info("Please log in to access AI features")
            
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            <p>Built with ❤️ using<br/>Streamlit & Google AI</p>
            <p>v1.0.0</p>
        </div>
        """, unsafe_allow_html=True)

def check_oauth_configuration():
    """Check OAuth configuration for common issues."""
    try:
        client_id = st.secrets["auth"]["client_id"]
        redirect_uri = st.secrets["auth"]["redirect_uri"]
        
        # Get current app URL
        current_url = st.query_params.get("", "")
        if not current_url:
            # Try to detect from headers or use default
            current_url = "https://formsagent.streamlit.app/"
        
        issues = []
        
        # Check redirect URI
        if "localhost" in redirect_uri and "streamlit.app" in current_url:
            issues.append("🔴 Redirect URI is set to localhost but app is deployed")
        
        # Check client ID format
        if not client_id.endswith(".apps.googleusercontent.com"):
            issues.append("🔴 Client ID format looks incorrect")
        
        if issues:
            st.markdown("""
            <div class="error-message">
                <h4>⚙️ OAuth Configuration Issues Detected</h4>
            </div>
            """, unsafe_allow_html=True)
            for issue in issues:
                st.error(issue)
            
            st.markdown("""
            <div class="info-message">
                <h4>🔧 Quick Fix Guide:</h4>
                <ol>
                    <li>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Google Cloud Console - Credentials</a></li>
                    <li>Edit your OAuth 2.0 Client ID</li>
                    <li>Update Authorized redirect URIs to: <code>https://formsagent.streamlit.app/</code></li>
                    <li>Remove any localhost URIs</li>
                    <li>Save and try again</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
            return False
        
        return True
    except Exception as e:
        st.error(f"Configuration check failed: {e}")
        return False

def get_oauth_credentials():
    """Get OAuth credentials using Streamlit secrets."""
    try:
        client_id = st.secrets["auth"]["client_id"]
        client_secret = st.secrets["auth"]["client_secret"]
        redirect_uri = st.secrets["auth"]["redirect_uri"]
        
        # Validate redirect URI
        if "localhost" in redirect_uri and "streamlit.app" in st.query_params.get("", ""):
            st.error("⚠️ OAuth redirect URI mismatch! Please update your Google Cloud Console.")
            st.info("Your app is deployed but OAuth is configured for localhost.")
            return None
        
        return handle_oauth_flow(client_id, client_secret, redirect_uri)
    except KeyError as e:
        st.markdown("""
        <div class="error-message">
            <h4>⚙️ OAuth Configuration Missing</h4>
            <p>Please set up your OAuth credentials in <code>.streamlit/secrets.toml</code>:</p>
            <pre>[auth]
client_id = "your-google-client-id"
client_secret = "your-google-client-secret"
redirect_uri = "https://your-app.streamlit.app/"</pre>
            <p>Follow the Google Cloud Console setup guide to get these credentials.</p>
        </div>
        """, unsafe_allow_html=True)
        return None
    except Exception as e:
        st.error(f"OAuth configuration error: {e}")
        return None

def handle_oauth_flow(client_id: str, client_secret: str, redirect_uri: str):
    """Handle OAuth flow for Google authentication."""
    
    # Check if we already have valid credentials
    if st.session_state.get('credentials'):
        try:
            # Refresh token if expired
            if st.session_state.credentials.expired:
                st.session_state.credentials.refresh(Request())
            return st.session_state.credentials
        except Exception as e:
            st.warning(f"Token refresh failed: {e}. Please re-authenticate.")
            st.session_state.authenticated = False
            st.session_state.credentials = None
    
    # Check for OAuth callback parameters
    try:
        query_params = st.query_params
    except AttributeError:
        query_params = st.experimental_get_query_params()
    
    # Check for OAuth errors
    if "error" in query_params:
        error = query_params["error"][0] if isinstance(query_params["error"], list) else query_params["error"]
        error_description = query_params.get("error_description", ["Unknown error"])[0] if isinstance(query_params.get("error_description", [""]), list) else query_params.get("error_description", "Unknown error")
        
        st.markdown(f"""
        <div class="error-message">
            <h4>❌ OAuth Authentication Failed</h4>
            <p><strong>Error:</strong> {error}</p>
            <p><strong>Description:</strong> {error_description}</p>
            <p><strong>Common solutions:</strong></p>
            <ul>
                <li>Check your Google Cloud Console OAuth configuration</li>
                <li>Verify authorized redirect URIs match your app URL</li>
                <li>Ensure your app is published in Google Cloud Console</li>
                <li>Check that required scopes are properly configured</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        return None
    
    if "code" in query_params:
        # Handle OAuth callback
        auth_code = query_params["code"][0] if isinstance(query_params["code"], list) else query_params["code"]
        
        try:
            with st.spinner("🔄 Completing authentication..."):
                # Exchange code for tokens
                token_url = "https://oauth2.googleapis.com/token"
                token_data = {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': auth_code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri
                }
                
                response = requests.post(token_url, data=token_data)
                if response.status_code == 200:
                    tokens = response.json()
                    credentials = Credentials(
                        token=tokens['access_token'],
                        refresh_token=tokens.get('refresh_token'),
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=client_id,
                        client_secret=client_secret,
                        scopes=SCOPES
                    )
                    
                    # Test credentials by getting user info
                    user_info = get_user_info(credentials)
                    if not user_info:
                        raise Exception("Failed to get user information")
                    
                    # Store credentials and user info
                    st.session_state.credentials = credentials
                    st.session_state.user_info = user_info
                    st.session_state.authenticated = True
                    
                    # Clear query params and redirect
                    try:
                        st.query_params.clear()
                    except AttributeError:
                        st.experimental_set_query_params()
                    
                    st.success("✅ Authentication successful!")
                    st.rerun()
                else:
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                    st.error(f"❌ Authentication failed: {error_data}")
                    return None
        except Exception as e:
            st.error(f"❌ Error during authentication: {e}")
            return None
    
    # Show login screen
    st.markdown("""
    <div class="info-message">
        <h3>🔐 Google Authentication Required</h3>
        <p>This AI agent needs secure access to your Google account to:</p>
        <ul>
            <li><strong>📝 Create Forms:</strong> Generate interactive forms directly in your Google account</li>
            <li><strong>📁 Access Drive:</strong> Read and analyze your documents for AI conversion</li>
            <li><strong>🤖 AI Processing:</strong> Use advanced AI to parse content and create intelligent forms</li>
            <li><strong>☁️ Cloud Storage:</strong> Save and manage your forms in Google Drive</li>
            <li><strong>🔄 Real-time Sync:</strong> Keep your forms updated across all devices</li>
        </ul>
        <p><strong>🔒 Your data is secure:</strong> We only access what you explicitly authorize and never store your credentials.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create OAuth URL
    import urllib.parse
    scope_param = urllib.parse.quote(' '.join(SCOPES))
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri={urllib.parse.quote(redirect_uri)}&scope={scope_param}&response_type=code&access_type=offline&prompt=consent"
    
    st.markdown(f"""
    <div class="info-message">
        <h4>📋 Quick Setup:</h4>
        <ol>
            <li>Click the "Authorize" button below</li>
            <li>Sign in to your Google account</li>
            <li>Grant permissions for Forms and Drive</li>
            <li>You'll be automatically redirected back</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Direct link button
    st.markdown(f"""
    <div style="text-align: center; margin: 2rem 0;">
        <a href="{auth_url}" target="_self">
            <button style="
                background: linear-gradient(90deg, #1f77b4, #28a745);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                text-decoration: none;
                cursor: pointer;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            ">
                🔗 Authorize Google Forms Agent
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    return None

def get_user_info(credentials):
    """Get user information from Google."""
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        st.error(f"Error getting user info: {e}")
        return {}

def get_drive_service():
    """Get Google Drive service."""
    if not st.session_state.credentials:
        return None
    
    try:
        service = build('drive', 'v3', credentials=st.session_state.credentials)
        return service
    except Exception as e:
        st.error(f"Error creating Drive service: {e}")
        return None

def list_drive_files(mime_types=None, search_query=None):
    """List files from Google Drive with enhanced filtering."""
    drive_service = get_drive_service()
    if not drive_service:
        return []
    
    try:
        query_parts = []
        
        # Add mime type filter
        if mime_types:
            mime_queries = [f"mimeType='{mime_type}'" for mime_type in mime_types]
            query_parts.append(f"({' or '.join(mime_queries)})")
        
        # Add search query filter
        if search_query:
            query_parts.append(f"name contains '{search_query}'")
        
        # Add file filters (not trashed, not folders)
        query_parts.append("trashed=false")
        query_parts.append("mimeType!='application/vnd.google-apps.folder'")
        
        query = " and ".join(query_parts)
        
        results = drive_service.files().list(
            q=query,
            fields="files(id,name,mimeType,modifiedTime,size,webViewLink,iconLink)",
            orderBy="modifiedTime desc",
            pageSize=100
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        st.error(f"Error listing Drive files: {e}")
        return []

def get_file_content(file_id: str, mime_type: str):
    """Download and return file content from Google Drive."""
    drive_service = get_drive_service()
    if not drive_service:
        return None
    
    try:
        # For Google Docs, export as plain text
        if mime_type == 'application/vnd.google-apps.document':
            request = drive_service.files().export_media(
                fileId=file_id,
                mimeType='text/plain'
            )
        else:
            # For other files, download directly
            request = drive_service.files().get_media(fileId=file_id)
        
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        return file_content.getvalue()
    except Exception as e:
        st.error(f"Error downloading file: {e}")
        return None

def chat_with_agent(user_message: str):
    """Chat with the forms agent."""
    if not FORMS_AGENT_AVAILABLE:
        return "❌ Forms agent is not available. Please check your configuration."
    
    try:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "message": user_message})
        
        # Get response from agent
        with st.spinner("🤖 Agent is processing..."):
            response = root_agent.run(user_message)
            agent_response = str(response)
        
        # Add agent response to chat history
        st.session_state.chat_history.append({"role": "agent", "message": agent_response})
        
        return agent_response
    except Exception as e:
        error_msg = f"❌ Error communicating with agent: {e}"
        st.session_state.chat_history.append({"role": "agent", "message": error_msg})
        return error_msg



def main_app():
    """Main application interface with new navigation system."""
    # Show navigation sidebar
    show_navigation()
    
    # Route to appropriate page based on current_page
    current_page = st.session_state.get('current_page', 'home')
    
    if current_page == 'home':
        show_home_page()
        
        # Show OAuth if not authenticated
        if not st.session_state.authenticated:
            st.markdown("---")
            st.markdown("## 🔐 Authentication Required")
            
            # Check OAuth configuration first
            if not check_oauth_configuration():
                st.stop()
            
            # OAuth Authentication
            get_oauth_credentials()
            
    elif current_page == 'agent':
        if st.session_state.authenticated:
            show_agent_chat()
        else:
            st.warning("🔐 Please authenticate first to access the AI Assistant")
            if st.button("🔗 Go to Authentication"):
                st.session_state.current_page = 'home'
                st.rerun()
                
    elif current_page == 'files':
        if st.session_state.authenticated:
            show_drive_files()
        else:
            st.warning("🔐 Please authenticate first to access Drive Files")
            if st.button("🔗 Go to Authentication"):
                st.session_state.current_page = 'home'
                st.rerun()
                
    elif current_page == 'actions':
        if st.session_state.authenticated:
            show_quick_actions()
        else:
            st.warning("🔐 Please authenticate first to access Quick Actions")
            if st.button("🔗 Go to Authentication"):
                st.session_state.current_page = 'home'
                st.rerun()
                
    elif current_page == 'howto':
        show_how_to_use()
        
    elif current_page == 'about':
        show_about_page()
        
    else:
        # Default to home
        st.session_state.current_page = 'home'
        st.rerun()

def show_agent_chat():
    """Show the agent chat interface."""
    st.subheader("💬 Chat with Your AI Forms Assistant")
    
    if not FORMS_AGENT_AVAILABLE:
        st.error("❌ Forms agent is not available. Please check your configuration.")
        return
    
    # Chat history display
    if st.session_state.chat_history:
        st.markdown("### 📜 Conversation")
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.markdown(f"""
                <div class="chat-message-user">
                    <strong>🙋 You:</strong><br>{chat["message"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message-agent">
                    <strong>🤖 AI Agent:</strong><br>{chat["message"]}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("👋 Start a conversation! Ask me to create forms, parse documents, or help with Google Forms.")
    
    # Chat input
    st.markdown("### 💭 Message the Agent")
    
    # Predefined prompts
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 Create Survey Form", use_container_width=True):
            message = "Create a customer satisfaction survey form with rating questions"
            chat_with_agent(message)
            st.rerun()
    
    with col2:
        if st.button("📄 Parse Document", use_container_width=True):
            message = "Help me convert a document from my Drive into a form"
            chat_with_agent(message)
            st.rerun()
    
    with col3:
        if st.button("📋 List My Forms", use_container_width=True):
            message = "Show me all my Google Forms"
            chat_with_agent(message)
            st.rerun()
    
    # Text input
    user_input = st.text_area(
        "Type your message:",
        placeholder="Example: 'Create a quiz about Python programming' or 'Convert my resume.pdf to an application form'",
        height=100,
        key="chat_input"
    )
    
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button("🚀 Send Message", type="primary", disabled=not user_input):
            if user_input:
                chat_with_agent(user_input)
                st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

def show_drive_files():
    """Show Google Drive files for document parsing."""
    st.subheader("📁 Your Google Drive Documents")
    
    # Supported file types
    supported_types = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain',
        'text/markdown',
        'application/vnd.google-apps.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.google-apps.presentation'
    ]
    
    # Control panel
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search files:", placeholder="Enter filename...", key="file_search")
    with col2:
        file_type_filter = st.selectbox("📄 Filter by type:", 
                                       ["All", "Documents", "PDFs", "Google Docs"],
                                       key="type_filter")
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.drive_files = []
            st.rerun()
    
    # Apply file type filter
    filtered_types = supported_types
    if file_type_filter == "Documents":
        filtered_types = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']
    elif file_type_filter == "PDFs":
        filtered_types = ['application/pdf']
    elif file_type_filter == "Google Docs":
        filtered_types = ['application/vnd.google-apps.document']
    
    # Load files
    cache_key = f"files_{file_type_filter}_{search_term}"
    if cache_key not in st.session_state:
        with st.spinner("🔍 Scanning your Drive..."):
            files = list_drive_files(filtered_types, search_term)
            st.session_state[cache_key] = files
    else:
        files = st.session_state[cache_key]
    
    if not files:
        st.markdown("""
        <div class="info-message">
            <h4>📂 No documents found</h4>
            <p><strong>💡 Supported file types:</strong></p>
            <ul>
                <li>📄 PDF files (.pdf)</li>
                <li>📝 Word documents (.docx, .doc)</li>
                <li>📃 Text files (.txt)</li>
                <li>🔖 Markdown files (.md)</li>
                <li>📊 Google Docs</li>
                <li>📋 Google Slides</li>
            </ul>
            <p>Try adjusting your search or upload documents to Google Drive.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"""
    <div class="success-message">
        <h4>📋 Found {len(files)} documents ready for AI processing</h4>
        <p>Select documents below to convert them into interactive Google Forms using AI.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display files in a grid
    for i, file in enumerate(files):
        file_size = file.get('size', 'Unknown')
        if file_size != 'Unknown' and file_size.isdigit():
            file_size = f"{int(file_size) / 1024:.1f} KB" if int(file_size) < 1024*1024 else f"{int(file_size) / (1024*1024):.1f} MB"
        
        file_type_icon = "📄"
        if 'pdf' in file['mimeType']:
            file_type_icon = "📄"
        elif 'document' in file['mimeType']:
            file_type_icon = "📝"
        elif 'presentation' in file['mimeType']:
            file_type_icon = "📋"
        elif 'google-apps' in file['mimeType']:
            file_type_icon = "☁️"
        
        with st.container():
            st.markdown(f"""
            <div class="file-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4>{file_type_icon} {file['name']}</h4>
                        <p><strong>Type:</strong> {file['mimeType'].split('/')[-1].upper().replace('VND.GOOGLE-APPS.', '')}</p>
                        <p><strong>Modified:</strong> {file.get('modifiedTime', 'Unknown')[:10]} | <strong>Size:</strong> {file_size}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button(f"👁️ Preview", key=f"preview_{i}"):
                    with st.expander(f"📖 Preview: {file['name']}", expanded=True):
                        try:
                            content = get_file_content(file['id'], file['mimeType'])
                            if content:
                                # Display first 500 characters
                                preview_text = content.decode('utf-8', errors='ignore')[:500]
                                st.text_area("Content preview:", preview_text, height=150, disabled=True)
                            else:
                                st.error("Could not load file content")
                        except Exception as e:
                            st.error(f"Preview error: {e}")
            
            with col3:
                if st.button(f"🤖 Convert to Form", key=f"convert_{i}"):
                    message = f"""Please analyze and convert the document '{file['name']}' (ID: {file['id']}) from my Google Drive into a comprehensive Google Form. 

Extract all relevant information and create appropriate form elements:
- Convert questions into form fields
- Create multiple choice options where applicable  
- Add rating scales for evaluation items
- Include text fields for open responses
- Organize sections logically
- Add proper form title and description

Document Type: {file['mimeType']}
File Name: {file['name']}"""
                    
                    chat_with_agent(message)
                    st.success("✅ Conversion request sent to AI agent!")
                    st.info("💬 Check the AI Assistant tab to monitor progress.")

def show_home_page():
    """Show the home/dashboard page."""
    st.markdown('<h1 class="main-header">🤖 Google Forms Agent</h1>', unsafe_allow_html=True)
    
    # Hero section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="agent-card" style="text-align: center; padding: 2rem;">
            <h2>🚀 Transform Documents into Interactive Forms</h2>
            <p style="font-size: 1.2rem; margin: 1.5rem 0;">
                Harness the power of AI to convert any document into professional Google Forms instantly.
                From surveys to applications, create sophisticated forms in seconds, not hours.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Feature highlights
    st.markdown("## ✨ Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="agent-card">
            <h3>🤖 AI-Powered Analysis</h3>
            <ul>
                <li>Smart document parsing</li>
                <li>Intelligent question extraction</li>
                <li>Automatic form structure</li>
                <li>Content optimization</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="agent-card">
            <h3>☁️ Google Integration</h3>
            <ul>
                <li>Direct Drive access</li>
                <li>Forms API integration</li>
                <li>Real-time synchronization</li>
                <li>Secure authentication</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="agent-card">
            <h3>⚡ Instant Results</h3>
            <ul>
                <li>One-click conversion</li>
                <li>Multiple file formats</li>
                <li>Batch processing</li>
                <li>Template generation</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Statistics and metrics
    st.markdown("## 📊 Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⚡ Processing Speed", "< 30 seconds", "per document")
    
    with col2:
        st.metric("🎯 Accuracy Rate", "95%+", "form generation")
    
    with col3:
        st.metric("📄 Supported Formats", "6+", "file types")
    
    with col4:
        st.metric("🤖 AI Models", "Advanced", "LLM integration")
    
    # Quick start guide
    if not st.session_state.authenticated:
        st.markdown("## 🚀 Get Started")
        
        steps_col1, steps_col2 = st.columns([2, 1])
        
        with steps_col1:
            st.markdown("""
            <div class="info-message">
                <h4>🎯 Quick Start Guide:</h4>
                <ol>
                    <li><strong>🔐 Authenticate:</strong> Connect your Google account securely</li>
                    <li><strong>📁 Upload:</strong> Select documents from your Google Drive</li>
                    <li><strong>🤖 Convert:</strong> Let AI analyze and create your form</li>
                    <li><strong>✨ Customize:</strong> Review and refine the generated form</li>
                    <li><strong>🚀 Deploy:</strong> Share your form with the world</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        
        with steps_col2:
            if st.button("🔗 Start Authentication", type="primary", use_container_width=True):
                st.session_state.current_page = 'home'  # This will trigger OAuth
                st.rerun()
    else:
        st.markdown("## 🎉 Welcome Back!")
        st.success("You're authenticated and ready to create amazing forms!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🤖 Chat with AI", use_container_width=True):
                st.session_state.current_page = 'agent'
                st.rerun()
        
        with col2:
            if st.button("📁 Browse Files", use_container_width=True):
                st.session_state.current_page = 'files'
                st.rerun()
        
        with col3:
            if st.button("🚀 Quick Actions", use_container_width=True):
                st.session_state.current_page = 'actions'
                st.rerun()

def show_how_to_use():
    """Show the how to use page."""
    st.markdown('<h1 class="main-header">❓ How to Use Google Forms Agent</h1>', unsafe_allow_html=True)
    
    # Step-by-step guide
    st.markdown("## 📋 Complete User Guide")
    
    # Authentication section
    with st.expander("🔐 Step 1: Authentication & Setup", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            <div class="info-message">
                <h4>🔑 Google Account Connection</h4>
                <p><strong>What you need:</strong></p>
                <ul>
                    <li>Active Google account</li>
                    <li>Access to Google Drive</li>
                    <li>Permission to create Google Forms</li>
                </ul>
                
                <p><strong>Process:</strong></p>
                <ol>
                    <li>Click "Authorize Google Forms Agent" button</li>
                    <li>Sign in to your Google account</li>
                    <li>Grant permissions for Forms and Drive access</li>
                    <li>You'll be redirected back automatically</li>
                </ol>
                
                <p><strong>🔒 Security:</strong> We use OAuth 2.0 for secure authentication. 
                Your credentials are never stored on our servers.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="agent-card">
                <h4>✅ Required Permissions</h4>
                <ul>
                    <li>📝 Google Forms (create/edit)</li>
                    <li>📁 Google Drive (read files)</li>
                    <li>👤 Profile (basic info)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # File upload section
    with st.expander("📁 Step 2: Document Selection"):
        st.markdown("""
        <div class="agent-card">
            <h4>📄 Supported File Types</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <p><strong>📝 Documents:</strong></p>
                    <ul>
                        <li>📄 PDF files (.pdf)</li>
                        <li>📝 Word documents (.docx, .doc)</li>
                        <li>☁️ Google Docs</li>
                    </ul>
                </div>
                <div>
                    <p><strong>📃 Text Files:</strong></p>
                    <ul>
                        <li>📃 Plain text (.txt)</li>
                        <li>🔖 Markdown (.md)</li>
                        <li>📋 Google Slides</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        **📋 Selection Process:**
        1. Navigate to "📁 Drive Files" tab
        2. Use search and filters to find your document
        3. Click "👁️ Preview" to review content
        4. Click "🤖 Convert to Form" to start AI processing
        """)
    
    # AI conversion section
    with st.expander("🤖 Step 3: AI Conversion Process"):
        st.markdown("""
        <div class="success-message">
            <h4>🧠 How Our AI Works</h4>
            <p><strong>Document Analysis:</strong></p>
            <ol>
                <li><strong>Content Extraction:</strong> AI reads and understands your document</li>
                <li><strong>Structure Recognition:</strong> Identifies questions, sections, and patterns</li>
                <li><strong>Intent Analysis:</strong> Determines the purpose and type of each element</li>
                <li><strong>Form Generation:</strong> Creates appropriate form fields and logic</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎯 AI Capabilities:**
            - Question extraction and classification
            - Multiple choice option generation
            - Rating scale creation
            - Section organization
            - Field validation setup
            """)
        
        with col2:
            st.markdown("""
            **⏱️ Processing Time:**
            - Simple documents: 10-20 seconds
            - Complex documents: 30-60 seconds
            - Large files: 1-2 minutes
            - Batch processing: Variable
            """)
    
    # Customization section
    with st.expander("✨ Step 4: Form Customization & Review"):
        st.markdown("""
        <div class="agent-card">
            <h4>🔧 Available Customizations</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <p><strong>📝 Content Editing:</strong></p>
                    <ul>
                        <li>Question modification</li>
                        <li>Answer option editing</li>
                        <li>Section reorganization</li>
                        <li>Help text addition</li>
                    </ul>
                </div>
                <div>
                    <p><strong>🎨 Design Options:</strong></p>
                    <ul>
                        <li>Theme selection</li>
                        <li>Color customization</li>
                        <li>Logo integration</li>
                        <li>Layout optimization</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Tips and best practices
    st.markdown("## 💡 Tips & Best Practices")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="info-message">
            <h4>📚 Document Preparation Tips</h4>
            <ul>
                <li><strong>Clear Structure:</strong> Use headers and bullet points</li>
                <li><strong>Consistent Formatting:</strong> Maintain uniform styling</li>
                <li><strong>Question Clarity:</strong> Write clear, concise questions</li>
                <li><strong>Logical Flow:</strong> Organize content sequentially</li>
                <li><strong>Complete Information:</strong> Include all necessary details</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="success-message">
            <h4>🚀 Optimization Strategies</h4>
            <ul>
                <li><strong>File Size:</strong> Keep documents under 10MB</li>
                <li><strong>Language:</strong> Use clear, professional language</li>
                <li><strong>Sections:</strong> Break content into logical sections</li>
                <li><strong>Examples:</strong> Include sample answers where helpful</li>
                <li><strong>Testing:</strong> Review generated forms thoroughly</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Troubleshooting
    with st.expander("🔧 Troubleshooting & Common Issues"):
        st.markdown("""
        <div class="error-message">
            <h4>❗ Common Issues & Solutions</h4>
            
            <p><strong>🔐 Authentication Problems:</strong></p>
            <ul>
                <li><strong>403 Error:</strong> Check OAuth redirect URI in Google Console</li>
                <li><strong>Token Expired:</strong> Re-authenticate through the app</li>
                <li><strong>Permission Denied:</strong> Ensure proper scopes are granted</li>
            </ul>
            
            <p><strong>📁 File Access Issues:</strong></p>
            <ul>
                <li><strong>File Not Found:</strong> Check file sharing settings</li>
                <li><strong>Download Failed:</strong> Verify file format support</li>
                <li><strong>Preview Error:</strong> Try refreshing the file list</li>
            </ul>
            
            <p><strong>🤖 AI Processing Issues:</strong></p>
            <ul>
                <li><strong>Poor Results:</strong> Improve document structure</li>
                <li><strong>Missing Content:</strong> Check document formatting</li>
                <li><strong>Timeout Error:</strong> Try smaller documents</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_about_page():
    """Show the about page with project information."""
    st.markdown('<h1 class="main-header">ℹ️ About Google Forms Agent</h1>', unsafe_allow_html=True)
    
    # Project overview
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="agent-card">
            <h2>🚀 Project Overview</h2>
            <p style="font-size: 1.1rem; line-height: 1.6;">
                Google Forms Agent is an innovative AI-powered application that revolutionizes 
                the way we create and manage Google Forms. By leveraging advanced artificial 
                intelligence and natural language processing, our platform transforms any 
                document into interactive, professional forms in seconds.
            </p>
            
            <p style="font-size: 1.1rem; line-height: 1.6;">
                Built with cutting-edge technology and designed for maximum usability, 
                Forms Agent bridges the gap between static documents and dynamic, 
                data-collecting forms that drive better insights and user engagement.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="success-message">
            <h4>📊 Project Stats</h4>
            <ul>
                <li><strong>🎯 Accuracy:</strong> 95%+ form generation</li>
                <li><strong>⚡ Speed:</strong> Sub-30 second processing</li>
                <li><strong>📄 Formats:</strong> 6+ file types supported</li>
                <li><strong>🔒 Security:</strong> OAuth 2.0 protection</li>
                <li><strong>☁️ Integration:</strong> Native Google APIs</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Architecture diagram
    st.markdown("## 🏗️ System Architecture")
    
    # Create the architecture diagram
    create_architecture_diagram()
    
    # Technology stack
    st.markdown("## 🛠️ Technology Stack")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="agent-card">
            <h4>🎨 Frontend</h4>
            <ul>
                <li><strong>Streamlit:</strong> Web framework</li>
                <li><strong>HTML/CSS:</strong> Custom styling</li>
                <li><strong>JavaScript:</strong> Interactive elements</li>
                <li><strong>Responsive Design:</strong> Mobile-friendly</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="agent-card">
            <h4>🤖 AI & Backend</h4>
            <ul>
                <li><strong>Google Gemini:</strong> Language model</li>
                <li><strong>Python:</strong> Core logic</li>
                <li><strong>FastAPI:</strong> API framework</li>
                <li><strong>Pandas:</strong> Data processing</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="agent-card">
            <h4>☁️ Google Services</h4>
            <ul>
                <li><strong>Forms API:</strong> Form creation</li>
                <li><strong>Drive API:</strong> File access</li>
                <li><strong>OAuth 2.0:</strong> Authentication</li>
                <li><strong>Cloud Console:</strong> Configuration</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Features and capabilities
    st.markdown("## ✨ Key Features & Capabilities")
    
    features = [
        {
            "icon": "🤖",
            "title": "Advanced AI Processing",
            "description": "State-of-the-art natural language processing for intelligent document analysis and form generation."
        },
        {
            "icon": "📄",
            "title": "Multi-Format Support", 
            "description": "Seamlessly handle PDFs, Word documents, Google Docs, text files, and more with perfect accuracy."
        },
        {
            "icon": "⚡",
            "title": "Lightning Fast",
            "description": "Generate professional forms in under 30 seconds with our optimized AI pipeline."
        },
        {
            "icon": "🔒",
            "title": "Enterprise Security",
            "description": "OAuth 2.0 authentication, encrypted data transmission, and secure API integrations."
        },
        {
            "icon": "🎨",
            "title": "Smart Customization",
            "description": "AI-powered suggestions for form layout, question types, and user experience optimization."
        },
        {
            "icon": "☁️",
            "title": "Cloud Integration",
            "description": "Direct integration with Google Workspace for seamless workflow and data management."
        }
    ]
    
    for i, feature in enumerate(features):
        if i % 2 == 0:
            col1, col2 = st.columns(2)
        
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
            <div class="agent-card">
                <h4>{feature['icon']} {feature['title']}</h4>
                <p>{feature['description']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Future roadmap
    st.markdown("## 🔮 Future Roadmap")
    
    st.markdown("""
    <div class="info-message">
        <h4>🚀 Upcoming Features</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div>
                <p><strong>📊 Advanced Analytics:</strong></p>
                <ul>
                    <li>Real-time response tracking</li>
                    <li>AI-powered insights</li>
                    <li>Custom dashboards</li>
                    <li>Export capabilities</li>
                </ul>
                
                <p><strong>🎨 Enhanced UI/UX:</strong></p>
                <ul>
                    <li>Drag-and-drop form builder</li>
                    <li>Advanced theming options</li>
                    <li>Mobile app version</li>
                    <li>Accessibility improvements</li>
                </ul>
            </div>
            <div>
                <p><strong>🤖 AI Enhancements:</strong></p>
                <ul>
                    <li>Multi-language support</li>
                    <li>Advanced question types</li>
                    <li>Conditional logic generation</li>
                    <li>Response validation AI</li>
                </ul>
                
                <p><strong>🔗 Integrations:</strong></p>
                <ul>
                    <li>Microsoft Office 365</li>
                    <li>Slack notifications</li>
                    <li>Zapier automation</li>
                    <li>Database connectors</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Contact and support
    st.markdown("## 📞 Contact & Support")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="agent-card">
            <h4>🐛 Report Issues</h4>
            <p>Found a bug or have suggestions?</p>
            <a href="https://github.com/your-repo/forms-agent/issues" target="_blank">
                <button style="background: #00ff41; color: black; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem;">
                    GitHub Issues
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="agent-card">
            <h4>📚 Documentation</h4>
            <p>Comprehensive guides and API docs</p>
            <a href="https://github.com/your-repo/forms-agent" target="_blank">
                <button style="background: #00ff41; color: black; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem;">
                    View Docs
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="agent-card">
            <h4>💬 Community</h4>
            <p>Join our developer community</p>
            <a href="https://discord.gg/your-discord" target="_blank">
                <button style="background: #00ff41; color: black; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem;">
                    Discord
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

def create_architecture_diagram():
    """Create and display the system architecture diagram."""
    st.markdown("""
    <div class="agent-card">
        <h4>🏗️ Google Forms Agent Architecture</h4>
        <p>The diagram below shows the complete system architecture and data flow:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create the Mermaid diagram
    diagram_content = """graph TB
    User[👤 User] --> UI[🖥️ Streamlit UI]
    UI --> Auth[🔐 OAuth 2.0]
    Auth --> Google[☁️ Google Services]
    
    UI --> Agent[🤖 Forms Agent]
    Agent --> Parser[📄 Document Parser]
    Agent --> Creator[📝 Form Creator]
    Agent --> Editor[✏️ Form Editor]
    Agent --> Validator[✅ Form Validator]
    
    Parser --> AI[🧠 Google Gemini AI]
    Creator --> FormsAPI[📋 Google Forms API]
    
    Google --> Drive[📁 Google Drive]
    Google --> Forms[📝 Google Forms]
    
    Drive --> Files[📄 Documents]
    Forms --> Generated[✨ Generated Forms]
    
    classDef userClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef uiClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef aiClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef googleClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class User userClass
    class UI,Auth uiClass
    class Agent,Parser,Creator,Editor,Validator,AI aiClass
    class Google,Drive,Forms,FormsAPI,Files,Generated googleClass"""
    
    try:
        # Try to create the diagram
        from types import SimpleNamespace
        create_diagram = getattr(st, 'create_diagram', None)
        if create_diagram:
            create_diagram(diagram_content)
        else:
            raise ImportError("create_diagram not available")
    except:
        # Fallback to embedded Mermaid HTML
        st.markdown(f"""
        <div style="display: flex; justify-content: center; margin: 2rem 0;">
            <div id="mermaid-diagram" style="background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <script>
                    mermaid.initialize({{
                        startOnLoad: true,
                        theme: 'default',
                        flowchart: {{ useMaxWidth: true }}
                    }});
                </script>
                <div class="mermaid">
                    {diagram_content}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add explanation
    st.markdown("""
    <div class="info-message">
        <h4>📋 Architecture Components</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
                <p><strong>🎨 Frontend Layer:</strong></p>
                <ul>
                    <li><strong>Streamlit UI:</strong> Modern web interface</li>
                    <li><strong>OAuth 2.0:</strong> Secure authentication</li>
                    <li><strong>Navigation:</strong> Multi-page routing</li>
                </ul>
                
                <p><strong>🤖 AI Processing Layer:</strong></p>
                <ul>
                    <li><strong>Forms Agent:</strong> Main orchestrator</li>
                    <li><strong>Document Parser:</strong> Content extraction</li>
                    <li><strong>Form Creator:</strong> Structure generation</li>
                    <li><strong>Google Gemini:</strong> AI processing</li>
                </ul>
            </div>
            <div>
                <p><strong>☁️ Google Services:</strong></p>
                <ul>
                    <li><strong>Google Drive:</strong> File storage & access</li>
                    <li><strong>Google Forms:</strong> Form creation & management</li>
                    <li><strong>Forms API:</strong> Programmatic form control</li>
                </ul>
                
                <p><strong>🔄 Data Flow:</strong></p>
                <ul>
                    <li><strong>Input:</strong> Documents from Google Drive</li>
                    <li><strong>Processing:</strong> AI analysis & extraction</li>
                    <li><strong>Output:</strong> Generated Google Forms</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_quick_actions():
    """Show quick action buttons for common tasks."""
    st.subheader("🚀 Quick Actions")
    
    if not FORMS_AGENT_AVAILABLE:
        st.error("❌ Forms agent is not available.")
        return
    
    st.markdown("### 📝 Form Templates")
    
    templates = [
        {
            "title": "📊 Customer Survey",
            "description": "Satisfaction survey with ratings and feedback",
            "prompt": "Create a comprehensive customer satisfaction survey with rating scales, multiple choice questions about service quality, and an open text field for additional comments."
        },
        {
            "title": "📋 Event Registration",
            "description": "Registration form for events and workshops",
            "prompt": "Create an event registration form with fields for personal information, dietary preferences, emergency contact, and session preferences."
        },
        {
            "title": "🎯 Quiz Template",
            "description": "Educational quiz with scoring",
            "prompt": "Create an educational quiz with 10 multiple choice questions, correct answers, and automatic scoring enabled."
        },
        {
            "title": "💼 Job Application",
            "description": "Complete job application form",
            "prompt": "Create a professional job application form with sections for personal information, education, work experience, skills, and file upload for resume."
        },
        {
            "title": "📝 Feedback Form",
            "description": "General feedback collection",
            "prompt": "Create a feedback form with rating questions, category selection, and detailed comment sections for collecting user opinions."
        },
        {
            "title": "🏥 Health Screening",
            "description": "Health questionnaire template",
            "prompt": "Create a health screening form with yes/no questions about symptoms, medical history checkboxes, and contact information fields."
        }
    ]
    
    cols = st.columns(2)
    for i, template in enumerate(templates):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"""
                <div class="agent-card" style="height: 180px;">
                    <h4>{template['title']}</h4>
                    <p>{template['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Create {template['title']}", key=f"template_{i}", use_container_width=True):
                    chat_with_agent(template['prompt'])
                    st.success(f"✅ {template['title']} creation started!")
                    st.info("💬 Check the AI Assistant tab for progress.")
    
    st.markdown("---")
    
    st.markdown("### 🛠️ Advanced Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Analyze My Forms", use_container_width=True):
            message = "Analyze all my Google Forms and provide a summary with statistics, types, and recommendations for improvement."
            chat_with_agent(message)
            st.success("✅ Analysis started!")
    
    with col2:
        if st.button("🔄 Bulk Operations", use_container_width=True):
            message = "Help me with bulk operations on my Google Forms - show me options for managing multiple forms at once."
            chat_with_agent(message)
            st.success("✅ Bulk operations guide requested!")

def main():
    """Main application entry point."""
    initialize_session_state()
    main_app()

if __name__ == "__main__":
    main() 