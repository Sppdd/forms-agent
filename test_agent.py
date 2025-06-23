#!/usr/bin/env python3
"""
Test script for the Forms Agent

This script tests if the forms agent can be imported and initialized properly.
"""

import os
import sys

def test_agent_import():
    """Test if we can import the forms agent."""
    try:
        from forms_agent.agent import forms_agent
        print("✅ Successfully imported forms_agent")
        print(f"Agent name: {forms_agent.name}")
        print(f"Number of sub-agents: {len(forms_agent.sub_agents)}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import forms_agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing forms_agent: {e}")
        return False

def test_subagents():
    """Test if individual subagents can be imported."""
    subagents = [
        ("document_parser", "forms_agent.subagents.document_parser.agent"),
        ("form_creator", "forms_agent.subagents.form_creator.agent"),
        ("form_editor", "forms_agent.subagents.form_editor.agent"),
        ("form_validator", "forms_agent.subagents.form_validator.agent"),
    ]
    
    results = {}
    for name, module_path in subagents:
        try:
            __import__(module_path)
            print(f"✅ Successfully imported {name}")
            results[name] = True
        except Exception as e:
            print(f"❌ Failed to import {name}: {e}")
            results[name] = False
    
    return results

def main():
    """Main test function."""
    print("🧪 Testing Forms Agent Setup...")
    print("=" * 50)
    
    # Test main agent import
    agent_ok = test_agent_import()
    
    print("\n" + "=" * 50)
    print("🧪 Testing Sub-agents...")
    
    # Test subagents
    subagent_results = test_subagents()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    
    if agent_ok:
        print("✅ Main agent: OK")
    else:
        print("❌ Main agent: FAILED")
    
    for name, status in subagent_results.items():
        status_icon = "✅" if status else "❌"
        status_text = "OK" if status else "FAILED"
        print(f"{status_icon} {name}: {status_text}")
    
    # Overall status
    all_ok = agent_ok and all(subagent_results.values())
    if all_ok:
        print("\n🎉 All tests passed! Forms Agent is ready to use.")
    else:
        print("\n⚠️  Some issues found. Check the errors above.")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 