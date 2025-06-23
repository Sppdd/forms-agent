#!/usr/bin/env python3
"""
Quick Form Access Utility

Simple utility for quickly accessing and managing Google Forms.
"""

import sys
import os

# Add the forms_agent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'forms_agent'))

def quick_form_list():
    """Quickly list all forms with basic info."""
    try:
        from forms_agent.subagents.form_creator.tools import list_my_forms
        
        print("📋 Your Google Forms:")
        print("-" * 40)
        
        result = list_my_forms()
        if result["status"] == "success":
            forms = result["forms"]
            if not forms:
                print("No forms found.")
                return
            
            for i, form in enumerate(forms, 1):
                print(f"{i:2d}. {form['title']}")
                print(f"     ID: {form['form_id']}")
                print(f"     📅 {form['created_time'][:10]}")
                print(f"     🔗 {form['edit_url']}")
                print()
        else:
            print(f"Error: {result['error_message']}")
            
    except Exception as e:
        print(f"Error: {e}")

def get_form_by_id(form_id):
    """Get details for a specific form by ID."""
    try:
        from forms_agent.subagents.form_creator.tools import get_form_details
        
        print(f"🔍 Form Details for ID: {form_id}")
        print("-" * 40)
        
        result = get_form_details(form_id)
        if result["status"] == "success":
            form_info = result["form_info"]
            print(f"Title: {form_info.get('title', 'Untitled')}")
            print(f"Description: {form_info.get('description', 'No description')}")
            print(f"Items: {result['item_count']}")
            print(f"Is Quiz: {result['is_quiz']}")
            print(f"Created: {result['created_time'][:10]}")
            print(f"Edit URL: {result['edit_url']}")
            print(f"Responder URL: {result['responder_url']}")
            
            if result['questions']:
                print(f"\nQuestions:")
                for i, q in enumerate(result['questions'], 1):
                    print(f"  {i}. {q['title']} ({q['type']})")
        else:
            print(f"Error: {result['error_message']}")
            
    except Exception as e:
        print(f"Error: {e}")

def create_quick_form(title, description=None):
    """Quickly create a simple form."""
    try:
        from forms_agent.subagents.form_creator.tools import create_google_form
        
        print(f"📝 Creating form: {title}")
        print("-" * 40)
        
        result = create_google_form(title, description)
        if result["status"] == "success":
            print(f"✅ Form created successfully!")
            print(f"Form ID: {result['form_id']}")
            print(f"Edit URL: {result['form_url']}")
            print(f"Responder URL: {result['responder_url']}")
        else:
            print(f"Error: {result['error_message']}")
            
    except Exception as e:
        print(f"Error: {e}")

def show_help():
    """Show usage help."""
    print("🔧 Quick Form Access Utility")
    print("=" * 30)
    print("Usage:")
    print("  python quick_form_access.py list                    - List all forms")
    print("  python quick_form_access.py details <form_id>       - Get form details")
    print("  python quick_form_access.py create <title> [desc]   - Create new form")
    print("  python quick_form_access.py help                    - Show this help")
    print()
    print("Examples:")
    print("  python quick_form_access.py list")
    print("  python quick_form_access.py details 1mWV3aXyB1q2tXok-PBvKm_Zit9Hlcofi0Cw81ccoNzE")
    print("  python quick_form_access.py create \"My Survey\" \"A simple survey\"")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        quick_form_list()
    elif command == "details" and len(sys.argv) >= 3:
        get_form_by_id(sys.argv[2])
    elif command == "create" and len(sys.argv) >= 3:
        title = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) >= 4 else None
        create_quick_form(title, description)
    elif command == "help":
        show_help()
    else:
        print("Invalid command. Use 'help' for usage information.")
        sys.exit(1) 