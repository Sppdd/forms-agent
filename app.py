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
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simple, clean CSS - Google Forms inspired
st.markdown("""
<style>
    /* Clean, minimal styling */
    .main-header {
        font-size: 2rem;
        font-weight: 400;
        color: #1f1f1f;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .chat-message-user {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #4285f4;
    }
    
    .chat-message-agent {
        background: #e8f0fe;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #34a853;
    }
    
    .file-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        transition: box-shadow 0.2s;
    }
    
    .file-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        background: #4285f4;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    
    .stButton > button:hover {
        background: #3367d6;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Remove default streamlit styling */
    .css-18e3th9 {
        padding-top: 1rem;
    }
    
    /* Input styling */
    .stTextArea textarea, .stTextInput input {
        border: 1px solid #dadce0;
        border-radius: 4px;
        background-color: white;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #4285f4;
        box-shadow: 0 0 0 1px #4285f4;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px;
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
        st.markdown("### 📝 Forms Agent")
        st.markdown("---")
        
        # Navigation menu
        pages = {
            "🏠 Home": "home",
            "💬 Chat": "agent",
            "📁 Files": "files"
        }
        
        for page_name, page_key in pages.items():
            if st.button(page_name, use_container_width=True, key=f"nav_{page_key}"):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # User info
        if st.session_state.authenticated:
            user_info = st.session_state.user_info
            st.markdown("**Signed in as:**")
            st.write(f"{user_info.get('name', 'Unknown')}")
            st.write(f"{user_info.get('email', 'Unknown')}")
            
            if st.button("Sign out", use_container_width=True):
                for key in ['authenticated', 'credentials', 'user_info', 'chat_history']:
                    st.session_state[key] = False if key == 'authenticated' else None if key != 'chat_history' else []
                st.session_state.current_page = 'home'
                st.rerun()
        else:
            st.info("Sign in to get started")

def get_oauth_credentials():
    """Get OAuth credentials using Streamlit secrets."""
    try:
        client_id = st.secrets["auth"]["client_id"]
        client_secret = st.secrets["auth"]["client_secret"]
        redirect_uri = st.secrets["auth"]["redirect_uri"]
        
        return handle_oauth_flow(client_id, client_secret, redirect_uri)
    except KeyError as e:
        st.error("OAuth configuration missing. Please set up credentials in .streamlit/secrets.toml")
        return None
    except Exception as e:
        st.error(f"OAuth configuration error: {e}")
        return None

def handle_oauth_flow(client_id: str, client_secret: str, redirect_uri: str):
    """Handle OAuth flow for Google authentication."""
    
    # Check if we already have valid credentials
    if st.session_state.get('credentials'):
        try:
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
        error = query_params.get("error", ["Unknown"])[0]
        error_description = query_params.get("error_description", ["No description provided."])[0]
        st.error(f"Authentication Failed: {error}")
        st.error(f"Details: {error_description}")

        if error == "redirect_uri_mismatch":
            st.error("This is a common error. It means the `redirect_uri` in your app's secrets doesn't match the one in your Google Cloud project.")
            st.info(f"Your app is configured with this redirect URI: `{redirect_uri}`")
            st.info("Please go to your [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials) and ensure that this URI is listed under 'Authorized redirect URIs' for your OAuth 2.0 Client ID.")
        
        return None
    
    if "code" in query_params:
        # Handle OAuth callback
        auth_code = query_params["code"][0] if isinstance(query_params["code"], list) else query_params["code"]
        
        try:
            with st.spinner("Completing authentication..."):
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
                    
                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("Authentication failed")
                    return None
        except Exception as e:
            st.error(f"Error during authentication: {e}")
            return None
    
    # Show login
    st.markdown("""
    <div class="card">
        <h3>Sign in to Google</h3>
        <p>Connect your Google account to create forms and access your Drive files.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create OAuth URL
    import urllib.parse
    scope_param = urllib.parse.quote(' '.join(SCOPES))
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri={urllib.parse.quote(redirect_uri)}&scope={scope_param}&response_type=code&access_type=offline&prompt=consent"
    
    # Direct link button
    st.markdown(f"""
    <div style="text-align: center; margin: 1rem 0;">
        <a href="{auth_url}" target="_self">
            <button style="
                background: #4285f4;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                text-decoration: none;
            ">
                Sign in with Google
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
    """List files from Google Drive."""
    drive_service = get_drive_service()
    if not drive_service:
        return []
    
    try:
        query_parts = []
        
        if mime_types:
            mime_queries = [f"mimeType='{mime_type}'" for mime_type in mime_types]
            query_parts.append(f"({' or '.join(mime_queries)})")
        
        if search_query:
            query_parts.append(f"name contains '{search_query}'")
        
        query_parts.append("trashed=false")
        query_parts.append("mimeType!='application/vnd.google-apps.folder'")
        
        query = " and ".join(query_parts)
        
        results = drive_service.files().list(
            q=query,
            fields="files(id,name,mimeType,modifiedTime,size,webViewLink)",
            orderBy="modifiedTime desc",
            pageSize=50
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
        if mime_type == 'application/vnd.google-apps.document':
            request = drive_service.files().export_media(
                fileId=file_id,
                mimeType='text/plain'
            )
        else:
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
        return "Forms agent is not available. Please check your configuration."
    
    try:
        st.session_state.chat_history.append({"role": "user", "message": user_message})
        
        with st.spinner("Processing..."):
            response = root_agent.run(user_message)
            agent_response = str(response)
        
        st.session_state.chat_history.append({"role": "agent", "message": agent_response})
        
        return agent_response
    except Exception as e:
        error_msg = f"Error communicating with agent: {e}"
        st.session_state.chat_history.append({"role": "agent", "message": error_msg})
        return error_msg

def main_app():
    """Main application interface."""
    show_navigation()
    
    current_page = st.session_state.get('current_page', 'home')
    
    if current_page == 'home':
        show_home_page()
        
        if not st.session_state.authenticated:
            st.markdown("---")
            get_oauth_credentials()
            
    elif current_page == 'agent':
        if st.session_state.authenticated:
            show_agent_chat()
        else:
            st.warning("Please sign in first to access the chat")
            if st.button("Go to sign in"):
                st.session_state.current_page = 'home'
                st.rerun()
                
    elif current_page == 'files':
        if st.session_state.authenticated:
            show_drive_files()
        else:
            st.warning("Please sign in first to access your files")
            if st.button("Go to sign in"):
                st.session_state.current_page = 'home'
                st.rerun()
    else:
        st.session_state.current_page = 'home'
        st.rerun()

def show_agent_chat():
    """Show the agent chat interface."""
    st.markdown('<h1 class="main-header">Chat with AI Assistant</h1>', unsafe_allow_html=True)
    
    if not FORMS_AGENT_AVAILABLE:
        st.error("Forms agent is not available.")
        return
    
    # Chat history
    if st.session_state.chat_history:
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.markdown(f"""
                <div class="chat-message-user">
                    <strong>You:</strong> {chat["message"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message-agent">
                    <strong>Assistant:</strong> {chat["message"]}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Ask me to create forms, parse documents, or help with Google Forms.")
    
    # Chat input
    user_input = st.text_area(
        "Message:",
        placeholder="Type your message here, or try an example below.",
        height=100,
        key="chat_input"
    )
    
    if st.button("Send", type="primary", disabled=not user_input):
        if user_input:
            chat_with_agent(user_input)
            st.rerun()

    st.markdown("---")
    st.markdown("##### Or try an example:")
    
    templates = [
        {
            "title": "Customer Survey",
            "prompt": "Create a customer satisfaction survey with rating questions and feedback"
        },
        {
            "title": "Event Registration",
            "prompt": "Create an event registration form with personal info and preferences"
        },
        {
            "title": "Quiz",
            "prompt": "Create a quiz with multiple choice questions and scoring"
        },
        {
            "title": "Job Application",
            "prompt": "Create a job application form with experience and skills sections"
        }
    ]
    
    col1, col2 = st.columns(2)
    for i, template in enumerate(templates):
        with col1 if i % 2 == 0 else col2:
            if st.button(template["title"], use_container_width=True, key=f"template_{i}"):
                chat_with_agent(template["prompt"])
                st.rerun()

def show_drive_files():
    """Show Google Drive files."""
    st.markdown('<h1 class="main-header">Your Drive Files</h1>', unsafe_allow_html=True)
    
    # Supported file types
    supported_types = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/plain',
        'application/vnd.google-apps.document'
    ]
    
    # Controls
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Search files:", placeholder="Enter filename...")
    with col2:
        if st.button("Refresh", use_container_width=True):
            st.rerun()
    
    # Load files
    with st.spinner("Loading files..."):
        files = list_drive_files(supported_types, search_term)
    
    if not files:
        st.info("No supported documents found. Upload some files to Google Drive first.")
        return
    
    st.write(f"Found {len(files)} files")
    
    # Display files
    for i, file in enumerate(files):
        with st.container():
            st.markdown(f"""
            <div class="file-card">
                <h4>📄 {file['name']}</h4>
                <p>Modified: {file.get('modifiedTime', 'Unknown')[:10]}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"Convert to Form", key=f"convert_{i}"):
                    message = f"Convert the document '{file['name']}' (ID: {file['id']}) to a Google Form"
                    chat_with_agent(message)
                    st.success("Conversion started! Check the Chat tab.")

def show_home_page():
    """Show the home page."""
    st.markdown('<h1 class="main-header">Google Forms Agent</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <h3>Transform documents into Google Forms</h3>
            <p>Use AI to convert any document into an interactive form in seconds.</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.authenticated:
        st.success("You're signed in and ready to go!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Start Chatting", use_container_width=True):
                st.session_state.current_page = 'agent'
                st.rerun()
        
        with col2:
            if st.button("Browse Files", use_container_width=True):
                st.session_state.current_page = 'files'
                st.rerun()
        
        with col3:
            if st.button("Quick Actions", use_container_width=True):
                st.session_state.current_page = 'actions'
                st.rerun()
    else:
        st.info("Sign in with your Google account to get started.")

def show_quick_actions():
    """Show quick action templates."""
    st.markdown('<h1 class="main-header">Quick Actions</h1>', unsafe_allow_html=True)
    
    if not FORMS_AGENT_AVAILABLE:
        st.error("Forms agent is not available.")
        return
    
    templates = [
        {
            "title": "Customer Survey",
            "description": "Create a satisfaction survey",
            "prompt": "Create a customer satisfaction survey with rating questions and feedback"
        },
        {
            "title": "Event Registration",
            "description": "Registration form for events",
            "prompt": "Create an event registration form with personal info and preferences"
        },
        {
            "title": "Quiz Template",
            "description": "Educational quiz with scoring",
            "prompt": "Create a quiz with multiple choice questions and scoring"
        },
        {
            "title": "Job Application",
            "description": "Professional application form",
            "prompt": "Create a job application form with experience and skills sections"
        }
    ]
    
    for template in templates:
        st.markdown(f"""
        <div class="card">
            <h4>{template['title']}</h4>
            <p>{template['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Create {template['title']}", key=template['title']):
            chat_with_agent(template['prompt'])
            st.success(f"{template['title']} creation started! Check the Chat tab.")

def main():
    """Main application entry point."""
    initialize_session_state()
    main_app()

if __name__ == "__main__":
    main() 