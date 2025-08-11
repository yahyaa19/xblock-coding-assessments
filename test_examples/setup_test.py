#!/usr/bin/env python3
"""
Setup Script for Multi-File Coding AI Eval XBlock Testing

This script helps set up the testing environment and provides guidance
for testing the enhanced XBlock functionality.
"""

import os
import sys
import subprocess
import json

def check_requirements():
    """Check if required packages are installed."""
    print("🔍 Checking requirements...")
    
    required_packages = [
        "xblock",
        "web-fragments", 
        "django",
        "requests"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package} is installed")
        except ImportError:
            print(f"  ❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n🚨 Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All required packages are installed!")
    return True

def install_xblock():
    """Install the XBlock in development mode."""
    print("\n📦 Installing XBlock in development mode...")
    
    try:
        xblock_dir = os.path.dirname(os.path.dirname(__file__))
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=xblock_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ XBlock installed successfully!")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def create_workbench_scenarios():
    """Create workbench scenario files."""
    print("\n📝 Creating workbench scenarios...")
    
    scenario_content = '''
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
                "content": "# Write your Python code here\\nprint(\\"Hello, World!\\")\\n",
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
'''
    
    try:
        scenario_file = os.path.join(os.path.dirname(__file__), "workbench_scenarios.py")
        with open(scenario_file, 'w') as f:
            f.write(scenario_content)
        print(f"✅ Workbench scenarios created: {scenario_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to create scenarios: {e}")
        return False

def run_tests():
    """Run the standalone test demonstration."""
    print("\n🧪 Running test demonstration...")
    
    try:
        test_script = os.path.join(os.path.dirname(__file__), "standalone_test_runner.py")
        result = subprocess.run([sys.executable, test_script], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tests completed successfully!")
            print("\n📊 Test Results Summary:")
            # Extract summary from output
            lines = result.stdout.split('\n')
            in_summary = False
            for line in lines:
                if "OVERALL TEST RESULTS SUMMARY" in line:
                    in_summary = True
                elif in_summary and line.startswith("="):
                    break
                elif in_summary and line.strip():
                    print(f"  {line}")
            return True
        else:
            print(f"❌ Tests failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def check_judge0_api():
    """Check if Judge0 API configuration is available."""
    print("\n🌐 Checking Judge0 API configuration...")
    
    # Check for API key in environment or config
    api_key = os.environ.get("JUDGE0_API_KEY")
    
    if api_key and api_key != "your-api-key-here":
        print("✅ Judge0 API key found in environment")
        return True
    else:
        print("⚠️  Judge0 API key not configured")
        print("   Set JUDGE0_API_KEY environment variable or")
        print("   Update the XBlock configuration with your API key")
        print("   Get a free key at: https://rapidapi.com/judge0-official/api/judge0-ce")
        return False

def print_next_steps():
    """Print instructions for next steps."""
    print("\n" + "="*60)
    print("🎯 NEXT STEPS TO TEST THE ENHANCED XBLOCK")
    print("="*60)
    
    print("\n1. 🔧 FOR WORKBENCH TESTING:")
    print("   If you have xblock-sdk workbench available:")
    print("   ```bash")
    print("   cd C:\\DEV\\OpenEDX\\xblock\\xblock-coding-assessments")
    print("   workbench")
    print("   ```")
    print("   Then open: http://localhost:8000")
    
    print("\n2. 🚀 FOR TUTOR TESTING:")
    print("   Deploy to your Tutor OpenEdX instance:")
    print("   ```bash")
    print("   # Copy XBlock to Tutor plugins")
    print("   # Restart Tutor services")
    print("   tutor local restart")
    print("   ```")
    
    print("\n3. 📝 MANUAL TESTING CHECKLIST:")
    print("   ✅ Create multi-file projects")
    print("   ✅ Test file operations (create, edit, delete)")
    print("   ✅ Run code execution with Judge0 API")
    print("   ✅ Test different comparison types (contains, regex, exact)")
    print("   ✅ Verify error handling (syntax, runtime, timeout)")
    print("   ✅ Check test result reporting and statistics")
    
    print("\n4. 🎮 FEATURES TO EXPLORE:")
    print("   - Multi-file project management")
    print("   - Enhanced Monaco Editor integration")
    print("   - Advanced test case execution")
    print("   - Detailed error reporting")
    print("   - Performance metrics tracking")
    print("   - Flexible output comparison")
    
    print("\n5. 🔗 USEFUL RESOURCES:")
    print("   - Test examples: test_examples/sample_test_cases.json")
    print("   - Workbench config: test_examples/workbench_config.py") 
    print("   - Standalone demo: test_examples/standalone_test_runner.py")

def main():
    """Main setup function."""
    print("🚀 Multi-File Coding AI Eval XBlock - Setup & Test")
    print("=" * 55)
    
    success_count = 0
    
    # Step 1: Check requirements
    if check_requirements():
        success_count += 1
    
    # Step 2: Install XBlock
    if install_xblock():
        success_count += 1
    
    # Step 3: Create workbench scenarios
    if create_workbench_scenarios():
        success_count += 1
    
    # Step 4: Run tests
    if run_tests():
        success_count += 1
    
    # Step 5: Check Judge0 API
    if check_judge0_api():
        success_count += 1
    
    # Summary
    print(f"\n📋 SETUP SUMMARY: {success_count}/5 steps completed")
    
    if success_count >= 4:
        print("✅ Setup successful! Your enhanced XBlock is ready for testing.")
    elif success_count >= 2:
        print("⚠️  Partial setup. You can still test basic functionality.")
    else:
        print("❌ Setup issues detected. Please resolve errors above.")
    
    # Print next steps regardless of success
    print_next_steps()

if __name__ == "__main__":
    main()
