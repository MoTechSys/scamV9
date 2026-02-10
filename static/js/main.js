/**
 * S-ACM v3.1 - Main JavaScript Controller
 * Smart Academic Content Management System
 * 
 * Modules:
 *   1. App Initialization
 *   2. Sidebar Controller (Desktop collapse + Mobile toggle)
 *   3. Bottom Navigation Controller (Mobile)
 *   4. Mobile Drawer Controller (More Menu)
 *   5. Toast & Notification System
 *   6. HTMX Integration
 *   7. Utility Functions
 *   8. File Upload & AI Chat
 *
 * Note: This is the SINGLE JS entry point for dashboard pages.
 * Legacy files (sidebar.js, instructor-panel.js) are NOT loaded
 * from the new dashboard_base.html template.
 */

(function () {
    'use strict';

    /* ==========================================================
       1. APP INITIALIZATION
       ========================================================== */
    document.addEventListener('DOMContentLoaded', function () {
        SidebarController.init();
        BottomNavController.init();
        DrawerController.init();
        ToastController.init();
        HtmxIntegration.init();
        initTooltips();
        initConfirmDialogs();
        initFileUpload();
        initNotifications();
    });


    /* ==========================================================
       2. SIDEBAR CONTROLLER
       ========================================================== */
    const SidebarController = {
        STORAGE_KEY: 'sacm-sidebar-collapsed',
        sidebar: null,
        overlay: null,
        mobileToggle: null,
        collapseBtn: null,

        init: function () {
            this.sidebar = document.getElementById('sidebar');
            this.overlay = document.getElementById('sidebarOverlay');
            this.mobileToggle = document.getElementById('mobileMenuToggle');
            this.collapseBtn = document.getElementById('sidebarCollapseBtn');

            if (!this.sidebar) return;

            // Desktop collapse toggle
            if (this.collapseBtn) {
                this.collapseBtn.addEventListener('click', this.toggleCollapse.bind(this));
            }

            // Mobile sidebar toggle (hamburger)
            if (this.mobileToggle) {
                this.mobileToggle.addEventListener('click', this.toggleMobile.bind(this));
            }

            // Close on overlay click
            if (this.overlay) {
                this.overlay.addEventListener('click', this.closeMobile.bind(this));
            }

            // Close sidebar on escape key
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') {
                    SidebarController.closeMobile();
                }
            });

            // Restore saved collapse state (desktop only)
            this.restoreState();
        },

        toggleCollapse: function () {
            if (!this.sidebar) return;
            var isCollapsed = this.sidebar.classList.toggle('collapsed');
            document.body.classList.toggle('sidebar-collapsed', isCollapsed);
            this.saveState(isCollapsed);

            // Trigger resize for charts/tables after transition
            setTimeout(function () {
                window.dispatchEvent(new Event('resize'));
            }, 350);
        },

        toggleMobile: function () {
            if (!this.sidebar || !this.overlay) return;
            this.sidebar.classList.toggle('show');
            this.overlay.classList.toggle('show');
            document.body.style.overflow = this.sidebar.classList.contains('show') ? 'hidden' : '';
        },

        closeMobile: function () {
            if (!this.sidebar || !this.overlay) return;
            this.sidebar.classList.remove('show');
            this.overlay.classList.remove('show');
            document.body.style.overflow = '';
        },

        saveState: function (collapsed) {
            try {
                localStorage.setItem(this.STORAGE_KEY, collapsed ? 'true' : 'false');
            } catch (e) { /* localStorage unavailable */ }
        },

        restoreState: function () {
            try {
                if (window.innerWidth >= 992) {
                    var saved = localStorage.getItem(this.STORAGE_KEY);
                    if (saved === 'true') {
                        this.sidebar.classList.add('collapsed');
                        document.body.classList.add('sidebar-collapsed');
                    }
                }
            } catch (e) { /* localStorage unavailable */ }
        }
    };


    /* ==========================================================
       3. BOTTOM NAVIGATION CONTROLLER
       ========================================================== */
    const BottomNavController = {
        init: function () {
            var currentPath = window.location.pathname;
            var navItems = document.querySelectorAll('.bottom-nav-item[href]');

            navItems.forEach(function (item) {
                var href = item.getAttribute('href');
                if (href && currentPath === href) {
                    item.classList.add('active');
                } else if (href && href !== '/' && currentPath.startsWith(href)) {
                    item.classList.add('active');
                }
            });

            // Add haptic-like feedback on tap
            var allNavItems = document.querySelectorAll('.bottom-nav-item');
            allNavItems.forEach(function (item) {
                item.addEventListener('touchstart', function () {
                    this.style.transform = 'scale(0.92)';
                }, { passive: true });
                item.addEventListener('touchend', function () {
                    this.style.transform = '';
                }, { passive: true });
            });
        }
    };


    /* ==========================================================
       4. MOBILE DRAWER CONTROLLER
       ========================================================== */
    const DrawerController = {
        drawer: null,
        overlay: null,
        closeBtn: null,
        moreBtn: null,
        startY: 0,
        currentY: 0,
        isDragging: false,

        init: function () {
            this.drawer = document.getElementById('mobileDrawer');
            this.overlay = document.getElementById('mobileDrawerOverlay');
            this.closeBtn = document.getElementById('drawerCloseBtn');
            this.moreBtn = document.getElementById('moreMenuBtn');

            if (!this.drawer) return;

            // Open drawer
            if (this.moreBtn) {
                this.moreBtn.addEventListener('click', this.toggle.bind(this));
            }

            // Close drawer
            if (this.closeBtn) {
                this.closeBtn.addEventListener('click', this.close.bind(this));
            }

            if (this.overlay) {
                this.overlay.addEventListener('click', this.close.bind(this));
            }

            // Close on escape
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') {
                    DrawerController.close();
                }
            });

            // Swipe-to-close
            this.initSwipe();
        },

        toggle: function () {
            if (!this.drawer || !this.overlay) return;
            var isOpen = this.drawer.classList.toggle('show');
            this.overlay.classList.toggle('show', isOpen);
        },

        close: function () {
            if (!this.drawer || !this.overlay) return;
            this.drawer.classList.remove('show');
            this.overlay.classList.remove('show');
        },

        initSwipe: function () {
            var self = this;
            if (!this.drawer) return;

            this.drawer.addEventListener('touchstart', function (e) {
                var rect = self.drawer.getBoundingClientRect();
                // Only start drag from the handle area (top 50px)
                if (e.touches[0].clientY - rect.top < 50) {
                    self.startY = e.touches[0].clientY;
                    self.isDragging = true;
                    self.drawer.style.transition = 'none';
                }
            }, { passive: true });

            this.drawer.addEventListener('touchmove', function (e) {
                if (!self.isDragging) return;
                self.currentY = e.touches[0].clientY;
                var diff = self.currentY - self.startY;
                if (diff > 0) {
                    self.drawer.style.transform = 'translateY(' + diff + 'px)';
                }
            }, { passive: true });

            this.drawer.addEventListener('touchend', function () {
                if (!self.isDragging) return;
                self.isDragging = false;
                self.drawer.style.transition = '';
                var diff = self.currentY - self.startY;
                if (diff > 80) {
                    self.close();
                }
                self.drawer.style.transform = '';
                self.startY = 0;
                self.currentY = 0;
            }, { passive: true });
        }
    };


    /* ==========================================================
       5. TOAST & NOTIFICATION SYSTEM
       ========================================================== */
    const ToastController = {
        init: function () {
            // Auto-dismiss toast alerts after 5 seconds
            setTimeout(function () {
                var alerts = document.querySelectorAll('.toast-container .alert');
                alerts.forEach(function (el) {
                    try {
                        var bsAlert = bootstrap.Alert.getOrCreateInstance(el);
                        if (bsAlert) bsAlert.close();
                    } catch (e) { el.remove(); }
                });
            }, 5000);
        }
    };

    /**
     * Show toast notification (global function)
     */
    window.showToast = function (message, type) {
        type = type || 'info';
        var container = document.getElementById('toast-container') || createToastContainer();

        var toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-' + type + ' border-0';
        toast.setAttribute('role', 'alert');
        toast.innerHTML =
            '<div class="d-flex">' +
            '  <div class="toast-body">' + message + '</div>' +
            '  <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>' +
            '</div>';

        container.appendChild(toast);
        var bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        toast.addEventListener('hidden.bs.toast', function () { toast.remove(); });
    };

    function createToastContainer() {
        var container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }


    /* ==========================================================
       6. HTMX INTEGRATION
       ========================================================== */
    const HtmxIntegration = {
        init: function () {
            // After HTMX swap: re-apply active states and re-init components
            document.body.addEventListener('htmx:afterSwap', function () {
                BottomNavController.init();
                initTooltips();
                initConfirmDialogs();
            });

            // Scroll to top after HTMX page load
            document.body.addEventListener('htmx:afterSettle', function (evt) {
                var target = evt.detail.target;
                if (target && target.classList && target.classList.contains('page-content')) {
                    target.scrollTop = 0;
                }
            });

            // Show spinner on HTMX button triggers
            document.body.addEventListener('htmx:beforeRequest', function (evt) {
                var trigger = evt.detail.elt;
                if (trigger && trigger.tagName === 'BUTTON') {
                    trigger.classList.add('htmx-loading');
                    var spinner = document.createElement('span');
                    spinner.className = 'spinner-border spinner-border-sm ms-2 htmx-spinner';
                    trigger.appendChild(spinner);
                }
            });

            document.body.addEventListener('htmx:afterRequest', function (evt) {
                var trigger = evt.detail.elt;
                if (trigger) {
                    trigger.classList.remove('htmx-loading');
                    var spinner = trigger.querySelector('.htmx-spinner');
                    if (spinner) spinner.remove();
                }
            });

            // Graceful error handling
            document.body.addEventListener('htmx:responseError', function () {
                window.showToast('حدث خطأ في الاتصال. حاول مرة أخرى.', 'danger');
            });
        }
    };


    /* ==========================================================
       7. UTILITY FUNCTIONS
       ========================================================== */

    /**
     * Initialize Bootstrap tooltips
     */
    function initTooltips() {
        var tooltipList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipList.forEach(function (el) {
            try { new bootstrap.Tooltip(el); } catch (e) { /* skip */ }
        });
    }

    /**
     * Initialize confirmation dialogs
     */
    function initConfirmDialogs() {
        document.querySelectorAll('[data-confirm]').forEach(function (element) {
            element.removeEventListener('click', handleConfirm);
            element.addEventListener('click', handleConfirm);
        });
    }

    function handleConfirm(e) {
        var message = this.dataset.confirm || 'هل أنت متأكد؟';
        if (!confirm(message)) {
            e.preventDefault();
        }
    }

    /**
     * Initialize notification badge polling
     */
    function initNotifications() {
        // Update both navbar badge and bottom nav badge
        function updateCount() {
            fetch('/notifications/unread-count/')
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    var count = data.count || 0;
                    // Navbar notification dot
                    var dots = document.querySelectorAll('.notification-dot');
                    dots.forEach(function (dot) {
                        if (count > 0) {
                            dot.textContent = count > 99 ? '99+' : count;
                            dot.style.display = '';
                        } else {
                            dot.style.display = 'none';
                        }
                    });
                    // Bottom nav badge
                    var bottomBadge = document.querySelector('.bottom-nav-badge');
                    if (bottomBadge) {
                        if (count > 0) {
                            bottomBadge.textContent = count > 99 ? '99+' : count;
                            bottomBadge.style.display = '';
                        } else {
                            bottomBadge.style.display = 'none';
                        }
                    }
                })
                .catch(function () { /* silent */ });
        }

        updateCount();
        setInterval(updateCount, 30000);
    }

    /**
     * Initialize file upload enhancements
     */
    function initFileUpload() {
        var fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(function (input) {
            input.addEventListener('change', function () {
                var fileName = this.files[0] ? this.files[0].name : '';
                var label = this.nextElementSibling;
                if (label && label.classList.contains('custom-file-label')) {
                    label.textContent = fileName || 'اختر ملف...';
                }
                if (this.files[0]) {
                    var size = formatFileSize(this.files[0].size);
                    var existing = this.parentElement.querySelector('.file-size-info');
                    if (existing) existing.remove();
                    var sizeSpan = document.createElement('span');
                    sizeSpan.className = 'text-muted ms-2 file-size-info';
                    sizeSpan.textContent = '(' + size + ')';
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
        var k = 1024;
        var sizes = ['Bytes', 'KB', 'MB', 'GB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /* ==========================================================
       8. GLOBAL FUNCTIONS (File Visibility, Notifications, AI Chat)
       ========================================================== */

    /**
     * Show/Hide loading spinner on element
     */
    window.showLoading = function (element) {
        var spinner = document.createElement('div');
        spinner.className = 'spinner-border spinner-border-sm ms-2';
        spinner.setAttribute('role', 'status');
        element.appendChild(spinner);
        element.disabled = true;
    };

    window.hideLoading = function (element) {
        var spinner = element.querySelector('.spinner-border');
        if (spinner) spinner.remove();
        element.disabled = false;
    };

    /**
     * AJAX form submission
     */
    window.submitFormAjax = function (form, successCallback) {
        var formData = new FormData(form);
        var submitBtn = form.querySelector('[type="submit"]');
        if (submitBtn) window.showLoading(submitBtn);

        fetch(form.action, {
            method: form.method || 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (submitBtn) window.hideLoading(submitBtn);
            if (data.success) {
                window.showToast(data.message || 'تمت العملية بنجاح', 'success');
                if (successCallback) successCallback(data);
            } else {
                window.showToast(data.error || 'حدث خطأ', 'danger');
            }
        })
        .catch(function () {
            if (submitBtn) window.hideLoading(submitBtn);
            window.showToast('حدث خطأ في الاتصال', 'danger');
        });
    };

    /**
     * Toggle file visibility (instructor)
     */
    window.toggleFileVisibility = function (fileId, button) {
        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        csrfToken = csrfToken ? csrfToken.value : '';

        fetch('/courses/instructor/files/' + fileId + '/toggle-visibility/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                var icon = button.querySelector('i');
                if (icon) {
                    icon.className = data.is_visible ? 'bi bi-eye' : 'bi bi-eye-slash';
                }
                button.title = data.is_visible ? 'إخفاء' : 'إظهار';
                window.showToast(data.message, 'success');
            }
        })
        .catch(function () {
            window.showToast('حدث خطأ', 'danger');
        });
    };

    /**
     * Mark notification as read
     */
    window.markNotificationRead = function (notificationId) {
        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        csrfToken = csrfToken ? csrfToken.value : '';

        fetch('/notifications/' + notificationId + '/read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                var item = document.querySelector('[data-notification-id="' + notificationId + '"]');
                if (item) item.classList.remove('unread');
            }
        });
    };

    /**
     * AI Chat functionality
     */
    window.sendChatMessage = function (fileId) {
        var input = document.getElementById('chat-input');
        var question = input ? input.value.trim() : '';
        if (!question) return;

        var chatContainer = document.getElementById('chat-messages');
        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        csrfToken = csrfToken ? csrfToken.value : '';

        // Add user message
        chatContainer.innerHTML +=
            '<div class="chat-message user animate-slide-up">' +
            '  <p class="mb-1">' + question + '</p>' +
            '  <small class="message-time">الآن</small>' +
            '</div>';

        input.value = '';
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Show loading
        var loadingId = 'loading-' + Date.now();
        chatContainer.innerHTML +=
            '<div class="chat-message ai" id="' + loadingId + '">' +
            '  <div class="spinner-border spinner-border-sm" role="status"></div>' +
            '  <span class="ms-2">جاري التفكير...</span>' +
            '</div>';

        var formData = new FormData();
        formData.append('question', question);

        fetch('/ai/ask/' + fileId + '/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            if (data.success) {
                chatContainer.innerHTML +=
                    '<div class="chat-message ai animate-slide-up">' +
                    '  <p class="mb-1">' + data.answer + '</p>' +
                    '  <small class="message-time">' + data.created_at + '</small>' +
                    '</div>';
            } else {
                chatContainer.innerHTML +=
                    '<div class="chat-message ai text-danger">' +
                    '  <p class="mb-0">' + data.error + '</p>' +
                    '</div>';
            }
            chatContainer.scrollTop = chatContainer.scrollHeight;
        })
        .catch(function () {
            var loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            chatContainer.innerHTML +=
                '<div class="chat-message ai text-danger">' +
                '  <p class="mb-0">حدث خطأ في الاتصال</p>' +
                '</div>';
        });
    };

})();
