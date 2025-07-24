/**
 * Base JavaScript functions and utilities
 * Organigramma Web App
 */

// Global app namespace
window.OrgApp = window.OrgApp || {};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    OrgApp.init();
});

/**
 * Main application initialization
 */
OrgApp.init = function() {
    // Initialize tooltips
    this.initTooltips();
    
    // Initialize popovers
    this.initPopovers();
    
    // Setup global event handlers
    this.setupEventHandlers();
    
    // Setup form validation
    this.setupFormValidation();
    
    console.log('OrgApp initialized');
};

/**
 * Initialize Bootstrap tooltips
 */
OrgApp.initTooltips = function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
};

/**
 * Initialize Bootstrap popovers
 */
OrgApp.initPopovers = function() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
};

/**
 * Setup global event handlers
 */
OrgApp.setupEventHandlers = function() {
    // Handle delete confirmations
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-delete') || e.target.closest('.btn-delete')) {
            e.preventDefault();
            const button = e.target.classList.contains('btn-delete') ? e.target : e.target.closest('.btn-delete');
            OrgApp.confirmDelete(button);
        }
    });
    
    // Handle form submissions with loading states
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.tagName === 'FORM' && !form.classList.contains('no-loading')) {
            OrgApp.setFormLoading(form, true);
        }
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert.alert-dismissible');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
};

/**
 * Setup form validation
 */
OrgApp.setupFormValidation = function() {
    // Add Bootstrap validation classes
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
};

/**
 * Confirm delete action
 */
OrgApp.confirmDelete = function(button) {
    const itemName = button.dataset.itemName || 'questo elemento';
    const itemType = button.dataset.itemType || 'elemento';
    
    if (confirm(`Sei sicuro di voler eliminare ${itemType} "${itemName}"?\n\nQuesta azione non può essere annullata.`)) {
        // If button is inside a form, submit it
        const form = button.closest('form');
        if (form) {
            form.submit();
        } else {
            // Otherwise, follow the href
            const href = button.getAttribute('href');
            if (href) {
                window.location.href = href;
            }
        }
    }
};

/**
 * Set form loading state
 */
OrgApp.setFormLoading = function(form, loading) {
    if (loading) {
        form.classList.add('loading');
        const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitButtons.forEach(function(button) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Elaborazione...';
        });
    } else {
        form.classList.remove('loading');
        const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitButtons.forEach(function(button) {
            button.disabled = false;
            if (button.dataset.originalText) {
                button.textContent = button.dataset.originalText;
                delete button.dataset.originalText;
            }
        });
    }
};

/**
 * Enhanced notification system - Task 6.3
 */

/**
 * Show success message with enhanced features
 */
OrgApp.showSuccess = function(message, options = {}) {
    const config = {
        type: 'success',
        message: message,
        duration: options.duration || 5000,
        persistent: options.persistent || false,
        actions: options.actions || null,
        ...options
    };
    OrgApp.showEnhancedNotification(config);
};

/**
 * Show error message with enhanced features
 */
OrgApp.showError = function(message, options = {}) {
    const config = {
        type: 'danger',
        message: message,
        duration: options.duration || 8000,
        persistent: options.persistent || true,
        actions: options.actions || null,
        ...options
    };
    OrgApp.showEnhancedNotification(config);
};

/**
 * Show warning message with enhanced features
 */
OrgApp.showWarning = function(message, options = {}) {
    const config = {
        type: 'warning',
        message: message,
        duration: options.duration || 6000,
        persistent: options.persistent || false,
        actions: options.actions || null,
        ...options
    };
    OrgApp.showEnhancedNotification(config);
};

/**
 * Show info message with enhanced features
 */
OrgApp.showInfo = function(message, options = {}) {
    const config = {
        type: 'info',
        message: message,
        duration: options.duration || 4000,
        persistent: options.persistent || false,
        actions: options.actions || null,
        ...options
    };
    OrgApp.showEnhancedNotification(config);
};

/**
 * Show enhanced notification
 */
