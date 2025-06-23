#!/usr/bin/env python3
"""
OAuth Troubleshooting Script for Google Forms Agent

This script helps diagnose and fix OAuth 403 errors by testing various configurations
and providing detailed feedback on what might be wrong.
"""

import requests
import json
import urllib.parse
from datetime import datetime
import sys
import os

# Add current directory to path to import config
sys.path.insert(0, os.path.dirname(__file__))

def load_config():
    """Load configuration from secrets.toml"""
    try:
        import toml
        with open('.streamlit/secrets.toml', 'r') as f:
            config = toml.load(f)
        return config['auth']
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def test_oauth_configuration(config):
    """Test OAuth configuration for common issues"""
    print("🔍 Testing OAuth Configuration...")
    print("-" * 50)
    
    issues = []
    warnings = []
    
    # Check required fields
    required_fields = ['client_id', 'client_secret', 'redirect_uri']
    for field in required_fields:
        if not config.get(field):
            issues.append(f"Missing required field: {field}")
        else:
            print(f"✅ {field}: Present")
    
    # Check client_id format
    client_id = config.get('client_id', '')
    if client_id and not client_id.endswith('.apps.googleusercontent.com'):
        warnings.append("Client ID doesn't end with '.apps.googleusercontent.com' - make sure you're using the correct client ID")
    
    # Check client_secret format
    client_secret = config.get('client_secret', '')
    if client_secret and not client_secret.startswith('GOCSPX-'):
        warnings.append("Client secret doesn't start with 'GOCSPX-' - make sure you're using the correct client secret")
    
    # Check redirect URI format
    redirect_uri = config.get('redirect_uri', '')
    if redirect_uri:
        if not redirect_uri.startswith(('http://', 'https://')):
            issues.append("Redirect URI must start with http:// or https://")
        
        # Common redirect URI issues
        if redirect_uri.startswith('http://') and 'localhost' not in redirect_uri:
            warnings.append("Using http:// for non-localhost redirect URI - Google may require https://")
        
        if redirect_uri.endswith('/') and redirect_uri.count('/') > 3:
            warnings.append("Redirect URI has trailing slash - make sure this matches exactly in Google Cloud Console")
    
    return issues, warnings

def test_google_apis():
    """Test if required Google APIs are accessible"""
    print("\n🌐 Testing Google API Accessibility...")
    print("-" * 50)
    
    apis_to_test = [
        ('OAuth Token Endpoint', 'https://oauth2.googleapis.com/token'),
        ('OAuth Authorization Endpoint', 'https://accounts.google.com/o/oauth2/auth'),
        ('Google Forms API', 'https://forms.googleapis.com/v1'),
        ('Google Drive API', 'https://www.googleapis.com/drive/v3'),
    ]
    
    for api_name, url in apis_to_test:
        try:
            response = requests.head(url, timeout=10)
            if response.status_code in [200, 401, 403]:  # These are expected
                print(f"✅ {api_name}: Accessible")
            else:
                print(f"⚠️  {api_name}: Unexpected status {response.status_code}")
        except Exception as e:
            print(f"❌ {api_name}: Not accessible - {e}")

