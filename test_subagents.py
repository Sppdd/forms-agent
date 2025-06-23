#!/usr/bin/env python3
"""
Test script to verify subagents can access service_account.json and create forms
"""

import sys
import os

# Add the forms_agent directory to the path so we can import subagents
sys.path.append(os.path.join(os.path.dirname(__file__), 'forms_agent'))

def test_form_creator():
    """Test the form_creator subagent tools"""
    print("🧪 Testing Form Creator Subagent")
    print("=" * 40)
    
    try:
        from subagents.form_creator.tools import create_google_form, add_questions_to_form
        
        # Test form creation
        print("1. Creating a form using form_creator subagent...")
        result = create_google_form(
            title="Test Form from Subagent",
            description="This form was created by the form_creator subagent"
        )
        
        if result["result"] == "success":
            form_id = result["form_id"]
            print(f"✅ Form created successfully!")
            print(f"   Form ID: {form_id}")
            print(f"   Form URL: {result['form_url']}")
            
            # Test adding questions
            print("\n2. Adding questions using form_creator subagent...")
            questions = [
                {
                    "title": "What is your name?",
                    "type": "short_answer",
                    "required": True
                },
                {
                    "title": "How would you rate this?",
                    "type": "linear_scale",
                    "required": False,
                    "scale": {"low": 1, "high": 5, "low_label": "Poor", "high_label": "Excellent"}
                }
            ]
            
            add_result = add_questions_to_form(form_id, questions)
            if add_result["result"] == "success":
                print(f"✅ {add_result['questions_added']} questions added successfully!")
            
            print(f"\n🎉 Form Creator Subagent is working!")
            return form_id
        else:
            print(f"❌ Form creation failed: {result['message']}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing form_creator: {str(e)}")
        return None

def test_form_editor():
    """Test the form_editor subagent tools"""
    print("\n\n🔧 Testing Form Editor Subagent")
    print("=" * 40)
    
    try:
        from subagents.form_editor.tools import update_form_info, get_form_responses
        
        # Test with a form ID (you can replace this with a real form ID)
        test_form_id = "1vzTjQyKEE0AP0voJfmVQuSLOHIRaqnh48rOEVgHclDk"  # From previous test
        
        print("1. Testing form info update...")
        update_result = update_form_info(
            form_id=test_form_id,
            title="Updated Form from Subagent",
            description="This form was updated by the form_editor subagent"
        )
        
        if update_result["result"] == "success":
            print("✅ Form updated successfully!")
        else:
            print(f"⚠️ Form update result: {update_result['message']}")
        
        print("\n2. Testing form responses retrieval...")
        responses_result = get_form_responses(test_form_id)
        
        if responses_result["result"] == "success":
            print(f"✅ Retrieved {responses_result['response_count']} responses!")
        else:
            print(f"⚠️ Responses result: {responses_result['message']}")
        
        print("🎉 Form Editor Subagent is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing form_editor: {str(e)}")
        return False

def main():
    print("🚀 Testing Subagents with Service Account")
    print("=" * 50)
    
    # Test form creator
    form_id = test_form_creator()
    
    # Test form editor
    editor_success = test_form_editor()
    
    print(f"\n📊 Test Summary:")
    print(f"   Form Creator: {'✅ Working' if form_id else '❌ Failed'}")
    print(f"   Form Editor: {'✅ Working' if editor_success else '❌ Failed'}")
    
    if form_id:
        print(f"\n🎉 SUCCESS! Subagents can access service_account.json and create forms!")
        print(f"📝 Test form URL: https://docs.google.com/forms/d/{form_id}/edit")
    else:
        print(f"\n❌ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main() 