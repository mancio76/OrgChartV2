/**
 * Enhanced Form Validation and User Feedback
 * Organigramma Web App - Task 6.3 Implementation
 */

// Form validation namespace
window.FormValidator = window.FormValidator || {};

/**
 * Initialize form validation system
 */
FormValidator.init = function() {
    this.setupValidation();
    this.setupRealTimeValidation();
    this.setupFormProgress();
    this.setupSuccessNotifications();
    this.setupAdvancedValidation();
    this.setupUserFeedback();
    this.setupFormInteractions();
    console.log('FormValidator initialized with enhanced features');
};

/**
 * Setup form validation
 */
FormValidator.setupValidation = function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            const isValid = FormValidator.validateForm(form);
            
            if (isValid) {
                FormValidator.showFormLoading(form);
                FormValidator.submitForm(form);
            } else {
                FormValidator.showValidationSummary(form);
                FormValidator.focusFirstInvalidField(form);
            }
            
            form.classList.add('was-validated');
        });
    });
};

/**
 * Setup real-time validation
 */
FormValidator.setupRealTimeValidation = function() {
    const inputs = document.querySelectorAll('.form-control, .form-select');
    
    inputs.forEach(function(input) {
        // Validate on blur
        input.addEventListener('blur', function() {
            FormValidator.validateField(this);
        });
        
        // Clear validation on focus
        input.addEventListener('focus', function() {
            FormValidator.clearFieldValidation(this);
        });
        
        // Real-time validation for specific field types
        if (input.type === 'email') {
            input.addEventListener('input', FormValidator.debounce(function() {
                FormValidator.validateEmail(this);
            }, 500));
        }
        
        if (input.type === 'number') {
            input.addEventListener('input', function() {
                FormValidator.validateNumber(this);
            });
        }
        
        if (input.hasAttribute('data-validate-length')) {
            input.addEventListener('input', function() {
                FormValidator.validateLength(this);
            });
        }
    });
};

/**
 * Validate entire form
 */
FormValidator.validateForm = function(form) {
    let isValid = true;
    const fields = form.querySelectorAll('.form-control, .form-select');
    
    fields.forEach(function(field) {
        if (!FormValidator.validateField(field)) {
            isValid = false;
        }
    });
    
    // Update form progress
    FormValidator.updateFormProgress(form);
    
    return isValid;
};

/**
 * Validate individual field
 */
FormValidator.validateField = function(field) {
    let isValid = true;
    const errors = [];
    
    // Required validation
    if (field.hasAttribute('required') && !field.value.trim()) {
        errors.push('Questo campo è obbligatorio');
        isValid = false;
    }
    
    // Type-specific validation
    if (field.value.trim()) {
        switch (field.type) {
            case 'email':
                if (!FormValidator.isValidEmail(field.value)) {
                    errors.push('Inserisci un indirizzo email valido');
                    isValid = false;
                }
                break;
                
            case 'number':
                const min = field.getAttribute('min');
                const max = field.getAttribute('max');
                const value = parseFloat(field.value);
                
                if (isNaN(value)) {
                    errors.push('Inserisci un numero valido');
                    isValid = false;
                } else {
                    if (min !== null && value < parseFloat(min)) {
                        errors.push(`Il valore deve essere almeno ${min}`);
                        isValid = false;
                    }
                    if (max !== null && value > parseFloat(max)) {
                        errors.push(`Il valore non può superare ${max}`);
                        isValid = false;
                    }
                }
                break;
                
            case 'date':
                if (!FormValidator.isValidDate(field.value)) {
                    errors.push('Inserisci una data valida');
                    isValid = false;
                }
                break;
        }
        
        // Length validation
        const minLength = field.getAttribute('minlength');
        const maxLength = field.getAttribute('maxlength');
        
        if (minLength && field.value.length < parseInt(minLength)) {
            errors.push(`Minimo ${minLength} caratteri richiesti`);
            isValid = false;
        }
        
        if (maxLength && field.value.length > parseInt(maxLength)) {
            errors.push(`Massimo ${maxLength} caratteri consentiti`);
            isValid = false;
        }
        
        // Custom validation patterns
        const pattern = field.getAttribute('pattern');
        if (pattern && !new RegExp(pattern).test(field.value)) {
            const patternTitle = field.getAttribute('title') || 'Formato non valido';
            errors.push(patternTitle);
            isValid = false;
        }
    }
    
    // Custom validation functions
    if (field.hasAttribute('data-validate-custom')) {
        const customValidator = field.getAttribute('data-validate-custom');
        if (window[customValidator] && typeof window[customValidator] === 'function') {
            const customResult = window[customValidator](field.value, field);
            if (customResult !== true) {
                errors.push(customResult || 'Valore non valido');
                isValid = false;
            }
        }
    }
    
    // Apply validation state
    FormValidator.setFieldValidationState(field, isValid, errors);
    
    return isValid;
};