def test_token_exchange(config, mock_code="test_code"):
    """Test token exchange with proper headers (using mock code to test request format)"""
    print("\n🔄 Testing Token Exchange Request Format...")
    print("-" * 50)
    
    if not config:
        print("❌ No configuration available")
        return
    
    token_url = "https://oauth2.googleapis.com/token"
    
    # Prepare headers exactly as in the app
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'User-Agent': 'StreamlitApp/1.0'
    }
    
    token_data = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': mock_code,  # This will fail, but we can see the error format
        'grant_type': 'authorization_code',
        'redirect_uri': config['redirect_uri']
    }
    
    print("Request details:")
    print(f"URL: {token_url}")
    print(f"Headers: {headers}")
    print(f"Data: {dict((k, v if k != 'client_secret' else '***') for k, v in token_data.items())}")
    
    try:
        response = requests.post(
            token_url, 
            data=token_data, 
            headers=headers,
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 400:
            try:
                error_data = response.json()
                if error_data.get('error') == 'invalid_grant':
                    print("✅ Request format appears correct (got expected 'invalid_grant' error for test code)")
                else:
                    print(f"⚠️  Unexpected error: {error_data}")
            except:
                print(f"❌ Could not parse error response: {response.text}")
        
        elif response.status_code == 403:
            print("❌ 403 Forbidden - This indicates a configuration problem!")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw response: {response.text}")
        
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def generate_auth_url(config):
    """Generate and validate OAuth authorization URL"""
    print("\n🔗 Generating OAuth Authorization URL...")
    print("-" * 50)
    
    if not config:
        print("❌ No configuration available")
        return
    
    scopes = [
        'https://www.googleapis.com/auth/forms',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'openid',
        'email',
        'profile'
    ]
    
    scope_param = urllib.parse.quote(' '.join(scopes))
    encoded_redirect_uri = urllib.parse.quote(config['redirect_uri'], safe='')
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={config['client_id']}&redirect_uri={encoded_redirect_uri}&scope={scope_param}&response_type=code&access_type=offline&prompt=consent"
    
    print(f"Authorization URL: {auth_url}")
    print(f"\nURL Components:")
    print(f"  Client ID: {config['client_id']}")
    print(f"  Redirect URI: {config['redirect_uri']}")
    print(f"  Encoded Redirect URI: {encoded_redirect_uri}")
    print(f"  Scopes: {', '.join(scopes)}")
    
    return auth_url

def check_google_cloud_setup():
    """Provide checklist for Google Cloud Console setup"""
    print("\n☁️  Google Cloud Console Setup Checklist...")
    print("-" * 50)
    
    checklist = [
        "✅ Created a Google Cloud Project",
        "✅ Enabled Google Forms API",
        "✅ Enabled Google Drive API", 
        "✅ Created OAuth 2.0 Client ID credentials",
        "✅ Added correct redirect URI to 'Authorized redirect URIs'",
        "✅ Configured OAuth consent screen",
        "✅ Set OAuth consent screen to 'External' (if needed)",
        "✅ Added test users (if consent screen is in testing mode)",
        "✅ Requested verification (if publishing publicly)",
    ]
    
    print("\nPlease verify each item in Google Cloud Console:")
    for item in checklist:
        print(f"  {item}")
    
    print(f"\n🔗 Google Cloud Console Links:")
    print(f"  • APIs & Services: https://console.cloud.google.com/apis/dashboard")
    print(f"  • Credentials: https://console.cloud.google.com/apis/credentials")
    print(f"  • OAuth Consent Screen: https://console.cloud.google.com/apis/credentials/consent")

def main():
    """Main troubleshooting function"""
    print("🚀 OAuth 403 Error Troubleshooter")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Load configuration
    config = load_config()
    if not config:
        print("\n❌ Could not load configuration. Make sure .streamlit/secrets.toml exists and is properly formatted.")
        return
    
    # Test configuration
    issues, warnings = test_oauth_configuration(config)
    
    if issues:
        print(f"\n❌ Configuration Issues Found:")
        for issue in issues:
            print(f"  • {issue}")
    
    if warnings:
        print(f"\n⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"  • {warning}")
    
    if not issues and not warnings:
        print("✅ Configuration looks good!")
    
    # Test API accessibility
    test_google_apis()
    
    # Test token exchange format
    test_token_exchange(config)
    
    # Generate auth URL
    auth_url = generate_auth_url(config)
    
    # Google Cloud setup checklist
    check_google_cloud_setup()
    
    # Final recommendations
    print("\n💡 Common 403 Error Fixes:")
    print("-" * 50)
    fixes = [
        "1. Verify redirect URI exactly matches Google Cloud Console (including trailing slash)",
        "2. Ensure APIs are enabled in Google Cloud Console",
        "3. Check OAuth consent screen is properly configured", 
        "4. Verify client_id and client_secret are correct",
        "5. Make sure you're not exceeding API quotas",
        "6. Try regenerating client_secret if needed",
        "7. For local development, use http://localhost:8501/",
        "8. For production, ensure redirect URI uses https://",
    ]
    
    for fix in fixes:
        print(f"  {fix}")
    
    print(f"\n🔍 If issues persist:")
    print(f"  • Check Google Cloud Console audit logs")
    print(f"  • Enable debug logging in your application")
    print(f"  • Test with a minimal OAuth implementation")
    print(f"  • Contact Google Cloud Support if using paid plan")

if __name__ == "__main__":
    try:
        import toml
    except ImportError:
        print("Installing required package: toml")
        os.system("pip install toml")
        import toml
    
    main() 