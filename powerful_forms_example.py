#!/usr/bin/env python3
"""
Powerful Google Forms Example

This script demonstrates the enhanced Google Forms Agent capabilities including:
- Quiz creation with grading
- Advanced question types (grids, date/time, file upload)
- Media integration (images, videos)
- Form sections and page breaks
- Advanced form settings
- Comprehensive form validation

Based on the Google Forms API documentation and enhanced agent tools.
"""

import json
from forms_agent.subagents.form_creator.agent import form_creator_agent
from forms_agent.subagents.form_validator.agent import form_validator_agent
from forms_agent.subagents.document_parser.agent import document_parser_agent
from forms_agent.subagents.form_editor.agent import form_editor_agent


def create_advanced_quiz():
    """Create a comprehensive quiz with advanced features."""
    
    # Step 1: Create a quiz form
    quiz_creation_result = form_creator_agent.run({
        "title": "Advanced Science Quiz",
        "description": "A comprehensive quiz covering various scientific topics with multimedia content and advanced question types.",
        "form_type": "quiz"
    })
    
    if quiz_creation_result.get("status") != "success":
        print(f"Failed to create quiz: {quiz_creation_result.get('error_message')}")
        return
    
    form_id = quiz_creation_result["created_form"]["form_id"]
    print(f"✅ Created quiz form: {form_id}")
    
    # Step 2: Configure advanced quiz settings
    quiz_settings = {
        "is_quiz": True,
        "collect_email": True,
        "allow_response_editing": False,
        "confirmation_message": "Thank you for completing the quiz! Your responses have been recorded.",
        "is_published": True,
        "is_accepting_responses": True,
        "quiz_settings": {
            "pointValue": 10,
            "correctAnswers": {
                "answers": [{"value": "Correct Answer"}]
            },
            "whenRight": {"text": "Excellent! That's correct."},
            "whenWrong": {"text": "Not quite right. Keep studying!"}
        }
    }
    
    settings_result = form_creator_agent.run({
        "form_id": form_id,
        "settings": quiz_settings
    })
    
    if settings_result.get("status") == "success":
        print("✅ Applied advanced quiz settings")
    
    # Step 3: Add comprehensive questions with different types
    advanced_questions = [
        # Multiple choice with grading
        {
            "type": "multiple_choice",
            "question": "What is the chemical symbol for gold?",
            "options": ["Au", "Ag", "Fe", "Cu"],
            "required": True,
            "shuffle": True,
            "grading": {
                "pointValue": 5,
                "correctAnswers": {
                    "answers": [{"value": "Au"}]
                },
                "whenRight": {"text": "Correct! Au comes from the Latin word 'aurum'."},
                "whenWrong": {"text": "Incorrect. The symbol for gold is Au."}
            }
        },
        
        # Checkbox with multiple correct answers
        {
            "type": "checkbox",
            "question": "Which of the following are noble gases? (Select all that apply)",
            "options": ["Helium", "Neon", "Argon", "Oxygen", "Nitrogen"],
            "required": True,
            "shuffle": True,
            "grading": {
                "pointValue": 10,
                "correctAnswers": {
                    "answers": [{"value": "Helium"}, {"value": "Neon"}, {"value": "Argon"}]
                },
                "whenRight": {"text": "Perfect! All noble gases selected."},
                "whenWrong": {"text": "Remember: Noble gases are in Group 18 of the periodic table."}
            }
        },
        
        # Linear scale for rating
        {
            "type": "linear_scale",
            "question": "Rate your understanding of chemistry concepts (1 = Poor, 5 = Excellent)",
            "min_value": 1,
            "max_value": 5,
            "min_label": "Poor",
            "max_label": "Excellent",
            "required": True
        },
        
        # Multiple choice grid
        {
            "type": "multiple_choice_grid",
            "question": "Rate the following scientific fields:",
            "rows": ["Physics", "Chemistry", "Biology", "Mathematics"],
            "columns": ["Beginner", "Intermediate", "Advanced", "Expert"],
            "required": True,
            "shuffle": False
        },
        
        # Date question
        {
            "type": "date",
            "question": "When did you first become interested in science?",
            "required": False,
            "include_time": False,
            "include_year": True
        },
        
        # Time question
        {
            "type": "time",
            "question": "What time do you typically study science?",
            "required": False,
            "duration": False
        },
        
        # File upload
        {
            "type": "file_upload",
            "question": "Upload a diagram or image related to your favorite scientific concept:",
            "required": False,
            "max_files": 1,
            "max_file_size": 10485760,  # 10MB
            "allowed_file_types": ["image/jpeg", "image/png", "image/gif"]
        },
        
        # Short answer with grading
        {
            "type": "short_answer",
            "question": "What is the formula for calculating density?",
            "required": True,
            "grading": {
                "pointValue": 5,
                "correctAnswers": {
                    "answers": [{"value": "density = mass/volume"}, {"value": "d = m/v"}]
                },
                "whenRight": {"text": "Correct! Density equals mass divided by volume."},
                "whenWrong": {"text": "The formula is: density = mass/volume"}
            }
        },
        
        # Long answer
        {
            "type": "long_answer",
            "question": "Explain the scientific method and provide an example of how you would apply it to solve a problem:",
            "required": True
        }
    ]
    
    # Step 4: Add questions to the form
    questions_result = form_creator_agent.run({
        "form_id": form_id,
        "questions": advanced_questions
    })
    
    if questions_result.get("status") == "success":
        print(f"✅ Added {questions_result['question_count']} advanced questions")
    
    # Step 5: Add media content
    media_items = [
        {
            "type": "image",
            "title": "Periodic Table",
            "description": "The modern periodic table of elements",
            "content_uri": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Periodic_table_%28polyatomic%29.svg/1200px-Periodic_table_%28polyatomic%29.svg.png",
            "alignment": "CENTER",
            "width": 800,
            "height": 400
        },
        {
            "type": "video",
            "title": "Introduction to Chemistry",
            "description": "A brief overview of chemistry fundamentals",
            "youtube_uri": "https://www.youtube.com/watch?v=7DjsD7Hcd9U"
        }
    ]
    
    media_result = form_creator_agent.run({
        "form_id": form_id,
        "media_items": media_items
    })
    
    if media_result.get("status") == "success":
        print(f"✅ Added {media_result['media_count']} media items")
    
    # Step 6: Add form sections
    sections = [
        {
            "title": "Basic Chemistry",
            "description": "Questions about fundamental chemistry concepts",
            "navigation_type": "CONTINUE"
        },
        {
            "title": "Advanced Topics",
            "description": "More challenging questions for advanced students",
            "navigation_type": "CONTINUE"
        }
    ]
    
    sections_result = form_creator_agent.run({
        "form_id": form_id,
        "sections": sections
    })
    
    if sections_result.get("status") == "success":
        print(f"✅ Added {sections_result['section_count']} form sections")
    
    print(f"\n🎉 Advanced quiz created successfully!")
    print(f"Form URL: {quiz_creation_result['created_form']['form_url']}")
    print(f"Responder URL: {quiz_creation_result['created_form']['responder_url']}")
    
    return form_id


