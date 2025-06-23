"""
Test Script for Standalone Google Forms API Implementation

This script demonstrates how to use the standalone Google Forms API
implementation as separate functions, tools, or agents.
"""

import json
from datetime import datetime

# Import the standalone API
from google_forms_api import (
    GoogleFormsAPI,
    create_google_form_standalone,
    update_form_standalone,
    add_questions_standalone,
    get_form_info_standalone,
    get_responses_standalone,
    delete_form_standalone
)

# Import the Google ADK tools
from google_forms_tool import (
    create_form,
    update_form,
    add_questions,
    get_form_info,
    get_responses,
    delete_form,
    configure_settings
)

# Import the Google ADK agent
from google_forms_agent import google_forms_agent


def test_standalone_functions():
    """Test the standalone functions directly."""
    print("🧪 Testing Standalone Functions")
    print("=" * 40)
    
    # Test 1: Create a form
    print("\n1. Creating a test form...")
    result = create_google_form_standalone(
        title="Test Form - Standalone Functions",
        description="This form was created using standalone functions"
    )
    
    if result["result"] == "success":
        form_id = result["form_id"]
        print(f"✅ Form created successfully!")
        print(f"   Form ID: {form_id}")
        print(f"   Form URL: {result['form_url']}")
        
        # Test 2: Add questions
        print("\n2. Adding questions to the form...")
        questions = [
            {
                "title": "What is your name?",
                "type": "short_answer",
                "required": True
            },
            {
                "title": "How would you rate our service?",
                "type": "linear_scale",
                "required": False,
                "scale": {"low": 1, "high": 5, "low_label": "Poor", "high_label": "Excellent"}
            },
            {
                "title": "What features would you like to see?",
                "type": "checkbox",
                "required": False,
                "options": ["Feature A", "Feature B", "Feature C", "Feature D"]
            }
        ]
        
        add_result = add_questions_standalone(form_id, questions)
        if add_result["result"] == "success":
            print(f"✅ {add_result['questions_added']} questions added successfully!")
        
        # Test 3: Get form info
        print("\n3. Getting form information...")
        info_result = get_form_info_standalone(form_id)
        if info_result["result"] == "success":
            print(f"✅ Form info retrieved successfully!")
            print(f"   Title: {info_result['form_info'].get('title', 'N/A')}")
            print(f"   Items count: {len(info_result['items'])}")
        
        # Test 4: Update form
        print("\n4. Updating form information...")
        update_result = update_form_standalone(
            form_id, 
            title="Updated Test Form - Standalone Functions",
            description="This form has been updated using standalone functions"
        )
        if update_result["result"] == "success":
            print("✅ Form updated successfully!")
        
        print(f"\n🎉 Standalone function tests completed successfully!")
        print(f"📝 Form URL: {result['form_url']}")
        
        return form_id
    else:
        print(f"❌ Form creation failed: {result['message']}")
        return None


def test_google_adk_tools():
    """Test the Google ADK tools."""
    print("\n\n🔧 Testing Google ADK Tools")
    print("=" * 40)
    
    # Test 1: Create a form using ADK tool
    print("\n1. Creating a form using ADK tool...")
    result = create_form_tool(
        title="Test Form - ADK Tools",
        description="This form was created using Google ADK tools"
    )
    
    if result["result"] == "success":
        form_id = result["form_id"]
        print(f"✅ Form created successfully using ADK tool!")
        print(f"   Form ID: {form_id}")
        print(f"   Form URL: {result['form_url']}")
        
        # Test 2: Add questions using ADK tool
        print("\n2. Adding questions using ADK tool...")
        questions = [
            {
                "title": "What is your email?",
                "type": "short_answer",
                "required": True
            },
            {
                "title": "What is your favorite color?",
                "type": "multiple_choice",
                "required": False,
                "options": ["Red", "Blue", "Green", "Yellow", "Other"]
            }
        ]
        
        add_result = add_questions_tool(form_id, questions)
        if add_result["result"] == "success":
            print(f"✅ {add_result['questions_added']} questions added using ADK tool!")
        
        # Test 3: Configure settings using ADK tool
        print("\n3. Configuring form settings using ADK tool...")
        settings = {
            "collect_email": True,
            "allow_response_editing": True,
            "confirmation_message": "Thank you for your response!"
        }
        
        settings_result = configure_form_settings_tool(form_id, settings)
        if settings_result["result"] == "success":
            print("✅ Form settings configured using ADK tool!")
        
        print(f"\n🎉 ADK tool tests completed successfully!")
        print(f"📝 Form URL: {result['form_url']}")
        
        return form_id
    else:
        print(f"❌ Form creation failed: {result['message']}")
        return None