/**
 * Set field validation state
 */
FormValidator.setFieldValidationState = function(field, isValid, errors = []) {
    const fieldContainer = field.closest('.form-field') || field.parentElement;
    
    // Remove existing validation classes
    field.classList.remove('is-valid', 'is-invalid');
    fieldContainer.classList.remove('field-valid', 'field-invalid');
    
    // Remove existing feedback
    const existingFeedback = fieldContainer.querySelectorAll('.valid-feedback, .invalid-feedback');
    existingFeedback.forEach(el => el.remove());
    
    if (isValid) {
        field.classList.add('is-valid');
        fieldContainer.classList.add('field-valid');
        
        // Add success feedback
        const feedback = document.createElement('div');
        feedback.className = 'valid-feedback';
        feedback.innerHTML = '<i class="bi bi-check-circle me-1"></i>Campo valido';
        field.parentElement.appendChild(feedback);
        
    } else {
        field.classList.add('is-invalid');
        fieldContainer.classList.add('field-invalid');
        
        // Add error feedback
        errors.forEach(function(error) {
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.innerHTML = `<i class="bi bi-exclamation-circle me-1"></i>${error}`;
            field.parentElement.appendChild(feedback);
        });
    }
};

/**
 * Clear field validation
 */
FormValidator.clearFieldValidation = function(field) {
    const fieldContainer = field.closest('.form-field') || field.parentElement;
    
    field.classList.remove('is-valid', 'is-invalid');
    fieldContainer.classList.remove('field-valid', 'field-invalid');
    
    const feedback = fieldContainer.querySelectorAll('.valid-feedback, .invalid-feedback');
    feedback.forEach(el => el.remove());
};

/**
 * Email validation
 */
FormValidator.validateEmail = function(field) {
    const isValid = FormValidator.isValidEmail(field.value);
    const errors = isValid ? [] : ['Inserisci un indirizzo email valido'];
    FormValidator.setFieldValidationState(field, isValid, errors);
    return isValid;
};

/**
 * Number validation
 */
FormValidator.validateNumber = function(field) {
    const value = parseFloat(field.value);
    const min = field.getAttribute('min');
    const max = field.getAttribute('max');
    let isValid = true;
    const errors = [];
    
    if (field.value.trim() && isNaN(value)) {
        errors.push('Inserisci un numero valido');
        isValid = false;
    } else if (!isNaN(value)) {
        if (min !== null && value < parseFloat(min)) {
            errors.push(`Il valore deve essere almeno ${min}`);
            isValid = false;
        }
        if (max !== null && value > parseFloat(max)) {
            errors.push(`Il valore non può superare ${max}`);
            isValid = false;
        }
    }
    
    FormValidator.setFieldValidationState(field, isValid, errors);
    return isValid;
};

/**
 * Length validation
 */
