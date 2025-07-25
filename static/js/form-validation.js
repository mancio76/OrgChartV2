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
                <i class="bi bi-check-circle me-2"></i>
                <span>Modulo completato!</span>
            </div>
        `;
        
        document.body.appendChild(completionIndicator);
        
        // Check completion on form changes
        const checkCompletion = FormValidator.debounce(function() {
            const requiredFields = form.querySelectorAll('[required]');
            const completedFields = Array.from(requiredFields).filter(field => 
                field.value.trim() && field.checkValidity()
            );
            
            if (requiredFields.length > 0 && completedFields.length === requiredFields.length) {
                completionIndicator.classList.add('show');
                setTimeout(() => {
                    completionIndicator.classList.remove('show');
                }, 3000);
            }
        }, 500);
        
        form.addEventListener('input', checkCompletion);
        form.addEventListener('change', checkCompletion);
    });
};

/**
 * Auto-save functionality
 */
FormValidator.setupAutoSave = function() {
    const forms = document.querySelectorAll('[data-auto-save]');
    
    forms.forEach(function(form) {
        const autoSaveIndicator = document.createElement('div');
        autoSaveIndicator.className = 'auto-save-indicator';
        autoSaveIndicator.innerHTML = `
            <i class="bi bi-cloud-check me-1"></i>
            <span>Salvato automaticamente</span>
        `;
        
        document.body.appendChild(autoSaveIndicator);
        
        const autoSave = FormValidator.debounce(function() {
            // Simulate auto-save (replace with actual implementation)
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            // Store in localStorage as fallback
            localStorage.setItem(`autosave_${form.id || 'form'}`, JSON.stringify(data));
            
            // Show indicator
            autoSaveIndicator.classList.add('show');
            setTimeout(() => {
                autoSaveIndicator.classList.remove('show');
            }, 2000);
        }, 2000);
        
        form.addEventListener('input', autoSave);
        form.addEventListener('change', autoSave);
        
        // Restore auto-saved data on page load
        const savedData = localStorage.getItem(`autosave_${form.id || 'form'}`);
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(key => {
                    const field = form.querySelector(`[name="${key}"]`);
                    if (field && !field.value) {
                        field.value = data[key];
                    }
                });
            } catch (e) {
                console.warn('Failed to restore auto-saved data:', e);
            }
        }
    });
};

/**
 * Smart suggestions
 */
FormValidator.setupSmartSuggestions = function() {
    const fieldsWithSuggestions = document.querySelectorAll('[data-suggestions]');
    
    fieldsWithSuggestions.forEach(function(field) {
        const suggestionsData = field.getAttribute('data-suggestions');
        let suggestions = [];
        
        try {
            suggestions = JSON.parse(suggestionsData);
        } catch (e) {
            // If not JSON, treat as comma-separated values
            suggestions = suggestionsData.split(',').map(s => s.trim());
        }
        
        const suggestionContainer = document.createElement('div');
        suggestionContainer.className = 'field-suggestion';
        field.parentElement.appendChild(suggestionContainer);
        
        field.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            const matches = suggestions.filter(suggestion => 
                suggestion.toLowerCase().includes(value) && 
                suggestion.toLowerCase() !== value
            );
            
            if (matches.length > 0 && value.length > 1) {
                suggestionContainer.innerHTML = `
                    <i class="bi bi-lightbulb me-1"></i>
                    Suggerimenti: ${matches.slice(0, 3).map(match => 
                        `<span class="suggestion-item" onclick="FormValidator.applySuggestion('${field.id}', '${match}')">${match}</span>`
                    ).join(', ')}
                `;
                suggestionContainer.style.display = 'block';
            } else {
                suggestionContainer.style.display = 'none';
            }
        });
        
        field.addEventListener('blur', function() {
            setTimeout(() => {
                suggestionContainer.style.display = 'none';
            }, 200);
        });
    });
};

/**
 * Apply suggestion to field
 */
FormValidator.applySuggestion = function(fieldId, suggestion) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.value = suggestion;
        field.dispatchEvent(new Event('input', { bubbles: true }));
        field.focus();
    }
};

/**
 * Accessibility enhancements
 */
FormValidator.setupAccessibilityFeatures = function() {
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
            
            // Link field to its error message
            const errorMessage = field.parentElement.querySelector('.invalid-feedback');
            if (errorMessage && !errorMessage.id) {
                errorMessage.id = `error-${field.id || Date.now()}`;
                field.setAttribute('aria-describedby', errorMessage.id);
            }
        });
    });
    
    // Keyboard navigation enhancements
    document.addEventListener('keydown', function(e) {
        // Escape key to clear validation
        if (e.key === 'Escape') {
            const activeField = document.activeElement;
            if (activeField && activeField.classList.contains('is-invalid')) {
                FormValidator.clearFieldValidation(activeField);
            }
        }
        
        // Ctrl+Enter to submit form
        if (e.ctrlKey && e.key === 'Enter') {
            const form = document.activeElement.closest('form');
            if (form && form.classList.contains('needs-validation')) {
                form.dispatchEvent(new Event('submit', { bubbles: true }));
            }
        }
    });
};

/**
 * Set field error (utility function)
 */
FormValidator.setFieldError = function(field, message) {
    FormValidator.setFieldValidationState(field, false, [message]);
};

/**
 * Clear field error (utility function)
 */
FormValidator.clearFieldError = function(field) {
    FormValidator.clearFieldValidation(field);
};

/**
 * Enhanced form submission with better user feedback
 */
FormValidator.enhanceFormSubmission = function() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const isValid = FormValidator.validateForm(form);
            
            if (isValid) {
                // Show success feedback
                FormValidator.showFormSuccess(form);
                
                // Submit after brief delay for user feedback
                setTimeout(() => {
                    if (form.hasAttribute('data-ajax-submit')) {
                        FormValidator.submitFormAjax(form);
                    } else {
                        form.submit();
                    }
                }, 500);
            } else {
                // Show error feedback
                FormValidator.showFormErrors(form);
            }
        });
    });
};

/**
 * Show form success feedback
 */
FormValidator.showFormSuccess = function(form) {
    form.classList.add('form-success');
    
    if (window.OrgApp && window.OrgApp.showSuccess) {
        window.OrgApp.showSuccess('Modulo validato correttamente!');
    }
};

/**
 * Show form error feedback
 */
FormValidator.showFormErrors = function(form) {
    const invalidFields = form.querySelectorAll('.is-invalid');
    const errors = Array.from(invalidFields).map(field => {
        const label = form.querySelector(`label[for="${field.id}"]`);
        const fieldName = label ? label.textContent.replace('*', '').trim() : field.name || 'Campo';
        return fieldName;
    });
    
    if (window.OrgApp && window.OrgApp.showFormError) {
        window.OrgApp.showFormError(
            'Correggi gli errori nel modulo prima di continuare.',
            errors.map(name => `${name}: campo non valido`)
        );
    }
};

/**
 * AJAX form submission
 */
FormValidator.submitFormAjax = function(form) {
    const formData = new FormData(form);
    const url = form.action || window.location.pathname;
    const method = form.method || 'POST';
    
    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Network response was not ok');
    })
    .then(data => {
        if (data.success) {
            if (window.OrgApp && window.OrgApp.showSuccess) {
                window.OrgApp.showSuccess(data.message || 'Operazione completata con successo!');
            }
            
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            }
        } else {
            throw new Error(data.message || 'Errore durante l\'elaborazione');
        }
    })
    .catch(error => {
        if (window.OrgApp && window.OrgApp.showError) {
            window.OrgApp.showError('Errore durante l\'invio del modulo: ' + error.message);
        }
    })
    .finally(() => {
        FormValidator.hideFormLoading(form);
    });
};

// Initialize enhanced form submission when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    FormValidator.enhanceFormSubmission();
});

// Export for global use
window.showSuccessNotification = FormValidator.showSuccessNotification;
window.applySuggestion = FormValidator.applySuggestion;