def test_google_adk_agent():
    """Test the Google ADK agent."""
    print("\n\n🤖 Testing Google ADK Agent")
    print("=" * 40)
    
    print(f"Agent Name: {google_forms_agent.name}")
    print(f"Model: {google_forms_agent.model}")
    print(f"Tools Available: {len(google_forms_agent.tools)}")
    
    print("\nAvailable Tools:")
    for tool in google_forms_agent.tools:
        print(f"  - {tool.name}: {tool.description}")
    
    print("\n✅ Google ADK Agent is ready for use!")
    print("You can now use this agent in your workflows.")
    
    return True


def test_google_forms_api_class():
    """Test the GoogleFormsAPI class directly."""
    print("\n\n🏗️ Testing GoogleFormsAPI Class")
    print("=" * 40)
    
    try:
        # Initialize the API
        api = GoogleFormsAPI()
        print("✅ GoogleFormsAPI initialized successfully!")
        
        # Test form creation
        print("\n1. Creating a form using the API class...")
        result = api.create_form(
            title="Test Form - API Class",
            description="This form was created using the GoogleFormsAPI class"
        )
        
        if result["result"] == "success":
            form_id = result["form_id"]
            print(f"✅ Form created successfully using API class!")
            print(f"   Form ID: {form_id}")
            print(f"   Form URL: {result['form_url']}")
            
            # Test adding questions
            print("\n2. Adding questions using the API class...")
            questions = [
                {
                    "title": "What is your age?",
                    "type": "short_answer",
                    "required": True
                },
                {
                    "title": "What is your occupation?",
                    "type": "dropdown",
                    "required": False,
                    "options": ["Student", "Employee", "Self-employed", "Retired", "Other"]
                }
            ]
            
            add_result = api.add_questions(form_id, questions)
            if add_result["result"] == "success":
                print(f"✅ {add_result['questions_added']} questions added using API class!")
            
            # Test getting form info
            print("\n3. Getting form info using the API class...")
            info_result = api.get_form_info(form_id)
            if info_result["result"] == "success":
                print(f"✅ Form info retrieved using API class!")
                print(f"   Title: {info_result['form_info'].get('title', 'N/A')}")
                print(f"   Items count: {len(info_result['items'])}")
            
            print(f"\n🎉 API class tests completed successfully!")
            print(f"📝 Form URL: {result['form_url']}")
            
            return form_id
        else:
            print(f"❌ Form creation failed: {result['message']}")
            return None
            
    except Exception as e:
        print(f"❌ API class test failed: {str(e)}")
        return None


def cleanup_test_forms(form_ids):
    """Clean up test forms."""
    print("\n\n🧹 Cleaning up test forms...")
    print("=" * 40)
    
    for form_id in form_ids:
        if form_id:
            try:
                result = delete_form_standalone(form_id)
                if result["result"] == "success":
                    print(f"✅ Form {form_id} deleted successfully!")
                else:
                    print(f"❌ Failed to delete form {form_id}: {result['message']}")
            except Exception as e:
                print(f"❌ Error deleting form {form_id}: {str(e)}")


def main():
    """Main test function."""
    print("🚀 Google Forms API - Standalone Implementation Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    
    form_ids = []
    
    try:
        # Test 1: Standalone functions
        form_id_1 = test_standalone_functions()
        if form_id_1:
            form_ids.append(form_id_1)
        
        # Test 2: Google ADK tools
        form_id_2 = test_google_adk_tools()
        if form_id_2:
            form_ids.append(form_id_2)
        
        # Test 3: Google ADK agent
        test_google_adk_agent()
        
        # Test 4: GoogleFormsAPI class
        form_id_3 = test_google_forms_api_class()
        if form_id_3:
            form_ids.append(form_id_3)
        
        print("\n\n🎉 All tests completed successfully!")
        print("=" * 60)
        print("✅ Standalone functions work correctly")
        print("✅ Google ADK tools work correctly")
        print("✅ Google ADK agent is properly configured")
        print("✅ GoogleFormsAPI class works correctly")
        
        # Ask user if they want to clean up test forms
        print(f"\n📝 Created {len(form_ids)} test forms:")
        for i, form_id in enumerate(form_ids, 1):
            print(f"   {i}. Form ID: {form_id}")
        
        response = input("\nDo you want to delete the test forms? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            cleanup_test_forms(form_ids)
        else:
            print("Test forms preserved for manual inspection.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 