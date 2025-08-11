# Local XBlock Development Setup Guide

## Quick Setup for Local Testing

### 1. Install XBlock SDK (Workbench)
```bash
# Create a new virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install XBlock SDK
pip install xblock-sdk

# Install your XBlock in development mode
pip install -e .

# Install additional requirements
pip install -r requirements/dev.txt
```

### 2. Start the Workbench
```bash
# Start the XBlock workbench server
python -m xblock_sdk.workbench.main

# Or run directly
workbench
```

This will start a local server (usually at http://localhost:8000) where you can test your XBlocks without needing a full Open edX installation.

### 3. Access Your XBlocks
- Navigate to http://localhost:8000
- You'll see the scenarios defined in your `workbench_scenarios()` methods
- Test all three XBlocks: ShortAnswer, Coding, and MultiFileCoding

### 4. Development Workflow
```bash
# Make changes to your code
# Restart the workbench to see changes
# Or use auto-reload (if supported)
python -m xblock_sdk.workbench.main --reload
```

## Alternative: Docker Development
```bash
# If you prefer Docker
docker run -it -p 8000:8000 -v $(pwd):/usr/local/src/xblock-ai-eval openedx/xblock-sdk
```

## Configuration for Testing

### Environment Variables
Create a `.env` file:
```bash
JUDGE0_API_KEY=your_judge0_key
GPT4O_API_KEY=your_openai_key
LLAMA_API_URL=your_llama_endpoint  # Only for Llama
```

### Test Data Setup
The workbench will use the default values from your XBlock fields, but you can modify them through the UI or programmatically.

## Benefits of Local Development
1. **Fast iteration**: No need to rebuild Docker images
2. **Easy debugging**: Use print statements, pdb, or IDE debugging
3. **Isolated testing**: Test individual components
4. **Quick UI changes**: See frontend changes immediately
5. **API testing**: Test external integrations safely

## Next Steps
Once you're satisfied with local testing:
1. Test in a staging Open edX environment
2. Deploy to production using pip install from git repo
3. Update Tutor configuration if needed
