/**
 * NeuraDocs - Main JavaScript
 * ===========================
 * Handles file uploads, chat functionality, and API integration.
 */

// ================================================
// Configuration & State
// ================================================
const API_BASE = '';
const state = {
    documents: [],
    isUploading: false,
    isQuerying: false
};

// ================================================
// DOM Elements
// ================================================
const elements = {
    statusBadge: document.getElementById('statusBadge'),
    uploadZone: document.getElementById('uploadZone'),
    fileInput: document.getElementById('fileInput'),
    uploadProgress: document.getElementById('uploadProgress'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    documentsList: document.getElementById('documentsList'),
    chatMessages: document.getElementById('chatMessages'),
    questionInput: document.getElementById('questionInput'),
    sendButton: document.getElementById('sendButton'),
    toastContainer: document.getElementById('toastContainer')
};

// ================================================
// Initialization
// ================================================
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    checkStatus();
    loadDocuments();
    setupUploadZone();
    setupChatInput();
}

// ================================================
// Status Check
// ================================================
async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();
        
        if (data.status === 'connected') {
            elements.statusBadge.classList.add('connected');
            elements.statusBadge.classList.remove('error');
            elements.statusBadge.querySelector('.status-text').textContent = 'Connected';
        } else {
            throw new Error('Not connected');
        }
    } catch (error) {
        elements.statusBadge.classList.add('error');
        elements.statusBadge.classList.remove('connected');
        elements.statusBadge.querySelector('.status-text').textContent = 'Disconnected';
    }
}

