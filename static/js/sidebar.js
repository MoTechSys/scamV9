/**
 * Sidebar 2.0 - JavaScript Controller
 * S-ACM - Smart Academic Content Management System
 * 
 * Features:
 * - State persistence with localStorage
 * - Smooth toggle animation
 * - Tooltip initialization when collapsed
 * - HTMX integration for SPA-like navigation
 */

(function () {
    'use strict';

    const STORAGE_KEY = 'sacm_sidebar_collapsed';

    // Elements
    let sidebar = null;
    let toggleBtn = null;
    let dashboardContent = null;

    /**
     * Initialize Sidebar
     */
    function init() {
        sidebar = document.getElementById('desktopSidebar');
        toggleBtn = document.getElementById('sidebarToggle');
        dashboardContent = document.querySelector('.dashboard-content');

        if (!sidebar || !toggleBtn) {
            return; // Not on a dashboard page
        }

        // Restore saved state
        restoreState();

        // Toggle button click
        toggleBtn.addEventListener('click', toggleSidebar);

        // Add tooltips to links when collapsed
        updateTooltips();

        // Initialize Bootstrap tooltips if collapsed
        if (isCollapsed()) {
            initTooltips();
        }

        // Handle submenu active state
        handleActiveSubmenu();

        console.log('[Sidebar] Initialized');
    }

    /**
     * Toggle sidebar collapsed state
     */
    function toggleSidebar() {
        const collapsed = sidebar.dataset.collapsed === 'true';
        sidebar.dataset.collapsed = !collapsed;

        // Save state
        saveState(!collapsed);

        // Update tooltips
        if (!collapsed) {
            initTooltips();
        } else {
            destroyTooltips();
        }

        // Trigger resize event for charts/tables
        setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
        }, 350);
    }

    /**
     * Check if sidebar is collapsed
     */
    function isCollapsed() {
        return sidebar && sidebar.dataset.collapsed === 'true';
    }

    /**
     * Save state to localStorage
     */
    function saveState(collapsed) {
        try {
            localStorage.setItem(STORAGE_KEY, collapsed ? 'true' : 'false');
        } catch (e) {
            console.warn('[Sidebar] Could not save state:', e);
        }
    }

    /**
     * Restore state from localStorage
     */
    function restoreState() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved === 'true') {
                sidebar.dataset.collapsed = 'true';
            }
        } catch (e) {
            console.warn('[Sidebar] Could not restore state:', e);
        }
    }

    /**
     * Update tooltip data attributes
     */
    function updateTooltips() {
        const links = sidebar.querySelectorAll('.sidebar-link');
        links.forEach(link => {
            const text = link.querySelector('.link-text');
            if (text) {
                link.setAttribute('data-tooltip', text.textContent.trim());
            }
        });
    }

    /**
     * Initialize Bootstrap tooltips
     */
    function initTooltips() {
        // Using Bootstrap's native tooltip
        const tooltipTriggerList = sidebar.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(el => {
            new bootstrap.Tooltip(el);
        });
    }

    /**
     * Destroy Bootstrap tooltips
     */
    function destroyTooltips() {
        const tooltipTriggerList = sidebar.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(el => {
            const tooltip = bootstrap.Tooltip.getInstance(el);
            if (tooltip) {
                tooltip.dispose();
            }
        });
    }

    /**
     * Handle active submenu - expand parent if child is active
     */
    function handleActiveSubmenu() {
        const activeLink = sidebar.querySelector('.submenu-link.active');
        if (activeLink) {
            const submenu = activeLink.closest('.collapse');
            if (submenu) {
                submenu.classList.add('show');
                const parentLink = sidebar.querySelector(`[href="#${submenu.id}"]`);
                if (parentLink) {
                    parentLink.setAttribute('aria-expanded', 'true');
                }
            }
        }
    }

    /**
     * HTMX Integration - Update sidebar after HTMX navigation
     */
    function setupHtmxIntegration() {
        document.body.addEventListener('htmx:afterSwap', function (evt) {
            // Re-apply active states after content swap
            const currentPath = window.location.pathname;
            const links = document.querySelectorAll('.sidebar-link');

            links.forEach(link => {
                const href = link.getAttribute('href');
                if (href && currentPath.startsWith(href) && href !== '#') {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        });
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Setup HTMX integration
    setupHtmxIntegration();

    // Expose for external use
    window.SACMSidebar = {
        toggle: toggleSidebar,
        isCollapsed: isCollapsed,
        collapse: () => {
            if (!isCollapsed()) toggleSidebar();
        },
        expand: () => {
            if (isCollapsed()) toggleSidebar();
        }
    };

})();
