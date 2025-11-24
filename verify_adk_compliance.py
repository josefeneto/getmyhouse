"""
ADK Compliance Verification Script

This script checks the codebase for common ADK-related errors that can cause
validation issues at runtime.

Based on Google ADK best practices from the 5-Day AI Agents Intensive course.

Author: José Neto
Date: November 2024
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def check_file_for_issues(filepath: Path) -> List[Tuple[int, str, str]]:
    """
    Check a Python file for ADK compliance issues.
    
    Args:
        filepath: Path to the Python file
        
    Returns:
        List of tuples (line_number, issue_type, line_content)
    """
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            # Check for generation_config usage (❌ FORBIDDEN)
            if 'generation_config' in line and not line.strip().startswith('#'):
                issues.append((
                    line_num,
                    "CRITICAL: generation_config not supported",
                    line.strip()
                ))
            
            # Check for max_output_tokens (❌ FORBIDDEN)
            if 'max_output_tokens' in line and not line.strip().startswith('#'):
                issues.append((
                    line_num,
                    "CRITICAL: max_output_tokens not supported",
                    line.strip()
                ))
            
            # Check for AgentTool usage (❌ FORBIDDEN in ADK)
            if re.search(r'\bAgentTool\b', line) and not line.strip().startswith('#'):
                issues.append((
                    line_num,
                    "ERROR: AgentTool doesn't exist in ADK",
                    line.strip()
                ))
            
            # Check for old workflow imports (⚠️ WARNING)
            if 'from google.adk.workflow' in line:
                issues.append((
                    line_num,
                    "WARNING: Check workflow import path",
                    line.strip()
                ))
            
            # Check for Tool class imports (⚠️ WARNING)
            if 'from google.adk.tools import Tool' in line:
                issues.append((
                    line_num,
                    "WARNING: Tools are plain functions, not classes",
                    line.strip()
                ))
    
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return issues


def scan_project(project_root: Path) -> dict:
    """
    Scan entire project for ADK compliance issues.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary mapping filepaths to lists of issues
    """
    results = {}
    
    # Find all Python files
    python_files = list(project_root.rglob("*.py"))
    
    print(f"🔍 Scanning {len(python_files)} Python files...\n")
    
    for filepath in python_files:
        # Skip virtual environment and cache directories
        if any(part in filepath.parts for part in ['.venv', 'venv', '__pycache__', '.git']):
            continue
        
        issues = check_file_for_issues(filepath)
        
        if issues:
            results[filepath] = issues
    
    return results


def print_results(results: dict):
    """
    Print scan results in a readable format.
    
    Args:
        results: Dictionary of filepath to issues
    """
    if not results:
        print("✅ No ADK compliance issues found!")
        print("\nYour code follows ADK best practices:")
        print("  • No generation_config usage")
        print("  • No max_output_tokens usage")
        print("  • No AgentTool references")
        print("  • Correct import paths")
        return
    
    print("❌ ADK Compliance Issues Found:\n")
    print("=" * 80)
    
    total_critical = 0
    total_errors = 0
    total_warnings = 0
    
    for filepath, issues in results.items():
        rel_path = filepath.relative_to(Path.cwd())
        print(f"\n📄 {rel_path}")
        print("-" * 80)
        
        for line_num, issue_type, line_content in issues:
            severity_icon = "🔴" if "CRITICAL" in issue_type else "🟡" if "WARNING" in issue_type else "🟠"
            print(f"{severity_icon} Line {line_num}: {issue_type}")
            print(f"   {line_content}")
            
            if "CRITICAL" in issue_type:
                total_critical += 1
            elif "ERROR" in issue_type:
                total_errors += 1
            elif "WARNING" in issue_type:
                total_warnings += 1
        
        print()
    
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"  🔴 Critical Issues: {total_critical}")
    print(f"  🟠 Errors: {total_errors}")
    print(f"  🟡 Warnings: {total_warnings}")
    
    if total_critical > 0:
        print("\n⚠️  CRITICAL issues will cause runtime validation errors!")
        print("   These must be fixed before deployment.")
    
    print("\n" + "=" * 80)


def print_fix_guide():
    """Print a guide for fixing common issues."""
    print("\n📖 ADK Compliance Fix Guide:")
    print("=" * 80)
    
    print("\n1️⃣ generation_config ERROR:")
    print("   ❌ Wrong:  LlmAgent(..., generation_config={'temperature': 0.2})")
    print("   ✅ Right:  LlmAgent(..., model='gemini-2.0-flash-exp')")
    print("   Note: Temperature is controlled by the model parameter")
    
    print("\n2️⃣ max_output_tokens ERROR:")
    print("   ❌ Wrong:  generation_config={'max_output_tokens': 4096}")
    print("   ✅ Right:  Remove it - ADK manages this automatically")
    
    print("\n3️⃣ AgentTool ERROR:")
    print("   ❌ Wrong:  from google.adk.tools import AgentTool")
    print("   ✅ Right:  Pass agents directly in tools list: tools=[agent1, agent2]")
    
    print("\n4️⃣ Tool Class ERROR:")
    print("   ❌ Wrong:  from google.adk.tools import Tool")
    print("   ✅ Right:  Tools are plain Python functions")
    print("   Example:")
    print("   ```python")
    print("   def my_tool(param: str) -> str:")
    print("       '''Tool description'''")
    print("       return f'Result: {param}'")
    print("   ```")
    
    print("\n5️⃣ Workflow Import ERROR:")
    print("   ❌ Wrong:  from google.adk.workflow import SequentialAgent")
    print("   ✅ Right:  from google.adk.agents.workflow import SequentialAgent")
    
    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    print("=" * 80)
    print("🤖 GetMyHouse - ADK Compliance Verification")
    print("=" * 80)
    print()
    
    # Get project root
    project_root = Path(__file__).parent
    
    # Scan project
    results = scan_project(project_root)
    
    # Print results
    print_results(results)
    
    # Print fix guide if issues found
    if results:
        print_fix_guide()
    
    print("\n✨ Scan complete!")


if __name__ == "__main__":
    main()