// ================================================
// Document Management
// ================================================
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE}/api/documents`);
        const data = await response.json();
        
        if (data.documents) {
            state.documents = data.documents;
            renderDocuments();
        }
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

function renderDocuments() {
    if (state.documents.length === 0) {
        elements.documentsList.innerHTML = '';
        return;
    }

    elements.documentsList.innerHTML = state.documents.map(doc => `
        <div class="document-item">
            <div class="document-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
            </div>
            <div class="document-info">
                <div class="document-name">${escapeHtml(doc.name)}</div>
                <div class="document-meta">${formatFileSize(doc.size)}</div>
            </div>
            <div class="document-badge">Ready</div>
        </div>
    `).join('');
}

// ================================================
// File Upload
// ================================================
function setupUploadZone() {
    // Click to upload
    elements.uploadZone.addEventListener('click', () => {
        if (!state.isUploading) {
            elements.fileInput.click();
        }
    });

    // File input change
    elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Drag & Drop
    elements.uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (!state.isUploading) {
            elements.uploadZone.classList.add('drag-over');
        }
    });

    elements.uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.remove('drag-over');
    });

    elements.uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.remove('drag-over');
        
        if (!state.isUploading && e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
}

async function handleFileUpload(file) {
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const allowedExtensions = ['.pdf', '.docx', '.txt'];
    
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(extension)) {
        showToast('Please upload a PDF, DOCX, or TXT file.', 'error');
        return;
    }

    state.isUploading = true;
    elements.uploadZone.classList.add('uploading');
    elements.progressFill.style.width = '0%';
    elements.progressText.textContent = 'Uploading...';

    // Simulate progress for upload
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        elements.progressFill.style.width = `${progress}%`;
    }, 200);

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        const data = await response.json();
        
        // Complete progress animation
        elements.progressFill.style.width = '100%';
        elements.progressText.textContent = 'Processing complete!';

        await sleep(500);
        
        showToast(`${data.filename} uploaded! ${data.chunks} chunks created.`, 'success');
        
        // Add to documents list
        state.documents.push({
            name: data.filename,
            size: file.size,
            chunks: data.chunks
        });
        renderDocuments();

        // Enable chat if this is first document
        updateChatState();

    } catch (error) {
        clearInterval(progressInterval);
        showToast(error.message, 'error');
    } finally {
        state.isUploading = false;
        elements.uploadZone.classList.remove('uploading');
        elements.fileInput.value = '';
    }
}

// ================================================
// Chat Functionality
// ================================================
function setupChatInput() {
    // Auto-resize textarea
    elements.questionInput.addEventListener('input', () => {
        elements.questionInput.style.height = 'auto';
        elements.questionInput.style.height = Math.min(elements.questionInput.scrollHeight, 150) + 'px';
        
        // Enable/disable send button
        elements.sendButton.disabled = !elements.questionInput.value.trim();
    });

    // Send on Enter (Shift+Enter for new line)
    elements.questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (elements.questionInput.value.trim() && !state.isQuerying) {
                sendQuestion();
            }
        }
    });

    // Send button click
    elements.sendButton.addEventListener('click', () => {
        if (elements.questionInput.value.trim() && !state.isQuerying) {
            sendQuestion();
        }
    });
}

function updateChatState() {
    const hasDocuments = state.documents.length > 0;
    elements.questionInput.disabled = !hasDocuments;
    elements.sendButton.disabled = !hasDocuments || !elements.questionInput.value.trim();
    
    if (hasDocuments) {
        elements.questionInput.placeholder = 'Ask a question about your documents...';
    } else {
        elements.questionInput.placeholder = 'Upload a document first...';
    }
}

async function sendQuestion() {
    const question = elements.questionInput.value.trim();
    if (!question || state.isQuerying) return;

    state.isQuerying = true;
    elements.sendButton.disabled = true;
    elements.questionInput.disabled = true;

    // Clear welcome message if present
    const welcomeMsg = elements.chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Add user message
    addMessage(question, 'user');
    elements.questionInput.value = '';
    elements.questionInput.style.height = 'auto';

    // Add typing indicator
    const typingIndicator = addTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Query failed');
        }

        const data = await response.json();

        // Remove typing indicator and add response
        typingIndicator.remove();
        addMessage(data.answer, 'assistant');

    } catch (error) {
        typingIndicator.remove();
        addMessage(`Sorry, I encountered an error: ${error.message}`, 'assistant');
        showToast('Failed to get response', 'error');
    } finally {
        state.isQuerying = false;
        elements.questionInput.disabled = false;
        elements.sendButton.disabled = !elements.questionInput.value.trim();
        elements.questionInput.focus();
    }
}

function addMessage(content, type) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    
    const avatarSvg = type === 'user' 
        ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
               <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
               <circle cx="12" cy="7" r="4"/>
           </svg>`
        : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
               <path d="M12 2L2 7l10 5 10-5-10-5z"/>
               <path d="M2 17l10 5 10-5"/>
               <path d="M2 12l10 5 10-5"/>
           </svg>`;

    messageEl.innerHTML = `
        <div class="message-avatar">${avatarSvg}</div>
        <div class="message-content">${escapeHtml(content)}</div>
    `;

    elements.chatMessages.appendChild(messageEl);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    return messageEl;
}

function addTypingIndicator() {
    const typingEl = document.createElement('div');
    typingEl.className = 'message assistant';
    typingEl.innerHTML = `
        <div class="message-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
            </svg>
        </div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    elements.chatMessages.appendChild(typingEl);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    return typingEl;
}

// ================================================
// Toast Notifications
// ================================================
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconSvg = type === 'success'
        ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
               <polyline points="20 6 9 17 4 12"/>
           </svg>`
        : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
               <circle cx="12" cy="12" r="10"/>
               <line x1="15" y1="9" x2="9" y2="15"/>
               <line x1="9" y1="9" x2="15" y2="15"/>
           </svg>`;

    toast.innerHTML = `
        <div class="toast-icon">${iconSvg}</div>
        <span class="toast-message">${escapeHtml(message)}</span>
    `;

    elements.toastContainer.appendChild(toast);

    // Auto remove after 4 seconds
    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ================================================
// Utility Functions
// ================================================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
