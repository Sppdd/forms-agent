"""
Form Validation Tools

This module provides tools for validating form structure and ensuring
compatibility with Google Forms API requirements.
"""

from typing import Any, Dict, List, Optional
import re

from google.adk.tools.tool_context import ToolContext


def validate_form_structure(form_structure: Dict[str, Any], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Validate the overall form structure for Google Forms compatibility.
    
    Use this tool when you need to validate a form structure before creating or editing a Google Form.
    This tool checks for required fields, character limits, question counts, and overall structure validity.
    
    Args:
        form_structure: The extracted form structure containing title, description, and questions
        
    Returns:
        A dictionary containing validation results with the following structure:
        - status: 'success' or 'error'
        - validation: Dictionary with is_valid (bool), issues (list), warnings (list), question_count (int)
        - summary: Human-readable summary of validation results
        - error_message: Present only if status is 'error'
    """
    try:
        issues = []
        warnings = []
        
        # Check required fields
        if not form_structure.get("title"):
            issues.append("Form title is required")
        elif len(form_structure["title"]) > 300:
            issues.append("Form title exceeds 300 character limit")
        
        if not form_structure.get("description"):
            warnings.append("Form description is recommended for better user experience")
        elif len(form_structure["description"]) > 4096:
            issues.append("Form description exceeds 4096 character limit")
        
        # Check questions
        questions = form_structure.get("questions", [])
        if not questions:
            issues.append("Form must have at least one question")
        elif len(questions) > 100:
            issues.append("Form exceeds maximum of 100 questions")
        
        # Validate individual questions
        question_validation = _validate_questions(questions)
        issues.extend(question_validation["issues"])
        warnings.extend(question_validation["warnings"])
        
        # Check for duplicates
        question_texts = [q.get("question", "") for q in questions]
        duplicates = _find_duplicates(question_texts)
        if duplicates:
            warnings.append(f"Duplicate questions found: {duplicates}")
        
        # Overall validation status
        is_valid = len(issues) == 0
        
        # Store validation results in session state if tool_context is available
        validation_result = {
            "is_valid": is_valid,
            "issues": issues,
            "warnings": warnings,
            "question_count": len(questions),
            "validated_structure": form_structure if is_valid else None
        }
        
        if tool_context:
            tool_context.state["validation_result"] = validation_result
        
        return {
            "status": "success",
            "validation": validation_result,
            "summary": f"{'Valid' if is_valid else 'Invalid'} form with {len(issues)} issues and {len(warnings)} warnings"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Validation failed: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def check_question_types(questions: List[Dict[str, Any]], tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Check if question types are supported by Google Forms and convert them to compatible formats.
    
    Use this tool when you have questions that need to be validated for Google Forms compatibility.
    This tool analyzes question types, suggests conversions for unsupported types, and provides
    converted questions ready for Google Forms creation.
    
    Args:
        questions: List of question dictionaries, each containing type, question text, and options
        
    Returns:
        A dictionary containing question type analysis with the following structure:
        - status: 'success' or 'error'
        - type_analysis: Dictionary with supported, unsupported, and conversion_needed lists
        - converted_questions: List of questions converted to Google Forms format
        - summary: Dictionary with counts of total, supported, needs_conversion, and unsupported questions
        - error_message: Present only if status is 'error'
    """
    try:
        supported_types = {
            "multiple_choice": "MULTIPLE_CHOICE",
            "short_answer": "SHORT_ANSWER", 
            "long_answer": "PARAGRAPH",
            "checkbox": "CHECKBOX",
            "dropdown": "DROP_DOWN",
            "linear_scale": "LINEAR_SCALE",
            "multiple_choice_grid": "MULTIPLE_CHOICE_GRID",
            "checkbox_grid": "CHECKBOX_GRID",
            "date": "DATE",
            "time": "TIME",
            "file_upload": "FILE_UPLOAD"
        }
        
        type_analysis = {
            "supported": [],
            "unsupported": [],
            "conversion_needed": []
        }
        
        converted_questions = []
        
        for i, question in enumerate(questions):
            question_type = question.get("type", "").lower()
            question_text = question.get("question", f"Question {i+1}")
            
            if question_type in supported_types:
                type_analysis["supported"].append({
                    "index": i,
                    "type": question_type,
                    "google_forms_type": supported_types[question_type]
                })
                
                # Convert to Google Forms format
                converted_question = _convert_to_google_forms_format(question, supported_types[question_type])
                converted_questions.append(converted_question)
                
            else:
                # Try to convert unsupported types
                converted_type = _suggest_type_conversion(question_type, question_text)
                if converted_type:
                    type_analysis["conversion_needed"].append({
                        "index": i,
                        "original_type": question_type,
                        "suggested_type": converted_type,
                        "google_forms_type": supported_types[converted_type]
                    })
                    
                    # Convert with suggested type
                    question_copy = question.copy()
                    question_copy["type"] = converted_type
                    converted_question = _convert_to_google_forms_format(question_copy, supported_types[converted_type])
                    converted_questions.append(converted_question)
                    
                else:
                    type_analysis["unsupported"].append({
                        "index": i,
                        "type": question_type,
                        "question": question_text
                    })
        
        # Store converted questions in session state if tool_context is available
        if tool_context:
            tool_context.state["converted_questions"] = converted_questions
            tool_context.state["type_analysis"] = type_analysis
        
        return {
            "status": "success",
            "type_analysis": type_analysis,
            "converted_questions": converted_questions,
            "summary": {
                "total_questions": len(questions),
                "supported": len(type_analysis["supported"]),
                "needs_conversion": len(type_analysis["conversion_needed"]),
                "unsupported": len(type_analysis["unsupported"])
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Question type validation failed: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _validate_questions(questions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Validate individual questions for structure and content."""
    issues = []
    warnings = []
    
    for i, question in enumerate(questions):
        question_text = question.get("question", "")
        question_type = question.get("type", "")
        
        # Check question text
        if not question_text or question_text.strip() == "":
            issues.append(f"Question {i+1}: Question text is required")
        elif len(question_text) > 4096:
            issues.append(f"Question {i+1}: Question text exceeds 4096 character limit")
        
        # Check question type
        if not question_type:
            issues.append(f"Question {i+1}: Question type is required")
        
        # Validate multiple choice options
        if question_type == "multiple_choice":
            options = question.get("options", [])
            if not options or len(options) < 2:
                issues.append(f"Question {i+1}: Multiple choice questions need at least 2 options")
            elif len(options) > 20:
                warnings.append(f"Question {i+1}: Many options ({len(options)}) may be overwhelming")
            
            # Check option text length
            for j, option in enumerate(options):
                if len(str(option)) > 1000:
                    issues.append(f"Question {i+1}, Option {j+1}: Option text exceeds 1000 character limit")
    
    return {"issues": issues, "warnings": warnings}


def _find_duplicates(items: List[str]) -> List[str]:
    """Find duplicate items in a list."""
    seen = set()
    duplicates = set()
    
    for item in items:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    
    return list(duplicates)


def _suggest_type_conversion(original_type: str, question_text: str) -> Optional[str]:
    """Suggest a supported question type for unsupported types."""
    question_lower = question_text.lower()
    
    # Type conversion mapping
    conversions = {
        "text": "short_answer",
        "textarea": "long_answer", 
        "number": "short_answer",
        "email": "short_answer",
        "url": "short_answer",
        "phone": "short_answer",
        "rating": "linear_scale",
        "scale": "linear_scale",
        "select": "dropdown",
        "radio": "multiple_choice",
        "multi_select": "checkbox"
    }
    
    # Check direct conversions
    if original_type in conversions:
        return conversions[original_type]
    
    # Content-based suggestions
    if any(word in question_lower for word in ["rate", "scale", "score"]):
        return "linear_scale"
    elif any(word in question_lower for word in ["select all", "check all", "multiple"]):
        return "checkbox"
    elif any(word in question_lower for word in ["explain", "describe", "elaborate"]):
        return "long_answer"
    else:
        return "short_answer"  # Default fallback


def _convert_to_google_forms_format(question: Dict[str, Any], google_forms_type: str) -> Dict[str, Any]:
    """Convert a question to Google Forms API format."""
    converted = {
        "type": google_forms_type,
        "question": question.get("question", ""),
        "required": question.get("required", False)
    }
    
    # Add type-specific properties
    if google_forms_type in ["MULTIPLE_CHOICE", "CHECKBOX", "DROP_DOWN"]:
        options = question.get("options", [])
        if options:
            converted["options"] = options
    
    elif google_forms_type == "LINEAR_SCALE":
        converted["min_value"] = question.get("min_value", 1)
        converted["max_value"] = question.get("max_value", 5)
        converted["min_label"] = question.get("min_label", "")
        converted["max_label"] = question.get("max_label", "")
    
    elif google_forms_type in ["MULTIPLE_CHOICE_GRID", "CHECKBOX_GRID"]:
        converted["rows"] = question.get("rows", [])
        converted["columns"] = question.get("columns", [])
    
    elif google_forms_type == "FILE_UPLOAD":
        converted["max_files"] = question.get("max_files", 1)
        converted["max_file_size"] = question.get("max_file_size", 10)  # MB
    
    return converted 