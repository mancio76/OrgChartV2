/**
 * Enhanced Form Interactions and User Feedback
 * Task 6.3 Implementation - Organigramma Web App
 */

// Form enhancements namespace
window.FormEnhancements = window.FormEnhancements || {};

/**
 * Initialize all form enhancements
 */
FormEnhancements.init = function() {
    this.setupRealTimeValidation();
    this.setupFormProgress();
    this.setupSmartHelp();
    this.setupFieldInteractions();
    this.setupNotificationSystem();
    this.setupAccessibilityFeatures();
    console.log('Form enhancements initialized');
};

/**
 * Setup real-time validation with enhanced feedback
 */
FormEnhancements.setupRealTimeValidation = function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        const fields = form.querySelectorAll('.form-control, .form-select, .form-check-input');
        
        fields.forEach(function(field) {
            // Real-time validation on input
            field.addEventListener('input', function() {
                FormEnhancements.validateFieldRealTime(this);
            });
            
            // Validation on blur with enhanced feedback
            field.addEventListener('blur', function() {
                FormEnhancements.validateFieldComplete(this);
            });
            
            // Clear validation on focus
            field.addEventListener('focus', function() {
                FormEnhancements.clearFieldFeedback(this);
            });
        });
        
        // Enhanced form submission
        form.addEventListener('submit', function(e) {
            console.log('.FormEnhancements.setupRealTimeValidation.needs-validation.handleFormSubmission');
            e.preventDefault();
            FormEnhancements.handleFormSubmission(this);
        });
    });
};

/**
 * Real-time field validation
 */
