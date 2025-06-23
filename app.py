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
    initial_sidebar_state="expanded"
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
        'drive_files': []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_oauth_credentials():
    """Get OAuth credentials using Streamlit secrets."""
    try:
        client_id = st.secrets["auth"]["client_id"]
        client_secret = st.secrets["auth"]["client_secret"]
        redirect_uri = st.secrets["auth"]["redirect_uri"]
        
        return handle_oauth_flow(client_id, client_secret, redirect_uri)
    except KeyError as e:
        st.markdown("""
        <div class="error-message">
            <h4>⚙️ OAuth Configuration Missing</h4>
            <p>Please set up your OAuth credentials in <code>.streamlit/secrets.toml</code>:</p>
            <pre>[auth]
client_id = "your-google-client-id"
client_secret = "your-google-client-secret"
redirect_uri = "your-app-url"</pre>
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

def login_screen():
    """Display login screen."""
    st.markdown('<h1 class="main-header">🤖 Google Forms Agent</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="agent-card">
            <h3>🚀 AI-Powered Forms Management</h3>
            <p>Transform your workflow with cutting-edge intelligent form creation:</p>
            <ul>
                <li><strong>📄 Document AI:</strong> Convert any document into interactive forms instantly</li>
                <li><strong>🤖 Smart Generation:</strong> Create sophisticated forms from simple descriptions</li>
                <li><strong>📝 Auto-Completion:</strong> AI intelligently fills in missing form elements</li>
                <li><strong>☁️ Drive Integration:</strong> Seamless access to your Google Drive ecosystem</li>
                <li><strong>💬 Natural Chat:</strong> Converse with AI like your personal assistant</li>
                <li><strong>⚡ Instant Creation:</strong> Professional forms ready in seconds, not hours</li>
                <li><strong>🔄 Real-time Processing:</strong> Live document analysis and form generation</li>
                <li><strong>🎯 Smart Suggestions:</strong> AI recommends optimal form structures</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # OAuth Authentication
        get_oauth_credentials()
        
        if st.session_state.authenticated:
            user_info = st.session_state.user_info
            st.markdown(f"""
            <div class="success-message">
                <h4>✅ Welcome, {user_info.get('name', 'User')}!</h4>
                <p><strong>Email:</strong> {user_info.get('email', 'Unknown')}</p>
                <p>🎉 You're ready to create amazing forms with AI!</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Launch Forms Agent", type="primary", use_container_width=True):
                st.rerun()

def main_app():
    """Main application interface."""
    st.markdown('<h1 class="main-header">🤖 Google Forms Agent</h1>', unsafe_allow_html=True)
    
    # Sidebar user info
    user_info = st.session_state.user_info
    with st.sidebar:
        st.markdown("### 👤 User Profile")
        st.write(f"**{user_info.get('name', 'Unknown')}**")
        st.write(f"📧 {user_info.get('email', 'Unknown')}")
        
        st.markdown("---")
        
        st.markdown("### 🤖 Agent Status")
        if FORMS_AGENT_AVAILABLE:
            st.success("✅ Agent Online")
            st.write("Ready to create forms!")
        else:
            st.error("❌ Agent Offline")
            st.write("Check configuration")
        
        st.markdown("---")
        
        if st.button("🔓 Logout", use_container_width=True):
            for key in ['authenticated', 'credentials', 'user_info', 'chat_history']:
                st.session_state[key] = False if key == 'authenticated' else None if key != 'chat_history' else []
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["💬 AI Assistant", "📁 Drive Files", "🚀 Quick Actions"])
    
    with tab1:
        show_agent_chat()
    
    with tab2:
        show_drive_files()
    
    with tab3:
        show_quick_actions()

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
    
    if not st.session_state.authenticated:
        login_screen()
    else:
        main_app()

if __name__ == "__main__":
    main() 