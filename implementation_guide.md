# Complete XBlock Implementation Guide

## Overview

This guide provides step-by-step instructions to fix the multi-file UI and test case issues in your XBlock project. You can develop and test everything locally using the XBlock workbench.

## Phase 1: Local Development Setup (15 minutes)

### 1. Set up XBlock Workbench

```powershell
# Create a virtual environment
python -m venv xblock-dev
xblock-dev\Scripts\activate

# Install XBlock SDK
pip install xblock-sdk

# Install your XBlock in development mode
pip install -e .

# Install development requirements
pip install -r requirements/dev.txt
```

### 2. Create Environment Configuration

Create a `.env` file in your project root:

```bash
# API Keys for testing
JUDGE0_API_KEY=your_judge0_api_key_here
GPT4O_API_KEY=your_openai_api_key_here
LLAMA_API_URL=your_llama_endpoint_here  # Only if using Llama

# Optional: Set Django settings
DJANGO_SETTINGS_MODULE=workbench.settings
```

### 3. Start the Workbench

```powershell
# Start the workbench server
python -m xblock_sdk.workbench.main

# Or if xblock-sdk installed globally
workbench
```

Navigate to http://localhost:8000 to see your XBlocks in action!

## Phase 2: Fix Multi-File UI Issues (2-3 hours)

### Step 1: Replace JavaScript File

1. **Backup the original file:**
   ```powershell
   copy ai_eval\static\js\src\multi_file_coding_ai_eval.js ai_eval\static\js\src\multi_file_coding_ai_eval.js.backup
   ```

2. **Replace with improved version:**
   ```powershell
   copy multi_file_coding_ai_eval_improved.js ai_eval\static\js\src\multi_file_coding_ai_eval.js
   ```

### Step 2: Replace CSS File

1. **Backup the original file:**
   ```powershell
   copy ai_eval\static\css\multi_file_coding_ai_eval.css ai_eval\static\css\multi_file_coding_ai_eval.css.backup
   ```

2. **Replace with improved version:**
   ```powershell
   copy multi_file_coding_ai_eval_improved.css ai_eval\static\css\multi_file_coding_ai_eval.css
   ```

### Step 3: Fix Monaco Editor Integration

Create `ai_eval/templates/multi_file_monaco_improved.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; padding: 0; overflow: hidden; }
        #container { height: 100vh; }
    </style>
</head>
<body>
    <div id="container"></div>
    
    <script src="https://unpkg.com/monaco-editor@0.44.0/min/vs/loader.js"></script>
    <script>
        require.config({ paths: { vs: 'https://unpkg.com/monaco-editor@0.44.0/min/vs' } });
        
        let editor = null;
        let models = new Map();
        let currentModel = null;
        
        require(['vs/editor/editor.main'], function () {
            // Initialize editor
            editor = monaco.editor.create(document.getElementById('container'), {
                value: '',
                language: '{{ monaco_language }}',
                theme: 'vs-dark',
                automaticLayout: true,
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                wordWrap: 'on',
                scrollBeyondLastLine: false
            });
            
            // Notify parent that Monaco is ready
            parent.postMessage({ type: 'monacoReady' }, '*');
            
            // Handle content changes
            editor.onDidChangeModelContent(function(e) {
                if (currentModel) {
                    parent.postMessage({
                        type: 'contentChanged',
                        filename: currentModel.filename,
                        content: editor.getValue()
                    }, '*');
                }
            });
        });
        
        // Handle messages from parent
        window.addEventListener('message', function(event) {
            if (!editor) return;
            
            const message = event.data;
            
            switch(message.type) {
                case 'createModel':
                    createModel(message.filename, message.content, message.language);
                    break;
                    
                case 'switchToModel':
                    switchToModel(message.filename);
                    break;
                    
                case 'deleteModel':
                    deleteModel(message.filename);
                    break;
                    
                case 'renameModel':
                    renameModel(message.oldFilename, message.newFilename);
                    break;
                    
                case 'getContent':
                    getContent(message.filename);
                    break;
                    
                case 'setContent':
                    // For single file mode
                    editor.setValue(message.content || '');
                    break;
            }
        });
        
        function createModel(filename, content, language) {
            const uri = monaco.Uri.parse(`file:///${filename}`);
            const model = monaco.editor.createModel(content, language, uri);
            models.set(filename, { model, filename, language });
            
            if (!currentModel) {
                switchToModel(filename);
            }
        }
        
        function switchToModel(filename) {
            const modelData = models.get(filename);
            if (modelData) {
                editor.setModel(modelData.model);
                currentModel = modelData;
                
                // Update language
                monaco.editor.setModelLanguage(modelData.model, modelData.language);
            }
        }
        
        function deleteModel(filename) {
            const modelData = models.get(filename);
            if (modelData) {
                modelData.model.dispose();
                models.delete(filename);
                
                // Switch to another model if this was current
                if (currentModel && currentModel.filename === filename) {
                    const remainingModels = Array.from(models.values());
                    if (remainingModels.length > 0) {
                        switchToModel(remainingModels[0].filename);
                    } else {
                        currentModel = null;
                        editor.setModel(monaco.editor.createModel('', 'plaintext'));
                    }
                }
            }
        }
        
        function renameModel(oldFilename, newFilename) {
            const modelData = models.get(oldFilename);
            if (modelData) {
                // Update filename
                modelData.filename = newFilename;
                
                // Move to new key
                models.set(newFilename, modelData);
                models.delete(oldFilename);
                
                // Update current model reference
                if (currentModel && currentModel.filename === oldFilename) {
                    currentModel.filename = newFilename;
                }
            }
        }
        
        function getContent(filename) {
            if (filename) {
                const modelData = models.get(filename);
                if (modelData) {
                    parent.postMessage({
                        type: 'contentResponse',
                        filename: filename,
                        content: modelData.model.getValue()
                    }, '*');
                }
            } else {
                // Single file mode
                parent.postMessage({
                    type: 'singleFileContent',
                    content: editor.getValue()
                }, '*');
            }
        }
        
        // Send usage ID when ready
        parent.postMessage('__USAGE_ID_PLACEHOLDER__', '*');
    </script>