OrgApp.showEnhancedNotification = function(config) {
    const notificationId = 'notification_' + Date.now();
    const alertsContainer = document.querySelector('.container-fluid') || document.body;
    
    // Create notification element
    const notification = document.createElement('div');
    notification.id = notificationId;
    notification.className = `alert alert-${config.type} alert-dismissible fade show enhanced-notification`;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'polite');
    
    // Build notification content
    let content = `
        <div class="notification-content">
            <div class="notification-header">
                <i class="bi bi-${OrgApp.getAlertIcon(config.type)} me-2"></i>
                <strong>${OrgApp.getAlertTitle(config.type)}</strong>
            </div>
            <div class="notification-message">${config.message}</div>
    `;
    
    // Add actions if provided
    if (config.actions && config.actions.length > 0) {
        content += '<div class="notification-actions mt-2">';
        config.actions.forEach(action => {
            content += `<button type="button" class="btn btn-sm btn-outline-${config.type === 'danger' ? 'light' : 'dark'} me-2" onclick="${action.handler}">${action.label}</button>`;
        });
        content += '</div>';
    }
    
    content += `
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Chiudi"></button>
    `;
    
    notification.innerHTML = content;
    
    // Add to container
    alertsContainer.insertBefore(notification, alertsContainer.firstElementChild);
    
    // Add progress bar for timed notifications
    if (!config.persistent && config.duration > 0) {
        const progressBar = document.createElement('div');
        progressBar.className = 'notification-progress';
        progressBar.innerHTML = '<div class="notification-progress-bar"></div>';
        notification.appendChild(progressBar);
        
        // Animate progress bar
        const progressBarElement = progressBar.querySelector('.notification-progress-bar');
        progressBarElement.style.animationDuration = config.duration + 'ms';
        progressBarElement.classList.add('animate');
    }
    
    // Auto-hide if not persistent
    if (!config.persistent && config.duration > 0) {
        setTimeout(function() {
            if (notification.parentElement) {
                const bsAlert = new bootstrap.Alert(notification);
                bsAlert.close();
            }
        }, config.duration);
    }
    
    // Add sound notification if enabled
    if (config.sound !== false) {
        OrgApp.playNotificationSound(config.type);
    }
    
    return notificationId;
};

/**
 * Get alert title based on type
 */
OrgApp.getAlertTitle = function(type) {
    const titles = {
        'success': 'Operazione completata',
        'danger': 'Errore',
        'warning': 'Attenzione',
        'info': 'Informazione'
    };
    return titles[type] || 'Notifica';
};

/**
 * Play notification sound
 */
