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
    page_title="Google Forms Agent - AI-Powered Form Creation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/forms-agent',
        'Report a bug': 'https://github.com/your-repo/forms-agent/issues',
        'About': """
        # Google Forms Agent 🚀
        
        Transform documents into interactive forms using AI!
        
        **Features:**
        - AI-powered document analysis
        - Automatic form generation
        - Google Drive integration
        - Secure OAuth authentication
        
        Made with ❤️ and Streamlit
        """
    }
)

# Modern, Beautiful UI Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }
    
    /* Hero Header */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><defs><radialGradient id="a"><stop offset="0" stop-color="%23ffffff" stop-opacity=".1"/><stop offset="1" stop-color="%23ffffff" stop-opacity="0"/></radialGradient></defs><circle cx="200" cy="200" r="180" fill="url(%23a)"/><circle cx="800" cy="800" r="250" fill="url(%23a)"/><circle cx="400" cy="600" r="120" fill="url(%23a)"/></svg>') no-repeat;
        background-size: cover;
        opacity: 0.6;
    }
    
    .hero-content {
        position: relative;
        z-index: 1;
    }
    
    .hero-title {
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        background: linear-gradient(45deg, #ffffff, #f0f9ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .hero-subtitle {
        font-size: 1.25rem !important;
        font-weight: 400 !important;
        opacity: 0.9;
        margin-bottom: 2rem !important;
    }
    
    /* Modern Cards */
    .modern-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .modern-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.15);
    }
    
    .card-title {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #1a202c !important;
        margin-bottom: 0.5rem !important;
    }
    
    .card-subtitle {
        color: #718096 !important;
        font-size: 1rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Glassmorphism Sidebar */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.25) !important;
        backdrop-filter: blur(10px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Navigation Cards */
    .nav-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .nav-card:hover {
        background: rgba(102, 126, 234, 0.1);
        transform: translateX(5px);
        border-color: #667eea;
    }
    
    .nav-icon {
        font-size: 1.5rem;
        margin-right: 0.75rem;
    }
    
    /* Premium Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* Animated Primary Button */
    .primary-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .primary-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        text-decoration: none;
        color: white;
    }
    
    .primary-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .primary-button:hover::before {
        left: 100%;
    }
    
    /* Modern Inputs */
    .stTextInput input, .stTextArea textarea {
        border: 2px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(5px) !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        outline: none !important;
    }
    
    /* Chat Messages */
    .chat-message-user {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 1rem 0;
        margin-left: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        position: relative;
    }
    
    .chat-message-agent {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        color: #1a202c;
        padding: 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 1rem 0;
        margin-right: 2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    /* File Cards */
    .file-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .file-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
        border-color: #667eea;
    }
    
    /* Status Indicators */
    .status-online {
        display: inline-block;
        width: 12px;
        height: 12px;
        background: #10b981;
        border-radius: 50%;
        margin-right: 0.5rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    /* Modern Alerts */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        color: #047857 !important;
        border-left: 4px solid #10b981 !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        color: #b91c1c !important;
        border-left: 4px solid #ef4444 !important;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.1) !important;
        color: #b45309 !important;
        border-left: 4px solid #f59e0b !important;
    }
    
    .stInfo {
        background: rgba(102, 126, 234, 0.1) !important;
        color: #3730a3 !important;
        border-left: 4px solid #667eea !important;
    }
    
    /* Feature Cards */
    .feature-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        color: #667eea;
    }
    
    .feature-title {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #1a202c !important;
        margin-bottom: 1rem !important;
    }
    
    .feature-description {
        color: #718096 !important;
        line-height: 1.6 !important;
    }
    
    /* Loading Animation */
    .loading-spinner {
        border: 3px solid rgba(102, 126, 234, 0.3);
        border-radius: 50%;
        border-top: 3px solid #667eea;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #667eea !important;
        margin-bottom: 0.5rem !important;
    }
    
    .metric-label {
        color: #718096 !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem !important;
        }
        
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        .modern-card {
            padding: 1.5rem !important;
        }
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fix text colors */
    .stMarkdown, .stText, p, span, div, h1, h2, h3, h4, h5, h6 {
        color: inherit !important;
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
    """Show modern navigation sidebar."""
    with st.sidebar:
        # Brand header
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 2rem;">
            <h2 style="color: white; margin: 0; font-weight: 700;">📝 Forms Agent</h2>
            <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">AI-Powered Form Creation</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation menu
        pages = {
            "🏠 Home": "home",
            "💬 AI Chat": "agent", 
            "📁 Drive Files": "files"
        }
        
        current_page = st.session_state.get('current_page', 'home')
        
        for page_name, page_key in pages.items():
            is_current = current_page == page_key
            button_style = "background: rgba(255,255,255,0.2); border-left: 4px solid white;" if is_current else ""
            
            st.markdown(f"""
            <div class="nav-card" style="{button_style}">
                <span class="nav-icon">{page_name.split()[0]}</span>
                <span style="font-weight: {'600' if is_current else '400'};">{' '.join(page_name.split()[1:])}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(page_name, use_container_width=True, key=f"nav_{page_key}", 
                        type="primary" if is_current else "secondary"):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # User info section
        if st.session_state.authenticated:
            user_info = st.session_state.user_info
            user_name = user_info.get('name', 'Unknown User')
            user_email = user_info.get('email', 'unknown@email.com')
            
            st.markdown(f"""
            <div class="modern-card" style="margin-top: 2rem;">
                <div style="text-align: center;">
                    <div class="status-online"></div>
                    <h4 style="color: #1a202c; margin: 0;">Signed In</h4>
                    <p style="color: #667eea; font-weight: 600; margin: 0.5rem 0;">{user_name}</p>
                    <p style="color: #718096; font-size: 0.8rem; margin: 0;">{user_email}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
                for key in ['authenticated', 'credentials', 'user_info', 'chat_history']:
                    st.session_state[key] = False if key == 'authenticated' else None if key != 'chat_history' else []
                st.session_state.current_page = 'home'
                st.rerun()
        else:
            st.markdown("""
            <div class="modern-card" style="margin-top: 2rem;">
                <div style="text-align: center;">
                    <h4 style="color: #1a202c; margin: 0;">Not Signed In</h4>
                    <p style="color: #718096; font-size: 0.9rem; margin: 0.5rem 0;">Sign in to get started</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style="position: absolute; bottom: 1rem; left: 1rem; right: 1rem; text-align: center;">
            <p style="color: rgba(255,255,255,0.6); font-size: 0.8rem; margin: 0;">
                Powered by AI • Secure & Fast
            </p>
        </div>
        """, unsafe_allow_html=True)

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
                # Exchange code for tokens - Fix 403 issues with proper headers and error handling
                token_url = "https://oauth2.googleapis.com/token"
                
                # Prepare headers with proper Content-Type (this fixes many 403 issues)
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                    'User-Agent': 'StreamlitApp/1.0'
                }
                
                token_data = {
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': auth_code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri
                }
                
                # Add timeout and better error handling
                response = requests.post(
                    token_url, 
                    data=token_data, 
                    headers=headers,
                    timeout=30
                )
                
                # Enhanced error handling for 403 and other status codes
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
                
                elif response.status_code == 403:
                    # Specific handling for 403 errors
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', 'Unknown error')
                        error_desc = error_data.get('error_description', 'No description')
                        
                        st.error("**403 Forbidden Error:** OAuth token exchange failed")
                        st.error(f"**Error:** {error_msg}")
                        st.error(f"**Description:** {error_desc}")
                        
                        # Common 403 fixes
                        st.markdown("### Possible solutions:")
                        st.markdown("1. **Check your OAuth credentials** - Verify client_id and client_secret in Google Cloud Console")
                        st.markdown("2. **Verify redirect URI** - Ensure it exactly matches your Google Cloud project settings")
                        st.markdown("3. **Check API quotas** - Ensure you haven't exceeded Google API limits")
                        st.markdown("4. **Enable required APIs** - Make sure Google Forms API and Google Drive API are enabled")
                        st.markdown("5. **Check OAuth consent screen** - Ensure it's properly configured and published")
                        
                        # Show debug info
                        with st.expander("Debug Information"):
                            st.write(f"**Client ID:** {client_id[:20]}...")
                            st.write(f"**Redirect URI:** {redirect_uri}")
                            st.write(f"**Response Status:** {response.status_code}")
                            st.write(f"**Response Headers:** {dict(response.headers)}")
                            
                    except json.JSONDecodeError:
                        st.error("403 Forbidden: Unable to parse error response")
                        st.text(f"Raw response: {response.text}")
                    
                    return None
                
                elif response.status_code == 400:
                    # Handle 400 Bad Request (often authorization code issues)
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', 'Unknown error')
                        
                        if error_msg == 'invalid_grant':
                            st.error("**Authorization code expired or invalid.** Please try authenticating again.")
                            st.info("Authorization codes expire quickly. Click 'Sign in with Google' again.")
                        else:
                            st.error(f"Bad Request (400): {error_msg}")
                            st.error(f"Description: {error_data.get('error_description', 'No description')}")
                    except json.JSONDecodeError:
                        st.error("400 Bad Request: Unable to parse error response")
                
                else:
                    # Handle other HTTP errors
                    st.error(f"Authentication failed with status code: {response.status_code}")
                    try:
                        error_data = response.json()
                        st.error(f"Error: {error_data}")
                    except:
                        st.error(f"Raw response: {response.text}")
                    
                    return None
                    
        except requests.exceptions.Timeout:
            st.error("Authentication request timed out. Please try again.")
            return None
        except requests.exceptions.ConnectionError:
            st.error("Network connection error. Please check your internet connection and try again.")
            return None
        except Exception as e:
            st.error(f"Error during authentication: {e}")
            st.error("Please try the authentication process again.")
            return None
    
    # Show login
    st.markdown("""
    <div class="modern-card">
        <div style="text-align: center;">
            <h3 class="card-title">🔐 Sign in to Google</h3>
            <p class="card-subtitle">Connect your Google account to create forms and access your Drive files.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create OAuth URL with proper encoding
    import urllib.parse
    scope_param = urllib.parse.quote(' '.join(SCOPES))
    
    # Ensure redirect_uri is properly encoded and matches exactly what's in Google Cloud Console
    encoded_redirect_uri = urllib.parse.quote(redirect_uri, safe='')
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri={encoded_redirect_uri}&scope={scope_param}&response_type=code&access_type=offline&prompt=consent"
    
    # Show current configuration for debugging
    with st.expander("🔧 OAuth Configuration (for debugging)", expanded=False):
        st.markdown(f"""
        <div class="modern-card">
            <p><strong>Client ID:</strong> {client_id}</p>
            <p><strong>Redirect URI:</strong> {redirect_uri}</p>
            <p><strong>Scopes:</strong> {', '.join(SCOPES)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Modern sign-in button
    st.markdown(f"""
    <div style="text-align: center; margin: 2rem 0;">
        <a href="{auth_url}" target="_self" class="primary-button">
            🚀 Sign in with Google
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
    """Show the modern, beautiful home page."""
    # Hero Section
    st.markdown("""
    <div class="hero-header">
        <div class="hero-content">
            <h1 class="hero-title">📝 Google Forms Agent</h1>
            <p class="hero-subtitle">Transform documents into interactive forms with the power of AI</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.authenticated:
        # Welcome back section
        user_name = st.session_state.user_info.get('name', 'User')
        st.markdown(f"""
        <div class="modern-card">
            <div style="text-align: center;">
                <div class="status-online"></div>
                <h3 style="color: #1a202c; margin: 0;">Welcome back, {user_name}! 👋</h3>
                <p style="color: #718096; margin-top: 0.5rem;">You're authenticated and ready to create amazing forms.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature Cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <h3 class="feature-title">AI Chat</h3>
                <p class="feature-description">Chat with our AI to create forms from your ideas and documents.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Start Chatting", use_container_width=True):
                st.session_state.current_page = 'agent'
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📁</div>
                <h3 class="feature-title">Drive Files</h3>
                <p class="feature-description">Browse and convert your Google Drive documents into forms.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Browse Files", use_container_width=True):
                st.session_state.current_page = 'files'
                st.rerun()
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h3 class="feature-title">Quick Actions</h3>
                <p class="feature-description">Access powerful form creation and editing tools instantly.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Quick Actions", use_container_width=True):
                st.session_state.current_page = 'actions'
                st.rerun()
        
        # Stats Section
        st.markdown("### 📊 Your Dashboard")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">0</div>
                <div class="metric-label">Forms Created</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">0</div>
                <div class="metric-label">Documents Processed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">0</div>
                <div class="metric-label">Responses Collected</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">100%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Sign-in section for non-authenticated users
        st.markdown("""
        <div class="modern-card">
            <div style="text-align: center;">
                <h3 class="card-title">🚀 Get Started</h3>
                <p class="card-subtitle">Sign in with your Google account to unlock powerful form creation capabilities.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Benefits section
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <h3 class="feature-title">AI-Powered</h3>
                <p class="feature-description">Convert any document into a structured form using advanced AI technology.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🔒</div>
                <h3 class="feature-title">Secure</h3>
                <p class="feature-description">Your data is protected with OAuth 2.0 authentication and encrypted connections.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h3 class="feature-title">Fast</h3>
                <p class="feature-description">Create professional forms in seconds, not hours. Streamline your workflow.</p>
            </div>
            """, unsafe_allow_html=True)

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