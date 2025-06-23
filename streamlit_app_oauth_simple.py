#!/usr/bin/env python3
"""
Google Forms Manager - Simplified OAuth-enabled Streamlit Web App

A streamlined web application for managing Google Forms with OAuth authentication.
Users can authenticate with their Google account and manage their own forms.
"""

import streamlit as st
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/forms',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]

# Page configuration
st.set_page_config(
    page_title="Google Forms Manager",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .form-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
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
    .oauth-info {
        background-color: #e2e3e5;
        color: #383d41;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #d6d8db;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'credentials' not in st.session_state:
        st.session_state.credentials = None
    if 'current_form_id' not in st.session_state:
        st.session_state.current_form_id = None
    if 'forms_cache' not in st.session_state:
        st.session_state.forms_cache = None

def get_oauth_credentials():
    """Get OAuth credentials from environment variables or user input."""
    # Check if credentials are already in session
    if st.session_state.credentials:
        return st.session_state.credentials
    
    # Try to get from environment variables (for Streamlit Cloud)
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if client_id and client_secret:
        # For Streamlit Cloud, we'll use a simplified OAuth flow
        return handle_streamlit_oauth(client_id, client_secret)
    else:
        # For local development, show instructions
        return handle_local_oauth()

def handle_streamlit_oauth(client_id: str, client_secret: str):
    """Handle OAuth for Streamlit Cloud deployment."""
    st.markdown("""
    <div class="oauth-info">
        <h3>🔐 OAuth Authentication Required</h3>
        <p>This app requires access to your Google Forms and Drive. Please authenticate with your Google account.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create OAuth URL
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri=urn:ietf:wg:oauth:2.0:oob&scope={'+'.join(SCOPES)}&response_type=code"
    
    st.markdown(f"""
    <div class="info-message">
        <h4>📋 Authentication Steps:</h4>
        <ol>
            <li>Click the link below to authorize this app</li>
            <li>Copy the authorization code from the page</li>
            <li>Paste it in the text box below</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"[🔗 Click here to authorize]({auth_url})")
    
    auth_code = st.text_input("Enter the authorization code:", type="password")
    
    if auth_code:
        try:
            # Exchange code for tokens
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
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
                st.session_state.credentials = credentials
                st.session_state.authenticated = True
                st.success("✅ Authentication successful!")
                st.rerun()
            else:
                st.error(f"❌ Authentication failed: {response.text}")
        except Exception as e:
            st.error(f"❌ Error during authentication: {e}")
    
    return None

def handle_local_oauth():
    """Handle OAuth for local development."""
    st.markdown("""
    <div class="oauth-info">
        <h3>🔧 Local Development Setup</h3>
        <p>For local development, you need to set up OAuth credentials:</p>
        <ol>
            <li>Go to <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a></li>
            <li>Create a new project or select existing one</li>
            <li>Enable Google Forms API and Google Drive API</li>
            <li>Create OAuth 2.0 credentials</li>
            <li>Download the credentials JSON file</li>
            <li>Set environment variables: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Allow manual credential input for testing
    st.markdown("### 🔑 Manual Credential Input (for testing)")
    client_id = st.text_input("Client ID:", type="password")
    client_secret = st.text_input("Client Secret:", type="password")
    
    if client_id and client_secret:
        return handle_streamlit_oauth(client_id, client_secret)
    
    return None

def get_forms_service():
    """Get Google Forms service using OAuth credentials."""
    if not st.session_state.credentials:
        return None
    
    try:
        service = build('forms', 'v1', credentials=st.session_state.credentials)
        return service
    except Exception as e:
        st.error(f"Error creating Forms service: {e}")
        return None

def get_drive_service():
    """Get Google Drive service using OAuth credentials."""
    if not st.session_state.credentials:
        return None
    
    try:
        service = build('drive', 'v3', credentials=st.session_state.credentials)
        return service
    except Exception as e:
        st.error(f"Error creating Drive service: {e}")
        return None

def list_my_forms():
    """List user's Google Forms using OAuth."""
    forms_service = get_forms_service()
    drive_service = get_drive_service()
    
    if not forms_service or not drive_service:
        return {"status": "error", "message": "Services not available"}
    
    try:
        # Get forms from Drive
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.form'",
            fields="files(id,name,createdTime,modifiedTime,parents)",
            orderBy="modifiedTime desc"
        ).execute()
        
        forms = results.get('files', [])
        
        # Get additional details for each form
        detailed_forms = []
        for form in forms:
            try:
                form_details = forms_service.forms().get(formId=form['id']).execute()
                form['title'] = form_details.get('title', form['name'])
                form['description'] = form_details.get('description', '')
                detailed_forms.append(form)
            except Exception as e:
                # Skip forms that can't be accessed
                continue
        
        return {
            "status": "success",
            "forms": detailed_forms,
            "count": len(detailed_forms)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def create_google_form(title: str, description: str = ""):
    """Create a new Google Form using OAuth."""
    forms_service = get_forms_service()
    
    if not forms_service:
        return {"status": "error", "message": "Forms service not available"}
    
    try:
        # Create the form
        form = {
            'title': title,
            'description': description
        }
        
        created_form = forms_service.forms().create(body=form).execute()
        
        return {
            "status": "success",
            "form_id": created_form['formId'],
            "form_url": created_form['responderUri'],
            "edit_url": created_form['editorUri'],
            "title": created_form['title']
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_form_details(form_id: str):
    """Get details of a specific form using OAuth."""
    forms_service = get_forms_service()
    
    if not forms_service:
        return {"status": "error", "message": "Forms service not available"}
    
    try:
        form = forms_service.forms().get(formId=form_id).execute()
        return {
            "status": "success",
            "form": form
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def login_screen():
    """Display login screen and OAuth authentication."""
    st.markdown('<h1 class="main-header">📝 Google Forms Manager</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="info-message">
            <h3>Welcome to Google Forms Manager!</h3>
            <p>This application allows you to:</p>
            <ul>
                <li>Create and manage Google Forms</li>
                <li>View your existing forms</li>
                <li>Access form details and URLs</li>
                <li>Manage all your forms in one place</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # OAuth Authentication
        credentials = get_oauth_credentials()
        
        if st.session_state.authenticated:
            st.markdown("""
            <div class="success-message">
                <h4>✅ Authenticated Successfully</h4>
                <p>You can now access and manage your Google Forms!</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Enter Application", type="primary", use_container_width=True):
                st.rerun()
        else:
            st.markdown("""
            <div class="info-message">
                <h4>🔐 Authentication Required</h4>
                <p>Please authenticate with your Google account to continue.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div class="info-message">
            <h4>📋 Features:</h4>
            <ul>
                <li><strong>Form Creation:</strong> Create new forms with titles and descriptions</li>
                <li><strong>Form Management:</strong> List and view your forms</li>
                <li><strong>Form Details:</strong> Access form URLs and metadata</li>
                <li><strong>Secure Access:</strong> OAuth 2.0 authentication</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def main_app():
    """Main application interface."""
    st.markdown('<h1 class="main-header">📝 Google Forms Manager</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["My Forms", "Create Form", "Settings"]
    )
    
    # User info
    if st.session_state.credentials:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Info")
        st.sidebar.markdown("**Status:** ✅ Authenticated")
        
        if st.sidebar.button("🔓 Logout"):
            st.session_state.authenticated = False
            st.session_state.credentials = None
            st.rerun()
    
    # Page routing
    if page == "My Forms":
        show_my_forms()
    elif page == "Create Form":
        create_new_form()
    elif page == "Settings":
        show_settings()

def show_my_forms():
    """Display user's forms."""
    st.header("📋 My Forms")
    
    if st.button("🔄 Refresh Forms", type="secondary"):
        st.session_state.forms_cache = None
    
    # Get forms
    forms_result = list_my_forms()
    
    if forms_result["status"] == "success":
        forms = forms_result["forms"]
        
        if not forms:
            st.info("📝 No forms found. Create your first form!")
            return
        
        st.success(f"✅ Found {len(forms)} forms")
        
        # Display forms in cards
        for form in forms:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="form-card">
                        <h4>{form.get('title', form.get('name', 'Untitled'))}</h4>
                        <p><strong>ID:</strong> {form['id']}</p>
                        <p><strong>Created:</strong> {form.get('createdTime', 'Unknown')}</p>
                        <p><strong>Modified:</strong> {form.get('modifiedTime', 'Unknown')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button(f"📊 View", key=f"view_{form['id']}"):
                        st.session_state.current_form_id = form['id']
                        st.rerun()
        
        # Show form details if selected
        if st.session_state.current_form_id:
            st.markdown("---")
            show_form_details(st.session_state.current_form_id)
    else:
        st.error(f"❌ Error loading forms: {forms_result['message']}")

def show_form_details(form_id: str):
    """Show details of a specific form."""
    st.subheader("📊 Form Details")
    
    form_result = get_form_details(form_id)
    
    if form_result["status"] == "success":
        form = form_result["form"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Title:** {form.get('title', 'Untitled')}")
            st.markdown(f"**Form ID:** {form['formId']}")
            st.markdown(f"**Description:** {form.get('description', 'No description')}")
        
        with col2:
            st.markdown(f"**Responder URL:** [Open Form]({form.get('responderUri', '#')})")
            st.markdown(f"**Editor URL:** [Edit Form]({form.get('editorUri', '#')})")
        
        # Show questions if available
        if 'items' in form:
            st.subheader("📝 Questions")
            for i, item in enumerate(form['items'], 1):
                st.markdown(f"**{i}. {item.get('title', 'Untitled Question')}**")
                st.markdown(f"Type: {item.get('questionItem', {}).get('question', {}).get('type', 'Unknown')}")
    else:
        st.error(f"❌ Error loading form details: {form_result['message']}")

def create_new_form():
    """Create a new Google Form."""
    st.header("➕ Create New Form")
    
    with st.form("create_form"):
        title = st.text_input("Form Title", placeholder="Enter form title...")
        description = st.text_area("Form Description", placeholder="Enter form description...")
        
        submitted = st.form_submit_button("Create Form", type="primary")
        
        if submitted:
            if not title:
                st.error("❌ Please enter a form title")
                return
            
            with st.spinner("Creating form..."):
                result = create_google_form(title, description)
                
                if result["status"] == "success":
                    st.success(f"✅ Form created successfully!")
                    st.markdown(f"**Form ID:** {result['form_id']}")
                    st.markdown(f"**Form URL:** [Open Form]({result['form_url']})")
                    st.markdown(f"**Edit URL:** [Edit Form]({result['edit_url']})")
                    
                    # Clear form
                    st.rerun()
                else:
                    st.error(f"❌ Error creating form: {result['message']}")

def show_settings():
    """Show application settings."""
    st.header("⚙️ Settings")
    
    st.markdown("""
    <div class="info-message">
        <h4>🔧 Application Settings</h4>
        <p>Configure your Google Forms Manager preferences.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Authentication status
    st.subheader("🔐 Authentication")
    if st.session_state.authenticated:
        st.success("✅ Authenticated with Google")
        st.markdown("**Scopes:** Forms, Drive, Drive File")
    else:
        st.error("❌ Not authenticated")
    
    # App info
    st.subheader("ℹ️ App Information")
    st.markdown("**Version:** 1.0.0")
    st.markdown("**Authentication:** OAuth 2.0")
    st.markdown("**APIs:** Google Forms API, Google Drive API")

def main():
    """Main application entry point."""
    initialize_session_state()
    
    if not st.session_state.authenticated:
        login_screen()
    else:
        main_app()

if __name__ == "__main__":
    main() 