FormValidator.validateLength = function(field) {
    const length = field.value.length;
    const minLength = parseInt(field.getAttribute('minlength')) || 0;
    const maxLength = parseInt(field.getAttribute('maxlength')) || Infinity;
    
    let isValid = true;
    const errors = [];
    
    if (length < minLength) {
        errors.push(`Minimo ${minLength} caratteri richiesti`);
        isValid = false;
    }
    
    if (length > maxLength) {
        errors.push(`Massimo ${maxLength} caratteri consentiti`);
        isValid = false;
    }
    
    FormValidator.setFieldValidationState(field, isValid, errors);
    return isValid;
};

/**
 * Show validation summary
 */
FormValidator.showValidationSummary = function(form) {
    let summary = form.querySelector('.validation-summary');
    
    if (!summary) {
        summary = document.createElement('div');
        summary.className = 'validation-summary';
        form.insertBefore(summary, form.firstChild);
    }
    
    const invalidFields = form.querySelectorAll('.is-invalid');
    
    if (invalidFields.length > 0) {
        const errors = [];
        invalidFields.forEach(function(field) {
            const label = form.querySelector(`label[for="${field.id}"]`);
            const fieldName = label ? label.textContent.replace('*', '').trim() : field.name || 'Campo';
            const feedback = field.parentElement.querySelector('.invalid-feedback');
            const errorText = feedback ? feedback.textContent.replace(/^\s*\S+\s*/, '') : 'Errore di validazione';
            errors.push(`${fieldName}: ${errorText}`);
        });
        
        summary.innerHTML = `
            <h6><i class="bi bi-exclamation-triangle me-2"></i>Correggi i seguenti errori:</h6>
            <ul>
                ${errors.map(error => `<li>${error}</li>`).join('')}
            </ul>
        `;
        summary.classList.remove('hidden');
        
        // Scroll to summary
        summary.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        summary.classList.add('hidden');
    }
};

/**
 * Focus first invalid field
 */
FormValidator.focusFirstInvalidField = function(form) {
    const firstInvalid = form.querySelector('.is-invalid');
    if (firstInvalid) {
        firstInvalid.focus();
        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
};

/**
 * Setup form progress indicator
 */
FormValidator.setupFormProgress = function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        const progressContainer = document.createElement('div');
        progressContainer.className = 'form-progress';
        progressContainer.innerHTML = '<div class="form-progress-bar"></div>';
        
        const firstField = form.querySelector('.form-control, .form-select');
        if (firstField) {
            firstField.closest('.form-field, .mb-3, .col-md-6')?.parentElement?.insertBefore(progressContainer, firstField.closest('.form-field, .mb-3, .col-md-6'));
        }
        
        // Update progress on field changes
        const fields = form.querySelectorAll('.form-control, .form-select');
        fields.forEach(function(field) {
            field.addEventListener('input', function() {
                FormValidator.updateFormProgress(form);
            });
            field.addEventListener('blur', function() {
                FormValidator.updateFormProgress(form);
            });
        });
    });
};

/**
 * Update form progress
 */
FormValidator.updateFormProgress = function(form) {
    const progressBar = form.querySelector('.form-progress-bar');
    if (!progressBar) return;
    
    const fields = form.querySelectorAll('.form-control, .form-select');
    const requiredFields = form.querySelectorAll('.form-control[required], .form-select[required]');
    
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
    const progress = totalFields > 0 ? (filledFields / totalFields) * 100 : 0;
    
    progressBar.style.width = progress + '%';
    
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
 * Show form loading state
 */
FormValidator.showFormLoading = function(form) {
    form.classList.add('form-loading');
    
    const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    submitButtons.forEach(function(button) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Elaborazione...';
    });
};

/**
 * Hide form loading state
 */
FormValidator.hideFormLoading = function(form) {
    form.classList.remove('form-loading');
    
    const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    submitButtons.forEach(function(button) {
        button.disabled = false;
        if (button.dataset.originalText) {
            button.textContent = button.dataset.originalText;
            delete button.dataset.originalText;
        }
    });
};

