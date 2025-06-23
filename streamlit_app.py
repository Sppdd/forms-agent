#!/usr/bin/env python3
"""
Google Forms Manager - Streamlit Web App

A fully functional web application for managing Google Forms with OAuth authentication.
Users can log in with their Google accounts and create, edit, organize, and manage forms.
"""

import streamlit as st
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the forms_agent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'forms_agent'))

# Import forms agent tools
try:
    from forms_agent.subagents.form_creator.tools import (
        create_google_form,
        list_my_forms,
        create_forms_folder,
        move_form_to_folder,
        get_form_details,
        add_questions_to_form,
        setup_form_settings
    )
    from forms_agent.subagents.form_editor.tools import (
        update_form_info,
        modify_questions,
        delete_form,
        get_form_responses
    )
    FORMS_AGENT_AVAILABLE = True
except ImportError as e:
    st.error(f"Forms agent not available: {e}")
    FORMS_AGENT_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Google Forms Manager",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .form-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .info-message {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #bee5eb;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'current_form_id' not in st.session_state:
        st.session_state.current_form_id = None
    if 'forms_cache' not in st.session_state:
        st.session_state.forms_cache = None
    if 'folders_cache' not in st.session_state:
        st.session_state.folders_cache = None

def login_screen():
    """Display login screen for unauthenticated users."""
    st.markdown('<h1 class="main-header">📝 Google Forms Manager</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="info-message">
            <h3>Welcome to Google Forms Manager!</h3>
            <p>This application allows you to:</p>
            <ul>
                <li>Create and manage Google Forms</li>
                <li>Organize forms in folders</li>
                <li>Edit existing forms</li>
                <li>View form responses</li>
                <li>Access all your forms in one place</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🔐 Authentication Required")
        st.write("Please log in with your Google account to access your forms.")
        
        if st.button("🔑 Log in with Google", type="primary", use_container_width=True):
            st.login()
        
        st.markdown("---")
        st.markdown("""
        <div class="info-message">
            <h4>📋 Features:</h4>
            <ul>
                <li><strong>Form Creation:</strong> Create new forms with various question types</li>
                <li><strong>Form Management:</strong> List, edit, and delete your forms</li>
                <li><strong>Organization:</strong> Create folders and organize your forms</li>
                <li><strong>Responses:</strong> View and analyze form responses</li>
                <li><strong>Settings:</strong> Configure form settings and permissions</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def main_app():
    """Main application interface for authenticated users."""
    st.markdown('<h1 class="main-header">📝 Google Forms Manager</h1>', unsafe_allow_html=True)
    
    # User info in sidebar
    with st.sidebar:
        st.subheader("👤 User Information")
        if st.user.is_logged_in:
            st.write(f"**Name:** {st.user.name}")
            st.write(f"**Email:** {st.user.email}")
            st.write(f"**Picture:** {st.user.picture}")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", type="secondary"):
            st.logout()
            st.rerun()
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 My Forms", 
        "➕ Create Form", 
        "📁 Organize", 
        "⚙️ Settings", 
        "📊 Analytics"
    ])
    
    with tab1:
        show_my_forms()
    
    with tab2:
        create_new_form()
    
    with tab3:
        organize_forms()
    
    with tab4:
        show_settings()
    
    with tab5:
        show_analytics()

def show_my_forms():
    """Display user's forms with management options."""
    st.subheader("📋 My Forms")
    
    if not FORMS_AGENT_AVAILABLE:
        st.error("Forms agent is not available. Please check your configuration.")
        return
    
    # Refresh button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", type="secondary"):
            st.session_state.forms_cache = None
            st.rerun()
    
    # Load forms
    with st.spinner("Loading your forms..."):
        try:
            forms_result = list_my_forms()
            
            if forms_result["status"] == "success":
                forms = forms_result["forms"]
                st.session_state.forms_cache = forms
                
                if not forms:
                    st.info("No forms found. Create your first form in the 'Create Form' tab!")
                    return
                
                st.success(f"Found {len(forms)} forms")
                
                # Search and filter
                search_term = st.text_input("🔍 Search forms by title:", placeholder="Enter form title...")
                
                if search_term:
                    forms = [f for f in forms if search_term.lower() in f.get('title', '').lower()]
                
                # Display forms
                for i, form in enumerate(forms):
                    with st.expander(f"📝 {form.get('title', 'Untitled Form')}", expanded=False):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**Description:** {form.get('description', 'No description')}")
                            st.write(f"**Created:** {form.get('created_time', 'Unknown')[:10]}")
                            st.write(f"**Items:** {form.get('item_count', 0)} questions")
                            st.write(f"**Type:** {'Quiz' if form.get('is_quiz') else 'Form'}")
                        
                        with col2:
                            st.write(f"**ID:** `{form['form_id']}`")
                            if form.get('edit_url'):
                                st.link_button("✏️ Edit", form['edit_url'])
                            if form.get('responder_url'):
                                st.link_button("📊 View", form['responder_url'])
                        
                        with col3:
                            if st.button(f"🔍 Details", key=f"details_{i}"):
                                st.session_state.current_form_id = form['form_id']
                                st.rerun()
                            
                            if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                                if st.session_state.current_form_id == form['form_id']:
                                    st.session_state.current_form_id = None
                                delete_form_result = delete_form(form['form_id'])
                                if delete_form_result["status"] == "success":
                                    st.success("Form deleted successfully!")
                                    st.session_state.forms_cache = None
                                    st.rerun()
                                else:
                                    st.error(f"Error deleting form: {delete_form_result['error_message']}")
                
                # Show detailed form information if selected
                if st.session_state.current_form_id:
                    st.markdown("---")
                    show_form_details(st.session_state.current_form_id)
                    
            else:
                st.error(f"Error loading forms: {forms_result['error_message']}")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

def show_form_details(form_id: str):
    """Display detailed information about a specific form."""
    st.subheader("🔍 Form Details")
    
    try:
        details_result = get_form_details(form_id)
        
        if details_result["status"] == "success":
            form_info = details_result["form_info"]
            questions = details_result["questions"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Form Information:**")
                st.write(f"**Title:** {form_info.get('title', 'Untitled')}")
                st.write(f"**Description:** {form_info.get('description', 'No description')}")
                st.write(f"**Created:** {details_result.get('created_time', 'Unknown')[:10]}")
                st.write(f"**Modified:** {details_result.get('modified_time', 'Unknown')[:10]}")
                st.write(f"**Is Quiz:** {details_result.get('is_quiz', False)}")
                st.write(f"**Total Items:** {details_result.get('item_count', 0)}")
            
            with col2:
                st.write("**Quick Actions:**")
                if details_result.get('edit_url'):
                    st.link_button("✏️ Edit Form", details_result['edit_url'])
                if details_result.get('responder_url'):
                    st.link_button("📊 View Responses", details_result['responder_url'])
                
                st.write("**Owners:**")
                for owner in details_result.get('owners', []):
                    st.write(f"• {owner}")
            
            # Questions section
            if questions:
                st.subheader("📝 Questions")
                for i, question in enumerate(questions, 1):
                    st.write(f"**{i}. {question.get('title', 'Untitled')}** ({question.get('type', 'Unknown')})")
            
            # Responses section
            st.subheader("📊 Recent Responses")
            try:
                responses_result = get_form_responses(form_id)
                if responses_result["status"] == "success":
                    responses = responses_result["responses"]
                    st.write(f"**Total Responses:** {len(responses)}")
                    
                    if responses:
                        # Show last 5 responses
                        for i, response in enumerate(responses[:5], 1):
                            with st.expander(f"Response {i} - {response.get('created_time', 'Unknown')[:10]}"):
                                st.write(f"**Response ID:** {response.get('response_id', 'Unknown')}")
                                st.write(f"**Created:** {response.get('created_time', 'Unknown')}")
                                
                                answers = response.get('answers', {})
                                if answers:
                                    st.write("**Answers:**")
                                    for question, answer in answers.items():
                                        st.write(f"• {question}: {answer}")
                else:
                    st.info("No responses available or error loading responses.")
            except Exception as e:
                st.info("Responses feature not available.")
                
        else:
            st.error(f"Error loading form details: {details_result['error_message']}")
            
    except Exception as e:
        st.error(f"Error: {str(e)}")

def create_new_form():
    """Interface for creating new forms."""
    st.subheader("➕ Create New Form")
    
    if not FORMS_AGENT_AVAILABLE:
        st.error("Forms agent is not available. Please check your configuration.")
        return
    
    # Form creation interface
    with st.form("create_form_form"):
        st.write("**Basic Information:**")
        title = st.text_input("Form Title:", placeholder="Enter form title...")
        description = st.text_area("Form Description:", placeholder="Enter form description...")
        form_type = st.selectbox("Form Type:", ["form", "quiz"], help="Choose between regular form or quiz")
        
        st.write("**Questions:**")
        num_questions = st.number_input("Number of Questions:", min_value=1, max_value=20, value=3)
        
        questions = []
        for i in range(num_questions):
            st.write(f"**Question {i+1}:**")
            col1, col2 = st.columns(2)
            
            with col1:
                question_type = st.selectbox(
                    f"Type {i+1}:", 
                    ["multiple_choice", "text", "checkbox", "dropdown", "linear_scale", "date", "time"],
                    key=f"type_{i}"
                )
                question_text = st.text_input(f"Question {i+1}:", key=f"text_{i}")
                required = st.checkbox(f"Required {i+1}:", key=f"required_{i}")
            
            with col2:
                if question_type in ["multiple_choice", "checkbox", "dropdown"]:
                    options_text = st.text_area(
                        f"Options {i+1} (one per line):", 
                        placeholder="Option 1\nOption 2\nOption 3",
                        key=f"options_{i}"
                    )
                    options = [opt.strip() for opt in options_text.split('\n') if opt.strip()] if options_text else []
                else:
                    options = []
            
            if question_text:  # Only add if question text is provided
                question = {
                    "type": question_type,
                    "question": question_text,
                    "required": required
                }
                if options:
                    question["options"] = options
                questions.append(question)
        
        submitted = st.form_submit_button("🚀 Create Form", type="primary")
        
        if submitted:
            if not title:
                st.error("Please enter a form title.")
                return
            
            if not questions:
                st.error("Please add at least one question.")
                return
            
            # Create the form
            with st.spinner("Creating your form..."):
                try:
                    # Create form
                    form_result = create_google_form(title, description, form_type)
                    
                    if form_result["status"] == "success":
                        form_id = form_result["form_id"]
                        
                        # Add questions
                        if questions:
                            questions_result = add_questions_to_form(form_id, questions)
                            if questions_result["status"] != "success":
                                st.warning(f"Form created but error adding questions: {questions_result['error_message']}")
                        
                        st.success("✅ Form created successfully!")
                        
                        # Show form links
                        col1, col2 = st.columns(2)
                        with col1:
                            st.link_button("✏️ Edit Form", form_result["form_url"])
                        with col2:
                            st.link_button("📊 View Form", form_result["responder_url"])
                        
                        # Clear cache to refresh forms list
                        st.session_state.forms_cache = None
                        
                    else:
                        st.error(f"Error creating form: {form_result['error_message']}")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def organize_forms():
    """Interface for organizing forms in folders."""
    st.subheader("📁 Organize Forms")
    
    if not FORMS_AGENT_AVAILABLE:
        st.error("Forms agent is not available. Please check your configuration.")
        return
    
    # Create new folder
    st.write("**Create New Folder:**")
    with st.form("create_folder_form"):
        folder_name = st.text_input("Folder Name:", placeholder="Enter folder name...")
        parent_folder_id = st.text_input("Parent Folder ID (optional):", placeholder="Leave empty for root folder")
        
        if st.form_submit_button("📁 Create Folder", type="primary"):
            if folder_name:
                with st.spinner("Creating folder..."):
                    try:
                        folder_result = create_forms_folder(folder_name, parent_folder_id if parent_folder_id else None)
                        
                        if folder_result["status"] == "success":
                            st.success(f"✅ Folder '{folder_name}' created successfully!")
                            st.write(f"**Folder ID:** `{folder_result['folder_id']}`")
                            st.write(f"**Folder URL:** {folder_result['folder_url']}")
                            st.session_state.folders_cache = None
                        else:
                            st.error(f"Error creating folder: {folder_result['error_message']}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.error("Please enter a folder name.")
    
    st.markdown("---")
    
    # Move forms to folders
    st.write("**Move Forms to Folders:**")
    
    # Load forms if not cached
    if st.session_state.forms_cache is None:
        forms_result = list_my_forms()
        if forms_result["status"] == "success":
            st.session_state.forms_cache = forms_result["forms"]
    
    if st.session_state.forms_cache:
        with st.form("move_forms_form"):
            # Form selection
            form_options = {f"{f.get('title', 'Untitled')} ({f['form_id'][:20]}...)" : f['form_id'] 
                           for f in st.session_state.forms_cache}
            selected_form = st.selectbox("Select Form:", list(form_options.keys()))
            
            # Folder input
            target_folder_id = st.text_input("Target Folder ID:", placeholder="Enter folder ID to move form to...")
            
            if st.form_submit_button("📂 Move Form", type="primary"):
                if selected_form and target_folder_id:
                    form_id = form_options[selected_form]
                    
                    with st.spinner("Moving form..."):
                        try:
                            move_result = move_form_to_folder(form_id, target_folder_id)
                            
                            if move_result["status"] == "success":
                                st.success("✅ Form moved successfully!")
                                st.session_state.forms_cache = None
                            else:
                                st.error(f"Error moving form: {move_result['error_message']}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.error("Please select a form and enter a folder ID.")

def show_settings():
    """Display application settings and configuration."""
    st.subheader("⚙️ Settings")
    
    st.write("**Application Information:**")
    st.write(f"**Forms Agent Available:** {'✅ Yes' if FORMS_AGENT_AVAILABLE else '❌ No'}")
    st.write(f"**Authentication Status:** {'✅ Authenticated' if st.user.is_logged_in else '❌ Not Authenticated'}")
    
    if st.user.is_logged_in:
        st.write("**User Information:**")
        st.write(f"**Name:** {st.user.name}")
        st.write(f"**Email:** {st.user.email}")
        st.write(f"**User ID:** {st.user.id}")
    
    st.markdown("---")
    
    st.write("**Cache Management:**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Forms Cache"):
            st.session_state.forms_cache = None
            st.success("Forms cache cleared!")
    
    with col2:
        if st.button("🗑️ Clear All Cache"):
            st.session_state.forms_cache = None
            st.session_state.folders_cache = None
            st.success("All cache cleared!")
    
    st.markdown("---")
    
    st.write("**Help & Support:**")
    st.markdown("""
    - **Documentation:** Check the README.md file for detailed usage instructions
    - **Forms Access Guide:** See FORMS_ACCESS_GUIDE.md for form management tips
    - **GitHub Repository:** [forms-agent](https://github.com/Sppdd/forms-agent.git)
    """)

def show_analytics():
    """Display analytics and statistics."""
    st.subheader("📊 Analytics")
    
    if not FORMS_AGENT_AVAILABLE:
        st.error("Forms agent is not available. Please check your configuration.")
        return
    
    # Load forms for analytics
    if st.session_state.forms_cache is None:
        forms_result = list_my_forms()
        if forms_result["status"] == "success":
            st.session_state.forms_cache = forms_result["forms"]
    
    if st.session_state.forms_cache:
        forms = st.session_state.forms_cache
        
        # Basic statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Forms", len(forms))
        
        with col2:
            quiz_count = sum(1 for f in forms if f.get('is_quiz', False))
            st.metric("Quizzes", quiz_count)
        
        with col3:
            regular_forms = len(forms) - quiz_count
            st.metric("Regular Forms", regular_forms)
        
        with col4:
            total_items = sum(f.get('item_count', 0) for f in forms)
            st.metric("Total Questions", total_items)
        
        # Charts and visualizations
        st.markdown("---")
        
        # Form types distribution
        st.write("**Form Types Distribution:**")
        form_types = {}
        for form in forms:
            form_type = "Quiz" if form.get('is_quiz', False) else "Form"
            form_types[form_type] = form_types.get(form_type, 0) + 1
        
        if form_types:
            for form_type, count in form_types.items():
                st.write(f"• {form_type}: {count}")
        
        # Recent forms
        st.write("**Recent Forms:**")
        recent_forms = sorted(forms, key=lambda x: x.get('created_time', ''), reverse=True)[:5]
        
        for form in recent_forms:
            st.write(f"• {form.get('title', 'Untitled')} - {form.get('created_time', 'Unknown')[:10]}")
    
    else:
        st.info("No forms available for analytics.")

def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Check if user is authenticated
    if not st.user.is_logged_in:
        login_screen()
    else:
        main_app()

if __name__ == "__main__":
    main() 