OrgApp.playNotificationSound = function(type) {
    // Create audio context for notification sounds
    if (typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined') {
        try {
            const audioContext = new (AudioContext || webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Different frequencies for different notification types
            const frequencies = {
                'success': 800,
                'info': 600,
                'warning': 400,
                'danger': 300
            };
            
            oscillator.frequency.setValueAtTime(frequencies[type] || 600, audioContext.currentTime);
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (e) {
            // Fallback: no sound if audio context fails
            console.log('Audio notification not available');
        }
    }
};

/**
 * Show form success with specific styling
 */
OrgApp.showFormSuccess = function(message, formElement) {
    // Add success class to form
    if (formElement) {
        formElement.classList.add('form-success');
        setTimeout(() => {
            formElement.classList.remove('form-success');
        }, 3000);
    }
    
    OrgApp.showSuccess(message, {
        actions: [
            {
                label: 'Continua',
                handler: 'OrgApp.dismissNotification(this)'
            }
        ]
    });
};

/**
 * Show form error with validation details
 */
OrgApp.showFormError = function(message, errors = []) {
    let fullMessage = message;
    
    if (errors.length > 0) {
        fullMessage += '<ul class="mt-2 mb-0">';
        errors.forEach(error => {
            fullMessage += `<li>${error}</li>`;
        });
        fullMessage += '</ul>';
    }
    
    OrgApp.showError(fullMessage, {
        persistent: true,
        actions: [
            {
                label: 'Correggi',
                handler: 'OrgApp.focusFirstError()'
            }
        ]
    });
};

/**
 * Focus first error field
 */
OrgApp.focusFirstError = function() {
    const firstError = document.querySelector('.is-invalid, .form-control:invalid');
    if (firstError) {
        firstError.focus();
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    OrgApp.dismissNotification();
};

/**
 * Dismiss notification
 */
OrgApp.dismissNotification = function(buttonElement) {
    const notification = buttonElement ? buttonElement.closest('.alert') : document.querySelector('.enhanced-notification');
    if (notification) {
        const bsAlert = new bootstrap.Alert(notification);
        bsAlert.close();
    }
};

/**
 * Show loading notification
 */
OrgApp.showLoading = function(message = 'Caricamento in corso...') {
    const loadingId = 'loading_' + Date.now();
    
    const loading = document.createElement('div');
    loading.id = loadingId;
    loading.className = 'loading-notification';
    loading.innerHTML = `
        <div class="loading-content">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Caricamento...</span>
            </div>
            ${message}
        </div>
    `;
    
    document.body.appendChild(loading);
    
    return loadingId;
};

/**
 * Hide loading notification
 */
OrgApp.hideLoading = function(loadingId) {
    const loading = loadingId ? document.getElementById(loadingId) : document.querySelector('.loading-notification');
    if (loading) {
        loading.remove();
    }
};

/**
 * Show alert message
 */
OrgApp.showAlert = function(type, message) {
    const alertsContainer = document.querySelector('.container-fluid') || document.body;
    
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="bi bi-${OrgApp.getAlertIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const alertElement = document.createElement('div');
    alertElement.innerHTML = alertHtml;
    
    alertsContainer.insertBefore(alertElement.firstElementChild, alertsContainer.firstElementChild);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        const alert = alertsContainer.querySelector('.alert');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
};

/**
 * Get alert icon based on type
 */
OrgApp.getAlertIcon = function(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
};

/**
 * Format date for display
 */
OrgApp.formatDate = function(dateString, format = 'dd/mm/yyyy') {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    
    switch (format) {
        case 'dd/mm/yyyy':
            return `${day}/${month}/${year}`;
        case 'yyyy-mm-dd':
            return `${year}-${month}-${day}`;
        case 'long':
            return date.toLocaleDateString('it-IT', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        default:
            return `${day}/${month}/${year}`;
    }
};

/**
 * Format percentage for display
 */
OrgApp.formatPercentage = function(value) {
    if (typeof value !== 'number') return '';
    return Math.round(value * 100) + '%';
};

/**
 * Debounce function
 */
OrgApp.debounce = function(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
};

/**
 * Scroll to element smoothly
 */
OrgApp.scrollTo = function(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
};

/**
 * Copy text to clipboard
 */
OrgApp.copyToClipboard = function(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            OrgApp.showSuccess('Testo copiato negli appunti');
        }).catch(function() {
            OrgApp.showError('Errore durante la copia');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            OrgApp.showSuccess('Testo copiato negli appunti');
        } catch (err) {
            OrgApp.showError('Errore durante la copia');
        }
        
        document.body.removeChild(textArea);
    }
};

/**
 * Validate email format
 */
OrgApp.isValidEmail = function(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

/**
 * Get URL parameter
 */
OrgApp.getUrlParameter = function(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
};

/**
 * Set URL parameter without reload
 */
OrgApp.setUrlParameter = function(name, value) {
    const url = new URL(window.location);
    if (value) {
        url.searchParams.set(name, value);
    } else {
        url.searchParams.delete(name);
    }
    window.history.replaceState({}, '', url);
};

/**
 * Escape HTML
 */
OrgApp.escapeHtml = function(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
};

/**
 * Export functions for global use
 */
window.showSuccess = OrgApp.showSuccess;
window.showError = OrgApp.showError;
window.showWarning = OrgApp.showWarning;
window.showInfo = OrgApp.showInfo;
window.formatDate = OrgApp.formatDate;
window.formatPercentage = OrgApp.formatPercentage;