/**
 * Submit form
 */
FormValidator.submitForm = function(form) {
    // Check if form has custom submit handler
    if (form.hasAttribute('data-custom-submit')) {
        const customHandler = form.getAttribute('data-custom-submit');
        if (window[customHandler] && typeof window[customHandler] === 'function') {
            window[customHandler](form);
            return;
        }
    }
    
    // Default form submission
    setTimeout(function() {
        form.submit();
    }, 500);
};

/**
 * Setup success notifications
 */
FormValidator.setupSuccessNotifications = function() {
    // Check for success messages in URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const successMessage = urlParams.get('success');
    
    if (successMessage) {
        FormValidator.showSuccessNotification(decodeURIComponent(successMessage));
        
        // Remove success parameter from URL
        urlParams.delete('success');
        const newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
        window.history.replaceState({}, '', newUrl);
    }
};

/**
 * Show success notification
 */
FormValidator.showSuccessNotification = function(message) {
    const notification = document.createElement('div');
    notification.className = 'success-notification alert alert-success alert-dismissible';
    notification.innerHTML = `
        <i class="bi bi-check-circle me-2"></i>
        <strong>Successo!</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        notification.classList.add('fade-out');
        setTimeout(function() {
            if (notification.parentElement) {
                notification.parentElement.removeChild(notification);
            }
        }, 300);
    }, 5000);
};

/**
 * Utility functions
 */
FormValidator.isValidEmail = function(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

FormValidator.isValidDate = function(dateString) {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date.getTime());
};

FormValidator.debounce = function(func, wait, immediate) {
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

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    FormValidator.init();
});

/**
 * Setup advanced validation features
 */
FormValidator.setupAdvancedValidation = function() {
    // Cross-field validation
    this.setupCrossFieldValidation();
    
    // Conditional validation
    this.setupConditionalValidation();
    
    // Custom validation rules
    this.setupCustomValidationRules();
    
    // Async validation
    this.setupAsyncValidation();
};

/**
 * Setup enhanced user feedback
 */
FormValidator.setupUserFeedback = function() {
    // Enhanced error messages
    this.setupEnhancedErrorMessages();
    
    // Success indicators
    this.setupSuccessIndicators();
    
    // Field help and hints
    this.setupFieldHelp();
    
    // Form completion feedback
    this.setupCompletionFeedback();
};

/**
 * Setup form interactions
 */
FormValidator.setupFormInteractions = function() {
    // Auto-save functionality
    this.setupAutoSave();
    
    // Smart suggestions
    this.setupSmartSuggestions();
    
    // Accessibility enhancements
    this.setupAccessibilityFeatures();
};

/**
 * Cross-field validation
 */
FormValidator.setupCrossFieldValidation = function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        // Date range validation
        const startDateFields = form.querySelectorAll('input[type="date"][name*="start"], input[type="date"][name*="from"]');
        const endDateFields = form.querySelectorAll('input[type="date"][name*="end"], input[type="date"][name*="to"]');
        
        startDateFields.forEach(function(startField) {
            const fieldName = startField.name.replace(/start|from/i, '');
            const endField = form.querySelector(`input[type="date"][name*="end${fieldName}"], input[type="date"][name*="to${fieldName}"]`);
            
            if (endField) {
                const validateDateRange = function() {
                    const startDate = new Date(startField.value);
                    const endDate = new Date(endField.value);
                    
                    if (startField.value && endField.value) {
                        if (startDate >= endDate) {
                            FormValidator.setFieldError(endField, 'La data di fine deve essere successiva alla data di inizio');
                            return false;
                        } else {
                            FormValidator.clearFieldError(endField);
                            return true;
                        }
                    }
                    return true;
                };
                
                startField.addEventListener('change', validateDateRange);
                endField.addEventListener('change', validateDateRange);
            }
        });
        
        // Percentage validation (total should not exceed 100%)
        const percentageFields = form.querySelectorAll('input[type="number"][name*="percentage"]');
        if (percentageFields.length > 1) {
            percentageFields.forEach(function(field) {
                field.addEventListener('input', function() {
                    let total = 0;
                    percentageFields.forEach(function(pField) {
                        total += parseFloat(pField.value) || 0;
                    });
                    
                    if (total > 100) {
                        FormValidator.setFieldError(field, `Il totale delle percentuali (${total}%) non può superare il 100%`);
                    } else {
                        FormValidator.clearFieldError(field);
                    }
                });
            });
        }
    });
};

/**
 * Conditional validation
 */
FormValidator.setupConditionalValidation = function() {
    const conditionalFields = document.querySelectorAll('[data-conditional-required]');
    
    conditionalFields.forEach(function(field) {
        const condition = field.getAttribute('data-conditional-required');
        const [triggerField, triggerValue] = condition.split('=');
        
        const trigger = document.querySelector(`[name="${triggerField}"]`);
        if (trigger) {
            const validateConditional = function() {
                const shouldBeRequired = trigger.type === 'checkbox' ? 
                    (trigger.checked && triggerValue === 'true') :
                    trigger.value === triggerValue;
                
                if (shouldBeRequired) {
                    field.setAttribute('required', '');
                    field.closest('.form-field, .mb-3')?.querySelector('label')?.classList.add('required');
                } else {
                    field.removeAttribute('required');
                    field.closest('.form-field, .mb-3')?.querySelector('label')?.classList.remove('required');
                    FormValidator.clearFieldValidation(field);
                }
            };
            
            trigger.addEventListener('change', validateConditional);
            validateConditional(); // Initial check
        }
    });
};

/**
 * Custom validation rules
 */
FormValidator.setupCustomValidationRules = function() {
    // Italian fiscal code validation
    window.validateFiscalCode = function(value) {
        const fiscalCodeRegex = /^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$/;
        return fiscalCodeRegex.test(value) || 'Codice fiscale non valido';
    };
    
    // Italian phone number validation
    window.validateItalianPhone = function(value) {
        const phoneRegex = /^(\+39\s?)?((3[0-9]{2}|0[0-9]{1,3})\s?[0-9]{6,7})$/;
        return phoneRegex.test(value.replace(/\s/g, '')) || 'Numero di telefono non valido';
    };
    
    // Strong password validation
    window.validateStrongPassword = function(value) {
        if (value.length < 8) return 'La password deve contenere almeno 8 caratteri';
        if (!/[A-Z]/.test(value)) return 'La password deve contenere almeno una lettera maiuscola';
        if (!/[a-z]/.test(value)) return 'La password deve contenere almeno una lettera minuscola';
        if (!/[0-9]/.test(value)) return 'La password deve contenere almeno un numero';
        if (!/[!@#$%^&*]/.test(value)) return 'La password deve contenere almeno un carattere speciale';
        return true;
    };
    
    // Unique field validation (simulated)
    window.validateUnique = function(value, field) {
        // This would typically make an AJAX call to check uniqueness
        const fieldName = field.name;
        if (fieldName === 'email' && value === 'test@example.com') {
            return 'Questo indirizzo email è già in uso';
        }
        return true;
    };
};

/**
 * Async validation setup
 */
FormValidator.setupAsyncValidation = function() {
    const asyncFields = document.querySelectorAll('[data-async-validate]');
    
    asyncFields.forEach(function(field) {
        const validateAsync = FormValidator.debounce(function() {
            const validationType = field.getAttribute('data-async-validate');
            FormValidator.performAsyncValidation(field, validationType);
        }, 1000);
        
        field.addEventListener('input', validateAsync);
    });
};

/**
 * Perform async validation
 */
FormValidator.performAsyncValidation = function(field, type) {
    const value = field.value.trim();
    if (!value) return;
    
    // Show loading indicator
    FormValidator.showFieldLoading(field);
    
    // Simulate async validation (replace with actual API calls)
    setTimeout(function() {
        let isValid = true;
        let message = '';
        
        switch (type) {
            case 'email-unique':
                // Simulate email uniqueness check
                if (value === 'admin@example.com') {
                    isValid = false;
                    message = 'Questo indirizzo email è già registrato';
                }
                break;
                
            case 'username-available':
                // Simulate username availability check
                if (value === 'admin' || value === 'root') {
                    isValid = false;
                    message = 'Questo nome utente non è disponibile';
                }
                break;
        }
        
        FormValidator.hideFieldLoading(field);
        
        if (isValid) {
            FormValidator.setFieldValidationState(field, true, []);
        } else {
            FormValidator.setFieldValidationState(field, false, [message]);
        }
    }, 1500);
};

/**
 * Show field loading indicator
 */
FormValidator.showFieldLoading = function(field) {
    const container = field.closest('.form-field') || field.parentElement;
    let loader = container.querySelector('.field-loader');
    
    if (!loader) {
        loader = document.createElement('div');
        loader.className = 'field-loader';
        loader.innerHTML = '<i class="bi bi-hourglass-split text-primary"></i>';
        container.appendChild(loader);
    }
    
    loader.style.display = 'block';
};

/**
 * Hide field loading indicator
 */
FormValidator.hideFieldLoading = function(field) {
    const container = field.closest('.form-field') || field.parentElement;
    const loader = container.querySelector('.field-loader');
    if (loader) {
        loader.style.display = 'none';
    }
};

/**
 * Enhanced error messages
 */
FormValidator.setupEnhancedErrorMessages = function() {
    // Create error message templates
    FormValidator.errorMessages = {
        required: 'Questo campo è obbligatorio',
        email: 'Inserisci un indirizzo email valido (es. nome@dominio.it)',
        minlength: 'Inserisci almeno {min} caratteri',
        maxlength: 'Non superare i {max} caratteri',
        min: 'Il valore deve essere almeno {min}',
        max: 'Il valore non può superare {max}',
        pattern: 'Il formato inserito non è valido',
        date: 'Inserisci una data valida nel formato gg/mm/aaaa',
        number: 'Inserisci un numero valido',
        url: 'Inserisci un URL valido (es. https://www.esempio.it)',
        tel: 'Inserisci un numero di telefono valido'
    };
};

/**
 * Success indicators
 */
FormValidator.setupSuccessIndicators = function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        // Add success animation to valid fields
        form.addEventListener('input', function(e) {
            const field = e.target;
            if (field.classList.contains('form-control') || field.classList.contains('form-select')) {
                if (field.checkValidity() && field.value.trim()) {
                    FormValidator.showFieldSuccess(field);
                }
            }
        });
    });
};

/**
 * Show field success animation
 */
FormValidator.showFieldSuccess = function(field) {
    const container = field.closest('.form-field') || field.parentElement;
    container.classList.add('field-success-animation');
    
    setTimeout(function() {
        container.classList.remove('field-success-animation');
    }, 1000);
};

/**
 * Field help and hints
 */
FormValidator.setupFieldHelp = function() {
    const fieldsWithHelp = document.querySelectorAll('[data-help]');
    
    fieldsWithHelp.forEach(function(field) {
        const helpText = field.getAttribute('data-help');
        const helpElement = document.createElement('div');
        helpElement.className = 'form-help';
        helpElement.innerHTML = `<i class="bi bi-info-circle me-1"></i>${helpText}`;
        
        field.parentElement.appendChild(helpElement);
        
        // Show help on focus
        field.addEventListener('focus', function() {
            helpElement.style.display = 'block';
        });
        
        field.addEventListener('blur', function() {
            helpElement.style.display = 'none';
        });
    });
};

/**
 * Form completion feedback
 */
FormValidator.setupCompletionFeedback = function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        const completionIndicator = document.createElement('div');
        completionIndicator.className = 'form-completion-indicator';
        completionIndicator.innerHTML = `
            <div class="completion-text">
                <i class="bi bi-check-circle-fill me-2"></i>
                <span>Modulo completato correttamente!</span>
            </div>
        `;
        
        form.appendChild(completionIndicator);
        
        // Check completion on form changes
        form.addEventListener('input', function() {
            FormValidator.updateCompletionStatus(form);
        });
        
        form.addEventListener('change', function() {
            FormValidator.updateCompletionStatus(form);
        });
    });
};

/**
 * Update form completion status
 */
FormValidator.updateCompletionStatus = function(form) {
    const requiredFields = form.querySelectorAll('[required]');
    const completionIndicator = form.querySelector('.form-completion-indicator');
    
    let allValid = true;
    let filledCount = 0;
    
    requiredFields.forEach(function(field) {
        if (field.value.trim() && field.checkValidity()) {
            filledCount++;
        } else {
            allValid = false;
        }
    });
    
    const completionPercentage = requiredFields.length > 0 ? 
        Math.round((filledCount / requiredFields.length) * 100) : 100;
    
    if (allValid && requiredFields.length > 0) {
        completionIndicator.classList.add('show');
        setTimeout(function() {
            completionIndicator.classList.remove('show');
        }, 3000);
    }
    
    // Update progress indicator
    const progressBar = form.querySelector('.form-progress-bar');
    if (progressBar) {
        progressBar.style.width = completionPercentage + '%';
        progressBar.setAttribute('aria-valuenow', completionPercentage);
    }
};

/**
 * Auto-save functionality
 */
FormValidator.setupAutoSave = function() {
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    
    autoSaveForms.forEach(function(form) {
        const autoSaveInterval = parseInt(form.getAttribute('data-auto-save')) || 30000; // 30 seconds default
        
        const autoSave = FormValidator.debounce(function() {
            FormValidator.performAutoSave(form);
        }, autoSaveInterval);
        
        form.addEventListener('input', autoSave);
        form.addEventListener('change', autoSave);
    });
};

/**
 * Perform auto-save
 */
FormValidator.performAutoSave = function(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Save to localStorage as fallback
    const formId = form.id || 'form_' + Date.now();
    localStorage.setItem('autosave_' + formId, JSON.stringify({
        data: data,
        timestamp: Date.now()
    }));
    
    // Show auto-save indicator
    FormValidator.showAutoSaveIndicator();
};

/**
 * Show auto-save indicator
 */
FormValidator.showAutoSaveIndicator = function() {
    let indicator = document.querySelector('.auto-save-indicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'auto-save-indicator';
        indicator.innerHTML = '<i class="bi bi-cloud-check me-1"></i>Salvato automaticamente';
        document.body.appendChild(indicator);
    }
    
    indicator.classList.add('show');
    
    setTimeout(function() {
        indicator.classList.remove('show');
    }, 2000);
};

/**
 * Smart suggestions
 */
FormValidator.setupSmartSuggestions = function() {
    // Name field suggestions
    const nameFields = document.querySelectorAll('input[name*="name"]:not([name*="short"]):not([name*="user"])');
    nameFields.forEach(function(field) {
        field.addEventListener('blur', function() {
            const shortNameField = document.querySelector('input[name*="short_name"], input[name*="short"]');
            if (shortNameField && !shortNameField.value && this.value) {
                FormValidator.suggestShortName(this.value, shortNameField);
            }
        });
    });
    
    // Email field suggestions
    const emailFields = document.querySelectorAll('input[type="email"]');
    emailFields.forEach(function(field) {
        field.addEventListener('input', function() {
            FormValidator.suggestEmailCompletion(this);
        });
    });
};

/**
 * Suggest short name
 */
FormValidator.suggestShortName = function(fullName, shortNameField) {
    const words = fullName.trim().split(' ');
    let suggestion = '';
    
    if (words.length === 1) {
        suggestion = words[0].substring(0, 10);
    } else if (words.length === 2) {
        suggestion = words[0].charAt(0).toUpperCase() + '. ' + words[1];
    } else {
        suggestion = words.map(word => word.charAt(0).toUpperCase()).join('');
    }
    
    if (suggestion.length <= 50) {
        FormValidator.showFieldSuggestion(shortNameField, suggestion);
    }
};

/**
 * Show field suggestion
 */
FormValidator.showFieldSuggestion = function(field, suggestion) {
    const container = field.closest('.form-field') || field.parentElement;
    let suggestionElement = container.querySelector('.field-suggestion');
    
    if (!suggestionElement) {
        suggestionElement = document.createElement('div');
        suggestionElement.className = 'field-suggestion';
        container.appendChild(suggestionElement);
    }
    
    suggestionElement.innerHTML = `
        <i class="bi bi-lightbulb me-1"></i>
        Suggerimento: <strong>${suggestion}</strong>
        <button type="button" class="btn btn-sm btn-outline-primary ms-2" onclick="FormValidator.applySuggestion('${field.id}', '${suggestion}')">
            Applica
        </button>
    `;
    
    suggestionElement.style.display = 'block';
    
    // Auto-hide after 10 seconds
    setTimeout(function() {
        suggestionElement.style.display = 'none';
    }, 10000);
};

/**
 * Apply suggestion
 */
FormValidator.applySuggestion = function(fieldId, suggestion) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.value = suggestion;
        field.dispatchEvent(new Event('input', { bubbles: true }));
        
        // Hide suggestion
        const container = field.closest('.form-field') || field.parentElement;
        const suggestionElement = container.querySelector('.field-suggestion');
        if (suggestionElement) {
            suggestionElement.style.display = 'none';
        }
        
        // Show success feedback
        FormValidator.showFieldSuccess(field);
    }
};

/**
 * Accessibility enhancements
 */
FormValidator.setupAccessibilityFeatures = function() {
    // Add ARIA labels and descriptions
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        // Add form role and labels
        form.setAttribute('role', 'form');
        form.setAttribute('novalidate', '');
        
        // Enhance field accessibility
        const fields = form.querySelectorAll('.form-control, .form-select');
        fields.forEach(function(field) {
            const label = form.querySelector(`label[for="${field.id}"]`);
            const helpText = field.parentElement.querySelector('.form-text, .form-hint');
            
            if (label) {
                field.setAttribute('aria-labelledby', label.id || 'label_' + field.id);
            }
            
            if (helpText) {
                const helpId = 'help_' + field.id;
                helpText.id = helpId;
                field.setAttribute('aria-describedby', helpId);
            }
            
            // Add required indicator
            if (field.hasAttribute('required')) {
                field.setAttribute('aria-required', 'true');
            }
        });
    });
    
    // Keyboard navigation enhancements
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.classList.contains('form-control')) {
            const form = e.target.closest('form');
            if (form) {
                const fields = Array.from(form.querySelectorAll('.form-control, .form-select'));
                const currentIndex = fields.indexOf(e.target);
                const nextField = fields[currentIndex + 1];
                
                if (nextField) {
                    e.preventDefault();
                    nextField.focus();
                }
            }
        }
    });
};

/**
 * Set field error (helper method)
 */
FormValidator.setFieldError = function(field, message) {
    FormValidator.setFieldValidationState(field, false, [message]);
};

/**
 * Clear field error (helper method)
 */
FormValidator.clearFieldError = function(field) {
    FormValidator.clearFieldValidation(field);
};

// Export for global use
window.showSuccessNotification = FormValidator.showSuccessNotification;
window.applySuggestion = FormValidator.applySuggestion;