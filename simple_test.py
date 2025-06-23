#!/usr/bin/env python3
"""
Simple test script to verify service_account.json works
"""

from google_forms_api import create_google_form_standalone

def test_service_account():
    print("Testing service account authentication...")
    
    try:
        # Try to create a simple form
        result = create_google_form_standalone(
            title="Service Account Test Form",
            description="Testing if the service account works correctly"
        )
        
        if result["result"] == "success":
            print("✅ SUCCESS! Service account is working!")
            print(f"   Form ID: {result['form_id']}")
            print(f"   Form URL: {result['form_url']}")
            print(f"   Message: {result['message']}")
            return True
        else:
            print("❌ FAILED! Service account authentication failed.")
            print(f"   Error: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

if __name__ == "__main__":
    test_service_account() 