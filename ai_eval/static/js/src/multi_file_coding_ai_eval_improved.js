/* Enhanced JavaScript for MultiFileCodingAIEvalXBlock */

function MultiFileCodingAIEvalXBlock(runtime, element, data) {
  // Handler URLs
  const createFileHandlerURL = runtime.handlerUrl(element, "create_file");
  const deleteFileHandlerURL = runtime.handlerUrl(element, "delete_file");
  const renameFileHandlerURL = runtime.handlerUrl(element, "rename_file");
  const saveFileHandlerURL = runtime.handlerUrl(element, "save_file");
  const getProjectStructureHandlerURL = runtime.handlerUrl(element, "get_project_structure");
  const initializeProjectHandlerURL = runtime.handlerUrl(element, "initialize_project");
  const submitProjectHandlerURL = runtime.handlerUrl(element, "submit_project");
  const runTestsHandlerURL = runtime.handlerUrl(element, "run_test_cases");
  const resetHandlerURL = runtime.handlerUrl(element, "reset_handler");
  const submissionResultURL = runtime.handlerUrl(element, "get_submission_result_handler");
  const llmResponseHandlerURL = runtime.handlerUrl(element, "get_response");

  // Constants
  const HTML_CSS = "HTML/CSS";
  const MAX_JUDGE0_RETRY_ITER = 5;
  const WAIT_TIME_MS = 1000;

  // DOM elements
  const iframe = $("#monaco", element)[0];
  const fileExplorer = $("#file-explorer", element);
  const fileTree = $("#file-tree", element);
  const editorTabs = $("#editor-tabs", element);
  const submitButton = $("#submit-button", element);
  const resetButton = $("#reset-button", element);
  const runTestsButton = $("#run-tests-btn", element);
  const newFileButton = $("#new-file-btn", element);
  const initializeProjectButton = $("#initialize-project-btn", element);
  const AIFeedback = $("#ai-feedback", element);
  const stdout = $(".stdout", element);
  const stderr = $(".stderr", element);
  const htmlRenderIframe = $(".html-render", element);

  // Test result elements
  const testResultsContainer = $("#test-results-list", element);
  const testCountElement = $("#test-count", element);
  const testPassedElement = $("#test-passed", element);
  const testFailedElement = $("#test-failed", element);

  // State management
  let currentProject = {
    files: data.project_files || {},
    structure: data.project_structure || {},
    currentFile: null,
    enableMultiFile: data.enable_multi_file || false,
    unsavedChanges: new Set()
  };

  let testResults = [];
  let isSubmitting = false;
  let monacoModels = new Map(); // Store Monaco models for each file

  // Initialize
  $(function () {
    const xblockUsageId =
      element.getAttribute?.("data-usage") ||
      element.getAttribute?.("data-usage-id") ||
      element?.[0].getAttribute("data-usage-id");

    if (!xblockUsageId) {
      throw new Error("XBlock is missing a usage ID attribute on its root HTML node.");
    }

    // Load marked for question rendering
    loadMarkedInIframe(data.marked_html);
    
    // Initialize Monaco Editor
    iframe.srcdoc = data.monaco_html.replace(
      "__USAGE_ID_PLACEHOLDER__",
      xblockUsageId,
    );
    
    runFuncAfterLoading(init);
  });

  // Initialize the interface
  function init() {
    $(document).trigger('xblock-initialized', [element]);
    
    if (currentProject.enableMultiFile) {
      initializeMultiFileInterface();
    } else {
      // Fall back to single file mode
      initializeSingleFileInterface();
    }

    // Set up event listeners
    setupEventListeners();
    
    // Load existing project data
    loadProjectData();
    
    // Render question with markdown
    $("#question-text", element).html(MarkdownToHTML(data.question));
    
    // Load existing AI feedback and test results
    if (data.ai_evaluation) {
      AIFeedback.html(MarkdownToHTML(data.ai_evaluation));
    }
    
    // Set initial tab
    switchTab('output');
  }

  function initializeMultiFileInterface() {
    // Initialize file explorer
    renderFileTree();
    
    // Initialize editor tabs
    renderEditorTabs();
    
    // Set up Monaco editor communication
    setupMonacoCommunication();
    
    // Show file explorer and adjust layout
    fileExplorer.show();
    $(".main-editor-area").css("flex", "1");
  }

  function initializeSingleFileInterface() {
    // Hide multi-file specific elements
    fileExplorer.hide();
    $(".result-panel").css("width", "100%");
    
    // Set up basic Monaco communication for single file
    setupBasicMonacoCommunication();
  }

  function setupEventListeners() {
    // Button event listeners
    submitButton.on("click", submitCode);
    resetButton.on("click", resetProject);
    runTestsButton.on("click", runTestCases);
    newFileButton.on("click", showCreateFileModal);
    initializeProjectButton.on("click", showInitializeProjectModal);

    // Tab switching
    $(".result-tab-btn").on("click", function() {
      const tabId = $(this).data("id");
      switchTab(tabId);
    });

    // Modal event listeners
    setupModalEventListeners();
    
    // Auto-save functionality
    setupAutoSave();
  }

  function setupModalEventListeners() {
    // File creation modal
    const fileModal = $("#file-modal", element);
    const closeButtons = fileModal.find(".close, #cancel-file-btn");
    const createFileBtn = $("#create-file-btn", element);

    closeButtons.on("click", function() {
      fileModal.hide();
      clearFileModal();
    });

    createFileBtn.on("click", createNewFile);

    // Project initialization modal
    const projectModal = $("#project-modal", element);
    const projectCloseButtons = projectModal.find(".close, #cancel-init-btn");
    const confirmInitBtn = $("#confirm-init-btn", element);

    projectCloseButtons.on("click", function() {
      projectModal.hide();
    });

    confirmInitBtn.on("click", initializeProject);

    // Close modals when clicking outside
    $(window).on("click", function(event) {
      if (event.target === fileModal[0]) {
        fileModal.hide();
        clearFileModal();
      }
      if (event.target === projectModal[0]) {
        projectModal.hide();
      }
    });
  }

  function setupAutoSave() {
    // Auto-save every 5 seconds if there are unsaved changes
    setInterval(() => {
      if (currentProject.unsavedChanges.size > 0 && currentProject.currentFile) {
        saveCurrentFile();
      }
    }, 5000);
  }

  // File Management Functions

  function renderFileTree() {
    fileTree.empty();
    
    const sortedFiles = Object.keys(currentProject.files).sort();
    
    sortedFiles.forEach(filename => {
      const fileItem = createFileItem(filename);
      fileTree.append(fileItem);
    });

    if (sortedFiles.length === 0) {
      fileTree.append('<div class="file-item empty-state">No files in project<br><small>Click + to create a new file</small></div>');
    }
    
    // Select first file if none is selected
    if (!currentProject.currentFile && sortedFiles.length > 0) {
      switchToFile(sortedFiles[0]);
    }
  }

  function createFileItem(filename) {
    const fileData = currentProject.files[filename];
    const isActive = currentProject.currentFile === filename;
    const hasUnsavedChanges = currentProject.unsavedChanges.has(filename);
    const fileIcon = getFileIcon(filename);
    
    const fileItem = $(`
      <div class="file-item ${isActive ? 'active' : ''}" data-filename="${filename}">
        <span class="file-item-icon ${fileIcon}"></span>
        <span class="file-item-name">${filename}${hasUnsavedChanges ? ' *' : ''}</span>
        <div class="file-item-actions">
          <button class="file-action-btn rename-file" title="Rename">✏️</button>
          <button class="file-action-btn delete-file" title="Delete">🗑️</button>
        </div>
      </div>
    `);
    
    return fileItem;
  }

  function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    const iconMap = {
      'py': 'file-icon-python',
      'js': 'file-icon-javascript', 
      'java': 'file-icon-java',
      'cpp': 'file-icon-cpp',
      'c': 'file-icon-cpp',
      'html': 'file-icon-html',
      'htm': 'file-icon-html',
      'css': 'file-icon-css',
      'json': 'file-icon-json',
      'txt': 'file-icon-text',
      'md': 'file-icon-text'
    };
    return iconMap[extension] || 'file-icon-text';
  }

  function renderEditorTabs() {
    editorTabs.empty();
    
    const sortedFiles = Object.keys(currentProject.files).sort();
    
    sortedFiles.forEach(filename => {
      const isActive = currentProject.currentFile === filename;
      const hasUnsavedChanges = currentProject.unsavedChanges.has(filename);
      const tab = createEditorTab(filename, isActive, hasUnsavedChanges);
      editorTabs.append(tab);
    });
    
    // Add scroll buttons if needed
    checkTabOverflow();
  }

  function createEditorTab(filename, isActive, hasUnsavedChanges) {
    return $(`
      <div class="editor-tab ${isActive ? 'active' : ''}" data-filename="${filename}">
        <span class="editor-tab-name">${filename}${hasUnsavedChanges ? ' *' : ''}</span>
        <span class="editor-tab-close" title="Close file">×</span>
      </div>
    `);
  }

  function checkTabOverflow() {
    const tabsContainer = editorTabs[0];
    const isOverflowing = tabsContainer.scrollWidth > tabsContainer.clientWidth;
    
    if (isOverflowing) {
      editorTabs.addClass('overflowing');
    } else {
      editorTabs.removeClass('overflowing');
    }
  }

  // Monaco Editor Communication

  function setupMonacoCommunication() {
    // Listen for Monaco editor ready
    window.addEventListener('message', function(event) {
      if (event.data && event.data.type === 'monacoReady') {
        setupMonacoModels();
      }
    });

    // Set up file tree interactions
    fileTree.on('click', '.file-item:not(.empty-state)', function() {
      const filename = $(this).data('filename');
      if (filename) {
        switchToFile(filename);
      }
    });

    fileTree.on('click', '.delete-file', function(e) {
      e.stopPropagation();
      const filename = $(this).closest('.file-item').data('filename');
      confirmDeleteFile(filename);
    });

    fileTree.on('click', '.rename-file', function(e) {
      e.stopPropagation();
      const filename = $(this).closest('.file-item').data('filename');
      showRenameFileModal(filename);
    });

    // Set up editor tab interactions
    editorTabs.on('click', '.editor-tab', function(e) {
      if (!$(e.target).hasClass('editor-tab-close')) {
        const filename = $(this).data('filename');
        switchToFile(filename);
      }
    });

    editorTabs.on('click', '.editor-tab-close', function(e) {
      e.stopPropagation();
      const filename = $(this).closest('.editor-tab').data('filename');
      confirmDeleteFile(filename);
    });
  }

  function setupBasicMonacoCommunication() {
    window.addEventListener('message', function(event) {
      if (event.data && event.data.type === 'monacoReady') {
        // Load single file content if available
        const singleFileContent = data.code || '';
        iframe.contentWindow.postMessage({
          type: 'setContent',
          content: singleFileContent
        }, '*');
      }
    });
  }

  function setupMonacoModels() {
    // Create Monaco models for all files
    Object.keys(currentProject.files).forEach(filename => {
      createMonacoModel(filename);
    });
    
    // Switch to current file
    if (currentProject.currentFile) {
      switchToFile(currentProject.currentFile);
    }
  }

  function createMonacoModel(filename) {
    const fileData = currentProject.files[filename];
    const language = getMonacoLanguage(filename);
    
    iframe.contentWindow.postMessage({
      type: 'createModel',
      filename: filename,
      content: fileData.content || '',
      language: language
    }, '*');
  }

  function getMonacoLanguage(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    const languageMap = {
      'py': 'python',
      'js': 'javascript',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'html': 'html',
      'htm': 'html',
      'css': 'css',
      'json': 'json',
      'txt': 'plaintext',
      'md': 'markdown'
    };
    return languageMap[extension] || 'plaintext';
  }

  function switchToFile(filename) {
    if (!currentProject.files[filename]) {
      console.error('File not found:', filename);
      return;
    }

    // Save current file before switching
    if (currentProject.currentFile && currentProject.currentFile !== filename) {
      saveCurrentFile();
    }

    currentProject.currentFile = filename;
    
    // Update UI
    updateFileTreeSelection(filename);
    updateEditorTabs(filename);
    
    // Switch model in Monaco editor
    iframe.contentWindow.postMessage({
      type: 'switchToModel',
      filename: filename
    }, '*');
  }

  function updateFileTreeSelection(filename) {
    fileTree.find('.file-item').removeClass('active');
    fileTree.find(`[data-filename="${filename}"]`).addClass('active');
  }

  function updateEditorTabs(filename) {
    editorTabs.find('.editor-tab').removeClass('active');
    editorTabs.find(`[data-filename="${filename}"]`).addClass('active');
  }

  // File Operations

  function showCreateFileModal() {
    const modal = $("#file-modal", element);
    clearFileModal();
    modal.show();
    $("#new-filename", element).focus();
  }

  function clearFileModal() {
    $("#new-filename", element).val('');
    $("#file-content", element).val('');
    $("#file-type", element).val('text');
  }

  function createNewFile() {
    const filename = $("#new-filename", element).val().trim();
    const content = $("#file-content", element).val();
    const fileType = $("#file-type", element).val();
    
    if (!filename) {
      alert('Please enter a filename');
      return;
    }
    
    if (currentProject.files[filename]) {
      alert('File already exists');
      return;
    }
    
    // Validate filename
    if (!isValidFilename(filename)) {
      alert('Invalid filename. Use only letters, numbers, dots, underscores and hyphens.');
      return;
    }
    
    // Add file to project
    currentProject.files[filename] = {
      content: content,
      type: fileType,
      created_at: new Date().toISOString(),
      modified_at: new Date().toISOString(),
      language: data.language
    };
    
    // Update UI
    renderFileTree();
    renderEditorTabs();
    createMonacoModel(filename);
    switchToFile(filename);
    
    // Save to backend
    saveFileToBackend(filename);
    
    // Close modal
    $("#file-modal", element).hide();
  }

  function confirmDeleteFile(filename) {
    if (!filename || !currentProject.files[filename]) {
      return;
    }
    
    const hasUnsavedChanges = currentProject.unsavedChanges.has(filename);
    const message = hasUnsavedChanges 
      ? `Delete "${filename}"? You have unsaved changes that will be lost.`
      : `Delete "${filename}"?`;
    
    if (confirm(message)) {
      deleteFile(filename);
    }
  }

  function deleteFile(filename) {
    if (!currentProject.files[filename]) {
      return;
    }
    
    // Remove from project
    delete currentProject.files[filename];
    currentProject.unsavedChanges.delete(filename);
    
    // If this was the current file, switch to another
    if (currentProject.currentFile === filename) {
      const remainingFiles = Object.keys(currentProject.files);
      currentProject.currentFile = remainingFiles.length > 0 ? remainingFiles[0] : null;
    }
    
    // Update UI
    renderFileTree();
    renderEditorTabs();
    
    // Delete Monaco model
    iframe.contentWindow.postMessage({
      type: 'deleteModel',
      filename: filename
    }, '*');
    
    // Switch to new current file
    if (currentProject.currentFile) {
      switchToFile(currentProject.currentFile);
    }
    
    // Delete from backend
    deleteFileFromBackend(filename);
  }

  function showRenameFileModal(filename) {
    const newName = prompt(`Rename "${filename}" to:`, filename);
    if (newName && newName !== filename && isValidFilename(newName)) {
      if (!currentProject.files[newName]) {
        renameFile(filename, newName);
      } else {
        alert('File already exists');
      }
    }
  }

  function renameFile(oldFilename, newFilename) {
    // Update project
    currentProject.files[newFilename] = currentProject.files[oldFilename];
    delete currentProject.files[oldFilename];
    
    // Update unsaved changes tracking
    if (currentProject.unsavedChanges.has(oldFilename)) {
      currentProject.unsavedChanges.delete(oldFilename);
      currentProject.unsavedChanges.add(newFilename);
    }
    
    // Update current file reference
    if (currentProject.currentFile === oldFilename) {
      currentProject.currentFile = newFilename;
    }
    
    // Update UI
    renderFileTree();
    renderEditorTabs();
    
    // Rename Monaco model
    iframe.contentWindow.postMessage({
      type: 'renameModel',
      oldFilename: oldFilename,
      newFilename: newFilename
    }, '*');
    
    // Save to backend
    renameFileInBackend(oldFilename, newFilename);
  }

  function isValidFilename(filename) {
    const validPattern = /^[a-zA-Z0-9._\-\/]+$/;
    return validPattern.test(filename) && filename.length <= 255;
  }

  // Backend Communication

  function saveFileToBackend(filename) {
    const fileData = currentProject.files[filename];
    
    $.ajax({
      url: createFileHandlerURL,
      method: 'POST',
      data: JSON.stringify({
        filename: filename,
        content: fileData.content,
        file_type: fileData.type
      }),
      success: function(response) {
        console.log('File created successfully:', response);
      },
      error: function(xhr, status, error) {
        console.error('Error creating file:', error);
        alert('Failed to create file on server');
      }
    });
  }

  function deleteFileFromBackend(filename) {
    $.ajax({
      url: deleteFileHandlerURL,
      method: 'POST',
      data: JSON.stringify({
        filename: filename
      }),
      success: function(response) {
        console.log('File deleted successfully:', response);
      },
      error: function(xhr, status, error) {
        console.error('Error deleting file:', error);
      }
    });
  }

  function renameFileInBackend(oldFilename, newFilename) {
    $.ajax({
      url: renameFileHandlerURL,
      method: 'POST',
      data: JSON.stringify({
        old_filename: oldFilename,
        new_filename: newFilename
      }),
      success: function(response) {
        console.log('File renamed successfully:', response);
      },
      error: function(xhr, status, error) {
        console.error('Error renaming file:', error);
        alert('Failed to rename file on server');
      }
    });
  }

  function saveCurrentFile() {
    if (!currentProject.currentFile) {
      return;
    }
    
    const filename = currentProject.currentFile;
    
    // Get content from Monaco editor
    iframe.contentWindow.postMessage({
      type: 'getContent',
      filename: filename
    }, '*');
    
    // Listen for content response
    window.addEventListener('message', function contentListener(event) {
      if (event.data && event.data.type === 'contentResponse' && event.data.filename === filename) {
        window.removeEventListener('message', contentListener);
        
        // Update project file content
        currentProject.files[filename].content = event.data.content;
        currentProject.files[filename].modified_at = new Date().toISOString();
        
        // Save to backend
        $.ajax({
          url: saveFileHandlerURL,
          method: 'POST',
          data: JSON.stringify({
            filename: filename,
            content: event.data.content
          }),
          success: function(response) {
            currentProject.unsavedChanges.delete(filename);
            updateFileDisplays(filename);
          },
          error: function(xhr, status, error) {
            console.error('Error saving file:', error);
          }
        });
      }
    });
  }

  function updateFileDisplays(filename) {
    // Update file tree display
    const fileItem = fileTree.find(`[data-filename="${filename}"]`);
    const fileName = fileItem.find('.file-item-name');
    fileName.text(filename); // Remove the * indicator
    
    // Update editor tab display
    const editorTab = editorTabs.find(`[data-filename="${filename}"]`);
    const tabName = editorTab.find('.editor-tab-name');
    tabName.text(filename); // Remove the * indicator
  }

  // Project Operations

  function loadProjectData() {
    // Load existing AI evaluation if available
    if (data.ai_evaluation) {
      AIFeedback.html(MarkdownToHTML(data.ai_evaluation));
    }
    
    // Load existing code execution results
    if (data.code_exec_result) {
      if (data.code_exec_result.stdout) {
        stdout.text(data.code_exec_result.stdout);
      }
      if (data.code_exec_result.stderr) {
        stderr.text(data.code_exec_result.stderr);
      }
    }
    
    // Initialize project if no files exist
    if (Object.keys(currentProject.files).length === 0 && data.file_templates) {
      initializeFromTemplates();
    }
  }

  function showInitializeProjectModal() {
    const modal = $("#project-modal", element);
    
    // Show template preview
    const preview = $("#template-preview", element);
    preview.empty();
    
    const templates = data.file_templates[data.language] || {};
    Object.keys(templates).forEach(filename => {
      const template = templates[filename];
      const templateElement = $(`
        <div class="template-file">
          <div class="template-file-name">${filename}</div>
          <div class="template-file-content">${template.content.substring(0, 200)}${template.content.length > 200 ? '...' : ''}</div>
        </div>
      `);
      preview.append(templateElement);
    });
    
    if (Object.keys(templates).length === 0) {
      preview.append('<div class="template-file">No templates available for this language</div>');
    }
    
    modal.show();
  }

  function initializeProject() {
    if (Object.keys(currentProject.files).length > 0) {
      if (!confirm('This will replace all existing files. Continue?')) {
        return;
      }
    }
    
    $.ajax({
      url: initializeProjectHandlerURL,
      method: 'POST',
      data: JSON.stringify({}),
      success: function(response) {
        // Reload project structure
        location.reload(); // Simple approach - reload the whole XBlock
      },
      error: function(xhr, status, error) {
        console.error('Error initializing project:', error);
        alert('Failed to initialize project');
      }
    });
    
    $("#project-modal", element).hide();
  }

  function initializeFromTemplates() {
    const templates = data.file_templates[data.language] || {};
    
    Object.keys(templates).forEach(filename => {
      const template = templates[filename];
      currentProject.files[filename] = {
        content: template.content || '',
        type: template.type || 'text',
        created_at: new Date().toISOString(),
        modified_at: new Date().toISOString(),
        language: data.language
      };
    });
    
    if (Object.keys(templates).length > 0) {
      renderFileTree();
      renderEditorTabs();
      
      // Set up Monaco models when ready
      setTimeout(() => {
        Object.keys(templates).forEach(filename => {
          createMonacoModel(filename);
        });
        
        // Switch to first file
        const firstFile = Object.keys(templates)[0];
        if (firstFile) {
          switchToFile(firstFile);
        }
      }, 1000);
    }
  }

  // Test Case Management

  function runTestCases() {
    if (!data.test_cases || data.test_cases.length === 0) {
      alert('No test cases defined for this assignment');
      return;
    }
    
    // Save current file before running tests
    if (currentProject.currentFile) {
      saveCurrentFile();
    }
    
    // Show test results tab and loading state
    switchTab('test-results');
    showTestsLoading();
    
    $.ajax({
      url: runTestsHandlerURL,
      method: 'POST',
      data: JSON.stringify({}),
      success: function(response) {
        handleTestResults(response.results || []);
      },
      error: function(xhr, status, error) {
        console.error('Error running tests:', error);
        showTestsError('Failed to run test cases: ' + error);
      }
    });
  }

  function showTestsLoading() {
    testResultsContainer.html(`
      <div class="test-loading">
        <div class="spinner"></div>
        <p>Running test cases...</p>
      </div>
    `);
    
    testCountElement.text('...');
    testPassedElement.text('...');
    testFailedElement.text('...');
  }

  function showTestsError(message) {
    testResultsContainer.html(`
      <div class="test-error">
        <p>❌ ${message}</p>
      </div>
    `);
    
    testCountElement.text('0');
    testPassedElement.text('0');
    testFailedElement.text('0');
  }

  function handleTestResults(results) {
    testResults = results;
    
    const totalTests = results.length;
    const passedTests = results.filter(r => r.passed).length;
    const failedTests = totalTests - passedTests;
    
    // Update summary
    testCountElement.text(totalTests);
    testPassedElement.text(passedTests);
    testFailedElement.text(failedTests);
    
    // Render test results
    renderTestResults(results);
  }

  function renderTestResults(results) {
    testResultsContainer.empty();
    
    if (results.length === 0) {
      testResultsContainer.append('<div class="no-tests">No test results available</div>');
      return;
    }
    
    results.forEach((result, index) => {
      const resultElement = createTestResultElement(result, index);
      testResultsContainer.append(resultElement);
    });
  }

  function createTestResultElement(result, index) {
    const status = result.passed ? 'passed' : 'failed';
    const statusIcon = result.passed ? '✅' : '❌';
    const testCase = result.test_case || {};
    
    return $(`
      <div class="test-result-item ${status}">
        <div class="test-result-header">
          <span class="test-result-name">Test ${index + 1}: ${testCase.name || 'Unnamed Test'}</span>
          <span class="test-result-status ${status}">${statusIcon} ${status.toUpperCase()}</span>
        </div>
        <div class="test-result-details">
          ${testCase.description ? `<div><strong>Description:</strong> ${testCase.description}</div>` : ''}
          ${result.error ? `<div class="test-error"><strong>Error:</strong> ${result.error}</div>` : ''}
          ${result.actual_output !== undefined ? `
            <div class="test-output">
              <div><strong>Expected Output:</strong></div>
              <pre class="expected-output">${result.expected_output || 'No expected output'}</pre>
              <div><strong>Actual Output:</strong></div>
              <pre class="actual-output">${result.actual_output || 'No output'}</pre>
            </div>
          ` : ''}
          ${result.execution_time ? `<div><small>Execution time: ${result.execution_time}s</small></div>` : ''}
        </div>
      </div>
    `);
  }

  // Code Submission

  function submitCode() {
    if (isSubmitting) {
      return;
    }
    
    // Save current file
    if (currentProject.currentFile) {
      saveCurrentFile();
    }
    
    // Check if we have any files
    if (Object.keys(currentProject.files).length === 0) {
      alert('No files to submit');
      return;
    }
    
    isSubmitting = true;
    disableSubmitButton();
    
    if (currentProject.enableMultiFile) {
      submitMultiFileProject();
    } else {
      submitSingleFile();
    }
  }

  function submitMultiFileProject() {
    $.ajax({
      url: submitProjectHandlerURL,
      method: 'POST',
      data: JSON.stringify({
        files: currentProject.files
      }),
      success: function(response) {
        if (response.submission_id) {
          pollSubmissionResult(response.submission_id);
        } else {
          handleSubmissionError('No submission ID received');
        }
      },
      error: function(xhr, status, error) {
        handleSubmissionError(error);
      }
    });
  }

  function submitSingleFile() {
    // Get the current file content or main file
    let codeContent = '';
    if (currentProject.currentFile) {
      codeContent = currentProject.files[currentProject.currentFile].content || '';
    } else if (data.code) {
      codeContent = data.code;
    } else {
      // Get content from Monaco if in single file mode
      iframe.contentWindow.postMessage({
        type: 'getContent'
      }, '*');
      return; // Will continue in message handler
    }
    
    submitCodeToJudge0(codeContent);
  }

  function submitCodeToJudge0(code) {
    const submitHandlerURL = runtime.handlerUrl(element, "submit_code_handler");
    
    $.ajax({
      url: submitHandlerURL,
      method: 'POST',
      data: JSON.stringify({
        user_code: code
      }),
      success: function(response) {
        if (response.submission_id) {
          pollSubmissionResult(response.submission_id);
        } else {
          handleSubmissionError('No submission ID received');
        }
      },
      error: function(xhr, status, error) {
        handleSubmissionError(error);
      }
    });
  }

  function pollSubmissionResult(submissionId) {
    let retries = 0;
    
    function checkResult() {
      $.ajax({
        url: submissionResultURL,
        method: 'POST',
        data: JSON.stringify({
          submission_id: submissionId
        }),
        success: function(result) {
          if (result.status && (result.status.id === 1 || result.status.id === 2)) {
            // Still processing
            if (retries < MAX_JUDGE0_RETRY_ITER) {
              retries++;
              setTimeout(checkResult, WAIT_TIME_MS);
            } else {
              handleSubmissionError('Submission timeout');
            }
          } else {
            // Execution completed
            handleExecutionResult(result);
          }
        },
        error: function(xhr, status, error) {
          handleSubmissionError(error);
        }
      });
    }
    
    // Initial delay before first check
    setTimeout(checkResult, WAIT_TIME_MS);
  }

  function handleExecutionResult(result) {
    // Update output displays
    const output = [result.compile_output, result.stdout].join('\n').trim();
    stdout.text(output);
    stderr.text(result.stderr || '');
    
    // Get AI evaluation
    getLLMFeedback({
      code: getCurrentCode(),
      stdout: output,
      stderr: result.stderr || ''
    });
  }

  function getCurrentCode() {
    if (currentProject.enableMultiFile) {
      // Return main file content or concatenated files
      const mainFile = getMainFileName();
      if (mainFile && currentProject.files[mainFile]) {
        return currentProject.files[mainFile].content;
      }
      
      // Fallback: concatenate all files
      return Object.keys(currentProject.files)
        .map(filename => `// File: ${filename}\n${currentProject.files[filename].content}`)
        .join('\n\n');
    }
    
    return currentProject.files[currentProject.currentFile]?.content || '';
  }

  function getMainFileName() {
    const mainFiles = {
      'Python': 'main.py',
      'Java': 'Main.java', 
      'C++': 'main.cpp',
      'JavaScript': 'index.js',
      'HTML/CSS': 'index.html'
    };
    return mainFiles[data.language] || 'main.py';
  }

  function getLLMFeedback(executionData) {
    $.ajax({
      url: llmResponseHandlerURL,
      method: 'POST',
      data: JSON.stringify(executionData),
      success: function(response) {
        AIFeedback.html(MarkdownToHTML(response.response || 'No feedback available'));
        switchTab('ai-feedback');
        enableSubmitButton();
        isSubmitting = false;
      },
      error: function(xhr, status, error) {
        console.error('Error getting AI feedback:', error);
        AIFeedback.html('<div class="error">Failed to get AI feedback: ' + error + '</div>');
        enableSubmitButton();
        isSubmitting = false;
      }
    });
  }

  function handleSubmissionError(error) {
    console.error('Submission error:', error);
    alert('Failed to submit code: ' + error);
    enableSubmitButton();
    isSubmitting = false;
  }

  function disableSubmitButton() {
    submitButton.prop('disabled', true).text('Submitting...');
  }

  function enableSubmitButton() {
    submitButton.prop('disabled', false).text('Submit Code');
  }

  // Project Reset

  function resetProject() {
    if (!confirm('Reset project? This will clear all files and results.')) {
      return;
    }
    
    $.ajax({
      url: resetHandlerURL,
      method: 'POST',
      data: JSON.stringify({}),
      success: function(response) {
        // Clear everything and reload
        location.reload();
      },
      error: function(xhr, status, error) {
        console.error('Error resetting project:', error);
        alert('Failed to reset project');
      }
    });
  }

  // UI Utilities

  function switchTab(tabId) {
    // Remove active class from all tabs and content
    $('.result-tab-btn', element).removeClass('active');
    $('.tabcontent', element).removeClass('active').hide();
    
    // Activate selected tab and content
    $(`.result-tab-btn[data-id="${tabId}"]`, element).addClass('active');
    $(`#${tabId}`, element).addClass('active').show();
  }

  // Handle content changes from Monaco
  window.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'contentChanged') {
      const filename = event.data.filename || currentProject.currentFile;
      if (filename) {
        currentProject.unsavedChanges.add(filename);
        updateFileDisplays(filename);
      }
    }
    
    // Handle single file content for submission
    if (event.data && event.data.type === 'singleFileContent') {
      submitCodeToJudge0(event.data.content);
    }
  });
}
