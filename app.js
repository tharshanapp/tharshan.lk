/**
 * OpenGov AI Assistant - Frontend JavaScript
 * Handles chat functionality, file uploads, and UI interactions
 */

// ==================== Configuration ====================

// Determine API base URL - handle both relative and absolute paths
const API_BASE_URL = (() => {
    // If we're on the same domain, use relative path
    if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
        // Use the origin (protocol + host + port)
        return window.location.origin;
    }
    return 'http://localhost:8000';
})();

console.log('API Base URL:', API_BASE_URL);

let adminToken = '';
let selectedFile = null;

// ==================== Initialization ====================

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Check for saved admin token
    const savedToken = localStorage.getItem('adminToken');
    if (savedToken) {
        adminToken = savedToken;
        showAdminUpload();
    }
    
    // Initialize file upload area
    initializeFileUpload();
    
    // Focus on question input
    setTimeout(() => {
        document.getElementById('question-input').focus();
    }, 100);
}

// ==================== Navigation ====================

function showSection(section) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(sec => {
        sec.classList.remove('active');
    });
    
    // Show selected section
    const sectionId = section + '-section';
    document.getElementById(sectionId).classList.add('active');
    
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    if (event.target.closest('.nav-link')) {
        event.target.closest('.nav-link').classList.add('active');
    }
}

// ==================== Chat Functionality ====================

function askQuestion() {
    const questionInput = document.getElementById('question-input');
    const categorySelect = document.getElementById('category-select');
    const askButton = document.getElementById('ask-button');
    
    const question = questionInput.value.trim();
    const category = categorySelect.value;
    
    // Validate input
    if (!question) {
        showToast('Please enter a question', 'warning');
        questionInput.focus();
        return;
    }
    
    // Disable button and show loading
    askButton.disabled = true;
    askButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
    
    // Add user message to chat
    addUserMessage(question);
    
    // Clear input
    questionInput.value = '';
    
    // Add loading message
    const loadingMessageId = addLoadingMessage();
    
    // Send request to API
    const requestUrl = `${API_BASE_URL}/ask`;
    console.log('Sending request to:', requestUrl);
    
    fetch(requestUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: question,
            category: category
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP error! status: ${response.status}, body: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Received data:', data);
        // Remove loading message
        removeMessage(loadingMessageId);
        
        // Add AI response
        addAIResponse(data.answer, data.sources, data.category);
    })
    .catch(error => {
        console.error('Error:', error);
        removeMessage(loadingMessageId);
        addErrorMessage('Connection error. Please check your connection and try again. Details: ' + error.message);
    })
    .finally(() => {
        // Re-enable button
        askButton.disabled = false;
        askButton.innerHTML = '<i class="fas fa-paper-plane me-1"></i>Ask AI';
        questionInput.focus();
    });
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        askQuestion();
    }
}

function addUserMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageId = 'msg-' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.id = messageId;
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-user"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble user-bubble">
                <p class="mb-0">${escapeHtml(message)}</p>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    return messageId;
}

function addAIResponse(answer, sources, category) {
    const chatMessages = document.getElementById('chat-messages');
    const messageId = 'msg-' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message';
    messageDiv.id = messageId;
    
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources-section mt-3">
                <h6><i class="fas fa-book me-1"></i> Sources</h6>
                ${sources.map(source => `
                    <span class="source-item">
                        <i class="fas fa-file-pdf"></i>
                        ${escapeHtml(source.source)} - Page ${source.page}
                        <span class="badge bg-light text-dark ms-1">${Math.round(source.relevance_score * 100)}% match</span>
                    </span>
                `).join('')}
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble ai-bubble">
                <div class="ai-answer">${formatAnswer(answer)}</div>
                ${sourcesHtml}
                <div class="message-actions mt-2">
                    <button class="btn btn-sm btn-outline-secondary" onclick="copyToClipboard('${messageId}')">
                        <i class="fas fa-copy me-1"></i>Copy
                    </button>
                </div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    
    // Apply typing effect
    applyTypingEffect(messageDiv);
    
    return messageId;
}

function addLoadingMessage() {
    const chatMessages = document.getElementById('chat-messages');
    const messageId = 'msg-' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message';
    messageDiv.id = messageId;
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble ai-bubble">
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="ms-2 text-muted">AI is thinking...</span>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    return messageId;
}

function addErrorMessage(error) {
    const chatMessages = document.getElementById('chat-messages');
    const messageId = 'msg-' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message';
    messageDiv.id = messageId;
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-exclamation-triangle"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble ai-bubble" style="border-left: 4px solid #f56565;">
                <p class="mb-0 text-danger">
                    <strong>Error:</strong> ${escapeHtml(error)}
                </p>
                <p class="mb-0 mt-2 text-muted small">
                    Please try again or check if documents have been uploaded.
                </p>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    return messageId;
}

function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';
    
    // Add welcome message back
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'message ai-message';
    welcomeDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble ai-bubble">
                <p class="mb-0">
                    <strong>Chat cleared!</strong> How can I help you today?
                </p>
            </div>
        </div>
    `;
    chatMessages.appendChild(welcomeDiv);
}

function showExamples() {
    const examples = [
        "What are the financial regulations for government procurement?",
        "How do I process travel claims?",
        "What is the approval process for expenditures?",
        "Explain the tender evaluation process",
        "What are the spending limits for different officers?"
    ];
    
    const chatMessages = document.getElementById('chat-messages');
    const messageId = 'msg-' + Date.now();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message';
    messageDiv.id = messageId;
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-lightbulb"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble ai-bubble">
                <p class="mb-2"><strong>Example Questions:</strong></p>
                <div class="example-questions">
                    ${examples.map(ex => `
                        <button class="example-btn" onclick="useExample('${escapeHtml(ex)}')">
                            <i class="fas fa-comment-dots me-1"></i>${ex}
                        </button>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function useExample(question) {
    document.getElementById('question-input').value = question;
    document.getElementById('question-input').focus();
}

