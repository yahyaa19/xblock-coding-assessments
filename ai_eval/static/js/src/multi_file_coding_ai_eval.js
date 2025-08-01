/* JavaScript for MultiFileCodingAIEvalXBlock */

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

  // State management
  let currentProject = {
    files: data.project_files || {},
    structure: data.project_structure || {},
    currentFile: null,
    enableMultiFile: data.enable_multi_file || false
  };

  let testResults = [];
  let isSubmitting = false;

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
  }

  function initializeMultiFileInterface() {
    // Initialize file explorer
    renderFileTree();
    
    // Initialize editor tabs
    renderEditorTabs();
    
    // Set up Monaco editor communication
    setupMonacoCommunication();
  }

  function initializeSingleFileInterface() {
    // Hide multi-file specific elements
    fileExplorer.hide();
    $(".result-panel").css("width", "100%");
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
  }

  function setupModalEventListeners() {
    // File creation modal
    const fileModal = $("#file-modal", element);
    const closeButtons = fileModal.find(".close, #cancel-file-btn");
    const createFileBtn = $("#create-file-btn", element);

    closeButtons.on("click", function() {
      fileModal.hide();
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
      }
      if (event.target === projectModal[0]) {
        projectModal.hide();
      }
    });
  }

  // File Management Functions

  function renderFileTree() {
    fileTree.empty();
    
    Object.keys(currentProject.files).forEach(filename => {
      const fileItem = createFileItem(filename);
      fileTree.append(fileItem);
    });

    if (Object.keys(currentProject.files).length === 0) {
      fileTree.append('<div class="file-item empty-state">No files in project</div>');
    }
  }

  function createFileItem(filename) {
    const fileData = currentProject.files[filename];
    const isActive = currentProject.currentFile === filename;
    const fileIcon = getFileIcon(filename);
    
    return $(`
      <div class="file-item ${isActive ? 'active' : ''}" data-filename="${filename}">
        <span class="file-item-icon ${fileIcon}"></span>
        <span class="file-item-name">${filename}</span>
        <div class="file-item-actions">
          <button class="file-action-btn rename-file" title="Rename">✏️</button>
          <button class="file-action-btn delete-file" title="Delete">🗑️</button>
        </div>
      </div>
    `);
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
      'css': 'file-icon-css',
      'json': 'file-icon-json',
      'txt': 'file-icon-text'
    };
    return iconMap[extension] || 'file-icon-text';
  }

  function renderEditorTabs() {
    editorTabs.empty();
    
    Object.keys(currentProject.files).forEach(filename => {
      const isActive = currentProject.currentFile === filename;
      const tab = createEditorTab(filename, isActive);
      editorTabs.append(tab);
    });
  }

  function createEditorTab(filename, isActive) {
    return $(`
      <div class="editor-tab ${isActive ? 'active' : ''}" data-filename="${filename}">
        <span class="editor-tab-name">${filename}</span>
        <span class="editor-tab-close">×</span>
      </div>
    `);
  }

  // Monaco Editor Communication

  function setupMonacoCommunication() {
    // Listen for messages from Monaco editor
    window.addEventListener('message', function(event) {
      const message = event.data;
      
      switch (message.type) {
        case 'editorReady':
          loadProjectFilesToEditor();
          break;
        case 'contentChanged':
          handleContentChange(message.file, message.content);
          break;
        case 'fileSwitched':
          handleFileSwitch(message.filename);
          break;
        case 'fileSaved':
          handleFileSave(message.filename, message.content);
          break;
      }
    });

    // Set up file tree interactions
    fileTree.on('click', '.file-item', function() {
      const filename = $(this).data('filename');
      switchToFile(filename);
    });

    fileTree.on('click', '.delete-file', function(e) {
      e.stopPropagation();
      const filename = $(this).closest('.file-item').data('filename');
      deleteFile(filename);
    });

    fileTree.on('click', '.rename-file', function(e) {
      e.stopPropagation();
      const filename = $(this).closest('.file-item').data('filename');
      showRenameFileModal(filename);
    });

    // Set up editor tab interactions
    editorTabs.on('click', '.editor-tab', function() {
      const filename = $(this).data('filename');
      switchToFile(filename);
    });

    editorTabs.on('click', '.editor-tab-close', function(e) {
      e.stopPropagation();
      const filename = $(this).closest('.editor-tab').data('filename');
      deleteFile(filename);
    });
  }

  function loadProjectFilesToEditor() {
    // Send all project files to Monaco editor
    iframe.contentWindow.postMessage({
      type: 'updateProject',
      files: currentProject.files
    }, '*');
  }

  function switchToFile(filename) {
    if (!currentProject.files[filename]) {
      console.error('File not found:', filename);
      return;
    }

    currentProject.currentFile = filename;
    
    // Update UI
    fileTree.find('.file-item').removeClass('active');
    fileTree.find(`[data-filename="${filename}"]`).addClass('active');
    
    editorTabs.find('.editor-tab').removeClass('active');
    editorTabs.find(`[data-filename="${filename}"]`).addClass('active');

    // Switch file in Monaco editor
    iframe.contentWindow.postMessage({
      type: 'switchFile',
      filename: filename
    }, '*');
  }

  function handleContentChange(filename, content) {
    if (currentProject.files[filename]) {
      currentProject.files[filename].content = content;
      // Auto-save after a delay
      clearTimeout(window.autoSaveTimer);
      window.autoSaveTimer = setTimeout(() => {
        saveFile(filename, content);
      }, 2000);
    }
  }

  function handleFileSwitch(filename) {
    currentProject.currentFile = filename;
    updateUIForFileSwitch(filename);
  }

  function handleFileSave(filename, content) {
    currentProject.files[filename].content = content;
    updateProjectStructure();
  }

  // File Operations

  function showCreateFileModal() {
    const modal = $("#file-modal", element);
    modal.show();
    
    // Reset form
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

    $.ajax({
      url: createFileHandlerURL,
      method: "POST",
      data: JSON.stringify({
        filename: filename,
        content: content,
        file_type: fileType
      }),
      contentType: "application/json",
    })
    .done(function(response) {
      if (response.success) {
        // Add file to current project
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
        
        // Switch to new file
        switchToFile(filename);

        // Send to Monaco editor
        iframe.contentWindow.postMessage({
          type: 'createFile',
          filename: filename,
          content: content,
          language: getLanguageForFileType(fileType)
        }, '*');

        $("#file-modal", element).hide();
      }
    })
    .fail(function(error) {
      console.error('Error creating file:', error);
      alert('Failed to create file: ' + (error.responseJSON?.message || 'Unknown error'));
    });
  }

  function deleteFile(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    $.ajax({
      url: deleteFileHandlerURL,
      method: "POST",
      data: JSON.stringify({ filename: filename }),
      contentType: "application/json",
    })
    .done(function(response) {
      if (response.success) {
        // Remove file from current project
        delete currentProject.files[filename];

        // Update UI
        renderFileTree();
        renderEditorTabs();

        // If this was the current file, switch to another
        if (currentProject.currentFile === filename) {
          const remainingFiles = Object.keys(currentProject.files);
          if (remainingFiles.length > 0) {
            switchToFile(remainingFiles[0]);
          } else {
            currentProject.currentFile = null;
          }
        }

        // Notify Monaco editor
        iframe.contentWindow.postMessage({
          type: 'deleteFile',
          filename: filename
        }, '*');
      }
    })
    .fail(function(error) {
      console.error('Error deleting file:', error);
      alert('Failed to delete file: ' + (error.responseJSON?.message || 'Unknown error'));
    });
  }

  function saveFile(filename, content) {
    $.ajax({
      url: saveFileHandlerURL,
      method: "POST",
      data: JSON.stringify({
        filename: filename,
        content: content
      }),
      contentType: "application/json",
    })
    .done(function(response) {
      if (response.success) {
        currentProject.files[filename].content = content;
        currentProject.files[filename].modified_at = new Date().toISOString();
        updateProjectStructure();
      }
    })
    .fail(function(error) {
      console.error('Error saving file:', error);
    });
  }

  function showInitializeProjectModal() {
    const modal = $("#project-modal", element);
    const preview = $("#template-preview", element);
    
    // Show template preview
    const templates = data.file_templates[data.language] || {};
    preview.empty();
    
    Object.keys(templates).forEach(filename => {
      const template = templates[filename];
      const previewItem = $(`
        <div class="template-file">
          <div class="template-file-name">${filename}</div>
          <div class="template-file-content">${template.content.substring(0, 100)}${template.content.length > 100 ? '...' : ''}</div>
        </div>
      `);
      preview.append(previewItem);
    });

    modal.show();
  }

  function initializeProject() {
    $.ajax({
      url: initializeProjectHandlerURL,
      method: "POST",
      data: JSON.stringify({}),
      contentType: "application/json",
    })
    .done(function(response) {
      if (response.success) {
        // Reload project data
        loadProjectData();
        $("#project-modal", element).hide();
      }
    })
    .fail(function(error) {
      console.error('Error initializing project:', error);
      alert('Failed to initialize project: ' + (error.responseJSON?.message || 'Unknown error'));
    });
  }

  function loadProjectData() {
    $.ajax({
      url: getProjectStructureHandlerURL,
      method: "POST",
      data: JSON.stringify({}),
      contentType: "application/json",
    })
    .done(function(response) {
      currentProject.files = response.project_files || {};
      currentProject.structure = response.project_structure || {};
      currentProject.enableMultiFile = response.enable_multi_file || false;

      // Update UI
      renderFileTree();
      renderEditorTabs();

      // Load files into Monaco editor
      if (iframe.contentWindow) {
        loadProjectFilesToEditor();
      }
    })
    .fail(function(error) {
      console.error('Error loading project data:', error);
    });
  }

  function updateProjectStructure() {
    currentProject.structure = {
      total_files: Object.keys(currentProject.files).length,
      languages: [...new Set(Object.values(currentProject.files).map(f => f.language))],
      last_modified: new Date().toISOString(),
      file_types: [...new Set(Object.values(currentProject.files).map(f => f.type))]
    };
  }

  // Code Execution Functions

  function submitCode() {
    if (isSubmitting) return;
    isSubmitting = true;
    disableSubmitButton();

    if (currentProject.enableMultiFile) {
      submitMultiFileProject();
    } else {
      submitSingleFile();
    }
  }

  function submitMultiFileProject() {
    // Get all file contents
    const filesContent = {};
    Object.keys(currentProject.files).forEach(filename => {
      filesContent[filename] = currentProject.files[filename].content;
    });

    $.ajax({
      url: submitProjectHandlerURL,
      method: "POST",
      data: JSON.stringify({ files: filesContent }),
      contentType: "application/json",
    })
    .done(function(response) {
      if (response.submission_id) {
        getSubmissionResult(response.submission_id);
      }
    })
    .fail(function(error) {
      console.error('Error submitting project:', error);
      enableSubmitButton();
      isSubmitting = false;
    });
  }

  function submitSingleFile() {
    const code = iframe.contentWindow.editor.getValue();
    
    $.ajax({
      url: submitProjectHandlerURL,
      method: "POST",
      data: JSON.stringify({ user_code: code }),
      contentType: "application/json",
    })
    .done(function(response) {
      if (response.submission_id) {
        getSubmissionResult(response.submission_id);
      }
    })
    .fail(function(error) {
      console.error('Error submitting code:', error);
      enableSubmitButton();
      isSubmitting = false;
    });
  }

  function getSubmissionResult(submissionId) {
    let retries = 0;
    const deferred = $.Deferred();

    function attempt() {
      return $.ajax({
        url: submissionResultURL,
        method: "POST",
        data: JSON.stringify({ submission_id: submissionId }),
        contentType: "application/json",
      })
      .then(function(result) {
        console.log("result", result, retries);
        if (result.status.id === 1 || result.status.id === 2) {
          // Retry if status is 1 (In Queue) or 2 (Processing)
          if (retries < MAX_JUDGE0_RETRY_ITER) {
            retries++;
            console.log("Judge0 fetch result retry attempt:", retries);
            setTimeout(function() {
              attempt();
            }, WAIT_TIME_MS);
          } else {
            deferred.reject(new Error("Judge0 submission result fetch failed after " + MAX_JUDGE0_RETRY_ITER + " attempts."));
          }
        } else {
          const output = [result.compile_output, result.stdout].join("\n").trim();
          stdout.text(output);
          stderr.text(result.stderr);
          
          if (data.language === HTML_CSS) {
            renderUserHTML(output);
          }
          
          deferred.resolve(result);
          enableSubmitButton();
          isSubmitting = false;
          
          // Get AI feedback
          getLLMFeedback(result);
        }
      })
      .fail(function(error) {
        console.log("Error: ", error);
        deferred.reject(new Error("An error occurred while trying to fetch Judge0 submission result."));
        enableSubmitButton();
        isSubmitting = false;
      });
    }

    attempt();
    return deferred.promise();
  }

  function getLLMFeedback(result) {
    const code = currentProject.enableMultiFile ? 
      Object.values(currentProject.files).map(f => f.content).join('\n\n') :
      iframe.contentWindow.editor.getValue();

    const answer = `
    student code :

    ${code}
    `;

    // Add stdout and stderr for executable languages
    if (data.language !== HTML_CSS) {
      answer += `
      stdout:

      ${result.stdout}

      stderr:

      ${result.stderr}
      `;
    }

    const messages = [
      {
        "role": "system",
        "content": `
        ${data.evaluation_prompt}

        ${data.question}.

        The programming language is ${data.language}

        Evaluation must be in Markdown format.
        `,
      },
      {
        "content": ` Here is the student's answer:
        ${answer}
        `,
        "role": "user",
      },
    ];

    $.ajax({
      url: llmResponseHandlerURL,
      method: "POST",
      data: JSON.stringify({
        code: code,
        stdout: result.stdout,
        stderr: result.stderr,
      }),
      contentType: "application/json",
    })
    .done(function(response) {
      if (response.response) {
        AIFeedback.html(response.response);
        switchTab("ai-feedback");
      }
    })
    .fail(function(error) {
      console.error("Error getting LLM feedback:", error);
    });
  }

  function runTestCases() {
    if (isSubmitting) return;
    isSubmitting = true;
    runTestsButton.prop('disabled', true);

    $.ajax({
      url: runTestsHandlerURL,
      method: "POST",
      data: JSON.stringify({}),
      contentType: "application/json",
    })
    .done(function(response) {
      if (response.success) {
        testResults = response.results || [];
        displayTestResults();
        switchTab("test-results");
      }
    })
    .fail(function(error) {
      console.error('Error running test cases:', error);
    })
    .always(function() {
      isSubmitting = false;
      runTestsButton.prop('disabled', false);
    });
  }

  function displayTestResults() {
    const resultsList = $("#test-results-list", element);
    const testCount = $("#test-count", element);
    const testPassed = $("#test-passed", element);
    const testFailed = $("#test-failed", element);

    resultsList.empty();
    
    let passedCount = 0;
    let failedCount = 0;

    testResults.forEach((result, index) => {
      const resultItem = createTestResultItem(result, index);
      resultsList.append(resultItem);
      
      if (result.passed) {
        passedCount++;
      } else {
        failedCount++;
      }
    });

    testCount.text(testResults.length);
    testPassed.text(passedCount);
    testFailed.text(failedCount);
  }

  function createTestResultItem(result, index) {
    const statusClass = result.passed ? 'passed' : 'failed';
    const statusText = result.passed ? 'PASSED' : 'FAILED';
    
    return $(`
      <div class="test-result-item ${statusClass}">
        <div class="test-result-header">
          <span class="test-result-name">Test Case ${index + 1}</span>
          <span class="test-result-status ${statusClass}">${statusText}</span>
        </div>
        <div class="test-result-details">
          <div><strong>Input:</strong> ${result.test_case.input || 'None'}</div>
          <div><strong>Expected:</strong> ${result.test_case.expected_output}</div>
          <div><strong>Actual:</strong> ${result.actual_output}</div>
          ${result.execution_time ? `<div><strong>Time:</strong> ${result.execution_time}s</div>` : ''}
          ${result.memory_used ? `<div><strong>Memory:</strong> ${result.memory_used}KB</div>` : ''}
        </div>
        ${result.error ? `<div class="test-result-output">Error: ${result.error}</div>` : ''}
      </div>
    `);
  }

  // Utility Functions

  function switchTab(tabId) {
    $(".tabcontent").removeClass("active");
    $(".tablinks").removeClass("active");
    
    $(`#${tabId}`).addClass("active");
    $(`.tablinks[data-id="${tabId}"]`).addClass("active");
  }

  function resetProject() {
    if (confirm("Are you sure you want to reset the project? This will clear all files and code.")) {
      $.ajax({
        url: resetHandlerURL,
        method: "POST",
        data: JSON.stringify({}),
        contentType: "application/json",
      })
      .done(function(response) {
        if (response.message === "reset successful.") {
          // Clear current project
          currentProject.files = {};
          currentProject.currentFile = null;
          
          // Update UI
          renderFileTree();
          renderEditorTabs();
          
          // Clear outputs
          stdout.text('');
          stderr.text('');
          AIFeedback.html('');
          
          // Reset test results
          testResults = [];
          displayTestResults();
          
          // Switch to output tab
          switchTab("output");
        }
      })
      .fail(function(error) {
        console.error('Error resetting project:', error);
      });
    }
  }

  function disableSubmitButton() {
    submitButton.prop('disabled', true).text('Submitting...');
  }

  function enableSubmitButton() {
    submitButton.prop('disabled', false).text('Submit Code');
  }

  function updateUIForFileSwitch(filename) {
    fileTree.find('.file-item').removeClass('active');
    fileTree.find(`[data-filename="${filename}"]`).addClass('active');
    
    editorTabs.find('.editor-tab').removeClass('active');
    editorTabs.find(`[data-filename="${filename}"]`).addClass('active');
  }

  function getLanguageForFileType(fileType) {
    const languageMap = {
      'python': 'python',
      'javascript': 'javascript',
      'java': 'java',
      'cpp': 'cpp',
      'html': 'html',
      'css': 'css',
      'json': 'json',
      'text': 'plaintext'
    };
    return languageMap[fileType] || 'plaintext';
  }

  function renderUserHTML(userHTML) {
    if (htmlRenderIframe.length > 0) {
      const iframe = htmlRenderIframe[0];
      iframe.srcdoc = userHTML;
    }
  }

  // Helper function to run after iframe loads
  function runFuncAfterLoading(func) {
    if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
      func();
    } else {
      iframe.onload = func;
    }
  }
} 