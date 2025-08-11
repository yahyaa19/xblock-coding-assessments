
from ai_eval.multi_file_coding_ai_eval import MultiFileCodingAIEvalXBlock

# Simple Python math problem
python_math_scenario = """
<multi_file_coding_ai_eval
    display_name="Python Math Challenge"
    language="python"
    question="Write Python code to solve basic math problems. Test your addition and multiplication skills!"
    enable_multi_file="true"
    judge0_api_key="your-api-key-here"
    test_cases='[{
        "name": "Addition Test",
        "description": "Test simple addition",
        "type": "output_comparison",
        "input": "print(5 + 3)",
        "expected_output": "8",
        "timeout": 5
    }]'
    file_templates='{
        "python": {
            "main.py": {
                "content": "# Write your Python code here\nprint(\"Hello, World!\")\n",
                "type": "python"
            }
        }
    }'
/>
"""

# Add to workbench scenarios
MultiFileCodingAIEvalXBlock.workbench_scenarios = [
    ("Python Math Challenge", python_math_scenario),
]
