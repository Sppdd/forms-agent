#!/usr/bin/env python3
"""
Test Enhanced Google Forms Features

This script tests the enhanced Google Forms Agent capabilities to ensure
all new features are working correctly.
"""

import json
from forms_agent.subagents.form_creator.tools import (
    create_google_form, 
    setup_form_settings, 
    add_questions_to_form,
    add_media_to_form,
    create_form_sections
)
from forms_agent.subagents.form_validator.tools import (
    validate_form_structure,
    check_question_types
)


def test_form_creation():
    """Test enhanced form creation with quiz support."""
    print("🧪 Testing Enhanced Form Creation...")
    
    # Test quiz form creation
    result = create_google_form(
        title="Test Quiz",
        description="A test quiz to verify enhanced features",
        form_type="quiz"
    )
    
    if result["status"] == "success":
        print("✅ Quiz form creation: PASSED")
        form_id = result["form_id"]
        return form_id
    else:
        print(f"❌ Quiz form creation: FAILED - {result['error_message']}")
        return None


def test_advanced_settings(form_id):
    """Test advanced form settings configuration."""
    print("🧪 Testing Advanced Settings...")
    
    settings = {
        "is_quiz": True,
        "collect_email": True,
        "allow_response_editing": False,
        "confirmation_message": "Test confirmation message",
        "is_published": True,
        "is_accepting_responses": True
    }
    
    result = setup_form_settings(form_id, settings)
    
    if result["status"] == "success":
        print("✅ Advanced settings: PASSED")
        return True
    else:
        print(f"❌ Advanced settings: FAILED - {result['error_message']}")
        return False


def test_advanced_questions(form_id):
    """Test advanced question types."""
    print("🧪 Testing Advanced Question Types...")
    
    questions = [
        # Multiple choice with grading
        {
            "type": "multiple_choice",
            "question": "Test multiple choice question?",
            "options": ["Option A", "Option B", "Option C"],
            "required": True,
            "shuffle": True,
            "grading": {
                "pointValue": 5,
                "correctAnswers": {"answers": [{"value": "Option A"}]},
                "whenRight": {"text": "Correct!"},
                "whenWrong": {"text": "Wrong!"}
            }
        },
        
        # Linear scale
        {
            "type": "linear_scale",
            "question": "Rate this test (1-5):",
            "min_value": 1,
            "max_value": 5,
            "min_label": "Poor",
            "max_label": "Excellent",
            "required": True
        },
        
        # Date question
        {
            "type": "date",
            "question": "When is your birthday?",
            "required": False,
            "include_time": False,
            "include_year": True
        },
        
        # File upload
        {
            "type": "file_upload",
            "question": "Upload a test file:",
            "required": False,
            "max_files": 1,
            "max_file_size": 10485760
        }
    ]
    
    result = add_questions_to_form(form_id, questions)
    
    if result["status"] == "success":
        print(f"✅ Advanced questions: PASSED ({result['question_count']} questions added)")
        return True
    else:
        print(f"❌ Advanced questions: FAILED - {result['error_message']}")
        return False


def test_media_integration(form_id):
    """Test media integration features."""
    print("🧪 Testing Media Integration...")
    
    media_items = [
        {
            "type": "image",
            "title": "Test Image",
            "description": "A test image for verification",
            "content_uri": "https://via.placeholder.com/400x300",
            "alignment": "CENTER",
            "width": 400,
            "height": 300
        }
    ]
    
    result = add_media_to_form(form_id, media_items)
    
    if result["status"] == "success":
        print(f"✅ Media integration: PASSED ({result['media_count']} items added)")
        return True
    else:
        print(f"❌ Media integration: FAILED - {result['error_message']}")
        return False


def test_form_sections(form_id):
    """Test form sections and page breaks."""
    print("🧪 Testing Form Sections...")
    
    sections = [
        {
            "title": "Test Section 1",
            "description": "First test section",
            "navigation_type": "CONTINUE"
        },
        {
            "title": "Test Section 2", 
            "description": "Second test section",
            "navigation_type": "CONTINUE"
        }
    ]
    
    result = create_form_sections(form_id, sections)
    
    if result["status"] == "success":
        print(f"✅ Form sections: PASSED ({result['section_count']} sections added)")
        return True
    else:
        print(f"❌ Form sections: FAILED - {result['error_message']}")
        return False


def test_form_validation():
    """Test enhanced form validation."""
    print("🧪 Testing Form Validation...")
    
    # Test form structure validation
    form_structure = {
        "title": "Test Form",
        "description": "A test form for validation",
        "questions": [
            {
                "type": "multiple_choice",
                "question": "Test question?",
                "options": ["A", "B", "C"],
                "required": True
            }
        ]
    }
    
    result = validate_form_structure(form_structure)
    
    if result["status"] == "success":
        validation = result["validation"]
        if validation["is_valid"]:
            print("✅ Form structure validation: PASSED")
        else:
            print(f"⚠️ Form structure validation: WARNINGS - {validation['issues']}")
    else:
        print(f"❌ Form structure validation: FAILED - {result['error_message']}")
        return False
    
    # Test question type validation
    questions = [
        {"type": "multiple_choice", "question": "MC Question", "options": ["A", "B"]},
        {"type": "text", "question": "Text Question"},  # Will need conversion
        {"type": "rating", "question": "Rating Question"}  # Will need conversion
    ]
    
    type_result = check_question_types(questions)
    
    if type_result["status"] == "success":
        summary = type_result["summary"]
        print(f"✅ Question type validation: PASSED")
        print(f"   - Supported: {summary['supported']}")
        print(f"   - Needs conversion: {summary['needs_conversion']}")
        print(f"   - Unsupported: {summary['unsupported']}")
        return True
    else:
        print(f"❌ Question type validation: FAILED - {type_result['error_message']}")
        return False


def main():
    """Run all enhanced feature tests."""
    print("🚀 Testing Enhanced Google Forms Features")
    print("=" * 50)
    
    test_results = []
    
    # Test 1: Form Creation
    form_id = test_form_creation()
    test_results.append(("Form Creation", form_id is not None))
    
    if form_id:
        # Test 2: Advanced Settings
        test_results.append(("Advanced Settings", test_advanced_settings(form_id)))
        
        # Test 3: Advanced Questions
        test_results.append(("Advanced Questions", test_advanced_questions(form_id)))
        
        # Test 4: Media Integration
        test_results.append(("Media Integration", test_media_integration(form_id)))
        
        # Test 5: Form Sections
        test_results.append(("Form Sections", test_form_sections(form_id)))
    
    # Test 6: Form Validation (doesn't require form_id)
    test_results.append(("Form Validation", test_form_validation()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All enhanced features are working correctly!")
    else:
        print("⚠️ Some features need attention.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 