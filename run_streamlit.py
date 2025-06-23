#!/usr/bin/env python3
"""
Streamlit App Runner

A simple script to run the Google Forms Manager Streamlit app with proper configuration.
"""

import os
import sys
import subprocess
import secrets
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit
        import authlib
        print("✅ Streamlit and Authlib are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements_streamlit.txt")
        return False
    return True

def check_secrets():
    """Check if secrets.toml exists and has required configuration."""
    secrets_path = Path(".streamlit/secrets.toml")
    
    if not secrets_path.exists():
        print("❌ .streamlit/secrets.toml not found")
        print("Creating template secrets file...")
        
        # Create .streamlit directory
        secrets_path.parent.mkdir(exist_ok=True)
        
        # Generate secure cookie secret
        cookie_secret = secrets.token_urlsafe(32)
        
        # Create template secrets file
        template = f"""[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "{cookie_secret}"
client_id = "your-google-client-id-here"
client_secret = "your-google-client-secret-here"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[forms_agent]
service_account_path = "forms_agent/service-account-key.json"
"""
        
        with open(secrets_path, 'w') as f:
            f.write(template)
        
        print("✅ Created .streamlit/secrets.toml template")
        print("⚠️  Please update the OAuth credentials in .streamlit/secrets.toml")
        print("   - Get client_id and client_secret from Google Cloud Console")
        print("   - See deploy_guide.md for detailed instructions")
        return False
    
    return True

def check_service_account():
    """Check if service account key exists."""
    service_account_paths = [
        "forms_agent/service-account-key.json",
        "service-account-key.json",
        "service-account.json"
    ]
    
    for path in service_account_paths:
        if Path(path).exists():
            print(f"✅ Found service account key: {path}")
            return True
    
    print("❌ Service account key not found")
    print("Please place your service account JSON file in one of these locations:")
    for path in service_account_paths:
        print(f"   - {path}")
    return False

def run_streamlit():
    """Run the Streamlit app."""
    print("🚀 Starting Google Forms Manager...")
    print("📱 Web interface will be available at: http://localhost:8501")
    print("🔐 Make sure you have configured OAuth credentials in .streamlit/secrets.toml")
    print("")
    
    try:
        # Run streamlit with proper configuration
        cmd = [
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--server.headless=false",
            "--browser.gatherUsageStats=false"
        ]
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down Google Forms Manager...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        return False
    
    return True

def main():
    """Main function."""
    print("=" * 60)
    print("📝 Google Forms Manager - Streamlit App")
    print("=" * 60)
    print("")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    print("")
    
    # Check configuration
    if not check_secrets():
        print("")
        print("⚠️  Please configure OAuth credentials before running the app")
        print("   See deploy_guide.md for detailed instructions")
        print("")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    if not check_service_account():
        print("")
        print("⚠️  Service account key is required for form operations")
        print("   Some features may not work without it")
        print("")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    print("")
    print("✅ All checks passed!")
    print("")
    
    # Run the app
    return run_streamlit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 