// ==================== Admin Functionality ====================

function verifyAdmin() {
    const tokenInput = document.getElementById('admin-token');
    const token = tokenInput.value.trim();
    
    if (!token) {
        showToast('Please enter the admin token', 'warning');
        return;
    }
    
    // Store token
    adminToken = token;
    localStorage.setItem('adminToken', token);
    
    // Show upload interface
    showAdminUpload();
    showToast('Login successful', 'success');
}

function showAdminUpload() {
    document.getElementById('admin-login').classList.add('d-none');
    document.getElementById('admin-upload').classList.remove('d-none');
}

function logoutAdmin() {
    adminToken = '';
    localStorage.removeItem('adminToken');
    document.getElementById('admin-login').classList.remove('d-none');
    document.getElementById('admin-upload').classList.add('d-none');
    document.getElementById('admin-token').value = '';
    showToast('Logged out successfully', 'info');
}

function initializeFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    if (!uploadArea || !fileInput) return;
    
    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // File selected
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
}

function handleFileSelect(file) {
    // Validate PDF
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showToast('Please select a PDF file', 'error');
        return;
    }
    
    selectedFile = file;
    
    // Show file preview
    const uploadArea = document.getElementById('upload-area');
    const fileSize = (file.size / 1024 / 1024).toFixed(2);
    
    uploadArea.innerHTML = `
        <div class="file-preview">
            <i class="fas fa-file-pdf"></i>
            <div class="file-info">
                <div class="file-name">${escapeHtml(file.name)}</div>
                <div class="file-size">${fileSize} MB</div>
            </div>
            <div class="remove-file" onclick="removeFile()">
                <i class="fas fa-times"></i>
            </div>
        </div>
        <p class="text-muted small mt-2 mb-0">Click to change file</p>
    `;
    
    // Enable upload button
    document.getElementById('upload-button').disabled = false;
}

function removeFile() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    
    const uploadArea = document.getElementById('upload-area');
    uploadArea.innerHTML = `
        <i class="fas fa-cloud-upload-alt fa-3x mb-3 text-primary"></i>
        <p class="mb-2"><strong>Drag & drop PDF here</strong></p>
        <p class="text-muted small">or click to browse</p>
        <input type="file" id="file-input" accept=".pdf" class="d-none">
    `;
    
    document.getElementById('upload-button').disabled = true;
    initializeFileUpload();
}

function uploadFile() {
    if (!selectedFile || !adminToken) {
        showToast('Please select a file and login', 'warning');
        return;
    }
    
    const category = document.getElementById('upload-category').value;
    const uploadButton = document.getElementById('upload-button');
    const progressDiv = document.getElementById('upload-progress');
    const resultDiv = document.getElementById('upload-result');
    
    // Show progress
    progressDiv.classList.remove('d-none');
    resultDiv.innerHTML = '';
    uploadButton.disabled = true;
    
    // Create form data
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('category', category);
    
    // Upload file
    const uploadUrl = `${API_BASE_URL}/admin/upload`;
    console.log('Uploading to:', uploadUrl);
    
    fetch(uploadUrl, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${adminToken}`
        },
        body: formData
    })
    .then(response => {
        console.log('Upload response status:', response.status);
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.detail || 'Upload failed') });
        }
        return response.json();
    })
    .then(data => {
        console.log('Upload success:', data);
        resultDiv.innerHTML = `
            <div class="result-success">
                <i class="fas fa-check-circle me-2"></i>
                <strong>Success!</strong> ${data.message}<br>
                <small>Documents processed: ${data.documents_processed} | Chunks created: ${data.chunks_created}</small>
            </div>
        `;
        
        // Reset file selection
        removeFile();
    })
    .catch(error => {
        console.error('Upload error:', error);
        resultDiv.innerHTML = `
            <div class="result-error">
                <i class="fas fa-times-circle me-2"></i>
                <strong>Error:</strong> ${escapeHtml(error.message)}
            </div>
        `;
    })
    .finally(() => {
        progressDiv.classList.add('d-none');
        uploadButton.disabled = false;
    });
}

// ==================== Utility Functions ====================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatAnswer(text) {
    // Convert markdown-like formatting to HTML
    let formatted = escapeHtml(text);
    
    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Line breaks
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Numbered lists
    formatted = formatted.replace(/(\d+)\.\s+(.*?)(<br>|$)/g, '<li>$2</li>');
    
    return formatted;
}

function copyToClipboard(messageId) {
    const message = document.getElementById(messageId);
    if (!message) return;
    
    const answerDiv = message.querySelector('.ai-answer');
    if (!answerDiv) return;
    
    const text = answerDiv.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.style.cssText = 'min-width: 250px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto dismiss
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 150);
    }, 3000);
}

function applyTypingEffect(messageDiv) {
    const answerDiv = messageDiv.querySelector('.ai-answer');
    if (!answerDiv) return;
    
    const html = answerDiv.innerHTML;
    answerDiv.innerHTML = '';
    
    let i = 0;
    const typingInterval = setInterval(() => {
        if (i < html.length) {
            answerDiv.innerHTML += html.charAt(i);
            i++;
        } else {
            clearInterval(typingInterval);
            // Restore full HTML for proper rendering
            answerDiv.innerHTML = html;
        }
    }, 10);
}