def create_survey_with_advanced_features():
    """Create a comprehensive survey with advanced features."""
    
    # Step 1: Create a survey form
    survey_creation_result = form_creator_agent.run({
        "title": "Employee Satisfaction Survey",
        "description": "A comprehensive survey to gather feedback on workplace satisfaction and improvement opportunities.",
        "form_type": "form"
    })
    
    if survey_creation_result.get("status") != "success":
        print(f"Failed to create survey: {survey_creation_result.get('error_message')}")
        return
    
    form_id = survey_creation_result["created_form"]["form_id"]
    print(f"✅ Created survey form: {form_id}")
    
    # Step 2: Configure survey settings
    survey_settings = {
        "collect_email": True,
        "allow_response_editing": True,
        "confirmation_message": "Thank you for your valuable feedback! Your responses will help us improve the workplace.",
        "is_published": True,
        "is_accepting_responses": True
    }
    
    settings_result = form_creator_agent.run({
        "form_id": form_id,
        "settings": survey_settings
    })
    
    if settings_result.get("status") == "success":
        print("✅ Applied survey settings")
    
    # Step 3: Add survey questions
    survey_questions = [
        # Dropdown for department selection
        {
            "type": "dropdown",
            "question": "Which department do you work in?",
            "options": ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "Other"],
            "required": True
        },
        
        # Linear scale for satisfaction
        {
            "type": "linear_scale",
            "question": "How satisfied are you with your current role?",
            "min_value": 1,
            "max_value": 10,
            "min_label": "Very Dissatisfied",
            "max_label": "Very Satisfied",
            "required": True
        },
        
        # Checkbox grid for benefits
        {
            "type": "checkbox_grid",
            "question": "Which benefits are most important to you?",
            "rows": ["Health Insurance", "Dental Insurance", "401(k)", "Paid Time Off", "Remote Work", "Professional Development"],
            "columns": ["Not Important", "Somewhat Important", "Very Important", "Critical"],
            "required": True
        },
        
        # Date question
        {
            "type": "date",
            "question": "When did you start working at this company?",
            "required": False,
            "include_time": False,
            "include_year": True
        },
        
        # Time question
        {
            "type": "time",
            "question": "What time do you typically start your workday?",
            "required": False,
            "duration": False
        },
        
        # Short answer
        {
            "type": "short_answer",
            "question": "What is one thing that would make your job more enjoyable?",
            "required": False
        },
        
        # Long answer
        {
            "type": "long_answer",
            "question": "Please provide any additional comments or suggestions for improving the workplace:",
            "required": False
        }
    ]
    
    # Step 4: Add questions to the form
    questions_result = form_creator_agent.run({
        "form_id": form_id,
        "questions": survey_questions
    })
    
    if questions_result.get("status") == "success":
        print(f"✅ Added {questions_result['question_count']} survey questions")
    
    print(f"\n🎉 Survey created successfully!")
    print(f"Form URL: {survey_creation_result['created_form']['form_url']}")
    print(f"Responder URL: {survey_creation_result['created_form']['responder_url']}")
    
    return form_id


