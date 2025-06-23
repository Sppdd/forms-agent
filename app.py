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

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #28a745);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 5px solid #28a745;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .chat-message-user {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #2196f3;
    }
    .chat-message-agent {
        background-color: #f1f8e9;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4caf50;
    }
    .file-card {
        background-color: #fff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin-bottom: 0.5rem;
        transition: box-shadow 0.3s;
    }
    .file-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .info-message {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #bee5eb;
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
    except Exception as e:
        st.error(f"OAuth configuration error: {e}")
        st.error("Please check your .streamlit/secrets.toml file")
        return None

def handle_oauth_flow(client_id: str, client_secret: str, redirect_uri: str):
    """Handle OAuth flow for Google authentication."""
    
    # Check for OAuth callback parameters (compatible with older Streamlit versions)
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
                    
                    # Get user info
                    user_info = get_user_info(credentials)
                    
                    st.session_state.credentials = credentials
                    st.session_state.user_info = user_info
                    st.session_state.authenticated = True
                    
                    # Clear query params and redirect (compatible with older Streamlit)
                    try:
                        st.query_params.clear()
                    except AttributeError:
                        st.experimental_set_query_params()
                    
                    st.success("✅ Authentication successful!")
                    st.rerun()
                else:
                    st.error(f"❌ Authentication failed: {response.text}")
                    return None
        except Exception as e:
            st.error(f"❌ Error during authentication: {e}")
            return None
    
    # Show login screen
    st.markdown("""
    <div class="info-message">
        <h3>🔐 Google Authentication Required</h3>
        <p>This AI agent needs access to your Google account to:</p>
        <ul>
            <li><strong>📝 Create Forms:</strong> Generate forms directly in your Google account</li>
            <li><strong>📁 Access Drive:</strong> Read your documents for AI conversion</li>
            <li><strong>🤖 AI Processing:</strong> Use advanced AI to parse and create forms</li>
        </ul>
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

def list_drive_files(mime_types=None):
    """List files from Google Drive."""
    drive_service = get_drive_service()
    if not drive_service:
        return []
    
    try:
        query = ""
        if mime_types:
            mime_queries = [f"mimeType='{mime_type}'" for mime_type in mime_types]
            query = " or ".join(mime_queries)
        
        results = drive_service.files().list(
            q=query,
            fields="files(id,name,mimeType,modifiedTime,size)",
            orderBy="modifiedTime desc",
            pageSize=50
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        st.error(f"Error listing Drive files: {e}")
        return []

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
            <p>Transform your workflow with intelligent form creation:</p>
            <ul>
                <li><strong>📄 Document AI:</strong> Convert any document into interactive forms</li>
                <li><strong>🤖 Smart Generation:</strong> Create forms from simple descriptions</li>
                <li><strong>📝 Auto-Completion:</strong> AI fills in missing form elements</li>
                <li><strong>☁️ Drive Integration:</strong> Direct access to your Google Drive files</li>
                <li><strong>💬 Natural Chat:</strong> Talk to AI like a human assistant</li>
                <li><strong>⚡ Instant Creation:</strong> Forms ready in seconds, not hours</li>
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
        'application/vnd.google-apps.document'
    ]
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.drive_files = []
            st.rerun()
    
    # Load files
    if not st.session_state.drive_files:
        with st.spinner("🔍 Scanning your Drive..."):
            files = list_drive_files(supported_types)
            st.session_state.drive_files = files
    else:
        files = st.session_state.drive_files
    
    if not files:
        st.info("📂 No supported documents found in your Drive.")
        st.markdown("""
        **💡 Supported file types:**
        - 📄 PDF files (.pdf)
        - 📝 Word documents (.docx, .doc)
        - 📃 Text files (.txt)
        - 🔖 Markdown files (.md)
        - 📊 Google Docs
        """)
        return
    
    st.success(f"📋 Found {len(files)} documents ready for AI processing")
    
    # Search files
    search_term = st.text_input("🔍 Search files:", placeholder="Enter filename...")
    if search_term:
        files = [f for f in files if search_term.lower() in f['name'].lower()]
    
    # Display files
    for i, file in enumerate(files):
        with st.container():
            st.markdown(f"""
            <div class="file-card">
                <h4>📄 {file['name']}</h4>
                <p><strong>Type:</strong> {file['mimeType'].split('/')[-1].upper()}</p>
                <p><strong>Modified:</strong> {file.get('modifiedTime', 'Unknown')[:10]}</p>
                <p><strong>Size:</strong> {file.get('size', 'Unknown')} bytes</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"🤖 Convert to Form", key=f"convert_{i}"):
                    message = f"Please parse and convert the document '{file['name']}' (ID: {file['id']}) from my Google Drive into a Google Form. Extract all relevant questions and create an interactive form."
                    chat_with_agent(message)
                    st.success("✅ Conversion request sent to AI agent!")
                    st.info("💬 Check the AI Assistant tab to see the response.")

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