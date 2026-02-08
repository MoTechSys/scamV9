/*
 * S-ACM - Smart Academic Content Management System
 * Main JavaScript File
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initNotifications();
    initTooltips();
    initConfirmDialogs();
    initFileUpload();
});

/**
 * Initialize notification system
 */
function initNotifications() {
    const badge = document.querySelector('.notification-badge');
    const notificationList = document.querySelector('.notification-list');
    
    if (!badge) return;
    
    // Fetch unread count
    function updateNotificationCount() {
        fetch('/notifications/unread-count/')
            .then(response => response.json())
            .then(data => {
                if (data.count > 0) {
                    badge.textContent = data.count > 99 ? '99+' : data.count;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            })
            .catch(error => console.error('Error fetching notifications:', error));
    }
    
    // Update every 30 seconds
    updateNotificationCount();
    setInterval(updateNotificationCount, 30000);
}

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
}

/**
 * Initialize confirmation dialogs
 */
function initConfirmDialogs() {
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'هل أنت متأكد؟';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Initialize file upload enhancements
 */
function initFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name;
            const label = this.nextElementSibling;
            
            if (label && label.classList.contains('custom-file-label')) {
                label.textContent = fileName || 'اختر ملف...';
            }
            
            // Show file size
            if (this.files[0]) {
                const size = formatFileSize(this.files[0].size);
                const sizeSpan = document.createElement('span');
                sizeSpan.className = 'text-muted ms-2';
                sizeSpan.textContent = `(${size})`;
                
                const existingSize = this.parentElement.querySelector('.file-size-info');
                if (existingSize) existingSize.remove();
                
                sizeSpan.className += ' file-size-info';
                this.parentElement.appendChild(sizeSpan);
            }
        });
    });
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Show loading spinner
 */
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border spinner-border-sm ms-2';
    spinner.setAttribute('role', 'status');
    element.appendChild(spinner);
    element.disabled = true;
}

/**
 * Hide loading spinner
 */
function hideLoading(element) {
    const spinner = element.querySelector('.spinner-border');
    if (spinner) spinner.remove();
    element.disabled = false;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

/**
 * AJAX form submission
 */
function submitFormAjax(form, successCallback) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('[type="submit"]');
    
    showLoading(submitBtn);
    
    fetch(form.action, {
        method: form.method || 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading(submitBtn);
        if (data.success) {
            showToast(data.message || 'تمت العملية بنجاح', 'success');
            if (successCallback) successCallback(data);
        } else {
            showToast(data.error || 'حدث خطأ', 'danger');
        }
    })
    .catch(error => {
        hideLoading(submitBtn);
        showToast('حدث خطأ في الاتصال', 'danger');
        console.error('Error:', error);
    });
}

/**
 * Toggle file visibility (for instructors)
 */
function toggleFileVisibility(fileId, button) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    fetch(`/courses/instructor/files/${fileId}/toggle-visibility/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const icon = button.querySelector('i');
            if (data.is_visible) {
                icon.className = 'bi bi-eye';
                button.title = 'إخفاء';
            } else {
                icon.className = 'bi bi-eye-slash';
                button.title = 'إظهار';
            }
            showToast(data.message, 'success');
        }
    })
    .catch(error => {
        showToast('حدث خطأ', 'danger');
    });
}

/**
 * Mark notification as read
 */
function markNotificationRead(notificationId) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    fetch(`/notifications/${notificationId}/read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (item) item.classList.remove('unread');
        }
    });
}

/**
 * AI Chat functionality
 */
function sendChatMessage(fileId) {
    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    
    if (!question) return;
    
    const chatContainer = document.getElementById('chat-messages');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Add user message
    chatContainer.innerHTML += `
        <div class="chat-message user">
            <p class="mb-1">${question}</p>
            <small class="message-time">الآن</small>
        </div>
    `;
    
    input.value = '';
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Show loading
    const loadingId = 'loading-' + Date.now();
    chatContainer.innerHTML += `
        <div class="chat-message ai" id="${loadingId}">
            <div class="spinner-border spinner-border-sm" role="status"></div>
            <span class="ms-2">جاري التفكير...</span>
        </div>
    `;
    
    // Send request
    const formData = new FormData();
    formData.append('question', question);
    
    fetch(`/ai/ask/${fileId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById(loadingId).remove();
        
        if (data.success) {
            chatContainer.innerHTML += `
                <div class="chat-message ai">
                    <p class="mb-1">${data.answer}</p>
                    <small class="message-time">${data.created_at}</small>
                </div>
            `;
        } else {
            chatContainer.innerHTML += `
                <div class="chat-message ai text-danger">
                    <p class="mb-0">${data.error}</p>
                </div>
            `;
        }
        
        chatContainer.scrollTop = chatContainer.scrollHeight;
    })
    .catch(error => {
        document.getElementById(loadingId).remove();
        chatContainer.innerHTML += `
            <div class="chat-message ai text-danger">
                <p class="mb-0">حدث خطأ في الاتصال</p>
            </div>
        `;
    });
}