</body>
</html>
```

### Step 4: Test the Multi-File Interface

1. **Restart the workbench:**
   ```powershell
   # Stop with Ctrl+C, then restart
   python -m xblock_sdk.workbench.main
   ```

2. **Navigate to the multi-file XBlock scenario**
3. **Test file operations:**
   - Create new files
   - Switch between files
   - Rename files
   - Delete files
   - Check unsaved changes indicators

## Phase 3: Fix Test Case System (2-3 hours)

### Step 1: Enhance Test Case Handler

Add this improved method to `ai_eval/multi_file_coding_ai_eval.py`:

```python
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
```

### Step 2: Add Sample Test Cases

Add this to your XBlock's `editable_fields` and create sample test cases in the Studio interface:

```python
# In your XBlock Studio interface, add test cases like:
test_cases = [
    {
        "name": "Basic Addition Test",
        "description": "Test basic addition functionality",
        "input": "print(2 + 3)",
        "expected_output": "5",
        "timeout": 5,
        "type": "output_comparison"
    },
    {
        "name": "String Output Test", 
        "description": "Test string output",
        "input": "print('Hello World')",
        "expected_output": "Hello World",
        "timeout": 5,
        "type": "exact_match"
    }
]
```

### Step 3: Test the Test Case System

1. **Restart workbench and navigate to multi-file XBlock**
2. **Configure test cases in the Studio interface**
3. **Click "Run Tests" button**
4. **Verify:**
   - Test execution starts (loading indicator)
   - Results display properly
   - Pass/fail counts are correct
   - Individual test details show

## Phase 4: Final Integration Testing (30 minutes)

### Test Checklist

#### Multi-File Interface:
- [ ] Create new files
- [ ] Switch between files smoothly
- [ ] File tabs show unsaved changes (*)
- [ ] Rename files works
- [ ] Delete files works
- [ ] Auto-save functionality
- [ ] Monaco editor syntax highlighting
- [ ] Project initialization from templates

#### Test Case System:
- [ ] Test cases execute properly
- [ ] Results display correctly
- [ ] Pass/fail indicators work
- [ ] Test output comparison accurate
- [ ] Error handling for failed tests
- [ ] Timeout handling works

#### Integration:
- [ ] Code submission works with multi-file
- [ ] AI evaluation receives correct code
- [ ] Judge0 execution works
- [ ] Reset functionality works
- [ ] Responsive design on mobile

## Phase 5: Deploy to Production

### Option 1: Direct Git Installation

1. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Fix multi-file UI and test case system"
   git push origin main
   ```

2. **Update Tutor configuration:**
   ```yaml
   OPENEDX_EXTRA_PIP_REQUIREMENTS:
     - git+https://github.com/your-repo/xblock-ai-evaluation@main
   ```

3. **Restart Tutor:**
   ```bash
   tutor local stop
   tutor local start
   ```

### Option 2: PyPI Package

1. **Update version in setup.py**
2. **Build and upload:**
   ```bash
   python setup.py sdist bdist_wheel
   twine upload dist/*
   ```

3. **Update Tutor configuration:**
   ```yaml
   OPENEDX_EXTRA_PIP_REQUIREMENTS:
     - xblock-ai-eval==0.3.0
   ```

## Troubleshooting Common Issues

### Monaco Editor Not Loading
- Check browser console for errors
- Verify CDN URLs are accessible
- Check iframe srcdoc content

### Test Cases Not Running
- Verify Judge0 API key is correct
- Check network connectivity
- Review server logs for errors

### File Operations Not Working
- Check backend handler responses
- Verify JSON data format
- Check browser network tab

### UI Layout Issues
- Clear browser cache
- Check CSS conflicts
- Test responsive breakpoints

## Performance Optimizations

1. **Lazy load Monaco Editor models**
2. **Implement debounced auto-save**
3. **Cache test results**
4. **Optimize file tree rendering for large projects**
5. **Add loading states for better UX**

---

This implementation guide should get your multi-file interface and test case system working smoothly. The local development setup with XBlock workbench allows for rapid iteration without needing to rebuild Docker images.

Start with Phase 1 to get the local environment running, then tackle the UI fixes in Phase 2. The test case system in Phase 3 is more complex but builds on the foundation you'll have established.

Let me know if you need help with any specific step!
