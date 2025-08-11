#!/usr/bin/env python3
"""
Test Runner for Multi-File Coding AI Eval XBlock

This script simulates the enhanced test case execution to validate
the new functionality without needing a full OpenEdX environment.
"""

import json
import sys
import os
import time
import requests
from typing import Dict, List, Any

# Add the parent directory to Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_eval.utils import submit_code, get_submission_result, LanguageLabels

class TestCaseSimulator:
    """Simulates the enhanced test case execution from the XBlock."""
    
    def __init__(self, judge0_api_key: str = None):
        self.judge0_api_key = judge0_api_key or "your-judge0-api-key-here"
        
    def _compare_test_output(self, actual: str, expected: str, test_type: str = "output_comparison") -> bool:
        """Compare test output using different comparison methods."""
        if test_type == "exact_match":
            return actual == expected
        
        elif test_type == "output_comparison":
            # Default: trim whitespace and compare
            return actual.strip() == expected.strip()
        
        elif test_type == "contains":
            return expected in actual
        
        elif test_type == "regex":
            import re
            try:
                return bool(re.search(expected, actual))
            except re.error:
                return False
        
        else:
            # Default to output comparison
            return actual.strip() == expected.strip()
    
    def _get_submission_result_with_timeout(self, submission_id: str, timeout_seconds: int = 10) -> Dict:
        """Get submission result with proper timeout handling (simulated)."""
        # For simulation, we'll create mock results
        print(f"  Simulating submission {submission_id} with {timeout_seconds}s timeout...")
        time.sleep(1)  # Simulate processing time
        
        # Mock different scenarios based on submission_id pattern
        if "syntax_error" in submission_id:
            return {
                "stdout": "",
                "stderr": "SyntaxError: unterminated string literal",
                "compile_output": "SyntaxError: unterminated string literal",
                "status": {"id": 6},  # Compilation Error
                "time": "0.001",
                "memory": 2048
            }
        elif "runtime_error" in submission_id:
            return {
                "stdout": "",
                "stderr": "ZeroDivisionError: division by zero",
                "compile_output": "",
                "status": {"id": 5},  # Runtime Error
                "time": "0.002",
                "memory": 3072
            }
        elif "timeout" in submission_id:
            return None  # Simulate timeout
        else:
            # Simulate successful execution
            return {
                "stdout": expected_outputs.get(submission_id, "Mocked output"),
                "stderr": "",
                "compile_output": "",
                "status": {"id": 3},  # Accepted
                "time": "0.05",
                "memory": 4096
            }
    
    def _execute_test_case_enhanced(self, test_case: Dict, test_number: int, language: str = "python") -> Dict:
        """Enhanced test case execution with better error handling."""
        try:
            # Get test case parameters
            test_name = test_case.get("name", f"Test {test_number}")
            test_description = test_case.get("description", "")
            input_data = test_case.get("input", "")
            expected_output = test_case.get("expected_output", "")
            timeout = test_case.get("timeout", 10)
            test_type = test_case.get("type", "output_comparison")
            
            print(f"  Running: {test_name}")
            print(f"    Description: {test_description}")
            print(f"    Type: {test_type}")
            print(f"    Timeout: {timeout}s")
            
            if not input_data:
                return {
                    "test_case": test_case,
                    "test_number": test_number,
                    "test_name": test_name,
                    "passed": False,
                    "error": "No input data provided",
                    "execution_time": 0,
                    "memory_used": 0
                }
            
            # Simulate code submission
            start_time = time.time()
            
            # Create mock submission ID based on test content
            if "Missing closing quote" in input_data:
                submission_id = "syntax_error_123"
            elif "10 / 0" in input_data:
                submission_id = "runtime_error_456"
            elif "while True:" in input_data:
                submission_id = "timeout_789"
            else:
                submission_id = f"success_{test_number}_{hash(input_data) % 1000}"
            
            # Store expected output for successful cases
            if submission_id.startswith("success_"):
                global expected_outputs
                if 'expected_outputs' not in globals():
                    expected_outputs = {}
                
                # Generate expected output based on the input
                if "print(5 + 3)" in input_data:
                    expected_outputs[submission_id] = "8"
                elif "print(12 * 7)" in input_data:
                    expected_outputs[submission_id] = "84"
                elif "print(10 / 4)" in input_data:
                    expected_outputs[submission_id] = "2.5"
                elif "factorial(5)" in input_data:
                    expected_outputs[submission_id] = "120"
                elif "is_even(4)" in input_data and "is_even(7)" in input_data:
                    expected_outputs[submission_id] = "True\nFalse"
                elif "reverse_string('hello')" in input_data:
                    expected_outputs[submission_id] = "olleh"
                elif "Processing data..." in input_data:
                    expected_outputs[submission_id] = "Processing data...\nResult: 42\nDone!"
                elif "datetime.datetime.now()" in input_data:
                    expected_outputs[submission_id] = "Current time: 2024-01-15 10:30:45.123456"
                elif "Exact match test" in input_data:
                    expected_outputs[submission_id] = "  Exact match test  "
                else:
                    expected_outputs[submission_id] = expected_output
            
            # Get result with timeout
            result = self._get_submission_result_with_timeout(submission_id, timeout_seconds=timeout)
            execution_time = time.time() - start_time
            
            if not result:
                return {
                    "test_case": test_case,
                    "test_number": test_number,
                    "test_name": test_name,
                    "passed": False,
                    "error": "Test execution timeout",
                    "execution_time": execution_time,
                    "memory_used": 0
                }
            
            # Extract execution results
            stdout = result.get("stdout", "").strip()
            stderr = result.get("stderr", "").strip()
            compile_output = result.get("compile_output", "").strip()
            exit_code = result.get("status", {}).get("id", 0)
            
            # Check for compilation errors
            if compile_output and exit_code != 3:  # 3 = Accepted
                return {
                    "test_case": test_case,
                    "test_number": test_number,
                    "test_name": test_name,
                    "passed": False,
                    "error": f"Compilation error: {compile_output}",
                    "actual_output": "",
                    "expected_output": expected_output,
                    "execution_time": execution_time,
                    "memory_used": result.get("memory", 0)
                }
            
            # Check for runtime errors
            if stderr and exit_code != 3:
                return {
                    "test_case": test_case,
                    "test_number": test_number,
                    "test_name": test_name,
                    "passed": False,
                    "error": f"Runtime error: {stderr}",
                    "actual_output": stdout,
                    "expected_output": expected_output,
                    "execution_time": execution_time,
                    "memory_used": result.get("memory", 0)
                }
            
            # Perform test comparison based on test type
            passed = self._compare_test_output(stdout, expected_output, test_type)
            
            return {
                "test_case": test_case,
                "test_number": test_number,
                "test_name": test_name,
                "description": test_description,
                "passed": passed,
                "actual_output": stdout,
                "expected_output": expected_output,
                "execution_time": execution_time,
                "memory_used": result.get("memory", 0),
                "exit_code": exit_code
            }
            
        except Exception as e:
            print(f"    ERROR: {e}")
            return {
                "test_case": test_case,
                "test_number": test_number,
                "test_name": test_name,
                "passed": False,
                "error": str(e),
                "execution_time": 0,
                "memory_used": 0
            }
    
    def run_test_suite(self, test_suite_name: str, test_data: Dict) -> Dict:
        """Run a complete test suite."""
        print(f"\n" + "="*60)
        print(f"Running Test Suite: {test_suite_name}")
        print(f"Problem: {test_data.get('problem_title', 'Unknown')}")
        print(f"Language: {test_data.get('language', 'unknown')}")
        print(f"Description: {test_data.get('description', '')}")
        print("="*60)
        
        test_cases = test_data.get('test_cases', [])
        results = []
        
        for i, test_case in enumerate(test_cases):
            print(f"\nTest {i+1}/{len(test_cases)}")
            result = self._execute_test_case_enhanced(test_case, i + 1, test_data.get('language', 'python'))
            results.append(result)
            
            # Print result summary
            status = "✅ PASS" if result.get("passed") else "❌ FAIL"
            print(f"    Result: {status}")
            if result.get("error"):
                print(f"    Error: {result['error']}")
            elif result.get("passed"):
                print(f"    Expected: {result.get('expected_output')}")
                print(f"    Actual: {result.get('actual_output')}")
            print(f"    Time: {result.get('execution_time', 0):.3f}s")
            print(f"    Memory: {result.get('memory_used', 0)} KB")
        
        # Calculate summary statistics
        total_tests = len(results)
        passed_count = sum(1 for r in results if r.get("passed", False))
        failed_count = total_tests - passed_count
        
        summary = {
            "total": total_tests,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": (passed_count / total_tests * 100) if total_tests > 0 else 0
        }
        
        print(f"\n" + "-"*40)
        print(f"Test Suite Summary:")
        print(f"  Total Tests: {summary['total']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Pass Rate: {summary['pass_rate']:.1f}%")
        print("-"*40)
        
        return {
            "success": True,
            "results": results,
            "summary": summary
        }

