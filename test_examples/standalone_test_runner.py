#!/usr/bin/env python3
"""
Standalone Test Runner for Multi-File Coding AI Eval XBlock

This script demonstrates the enhanced test case execution functionality
without requiring Django or XBlock dependencies.
"""

import json
import time
import re
from typing import Dict, List, Any, Optional

class EnhancedTestCaseRunner:
    """Demonstrates the enhanced test case execution from the XBlock."""
    
    def __init__(self):
        # Global storage for expected outputs in successful test scenarios
        self.expected_outputs = {}
        
    def _compare_test_output(self, actual: str, expected: str, test_type: str = "output_comparison") -> bool:
        """Compare test output using different comparison methods."""
        print(f"      Comparing: '{actual}' vs '{expected}' (type: {test_type})")
        
        if test_type == "exact_match":
            return actual == expected
        
        elif test_type == "output_comparison":
            # Default: trim whitespace and compare
            return actual.strip() == expected.strip()
        
        elif test_type == "contains":
            return expected in actual
        
        elif test_type == "regex":
            try:
                result = bool(re.search(expected, actual))
                print(f"        Regex match result: {result}")
                return result
            except re.error as e:
                print(f"        Regex error: {e}")
                return False
        
        else:
            # Default to output comparison
            return actual.strip() == expected.strip()
    
    def _simulate_code_execution(self, input_data: str, submission_id: str) -> Optional[Dict]:
        """Simulate code execution with different scenarios."""
        print(f"      Executing code: {input_data[:50]}...")
        
        # Mock different scenarios based on submission_id or input content
        if "syntax_error" in submission_id or "Missing closing quote" in input_data:
            return {
                "stdout": "",
                "stderr": "SyntaxError: unterminated string literal (line 1)",
                "compile_output": "SyntaxError: unterminated string literal (line 1)",
                "status": {"id": 6},  # Compilation Error
                "time": "0.001",
                "memory": 2048
            }
        elif "runtime_error" in submission_id or "10 / 0" in input_data:
            return {
                "stdout": "",
                "stderr": "ZeroDivisionError: division by zero",
                "compile_output": "",
                "status": {"id": 5},  # Runtime Error
                "time": "0.002",
                "memory": 3072
            }
        elif "timeout" in submission_id or "while True:" in input_data:
            # Simulate timeout by returning None
            return None
        else:
            # Simulate successful execution - generate realistic outputs
            stdout = self._generate_expected_output(input_data)
            return {
                "stdout": stdout,
                "stderr": "",
                "compile_output": "",
                "status": {"id": 3},  # Accepted
                "time": "0.05",
                "memory": 4096
            }
    
    def _generate_expected_output(self, input_data: str) -> str:
        """Generate expected output based on input code."""
        # Simulate execution of simple Python expressions
        if "print(5 + 3)" in input_data:
            return "8"
        elif "print(12 * 7)" in input_data:
            return "84"
        elif "print(10 / 4)" in input_data:
            return "2.5"
        elif "factorial(5)" in input_data:
            return "120"
        elif "is_even(4)" in input_data and "is_even(7)" in input_data:
            return "True\nFalse"
        elif "reverse_string('hello')" in input_data:
            return "olleh"
        elif "Processing data..." in input_data:
            return "Processing data...\nResult: 42\nDone!"
        elif "datetime.datetime.now()" in input_data:
            return "Current time: 2024-01-15 10:30:45.123456"
        elif "Exact match test" in input_data:
            return "  Exact match test  "
        else:
            return "Simulated output"
    
    def _get_submission_result_with_timeout(self, submission_id: str, timeout_seconds: int = 10) -> Optional[Dict]:
        """Get submission result with proper timeout handling (simulated)."""
        print(f"      Waiting for result (timeout: {timeout_seconds}s)...")
        
        # Simulate processing delay
        time.sleep(0.5)
        
        # Simulate timeout for specific test cases
        if "timeout" in submission_id:
            print(f"      Simulated timeout after {timeout_seconds}s")
            return None
            
        # Return mock result for other cases
        return self._simulate_code_execution("", submission_id)
    
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
                submission_id = f"success_{test_number}_{abs(hash(input_data)) % 1000}"
            
            # Get result with timeout
            if "timeout" in submission_id:
                # Simulate timeout
                time.sleep(min(timeout + 0.1, 2))  # Don't wait too long in demo
                result = None
            else:
                result = self._simulate_code_execution(input_data, submission_id)
            
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
            else:
                print(f"    Expected: '{result.get('expected_output')}'")
                print(f"    Actual: '{result.get('actual_output')}'")
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
    
    # Sample test data (simplified from JSON file)
    sample_test_data = {
        "python_basic_math": {
            "language": "python",
            "problem_title": "Basic Math Operations",
            "description": "Write a Python program that performs basic mathematical operations",
            "test_cases": [
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
            ]
        },
        "python_advanced_testing": {
            "language": "python",
            "problem_title": "Advanced Pattern Matching",
            "description": "Implement functions with complex output patterns",
            "test_cases": [
                {
                    "name": "Contains Test",
                    "description": "Test output contains specific text",
                    "type": "contains",
                    "input": "print('Processing data...')\\nprint('Result: 42')\\nprint('Done!')",
                    "expected_output": "Result: 42",
                    "timeout": 5
                },
                {
                    "name": "Regex Pattern Test",
                    "description": "Test output matches regex pattern",
                    "type": "regex",
                    "input": "import datetime\\nprint(f'Current time: {datetime.datetime.now()}')",
                    "expected_output": "Current time: \\d{4}-\\d{2}-\\d{2}",
                    "timeout": 5
                },
                {
                    "name": "Exact Match Test",
                    "description": "Test exact output matching (with whitespace)",
                    "type": "exact_match",
                    "input": "print('  Exact match test  ')",
                    "expected_output": "  Exact match test  ",
                    "timeout": 5
                }
            ]
        },
        "python_error_handling": {
            "language": "python",
            "problem_title": "Error Handling Tests",
            "description": "Test cases that should produce errors for testing error handling",
            "test_cases": [
                {
                    "name": "Syntax Error Test",
                    "description": "Test compilation error handling",
                    "type": "output_comparison",
                    "input": "print('Missing closing quote",
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
                },
                {
                    "name": "Timeout Test",
                    "description": "Test timeout handling with infinite loop",
                    "type": "output_comparison",
                    "input": "while True:\\n    pass",
                    "expected_output": "This should timeout",
                    "timeout": 2
                }
            ]
        }
    }
    
    # Initialize test runner
    runner = EnhancedTestCaseRunner()
    
    # Track overall results
    all_results = {}
    
    # Run each test suite
    test_suites_to_run = [
        "python_basic_math",
        "python_advanced_testing",
        "python_error_handling"
    ]
    
    for suite_name in test_suites_to_run:
        if suite_name in sample_test_data:
            try:
                result = runner.run_test_suite(suite_name, sample_test_data[suite_name])
                all_results[suite_name] = result
            except Exception as e:
                print(f"Error running test suite {suite_name}: {e}")
        else:
            print(f"Warning: Test suite '{suite_name}' not found in test data")
    
    # Print overall summary
    print(f"\n" + "="*60)
    print("OVERALL TEST RESULTS SUMMARY")
    print("="*60)
    
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
    
    print(f"\n🎯 ENHANCEMENT HIGHLIGHTS:")
    print(f"  🔧 Better Error Messages: Distinguishes between compilation and runtime errors")
    print(f"  ⏱️  Timeout Handling: Properly handles infinite loops and long-running code")
    print(f"  📊 Performance Metrics: Tracks execution time and memory usage")
    print(f"  🎯 Flexible Testing: Supports multiple comparison types for different use cases")
    print(f"  📈 Comprehensive Reports: Detailed statistics and pass rates")
    
    print(f"\n🚀 READY FOR PRODUCTION:")
    print(f"  1. Connect to Judge0 API for real code execution")
    print(f"  2. Deploy to OpenEdX with Tutor")
    print(f"  3. Create engaging coding assignments")
    print(f"  4. Monitor student progress with detailed analytics")

if __name__ == "__main__":
    main()
