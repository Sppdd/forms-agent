#!/usr/bin/env python3
"""
Google Forms Drive Management Example

This script demonstrates how to:
1. List all your Google Forms
2. Create folders to organize forms
3. Move forms to specific folders
4. Get detailed information about forms
5. Access and manage forms in Google Drive
"""

import sys
import os

# Add the forms_agent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'forms_agent'))

def demonstrate_form_management():
    """Demonstrate comprehensive form management capabilities."""
    try:
        from forms_agent.subagents.form_creator.tools import (
            list_my_forms, 
            create_forms_folder, 
            move_form_to_folder, 
            get_form_details,
            create_google_form,
            add_questions_to_form
        )
        
        print("🚀 Google Forms Drive Management Demo")
        print("=" * 50)
        
        # Step 1: List all existing forms
        print("\n📋 Step 1: Listing all your Google Forms...")
        forms_result = list_my_forms()
        
        if forms_result["status"] == "success":
            forms = forms_result["forms"]
            print(f"✅ Found {forms_result['total_count']} forms:")
            
            for i, form in enumerate(forms[:5], 1):  # Show first 5 forms
                print(f"  {i}. {form['title']} (ID: {form['form_id'][:20]}...)")
                print(f"     📅 Created: {form['created_time'][:10]}")
                print(f"     📝 Items: {form.get('item_count', 'N/A')}")
                print(f"     🔗 Edit URL: {form['edit_url']}")
                print()
        else:
            print(f"❌ Error listing forms: {forms_result['error_message']}")
            return
        
        # Step 2: Create a folder for organizing forms
        print("\n📁 Step 2: Creating a folder for form organization...")
        folder_result = create_forms_folder("My Forms Collection")
        
        if folder_result["status"] == "success":
            folder_id = folder_result["folder_id"]
            folder_name = folder_result["folder_name"]
            folder_url = folder_result["folder_url"]
            print(f"✅ Created folder: {folder_name}")
            print(f"   📁 Folder ID: {folder_id}")
            print(f"   🔗 Folder URL: {folder_url}")
        else:
            print(f"❌ Error creating folder: {folder_result['error_message']}")
            return
        
        # Step 3: Create a new form to demonstrate organization
        print("\n📝 Step 3: Creating a new form for demonstration...")
        form_result = create_google_form(
            title="Customer Feedback Survey",
            description="A comprehensive survey to gather customer feedback and improve our services."
        )
        
        if form_result["status"] == "success":
            form_id = form_result["form_id"]
            form_url = form_result["form_url"]
            print(f"✅ Created form: {form_result['form_info'].get('title', 'Untitled')}")
            print(f"   🆔 Form ID: {form_id}")
            print(f"   🔗 Edit URL: {form_url}")
            
            # Add some sample questions
            print("\n📝 Adding sample questions to the form...")
            questions = [
                {
                    "type": "multiple_choice",
                    "question": "How satisfied are you with our service?",
                    "required": True,
                    "options": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"]
                },
                {
                    "type": "text",
                    "question": "What suggestions do you have for improvement?",
                    "required": False
                },
                {
                    "type": "checkbox",
                    "question": "Which features do you use most?",
                    "required": True,
                    "options": ["Feature A", "Feature B", "Feature C", "Feature D"]
                }
            ]
            
            questions_result = add_questions_to_form(form_id, questions)
            if questions_result["status"] == "success":
                print(f"✅ Added {len(questions)} questions to the form")
            else:
                print(f"⚠️ Warning: Could not add questions: {questions_result['error_message']}")
            
        else:
            print(f"❌ Error creating form: {form_result['error_message']}")
            return
        
        # Step 4: Move the form to the organized folder
        print(f"\n📂 Step 4: Moving form to the '{folder_name}' folder...")
        move_result = move_form_to_folder(form_id, folder_id)
        
        if move_result["status"] == "success":
            print(f"✅ Successfully moved form to folder")
            print(f"   📁 Destination: {folder_name}")
        else:
            print(f"❌ Error moving form: {move_result['error_message']}")
        
        # Step 5: Get detailed information about the form
        print(f"\n🔍 Step 5: Getting detailed information about the form...")
        details_result = get_form_details(form_id)
        
        if details_result["status"] == "success":
            form_info = details_result["form_info"]
            questions = details_result["questions"]
            
            print(f"✅ Form Details:")
            print(f"   📝 Title: {form_info.get('title', 'Untitled')}")
            print(f"   📄 Description: {form_info.get('description', 'No description')}")
            print(f"   📊 Total Items: {details_result['item_count']}")
            print(f"   🎯 Is Quiz: {details_result['is_quiz']}")
            print(f"   📅 Created: {details_result['created_time'][:10]}")
            print(f"   🔗 Responder URL: {details_result['responder_url']}")
            
            print(f"\n📝 Questions in the form:")
            for i, question in enumerate(questions, 1):
                print(f"   {i}. {question['title']} ({question['type']})")
        
        else:
            print(f"❌ Error getting form details: {details_result['error_message']}")
        
        # Step 6: List forms again to show the updated organization
        print(f"\n📋 Step 6: Listing forms again to show updated organization...")
        updated_forms_result = list_my_forms()
        
        if updated_forms_result["status"] == "success":
            updated_forms = updated_forms_result["forms"]
            print(f"✅ Updated form count: {updated_forms_result['total_count']} forms")
            
            # Find our newly created form
            new_form = None
            for form in updated_forms:
                if form['form_id'] == form_id:
                    new_form = form
                    break
            
            if new_form:
                print(f"✅ Our new form is now organized:")
                print(f"   📝 Title: {new_form['title']}")
                print(f"   📅 Created: {new_form['created_time'][:10]}")
                print(f"   📊 Items: {new_form.get('item_count', 'N/A')}")
        
        print(f"\n🎉 Form Management Demo Complete!")
        print(f"📚 Summary of what you can do:")
        print(f"   • List all your forms: list_my_forms()")
        print(f"   • Create organized folders: create_forms_folder(folder_name)")
        print(f"   • Move forms to folders: move_form_to_folder(form_id, folder_id)")
        print(f"   • Get form details: get_form_details(form_id)")
        print(f"   • Create new forms: create_google_form(title, description)")
        print(f"   • Add questions: add_questions_to_form(form_id, questions)")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory.")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

def show_form_access_methods():
    """Show different ways to access and manage forms."""
    print("\n🔗 Form Access Methods:")
    print("=" * 30)
    
    print("1. 📋 List All Forms:")
    print("   list_my_forms() - Get all forms you have access to")
    
    print("\n2. 🔍 Get Specific Form Details:")
    print("   get_form_details(form_id) - Get comprehensive form information")
    
    print("\n3. 📁 Organize Forms in Drive:")
    print("   create_forms_folder(folder_name) - Create a new folder")
    print("   move_form_to_folder(form_id, folder_id) - Move form to folder")
    
    print("\n4. 📝 Create New Forms:")
    print("   create_google_form(title, description) - Create a new form")
    print("   add_questions_to_form(form_id, questions) - Add questions")
    
    print("\n5. 🔗 Direct URLs:")
    print("   Edit URL: https://docs.google.com/forms/d/{form_id}/edit")
    print("   Responder URL: https://docs.google.com/forms/d/e/{form_id}/viewform")
    print("   Drive URL: https://drive.google.com/drive/folders/{folder_id}")

if __name__ == "__main__":
    demonstrate_form_management()
    show_form_access_methods() 