"""Multi-File Coding XBlock with AI evaluation."""

import json
import logging
import traceback
from typing import Dict, List, Optional
import pkg_resources

from django.utils.translation import gettext_noop as _
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Dict, List, Scope, String, Boolean
from xblock.validation import ValidationMessage

from .coding_ai_eval import CodingAIEvalXBlock
from .llm import get_llm_response
from .utils import (
    submit_code,
    get_submission_result,
    SUPPORTED_LANGUAGE_MAP,
    LanguageLabels,
)

logger = logging.getLogger(__name__)

USER_RESPONSE = "USER_RESPONSE"
AI_EVALUATION = "AI_EVALUATION"
CODE_EXEC_RESULT = "CODE_EXEC_RESULT"


class MultiFileCodingAIEvalXBlock(CodingAIEvalXBlock):
    """
    Enhanced Coding XBlock with multi-file support.
    
    Features:
    - Multi-file project management
    - File templates for different languages
    - Test case evaluation
    - Enhanced Monaco Editor integration
    - Project structure validation
    """

    has_author_view = True

    display_name = String(
        display_name=_("Display Name"),
        help=_("Name of the component in the studio"),
        default="Multi-File Coding with AI Evaluation",
        scope=Scope.settings,
    )

    # Multi-file specific fields
    enable_multi_file = Boolean(
        display_name=_("Enable Multi-File Support"),
        help=_("Enable multi-file project support"),
        default=True,
        scope=Scope.settings,
    )

    project_files = Dict(
        help=_("Dictionary of project files with content and metadata"),
        scope=Scope.user_state,
        default={}
    )

    file_templates = Dict(
        help=_("Starter file templates for different languages"),
        scope=Scope.settings,
        default={}
    )

    test_cases = List(
        help=_("List of test cases for evaluation"),
        scope=Scope.settings,
        default=[]
    )

    build_config = Dict(
        help=_("Build configuration for compiled languages"),
        scope=Scope.settings,
        default={}
    )

    # Project structure and settings
    project_structure = Dict(
        help=_("Project file structure and metadata"),
        scope=Scope.user_state,
        default={}
    )

    editable_fields = CodingAIEvalXBlock.editable_fields + (
        "enable_multi_file",
        "file_templates",
        "test_cases",
        "build_config"
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def student_view(self, context=None):
        """
        The primary view of the MultiFileCodingAIEvalXBlock, shown to students
        when viewing courses.
        """
        html = self.loader.render_django_template(
            "/templates/multi_file_coding_ai_eval.html",
            {
                "self": self,
            },
        )

        frag = Fragment(html)
        frag.add_css(self.resource_string("static/css/multi_file_coding_ai_eval.css"))
        frag.add_javascript(self.resource_string("static/js/src/utils.js"))
        frag.add_javascript(self.resource_string("static/js/src/multi_file_coding_ai_eval.js"))

        monaco_html = self.loader.render_django_template(
            "/templates/multi_file_monaco.html",
            {
                "monaco_language": SUPPORTED_LANGUAGE_MAP[self.language].monaco_id,
                "enable_multi_file": self.enable_multi_file,
            },
        )
        marked_html = self.resource_string("static/html/marked-iframe.html")
        
        js_data = {
            "monaco_html": monaco_html,
            "question": self.question,
            "project_files": self.project_files,
            "file_templates": self.file_templates,
            "test_cases": self.test_cases,
            "build_config": self.build_config,
            "project_structure": self.project_structure,
            "enable_multi_file": self.enable_multi_file,
            "ai_evaluation": self.messages.get(AI_EVALUATION, ""),
            "code_exec_result": self.messages.get(CODE_EXEC_RESULT, {}),
            "marked_html": marked_html,
            "language": self.language,
        }
        frag.initialize_js("MultiFileCodingAIEvalXBlock", js_data)
        return frag

    def author_view(self, context=None):
        """
        Create preview to be shown to course authors in Studio.
        """
        if not self.validate():
            fragment = Fragment()
            fragment.add_content(
                _(
                    "To ensure this component works correctly, please fix the validation issues."
                )
            )
            return fragment

        return self.student_view(context=context)

    def validate_field_data(self, validation, data):
        """
        Validate fields
        """
        super().validate_field_data(validation, data)

        if data.language != LanguageLabels.HTML_CSS and not data.judge0_api_key:
            validation.add(
                ValidationMessage(
                    ValidationMessage.ERROR, _("Judge0 API key is mandatory")
                )
            )

        # Validate multi-file specific settings
        if data.enable_multi_file:
            if not data.file_templates:
                validation.add(
                    ValidationMessage(
                        ValidationMessage.WARNING, 
                        _("No file templates defined. Students will start with empty projects.")
                    )
                )

    # File Management API Handlers

    @XBlock.json_handler
    def create_file(self, data, suffix=""):
        """Create a new file in the project."""
        try:
            filename = data.get("filename", "")
            content = data.get("content", "")
            file_type = data.get("file_type", "text")
            
            if not filename:
                raise JsonHandlerError(400, "Filename is required")
            
            # Validate filename
            if not self._is_valid_filename(filename):
                raise JsonHandlerError(400, "Invalid filename")
            
            # Check if file already exists
            if filename in self.project_files:
                raise JsonHandlerError(409, "File already exists")
            
            # Create file entry
            self.project_files[filename] = {
                "content": content,
                "type": file_type,
                "created_at": self._get_timestamp(),
                "modified_at": self._get_timestamp(),
                "language": self.language
            }
            
            # Update project structure
            self._update_project_structure()
            
            return {"success": True, "filename": filename}
            
        except JsonHandlerError:
            raise
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            raise JsonHandlerError(500, "Failed to create file")

    @XBlock.json_handler
    def delete_file(self, data, suffix=""):
        """Delete a file from the project."""
        try:
            filename = data.get("filename", "")
            
            if not filename:
                raise JsonHandlerError(400, "Filename is required")
            
            if filename not in self.project_files:
                raise JsonHandlerError(404, "File not found")
            
            # Check if it's a protected file (e.g., main entry point)
            if self._is_protected_file(filename):
                raise JsonHandlerError(403, "Cannot delete protected file")
            
            del self.project_files[filename]
            self._update_project_structure()
            
            return {"success": True, "filename": filename}
            
        except JsonHandlerError:
            raise
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            raise JsonHandlerError(500, "Failed to delete file")

    @XBlock.json_handler
    def rename_file(self, data, suffix=""):
        """Rename a file in the project."""
        try:
            old_filename = data.get("old_filename", "")
            new_filename = data.get("new_filename", "")
            
            if not old_filename or not new_filename:
                raise JsonHandlerError(400, "Both old and new filenames are required")
            
            if old_filename not in self.project_files:
                raise JsonHandlerError(404, "File not found")
            
            if not self._is_valid_filename(new_filename):
                raise JsonHandlerError(400, "Invalid filename")
            
            if new_filename in self.project_files:
                raise JsonHandlerError(409, "File already exists")
            
            # Move file content
            self.project_files[new_filename] = self.project_files[old_filename]
            self.project_files[new_filename]["modified_at"] = self._get_timestamp()
            del self.project_files[old_filename]
            
            self._update_project_structure()
            
            return {"success": True, "old_filename": old_filename, "new_filename": new_filename}
            
        except JsonHandlerError:
            raise
        except Exception as e:
            logger.error(f"Error renaming file: {e}")
            raise JsonHandlerError(500, "Failed to rename file")

    @XBlock.json_handler
    def save_file(self, data, suffix=""):
        """Save file content."""
        try:
            filename = data.get("filename", "")
            content = data.get("content", "")
            
            if not filename:
                raise JsonHandlerError(400, "Filename is required")
            
            if filename not in self.project_files:
                raise JsonHandlerError(404, "File not found")
            
            # Update file content
            self.project_files[filename]["content"] = content
            self.project_files[filename]["modified_at"] = self._get_timestamp()
            
            return {"success": True, "filename": filename}
            
        except JsonHandlerError:
            raise
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise JsonHandlerError(500, "Failed to save file")

    @XBlock.json_handler
    def get_project_structure(self, data, suffix=""):
        """Get current project structure."""
        return {
            "project_files": self.project_files,
            "project_structure": self.project_structure,
            "language": self.language,
            "enable_multi_file": self.enable_multi_file
        }

    @XBlock.json_handler
    def initialize_project(self, data, suffix=""):
        """Initialize project with templates."""
        try:
            if not self.enable_multi_file:
                raise JsonHandlerError(400, "Multi-file support is disabled")
            
            # Clear existing files
            self.project_files = {}
            
            # Load templates for the current language
            templates = self.file_templates.get(self.language, {})
            
            for filename, template_data in templates.items():
                self.project_files[filename] = {
                    "content": template_data.get("content", ""),
                    "type": template_data.get("type", "text"),
                    "created_at": self._get_timestamp(),
                    "modified_at": self._get_timestamp(),
                    "language": self.language
                }
            
            self._update_project_structure()
            
            return {"success": True, "files_created": len(templates)}
            
        except JsonHandlerError:
            raise
        except Exception as e:
            logger.error(f"Error initializing project: {e}")
            raise JsonHandlerError(500, "Failed to initialize project")

    @XBlock.json_handler
    def submit_project(self, data, suffix=""):
        """Submit entire project for execution."""
        try:
            if not self.enable_multi_file:
                # Fall back to single file mode
                return super().submit_code_handler(data, suffix)
            
            # Get all files content
            files_content = {}
            for filename, file_data in self.project_files.items():
                files_content[filename] = file_data["content"]
            
            # Submit to Judge0 with multiple files
            submission_id = self._submit_multi_file_project(files_content)
            
            return {"submission_id": submission_id}
            
        except Exception as e:
            logger.error(f"Error submitting project: {e}")
            raise JsonHandlerError(500, "Failed to submit project")

    @XBlock.json_handler
    def run_test_cases(self, data, suffix=""):
        """Enhanced test case runner with better error handling and reporting."""
        try:
            if not self.test_cases:
                return {
                    "success": True, 
                    "message": "No test cases defined",
                    "results": []
                }
            
            results = []
            total_tests = len(self.test_cases)
            
            for i, test_case in enumerate(self.test_cases):
                try:
                    # Enhanced test case execution with timeout
                    result = self._execute_test_case_enhanced(test_case, i + 1)
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error executing test case {i + 1}: {e}")
                    results.append({
                        "test_case": test_case,
                        "test_number": i + 1,
                        "test_name": test_case.get("name", f"Test {i + 1}"),
                        "passed": False,
                        "error": str(e),
                        "execution_time": 0,
                        "memory_used": 0
                    })
            
            # Calculate summary statistics
            passed_count = sum(1 for r in results if r.get("passed", False))
            failed_count = total_tests - passed_count
            
            return {
                "success": True,
                "results": results,
                "summary": {
                    "total": total_tests,
                    "passed": passed_count,
                    "failed": failed_count,
                    "pass_rate": (passed_count / total_tests * 100) if total_tests > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error running test cases: {e}")
            raise JsonHandlerError(500, f"Failed to run test cases: {str(e)}")

    # Helper methods

    def _is_valid_filename(self, filename):
        """Validate filename for security."""
        import re
        # Allow alphanumeric, dots, underscores, hyphens, and slashes for directories
        valid_pattern = r'^[a-zA-Z0-9._\-/]+$'
        return bool(re.match(valid_pattern, filename)) and len(filename) <= 255

    def _is_protected_file(self, filename):
        """Check if file is protected from deletion."""
        protected_files = ["main.py", "Main.java", "main.cpp", "index.html", "package.json"]
        return filename in protected_files

    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def _update_project_structure(self):
        """Update project structure metadata."""
        self.project_structure = {
            "total_files": len(self.project_files),
            "languages": list(set(file_data.get("language", self.language) 
                                for file_data in self.project_files.values())),
            "last_modified": self._get_timestamp(),
            "file_types": list(set(file_data.get("type", "text") 
                                 for file_data in self.project_files.values()))
        }

    def _submit_multi_file_project(self, files_content):
        """Submit multi-file project to Judge0."""
        # For now, we'll concatenate files or use the main entry point
        # This can be enhanced based on language-specific requirements
        
        main_file = self._get_main_file()
        if main_file and main_file in files_content:
            code = files_content[main_file]
        else:
            # Fallback: concatenate all files
            code = "\n\n".join(f"// {filename}\n{content}" 
                              for filename, content in files_content.items())
        
        return submit_code(self.judge0_api_key, code, self.language)

    def _get_main_file(self):
        """Get the main entry point file for the current language."""
        main_files = {
            LanguageLabels.Python: "main.py",
            LanguageLabels.Java: "Main.java",
            LanguageLabels.CPP: "main.cpp",
            LanguageLabels.JavaScript: "index.js",
            LanguageLabels.HTML_CSS: "index.html"
        }
        return main_files.get(self.language, "main.py")

    def _execute_test_case_enhanced(self, test_case, test_number):
        """Enhanced test case execution with better error handling."""
        try:
            # Get test case parameters
            test_name = test_case.get("name", f"Test {test_number}")
            test_description = test_case.get("description", "")
            input_data = test_case.get("input", "")
            expected_output = test_case.get("expected_output", "")
            timeout = test_case.get("timeout", 10)
            test_type = test_case.get("type", "output_comparison")
            
            # Get the main file content
            main_file_content = self._get_main_file_content()
            
            if not main_file_content:
                return {
                    "test_case": test_case,
                    "test_number": test_number,
                    "test_name": test_name,
                    "passed": False,
                    "error": "No main file content found",
                    "execution_time": 0,
                    "memory_used": 0
                }
            
            # Prepare code with test input
            test_code = main_file_content
            if input_data:
                if self.language == LanguageLabels.Python:
                    test_code += f"\n\n# Test input\n{input_data}"
                elif self.language == LanguageLabels.Java:
                    # For Java, we might need to modify the main method
                    pass  # Handle Java-specific input injection
                # Add other language-specific input handling
            
            # Submit code for execution
            submission_id = submit_code(
                self.judge0_api_key,
                test_code,
                self.language
            )
            
            # Wait and get result with timeout
            import time
            start_time = time.time()
            result = self._get_submission_result_with_timeout(
                submission_id, 
                timeout_seconds=timeout
            )
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
            passed = self._compare_test_output(
                stdout, expected_output, test_type
            )
            
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
            logger.error(f"Error in test case execution: {e}")
            return {
                "test_case": test_case,
                "test_number": test_number,
                "test_name": test_name,
                "passed": False,
                "error": str(e),
                "execution_time": 0,
                "memory_used": 0
            }

    def _get_submission_result_with_timeout(self, submission_id, timeout_seconds=10):
        """Get submission result with proper timeout handling."""
        import time
        
        max_attempts = timeout_seconds
        attempt = 0
        
        while attempt < max_attempts:
            try:
                result = get_submission_result(self.judge0_api_key, submission_id)
                status_id = result.get("status", {}).get("id", 0)
                
                # Check if execution is complete
                if status_id not in [1, 2]:  # Not "In Queue" or "Processing"
                    return result
                
                time.sleep(1)
                attempt += 1
                
            except Exception as e:
                logger.error(f"Error getting submission result: {e}")
                break
        
        return None

    def _compare_test_output(self, actual, expected, test_type="output_comparison"):
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
    
    def _execute_test_case(self, test_case):
        """Execute a single test case."""
        try:
            input_data = test_case.get("input", "")
            expected_output = test_case.get("expected_output", "")
            timeout = test_case.get("timeout", 5)
            
            # Submit code with input
            submission_id = submit_code(
                self.judge0_api_key, 
                self._get_main_file_content() + f"\n\n# Test input\n{input_data}", 
                self.language
            )
            
            # Get result
            result = get_submission_result(self.judge0_api_key, submission_id)
            
            # Compare output
            actual_output = result.get("stdout", "").strip()
            passed = actual_output == expected_output.strip()
            
            return {
                "test_case": test_case,
                "passed": passed,
                "actual_output": actual_output,
                "expected_output": expected_output,
                "execution_time": result.get("time", 0),
                "memory_used": result.get("memory", 0)
            }
            
        except Exception as e:
            logger.error(f"Error executing test case: {e}")
            return {
                "test_case": test_case,
                "passed": False,
                "error": str(e)
            }

    def _get_main_file_content(self):
        """Get content of the main file."""
        main_file = self._get_main_file()
        if main_file in self.project_files:
            return self.project_files[main_file]["content"]
        return ""

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            (
                "MultiFileCodingAIEvalXBlock",
                """<multi_file_coding_ai_eval/>
             """,
            ),
            (
                "Multiple MultiFileCodingAIEvalXBlock",
                """<vertical_demo>
                <multi_file_coding_ai_eval/>
                <multi_file_coding_ai_eval/>
                <multi_file_coding_ai_eval/>
                </vertical_demo>
             """,
            ),
        ] 