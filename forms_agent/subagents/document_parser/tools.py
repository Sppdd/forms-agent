"""
Document Parsing Tools

This module provides tools for parsing various document formats and extracting
content that can be converted into Google Forms.
"""

import os
import re
from typing import Any, Dict, List, Optional
import json

import PyPDF2
from docx import Document
from google.adk.tools.tool_context import ToolContext


def parse_document(file_path: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Parse a document file and extract text content for form creation.
    
    Use this tool when you have a document (PDF, DOCX, TXT, MD) that contains questions
    or form content that needs to be converted into a Google Form. This tool extracts
    the text content and stores it in the session for further processing.
    
    Args:
        file_path: Path to the document file to parse
        
    Returns:
        A dictionary containing extraction results with the following structure:
        - status: 'success' or 'error'
        - extracted_text: The full text content from the document
        - metadata: Dictionary with file_type, file_path, and other file information
        - text_length: Number of characters in the extracted text
        - word_count: Number of words in the extracted text
        - error_message: Present only if status is 'error'
    """
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        extracted_text = ""
        metadata = {"file_type": file_extension, "file_path": file_path}
        
        if file_extension == ".pdf":
            extracted_text = _parse_pdf(file_path)
        elif file_extension == ".docx":
            extracted_text = _parse_docx(file_path)
        elif file_extension in [".txt", ".md"]:
            extracted_text = _parse_text_file(file_path)
        else:
            return {
                "status": "error",
                "error_message": f"Unsupported file type: {file_extension}",
                "supported_types": [".pdf", ".docx", ".txt", ".md"]
            }
        
        # Store in session state if tool_context is available
        if tool_context:
            tool_context.state["document_text"] = extracted_text
            tool_context.state["document_metadata"] = metadata
        
        return {
            "status": "success",
            "extracted_text": extracted_text,
            "metadata": metadata,
            "text_length": len(extracted_text),
            "word_count": len(extracted_text.split())
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to parse document: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def extract_questions(text: str, tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """
    Extract potential questions and form elements from parsed text.
    
    Use this tool when you have extracted text from a document and want to identify
    questions, form elements, and structure them for Google Forms creation. This tool
    uses pattern matching to identify different question types and creates a structured
    form representation.
    
    Args:
        text: The parsed document text to analyze for questions
        
    Returns:
        A dictionary containing extracted form structure with the following structure:
        - status: 'success' or 'error'
        - form_structure: Dictionary with title, description, questions array, and metadata
        - extraction_stats: Dictionary with counts of different question types
        - error_message: Present only if status is 'error'
    """
    try:
        questions = []
        
        # Pattern matching for different question types
        multiple_choice_pattern = r"(\d+\.?\s*.*?\?.*?)(?=\n\s*[A-D]\)|\n\s*a\))"
        fill_blank_pattern = r".*?_+.*?"
        numbered_questions = r"(\d+\.?\s*.*?\?)"
        
        # Extract multiple choice questions
        mc_matches = re.findall(multiple_choice_pattern, text, re.DOTALL | re.IGNORECASE)
        for match in mc_matches:
            # Extract options for this question
            options = _extract_options_for_question(text, match)
            questions.append({
                "type": "multiple_choice",
                "question": match.strip(),
                "options": options,
                "required": True
            })
        
        # Extract fill-in-the-blank questions
        blank_matches = re.findall(fill_blank_pattern, text)
        for match in blank_matches:
            if match.strip() and "?" in match:
                questions.append({
                    "type": "short_answer",
                    "question": match.strip(),
                    "required": True
                })
        
        # Extract numbered questions that aren't multiple choice
        numbered_matches = re.findall(numbered_questions, text)
        for match in numbered_matches:
            if not any(mc in match for mc in mc_matches):
                question_type = _determine_question_type(match)
                questions.append({
                    "type": question_type,
                    "question": match.strip(),
                    "required": True
                })
        
        # Extract form metadata
        title_match = re.search(r"^#\s*(.+?)$", text, re.MULTILINE)
        title = title_match.group(1) if title_match else "Extracted Form"
        
        description_match = re.search(r"^##?\s*Description:?\s*(.+?)$", text, re.MULTILINE | re.IGNORECASE)
        description = description_match.group(1) if description_match else "Form created from document"
        
        form_structure = {
            "title": title,
            "description": description,
            "questions": questions,
            "total_questions": len(questions),
            "question_types": list(set([q["type"] for q in questions]))
        }
        
        # Store in session state if tool_context is available
        if tool_context:
            tool_context.state["extracted_questions"] = questions
            tool_context.state["form_structure"] = form_structure
        
        return {
            "status": "success",
            "form_structure": form_structure,
            "extraction_stats": {
                "total_questions": len(questions),
                "multiple_choice": len([q for q in questions if q["type"] == "multiple_choice"]),
                "short_answer": len([q for q in questions if q["type"] == "short_answer"]),
                "long_answer": len([q for q in questions if q["type"] == "long_answer"])
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to extract questions: {str(e)}",
            "error_type": str(type(e).__name__)
        }


def _parse_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text


def _parse_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text


def _parse_text_file(file_path: str) -> str:
    """Extract text from TXT or MD file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def _extract_options_for_question(text: str, question: str) -> List[str]:
    """Extract multiple choice options for a given question."""
    options = []
    # Look for options after the question
    question_index = text.find(question)
    if question_index != -1:
        text_after_question = text[question_index + len(question):question_index + len(question) + 500]
        
        # Pattern for options (A), B), a), b), etc.
        option_pattern = r"[A-D]\)\s*(.+?)(?=\n|[A-D]\)|$)"
        option_matches = re.findall(option_pattern, text_after_question, re.IGNORECASE)
        options = [option.strip() for option in option_matches]
    
    return options


def _determine_question_type(question: str) -> str:
    """Determine the most appropriate question type based on question content."""
    question_lower = question.lower()
    
    # Keywords that suggest different question types
    if any(word in question_lower for word in ["explain", "describe", "elaborate", "why", "how"]):
        return "long_answer"
    elif any(word in question_lower for word in ["rate", "scale", "score", "1-5", "1-10"]):
        return "linear_scale"
    elif any(word in question_lower for word in ["select all", "check all", "multiple"]):
        return "checkbox"
    elif any(word in question_lower for word in ["date", "when"]):
        return "date"
    elif any(word in question_lower for word in ["time", "hour"]):
        return "time"
    else:
        return "short_answer"  # Default fallback 