FormEnhancements.validateFieldRealTime = function(field) {
    const value = field.value.trim();
    const fieldContainer = field.closest('.mb-3, .form-field') || field.parentElement;
    
    // Remove existing real-time feedback
    const existingFeedback = fieldContainer.querySelector('.realtime-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // Skip if field is empty (will be handled on blur)
    if (!value && !field.hasAttribute('required')) {
        return;
    }
    
    // Perform validation
    const validation = FormEnhancements.performFieldValidation(field);
    
    if (validation.isValid) {
        FormEnhancements.showFieldSuccess(field);
    } else if (value) {
        FormEnhancements.showFieldWarning(field, validation.errors[0]);
    }
};

/**
 * Complete field validation on blur
 */
FormEnhancements.validateFieldComplete = function(field) {
    const validation = FormEnhancements.performFieldValidation(field);
    
    if (validation.isValid) {
        FormEnhancements.showFieldSuccess(field);
    } else {
        FormEnhancements.showFieldError(field, validation.errors);
    }
    
    // Update form progress
    FormEnhancements.updateFormProgress(field.closest('form'));
};

/**
 * Perform comprehensive field validation
 */
FormEnhancements.performFieldValidation = function(field) {
    const value = field.value.trim();
    const errors = [];
    let isValid = true;
    
    // Required validation
    if (field.hasAttribute('required') && !value) {
        errors.push('Questo campo è obbligatorio');
        isValid = false;
    }
    
    // Type-specific validation
    if (value) {
        switch (field.type) {
            case 'email':
                if (!FormEnhancements.isValidEmail(value)) {
                    errors.push('Inserisci un indirizzo email valido (es. nome@dominio.it)');
                    isValid = false;
                }
                break;
                
            case 'tel':
                if (!FormEnhancements.isValidPhone(value)) {
                    errors.push('Inserisci un numero di telefono valido');
                    isValid = false;
                }
                break;
                
            case 'url':
                if (!FormEnhancements.isValidUrl(value)) {
                    errors.push('Inserisci un URL valido (es. https://www.esempio.it)');
                    isValid = false;
                }
                break;
                
            case 'number':
                const numValue = parseFloat(value);
                if (isNaN(numValue)) {
                    errors.push('Inserisci un numero valido');
                    isValid = false;
                } else {
                    const min = field.getAttribute('min');
                    const max = field.getAttribute('max');
                    if (min !== null && numValue < parseFloat(min)) {
                        errors.push(`Il valore deve essere almeno ${min}`);
                        isValid = false;
                    }
                    if (max !== null && numValue > parseFloat(max)) {
                        errors.push(`Il valore non può superare ${max}`);
                        isValid = false;
                    }
                }
                break;
                
            case 'date':
                if (!FormEnhancements.isValidDate(value)) {
                    errors.push('Inserisci una data valida');
                    isValid = false;
                }
                break;
        }
        
        // Length validation
        const minLength = field.getAttribute('minlength');
        const maxLength = field.getAttribute('maxlength');
        
        if (minLength && value.length < parseInt(minLength)) {
            errors.push(`Inserisci almeno ${minLength} caratteri`);
            isValid = false;
        }
        
        if (maxLength && value.length > parseInt(maxLength)) {
            errors.push(`Non superare i ${maxLength} caratteri`);
            isValid = false;
        }
        
        // Pattern validation
        const pattern = field.getAttribute('pattern');
        if (pattern && !new RegExp(pattern).test(value)) {
            const title = field.getAttribute('title') || 'Il formato inserito non è valido';
            errors.push(title);
            isValid = false;
        }
        
        // Custom validation
        const customValidator = field.getAttribute('data-validator');
        if (customValidator && window[customValidator]) {
            const customResult = window[customValidator](value, field);
            if (customResult !== true) {
                errors.push(customResult || 'Valore non valido');
                isValid = false;
            }
        }
    }
    
    return { isValid, errors };
};

/**
 * Show field success state
 */
FormEnhancements.showFieldSuccess = function(field) {
    const fieldContainer = field.closest('.mb-3, .form-field') || field.parentElement;
    
    // Clear existing states
    field.classList.remove('is-invalid');
    fieldContainer.classList.remove('has-error');
    
    // Add success state
    field.classList.add('is-valid');
    fieldContainer.classList.add('has-success');
    
    // Remove existing feedback
    const existingFeedback = fieldContainer.querySelectorAll('.invalid-feedback, .realtime-feedback');
    existingFeedback.forEach(el => el.remove());
    
    // Add success feedback
    const feedback = document.createElement('div');
    feedback.className = 'valid-feedback';
    feedback.innerHTML = '<i class="bi bi-check-circle me-1"></i>Campo valido';
    field.parentElement.appendChild(feedback);
    
    // Add success animation
    fieldContainer.classList.add('field-success-animation');
    setTimeout(() => {
        fieldContainer.classList.remove('field-success-animation');
    }, 1000);
};

/**
 * Show field error state
 */
FormEnhancements.showFieldError = function(field, errors) {
    const fieldContainer = field.closest('.mb-3, .form-field') || field.parentElement;
    
    // Clear existing states
    field.classList.remove('is-valid');
    fieldContainer.classList.remove('has-success');
    
    // Add error state
    field.classList.add('is-invalid');
    fieldContainer.classList.add('has-error');
    
    // Remove existing feedback
    const existingFeedback = fieldContainer.querySelectorAll('.valid-feedback, .realtime-feedback');
    existingFeedback.forEach(el => el.remove());
    
    // Add error feedback
    errors.forEach(function(error) {
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.innerHTML = `<i class="bi bi-exclamation-circle me-1"></i>${error}`;
        field.parentElement.appendChild(feedback);
    });
    
    // Add error animation
    fieldContainer.classList.add('field-invalid');
    setTimeout(() => {
        fieldContainer.classList.remove('field-invalid');
    }, 500);
};

/**
 * Show field warning (for real-time feedback)
 */
FormEnhancements.showFieldWarning = function(field, message) {
    const fieldContainer = field.closest('.mb-3, .form-field') || field.parentElement;
    
    // Remove existing real-time feedback
    const existingFeedback = fieldContainer.querySelector('.realtime-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // Add warning feedback
    const feedback = document.createElement('div');
    feedback.className = 'realtime-feedback text-warning';
    feedback.innerHTML = `<i class="bi bi-exclamation-triangle me-1"></i>${message}`;
    field.parentElement.appendChild(feedback);
};

/**
 * Clear field feedback
 */
FormEnhancements.clearFieldFeedback = function(field) {
    const fieldContainer = field.closest('.mb-3, .form-field') || field.parentElement;
    
    // Remove validation classes
    field.classList.remove('is-valid', 'is-invalid');
    fieldContainer.classList.remove('has-success', 'has-error');
    
    // Remove feedback elements
    const feedback = fieldContainer.querySelectorAll('.valid-feedback, .invalid-feedback, .realtime-feedback');
    feedback.forEach(el => el.remove());
};

/**
 * Setup form progress indicator
 */
FormEnhancements.setupFormProgress = function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        // Create progress indicator
        const progressContainer = document.createElement('div');
        progressContainer.className = 'form-progress-container mb-3';
        progressContainer.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <small class="text-muted">Completamento modulo</small>
                <small class="text-muted"><span class="progress-percentage">0</span>%</small>
            </div>
            <div class="form-progress">
                <div class="form-progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
        `;
        
        const firstElement = form.firstChild;
        form.insertBefore(progressContainer, firstElement);

        /*
        // Insert at the beginning of the form
        const firstField = form.querySelector('.form-control, .form-select');
        if (firstField) {
            const firstContainer = firstField.closest('.mb-3, .form-field');
            if (firstContainer) {
                firstContainer.parentElement.insertBefore(progressContainer, firstContainer);
            }
        }
        */

        // Update progress on field changes
        const fields = form.querySelectorAll('.form-control, .form-select');
        fields.forEach(function(field) {
            field.addEventListener('input', () => FormEnhancements.updateFormProgress(form));
            field.addEventListener('blur', () => FormEnhancements.updateFormProgress(form));
        });
        
        // Initial progress update
        FormEnhancements.updateFormProgress(form);
    });
};

/**
 * Update form progress
 */
FormEnhancements.updateFormProgress = function(form) {
    const progressBar = form.querySelector('.form-progress-bar');
    const progressPercentage = form.querySelector('.progress-percentage');
    
    if (!progressBar || !progressPercentage) return;
    
    const fields = form.querySelectorAll('.form-control, .form-select');
    const requiredFields = form.querySelectorAll('[required]');
    
    let filledFields = 0;
    let validFields = 0;
    
    fields.forEach(function(field) {
        if (field.value.trim()) {
            filledFields++;
        }
        if (field.classList.contains('is-valid')) {
            validFields++;
        }
    });
    
    const totalFields = Math.max(fields.length, requiredFields.length);
    const progress = totalFields > 0 ? Math.round((filledFields / totalFields) * 100) : 0;
    
    progressBar.style.width = progress + '%';
    progressBar.setAttribute('aria-valuenow', progress);
    progressPercentage.textContent = progress;
    
    // Change color based on validation state
    if (validFields === filledFields && filledFields > 0) {
        progressBar.style.background = 'linear-gradient(90deg, var(--success-color), var(--info-color))';
    } else if (form.querySelectorAll('.is-invalid').length > 0) {
        progressBar.style.background = 'linear-gradient(90deg, var(--danger-color), var(--warning-color))';
    } else {
        progressBar.style.background = 'linear-gradient(90deg, var(--primary-color), var(--info-color))';
    }
};

/**
 * Setup smart help system
 */
FormEnhancements.setupSmartHelp = function() {
    const fieldsWithHelp = document.querySelectorAll('[data-help], [title]');
    
    fieldsWithHelp.forEach(function(field) {
        const helpText = field.getAttribute('data-help') || field.getAttribute('title');
        if (!helpText) return;
        
        // Create help element
        const helpElement = document.createElement('div');
        helpElement.className = 'form-help';
        helpElement.innerHTML = `<i class="bi bi-info-circle me-1"></i>${helpText}`;
        
        // Insert after field
        field.parentElement.appendChild(helpElement);
        
        // Show/hide on focus/blur
        field.addEventListener('focus', function() {
            helpElement.style.display = 'block';
        });
        
        field.addEventListener('blur', function() {
            setTimeout(() => {
                helpElement.style.display = 'none';
            }, 200);
        });
    });
};

/**
 * Setup field interactions
 */
FormEnhancements.setupFieldInteractions = function() {
    // Auto-format phone numbers
    const phoneFields = document.querySelectorAll('input[type="tel"]');
    phoneFields.forEach(function(field) {
        field.addEventListener('input', function() {
            this.value = FormEnhancements.formatPhoneNumber(this.value);
        });
    });
    
    // Auto-capitalize names
    const nameFields = document.querySelectorAll('input[name*="name"], input[name*="nome"]');
    nameFields.forEach(function(field) {
        field.addEventListener('blur', function() {
            this.value = FormEnhancements.capitalizeWords(this.value);
        });
    });
    
    // Auto-suggest based on existing data
    const fieldsWithSuggestions = document.querySelectorAll('[data-suggestions]');
    fieldsWithSuggestions.forEach(function(field) {
        FormEnhancements.setupFieldSuggestions(field);
    });
};

/**
 * Setup field suggestions
 */
FormEnhancements.setupFieldSuggestions = function(field) {
    const suggestionsData = field.getAttribute('data-suggestions');
    let suggestions = [];
    
    try {
        suggestions = JSON.parse(suggestionsData);
    } catch (e) {
        suggestions = suggestionsData.split(',').map(s => s.trim());
    }
    
    // Create suggestions container
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'field-suggestions';
    field.parentElement.appendChild(suggestionsContainer);
    
    field.addEventListener('input', function() {
        const value = this.value.toLowerCase();
        const matches = suggestions.filter(suggestion => 
            suggestion.toLowerCase().includes(value) && 
            suggestion.toLowerCase() !== value
        );
        
        if (matches.length > 0 && value.length > 1) {
            suggestionsContainer.innerHTML = matches.slice(0, 5).map(match => 
                `<div class="suggestion-item" onclick="FormEnhancements.applySuggestion('${field.id}', '${match}')">${match}</div>`
            ).join('');
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    field.addEventListener('blur', function() {
        setTimeout(() => {
            suggestionsContainer.style.display = 'none';
        }, 200);
    });
};

/**
 * Apply suggestion to field
 */
FormEnhancements.applySuggestion = function(fieldId, suggestion) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.value = suggestion;
        field.dispatchEvent(new Event('input', { bubbles: true }));
        field.focus();
    }
};

/**
 * Setup notification system
 */
FormEnhancements.setupNotificationSystem = function() {
    // Check for URL parameters indicating success/error
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.get('success')) {
        FormEnhancements.showNotification('success', decodeURIComponent(urlParams.get('success')));
        FormEnhancements.removeUrlParameter('success');
    }
    
    if (urlParams.get('error')) {
        FormEnhancements.showNotification('error', decodeURIComponent(urlParams.get('error')));
        FormEnhancements.removeUrlParameter('error');
    }
};

/**
 * Show notification
 */
FormEnhancements.showNotification = function(type, message) {
    if (window.OrgApp) {
        switch (type) {
            case 'success':
                window.OrgApp.showSuccess(message);
                break;
            case 'error':
                window.OrgApp.showError(message);
                break;
            case 'warning':
                window.OrgApp.showWarning(message);
                break;
            case 'info':
                window.OrgApp.showInfo(message);
                break;
        }
    }
};

/**
 * Handle form submission
 */
FormEnhancements.handleFormSubmission = function(form) {
    console.log('.FormEnhancements.handleFormSubmission');
    // Validate all fields
    const fields = form.querySelectorAll('.form-control, .form-select');
    let isValid = true;
    const errors = [];
    
    fields.forEach(function(field) {
        const validation = FormEnhancements.performFieldValidation(field);
        if (!validation.isValid) {
            FormEnhancements.showFieldError(field, validation.errors);
            errors.push(...validation.errors);
            isValid = false;
        } else {
            FormEnhancements.showFieldSuccess(field);
        }
    });
    
    if (isValid) {
        console.log('.FormEnhancements.handleFormSubmission.valid');
        // Skip enhanced submission for simple forms
        if (form.hasAttribute('data-simple-submit')) {
            console.log('.FormEnhancements.handleFormSubmission.data-simple-submit');
            form.submit();
            return;
        }
        
        // Show loading state
        FormEnhancements.setFormLoading(form, true);
        
        // Show success feedback
        FormEnhancements.showNotification('success', 'Modulo validato correttamente!');
        
        // Submit form after brief delay
        setTimeout(() => {
            console.log('.FormEnhancements.handleFormSubmission.submit');
            form.submit();
        }, 500);
    } else {
        console.log('.FormEnhancements.handleFormSubmission.invalid');
        // Show error summary
        FormEnhancements.showValidationSummary(form, errors);
        
        // Focus first invalid field
        const firstInvalid = form.querySelector('.is-invalid');
        if (firstInvalid) {
            firstInvalid.focus();
            firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
};

/**
 * Show validation summary
 */
FormEnhancements.showValidationSummary = function(form, errors) {
    let summary = form.querySelector('.validation-summary');
    
    if (!summary) {
        summary = document.createElement('div');
        summary.className = 'validation-summary alert alert-danger';
        form.insertBefore(summary, form.firstChild);
    }
    
    const uniqueErrors = [...new Set(errors)];
    
    summary.innerHTML = `
        <h6><i class="bi bi-exclamation-triangle me-2"></i>Correggi i seguenti errori:</h6>
        <ul class="mb-0">
            ${uniqueErrors.map(error => `<li>${error}</li>`).join('')}
        </ul>
    `;
    
    summary.scrollIntoView({ behavior: 'smooth', block: 'center' });
};

/**
 * Set form loading state
 */
FormEnhancements.setFormLoading = function(form, loading) {
    if (loading) {
        form.classList.add('form-loading');
        const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
        submitButtons.forEach(function(button) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Elaborazione...';
        });
    } else {
        form.classList.remove('form-loading');
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
 * Setup accessibility features
 */
FormEnhancements.setupAccessibilityFeatures = function() {
    // Add ARIA labels and descriptions
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        // Add form description
        if (!form.getAttribute('aria-describedby')) {
            const description = document.createElement('div');
            description.id = `form-description-${Date.now()}`;
            description.className = 'visually-hidden';
            description.textContent = 'Modulo con validazione in tempo reale. I campi obbligatori sono contrassegnati con asterisco.';
            form.insertBefore(description, form.firstChild);
            form.setAttribute('aria-describedby', description.id);
        }
        
        // Enhance field accessibility
        const fields = form.querySelectorAll('.form-control, .form-select');
        fields.forEach(function(field) {
            // Add aria-invalid attribute
            field.addEventListener('invalid', function() {
                this.setAttribute('aria-invalid', 'true');
            });
            
            field.addEventListener('input', function() {
                if (this.checkValidity()) {
                    this.setAttribute('aria-invalid', 'false');
                }
            });
        });
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Escape to clear validation
        if (e.key === 'Escape') {
            const activeField = document.activeElement;
            if (activeField && activeField.classList.contains('is-invalid')) {
                FormEnhancements.clearFieldFeedback(activeField);
            }
        }
        
        // Ctrl+Enter to submit form
        if (e.ctrlKey && e.key === 'Enter') {
            const form = document.activeElement.closest('form');
            if (form && form.classList.contains('needs-validation')) {
                FormEnhancements.handleFormSubmission(form);
            }
        }
    });
};

/**
 * Utility functions
 */
FormEnhancements.isValidEmail = function(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

FormEnhancements.isValidPhone = function(phone) {
    const phoneRegex = /^(\+39\s?)?((3[0-9]{2}|0[0-9]{1,3})\s?[0-9]{6,7})$/;
    return phoneRegex.test(phone.replace(/\s/g, ''));
};

FormEnhancements.isValidUrl = function(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
};

FormEnhancements.isValidDate = function(dateString) {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date.getTime());
};

FormEnhancements.formatPhoneNumber = function(phone) {
    // Remove all non-digits
    const digits = phone.replace(/\D/g, '');
    
    // Format Italian phone numbers
    if (digits.startsWith('39')) {
        return '+39 ' + digits.slice(2).replace(/(\d{3})(\d{3})(\d{4})/, '$1 $2 $3');
    } else if (digits.startsWith('3')) {
        return digits.replace(/(\d{3})(\d{3})(\d{4})/, '$1 $2 $3');
    } else if (digits.startsWith('0')) {
        return digits.replace(/(\d{2,4})(\d{6,7})/, '$1 $2');
    }
    
    return phone;
};

FormEnhancements.capitalizeWords = function(str) {
    return str.replace(/\b\w/g, l => l.toUpperCase());
};

FormEnhancements.removeUrlParameter = function(param) {
    const url = new URL(window.location);
    url.searchParams.delete(param);
    window.history.replaceState({}, '', url);
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    FormEnhancements.init();
});

// Export for global use
window.FormEnhancements = FormEnhancements;