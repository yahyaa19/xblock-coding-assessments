# Testing XBlock Changes in Your Tutor Environment

Since the XBlock SDK has compatibility issues, let's use your existing Tutor setup for development. This is actually more realistic since you'll test in the same environment where the XBlock will run in production.

## Quick Development Setup

### 1. Install Your XBlock in Tutor's OpenEDX

First, let's get your XBlock installed in your Tutor environment:

```powershell
# Make sure Tutor is running
tutor local status

# If not running, start it
tutor local start

# Install your XBlock in development mode
tutor local exec lms pip install -e /openedx/xblock-coding-assessments

# OR install from git (if you've pushed changes)
tutor local exec lms pip install git+https://github.com/your-username/xblock-ai-evaluation

# Restart the LMS to pick up changes
tutor local restart lms
```

### 2. Enable Your XBlocks in Studio

1. **Access Studio**: Go to `http://studio.localhost` (or your Tutor domain)

2. **Navigate to Advanced Settings**: 
   - Go to `Settings > Advanced Settings`
   - Find `Advanced Module List`

3. **Add Your XBlocks**:
   ```json
   [
       "shortanswer_ai_eval",
       "coding_ai_eval", 
       "multi_file_coding_ai_eval"
   ]
   ```

4. **Save the settings**

### 3. Create Test Course and Add XBlocks

1. **Create a new course** in Studio
2. **Add a new Unit**
3. **Click "Advanced"** in the "Add New Component" section  
4. **Select your XBlocks** from the list

### 4. Configure XBlocks

1. **Click "Edit" on your XBlock**
2. **Configure the settings**:
   - Set Judge0 API Key: `e950c8f429msh00449efd78f10acp13e30ajsn0c46894c0ee4`
   - Set OpenAI API Key (if you have one)
   - Add test questions
   - Configure programming language

### 5. Development Workflow

For rapid development, you can:

1. **Mount your code directory** in Tutor:
   ```powershell
   # Edit your tutor config
   tutor config save --set MOUNTS="/path/to/your/xblock:/openedx/xblock-coding-assessments"
   
   # Or add to your existing mounts in config.yml:
   MOUNTS:
     - "/path/to/your/xblock:/openedx/xblock-coding-assessments"
   ```

2. **Make changes** to your XBlock code locally

3. **Restart the LMS** to see changes:
   ```powershell
   tutor local restart lms
   ```

## Benefits of This Approach

- ✅ **No compatibility issues** - Uses your working Tutor setup
- ✅ **Real environment testing** - Same as production
- ✅ **Studio integration** - Test the full authoring experience  
- ✅ **Quick iterations** - Mount local code for fast development
- ✅ **Database persistence** - Your test data stays between restarts

## Implementing Your Improvements

Now you can implement the improvements I provided:

1. **Replace the JavaScript file**:
   ```powershell
   copy multi_file_coding_ai_eval_improved.js ai_eval\static\js\src\multi_file_coding_ai_eval.js
   ```

2. **Replace the CSS file**:
   ```powershell
   copy multi_file_coding_ai_eval_improved.css ai_eval\static\css\multi_file_coding_ai_eval.css
   ```

3. **Add enhanced test case handling** to your Python files

4. **Restart LMS** to see changes:
   ```powershell
   tutor local restart lms
   ```

5. **Test in Studio and LMS** by creating units with your XBlocks

## Testing Specific Issues

### Multi-File UI Testing
1. Create a multi-file coding assessment
2. Test file creation, deletion, renaming
3. Test tab switching
4. Test Monaco editor integration

### Test Case System Testing  
1. Configure test cases in Studio
2. Write student code
3. Click "Run Tests"
4. Verify results display properly

This approach lets you test everything in a real OpenEDX environment without SDK compatibility headaches!
