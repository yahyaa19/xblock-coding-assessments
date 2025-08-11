"""
Workbench configuration for Multi-File Coding AI Eval XBlock testing.

This configuration provides sample problems and settings for testing
the enhanced multi-file coding XBlock in the workbench environment.
"""

# Sample XBlock configurations for testing
MULTI_FILE_XBLOCK_SCENARIOS = [
    {
        "name": "Basic Python Math Problem",
        "xml": """
<multi_file_coding_ai_eval
    display_name="Basic Python Math Operations"
    language="python"
    question="Write Python code to solve basic math problems. Implement functions that can add, multiply, and divide numbers."
    enable_multi_file="true"
    judge0_api_key="your-judge0-api-key-here"
    test_cases='[
        {
            "name": "Addition Test",
            "description": "Test simple addition functionality",
            "type": "output_comparison",
            "input": "print(5 + 3)",
            "expected_output": "8",
            "timeout": 5
        },
        {
            "name": "Multiplication Test", 
            "description": "Test multiplication with larger numbers",
            "type": "output_comparison",
            "input": "print(12 * 7)",
            "expected_output": "84",
            "timeout": 5
        }
    ]'
    file_templates='{
        "python": {
            "main.py": {
                "content": "# Write your Python code here\\n# Example: print(5 + 3)\\n\\n",
                "type": "python"
            }
        }
    }'
/>
        """,
        "description": "Basic Python math operations with simple test cases"
    },
    
    {
        "name": "Advanced Pattern Matching",
        "xml": """
<multi_file_coding_ai_eval
    display_name="Advanced Pattern Matching Tests"
    language="python"
    question="Implement code that demonstrates different types of output validation including contains, regex, and exact matching."
    enable_multi_file="true"
    judge0_api_key="your-judge0-api-key-here"
    test_cases='[
        {
            "name": "Contains Test",
            "description": "Test output contains specific text",
            "type": "contains",
            "input": "print(\"Processing data...\")\\nprint(\"Result: 42\")\\nprint(\"Done!\")",
            "expected_output": "Result: 42",
            "timeout": 5
        },
        {
            "name": "Regex Pattern Test",
            "description": "Test output matches regex pattern",
            "type": "regex",
            "input": "import datetime\\nprint(f\"Current time: {datetime.datetime.now()}\")",
            "expected_output": "Current time: \\\\d{4}-\\\\d{2}-\\\\d{2}",
            "timeout": 5
        },
        {
            "name": "Exact Match Test",
            "description": "Test exact output matching (with whitespace)",
            "type": "exact_match",
            "input": "print(\"  Exact match test  \")",
            "expected_output": "  Exact match test  ",
            "timeout": 5
        }
    ]'
    file_templates='{
        "python": {
            "main.py": {
                "content": "# Advanced testing examples\\nimport datetime\\n\\n# Your code here\\n",
                "type": "python"
            }
        }
    }'
/>
        """,
        "description": "Advanced pattern matching with contains, regex, and exact match tests"
    },
    
    {
        "name": "Multi-File Python Project",
        "xml": """
<multi_file_coding_ai_eval
    display_name="Multi-File Python Calculator"
    language="python"
    question="Create a multi-file Python project with a Calculator class and utility functions. The main.py should import and use the Calculator from calculator.py and utility functions from utils.py."
    enable_multi_file="true"
    judge0_api_key="your-judge0-api-key-here"
    test_cases='[
        {
            "name": "Calculator Test",
            "description": "Test calculator functionality across multiple files",
            "type": "output_comparison",
            "input": "from calculator import Calculator\\ncalc = Calculator()\\nprint(calc.add(5, 3))\\nprint(calc.multiply(4, 6))",
            "expected_output": "8\\n24",
            "timeout": 10
        }
    ]'
    file_templates='{
        "python": {
            "main.py": {
                "content": "# Main application file\\nfrom calculator import Calculator\\nfrom utils import format_number, is_prime\\n\\nif __name__ == \"__main__\":\\n    calc = Calculator()\\n    print(f\"Calculator ready: {calc.version}\")\\n",
                "type": "python"
            },
            "calculator.py": {
                "content": "# Calculator module\\nclass Calculator:\\n    def __init__(self):\\n        self.version = \"1.0\"\\n    \\n    def add(self, a, b):\\n        return a + b\\n    \\n    def multiply(self, a, b):\\n        return a * b\\n",
                "type": "python"
            },
            "utils.py": {
                "content": "# Utility functions\\ndef format_number(num):\\n    return f\"{num:,.2f}\"\\n\\ndef is_prime(n):\\n    if n < 2:\\n        return False\\n    for i in range(2, int(n ** 0.5) + 1):\\n        if n % i == 0:\\n            return False\\n    return True\\n",
                "type": "python"
            }
        }
    }'
/>
        """,
        "description": "Multi-file Python project with Calculator class and utilities"
    },
    
    {
        "name": "Error Handling Demo",
        "xml": """
<multi_file_coding_ai_eval
    display_name="Error Handling Tests"
    language="python"
    question="This problem demonstrates various error handling scenarios including syntax errors, runtime errors, and timeouts."
    enable_multi_file="true"
    judge0_api_key="your-judge0-api-key-here"
    test_cases='[
        {
            "name": "Syntax Error Test",
            "description": "Test compilation error handling",
            "type": "output_comparison",
            "input": "print(\"Missing closing quote",
            "expected_output": "This should fail",
            "timeout": 5
        },
        {
            "name": "Runtime Error Test",
            "description": "Test runtime error handling", 
            "type": "output_comparison",
            "input": "print(10 / 0)",
            "expected_output": "This should fail with division by zero",
            "timeout": 5
        }
    ]'
    file_templates='{
        "python": {
            "main.py": {
                "content": "# Error handling test cases\\n# These are intentionally problematic\\n\\n",
                "type": "python"
            }
        }
    }'
/>
        """,
        "description": "Demonstrates error handling for syntax errors, runtime errors, and timeouts"
    }
]

# Instructions for testing
TESTING_INSTRUCTIONS = """
To test the Multi-File Coding AI Eval XBlock:

1. **Setup XBlock SDK (if available):**
   ```bash
   cd C:\\DEV\\OpenEDX\\xblock\\xblock-coding-assessments
   pip install -e .
   workbench  # If available
   ```

2. **Run Test Simulation:**
   ```bash
   python test_examples/test_runner.py
   ```

3. **Manual Testing Steps:**
   - Create files using the file manager
   - Edit code in Monaco editor
   - Run test cases
   - Verify error handling
   - Check test result reporting

4. **Features to Test:**
   - Multi-file project creation and management
   - Code execution with Judge0 API
   - Enhanced test case execution with different comparison types
   - Error handling (compilation, runtime, timeout)
   - Test result reporting and statistics
   - File operations (create, delete, rename, save)

5. **Expected Behavior:**
   - Test cases should execute with detailed error reporting
   - Different comparison types should work correctly
   - Error scenarios should be handled gracefully
   - Test statistics should be calculated accurately
"""
