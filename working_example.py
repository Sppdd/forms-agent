#!/usr/bin/env python3
"""
Working example showing how to use service_account.json
"""

from google_forms_api import GoogleFormsAPI

def main():
    print("🚀 Google Forms API with Service Account")
    print("=" * 40)
    
    try:
        # Initialize the API (automatically uses service_account.json)
        print("1. Initializing Google Forms API...")
        api = GoogleFormsAPI()
        print("✅ API initialized successfully!")
        
        # Create a form
        print("\n2. Creating a new form...")
        result = api.create_form(
            title="My First Form with Service Account",
            description="This form was created using the service account authentication"
        )
        
        if result["result"] == "success":
            form_id = result["form_id"]
            print(f"✅ Form created successfully!")
            print(f"   Form ID: {form_id}")
            print(f"   Form URL: {result['form_url']}")
            
            # Add some questions
            print("\n3. Adding questions to the form...")
            questions = [
                {
                    "title": "What is your name?",
                    "type": "short_answer",
                    "required": True
                },
                {
                    "title": "How would you rate this service?",
                    "type": "linear_scale",
                    "required": False,
                    "scale": {"low": 1, "high": 5, "low_label": "Poor", "high_label": "Excellent"}
                },
                {
                    "title": "What features would you like?",
                    "type": "checkbox",
                    "required": False,
                    "options": ["Feature A", "Feature B", "Feature C"]
                }
            ]
            
            add_result = api.add_questions(form_id, questions)
            if add_result["result"] == "success":
                print(f"✅ {add_result['questions_added']} questions added successfully!")
            
            # Get form info
            print("\n4. Getting form information...")
            info_result = api.get_form_info(form_id)
            if info_result["result"] == "success":
                print(f"✅ Form info retrieved!")
                print(f"   Title: {info_result['form_info'].get('title', 'N/A')}")
                print(f"   Items count: {len(info_result['items'])}")
            
            print(f"\n🎉 SUCCESS! Your service account is working perfectly!")
            print(f"📝 You can view your form at: {result['form_url']}")
            
        else:
            print(f"❌ Form creation failed: {result['message']}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main() 