def main():
    """Main function to run the test demonstration."""
    print("Multi-File Coding AI Eval XBlock - Enhanced Test Case Demo")
    print("=========================================================")
    
    # Load test cases
    test_file = os.path.join(os.path.dirname(__file__), 'sample_test_cases.json')
    try:
        with open(test_file, 'r') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Test file not found at {test_file}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in test file: {e}")
        return
    
    # Initialize test simulator
    simulator = TestCaseSimulator()
    
    # Track overall results
    all_results = {}
    
    # Run each test suite
    test_suites_to_run = [
        "python_basic_math",
        "python_function_testing", 
        "python_advanced_testing",
        "python_error_handling"
    ]
    
    for suite_name in test_suites_to_run:
        if suite_name in test_data:
            try:
                result = simulator.run_test_suite(suite_name, test_data[suite_name])
                all_results[suite_name] = result
            except Exception as e:
                print(f"Error running test suite {suite_name}: {e}")
        else:
            print(f"Warning: Test suite '{suite_name}' not found in test data")
    
    # Print overall summary
    print(f"\n" + "="*60)
    print("OVERALL TEST RESULTS SUMMARY")
    print("="*60)
    
    total_suites = len(all_results)
    total_tests = 0
    total_passed = 0
    
    for suite_name, result in all_results.items():
        summary = result.get('summary', {})
        suite_total = summary.get('total', 0)
        suite_passed = summary.get('passed', 0)
        suite_pass_rate = summary.get('pass_rate', 0)
        
        total_tests += suite_total
        total_passed += suite_passed
        
        print(f"{suite_name:25s}: {suite_passed:2d}/{suite_total:2d} ({suite_pass_rate:5.1f}%)")
    
    overall_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print("-" * 60)
    print(f"{'OVERALL':25s}: {total_passed:2d}/{total_tests:2d} ({overall_pass_rate:5.1f}%)")
    print("=" * 60)
    
    # Print feature demonstration summary
    print(f"\n📋 FEATURES DEMONSTRATED:")
    print(f"  ✅ Enhanced test case execution with detailed error handling")
    print(f"  ✅ Multiple comparison types (output_comparison, contains, regex, exact_match)")
    print(f"  ✅ Compilation error detection and reporting")
    print(f"  ✅ Runtime error handling and reporting") 
    print(f"  ✅ Timeout handling for infinite loops")
    print(f"  ✅ Execution time and memory usage tracking")
    print(f"  ✅ Test summary statistics and pass rate calculation")
    print(f"  ✅ Detailed test result reporting")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"  1. Install and configure Judge0 API for real code execution")
    print(f"  2. Test with real XBlock-SDK workbench environment")
    print(f"  3. Deploy to Tutor OpenEdX instance")
    print(f"  4. Create course content with multi-file coding problems")

if __name__ == "__main__":
    main()