def validate_and_enhance_form(form_structure):
    """Validate a form structure and enhance it with advanced features."""
    
    # Step 1: Validate the form structure
    validation_result = form_validator_agent.run({
        "form_structure": form_structure
    })
    
    if validation_result.get("status") != "success":
        print(f"Form validation failed: {validation_result.get('error_message')}")
        return
    
    validation = validation_result["validation"]
    print(f"✅ Form validation: {validation['summary']}")
    
    if not validation["is_valid"]:
        print("Issues found:")
        for issue in validation["issues"]:
            print(f"  - {issue}")
    
    # Step 2: Check and convert question types
    questions = form_structure.get("questions", [])
    type_analysis_result = form_validator_agent.run({
        "questions": questions
    })
    
    if type_analysis_result.get("status") == "success":
        analysis = type_analysis_result["type_analysis"]
        summary = type_analysis_result["summary"]
        
        print(f"\n📊 Question Type Analysis:")
        print(f"  - Total questions: {summary['total_questions']}")
        print(f"  - Supported: {summary['supported']}")
        print(f"  - Needs conversion: {summary['needs_conversion']}")
        print(f"  - Unsupported: {summary['unsupported']}")
        
        if analysis["conversion_needed"]:
            print("\n🔄 Conversions needed:")
            for conv in analysis["conversion_needed"]:
                print(f"  - {conv['original_type']} → {conv['suggested_type']}")
        
        if analysis["unsupported"]:
            print("\n❌ Unsupported types:")
            for unsup in analysis["unsupported"]:
                print(f"  - {unsup['type']}: {unsup['question']}")
    
    return type_analysis_result.get("converted_questions", questions)


def main():
    """Main function to demonstrate powerful forms creation."""
    
    print("🚀 Google Forms Agent - Powerful Forms Example")
    print("=" * 50)
    
    # Example 1: Create an advanced quiz
    print("\n📚 Creating Advanced Science Quiz...")
    quiz_form_id = create_advanced_quiz()
    
    # Example 2: Create a survey with advanced features
    print("\n📊 Creating Employee Satisfaction Survey...")
    survey_form_id = create_survey_with_advanced_features()
    
    # Example 3: Validate and enhance a form structure
    print("\n🔍 Validating and Enhancing Form Structure...")
    
    sample_form_structure = {
        "title": "Sample Form",
        "description": "A sample form for validation testing",
        "questions": [
            {
                "type": "multiple_choice",
                "question": "What is your favorite color?",
                "options": ["Red", "Blue", "Green", "Yellow"],
                "required": True
            },
            {
                "type": "text",  # This will need conversion
                "question": "Tell us about yourself:",
                "required": False
            },
            {
                "type": "rating",  # This will need conversion
                "question": "Rate your experience:",
                "required": True
            }
        ]
    }
    
    enhanced_questions = validate_and_enhance_form(sample_form_structure)
    
    print(f"\n✅ Enhanced questions: {len(enhanced_questions)}")
    for i, question in enumerate(enhanced_questions):
        print(f"  {i+1}. {question['type']}: {question['question']}")
    
    print("\n🎉 All examples completed successfully!")
    print("\nKey Features Demonstrated:")
    print("  ✅ Quiz creation with grading")
    print("  ✅ Advanced question types (grids, date/time, file upload)")
    print("  ✅ Media integration (images, videos)")
    print("  ✅ Form sections and page breaks")
    print("  ✅ Comprehensive form validation")
    print("  ✅ Question type conversion")
    print("  ✅ Advanced form settings")


if __name__ == "__main__":
    main() 