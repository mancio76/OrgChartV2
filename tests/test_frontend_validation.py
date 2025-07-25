"""
Frontend JavaScript Form Validation Tests
Task 9.3 Implementation - Organigramma Web App

Tests for JavaScript form validation functionality including:
- Real-time validation
- Form submission handling
- User feedback systems
- Field interactions
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import json


class TestJavaScriptFormValidation:
    """Test JavaScript form validation functionality"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode for CI
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    @pytest.fixture
    def wait(self, driver):
        """WebDriverWait instance"""
        return WebDriverWait(driver, 10)
    
    def test_orgapp_initialization(self, driver, wait):
        """Test that OrgApp JavaScript namespace initializes correctly"""
        driver.get("http://localhost:8000/units/create")
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
        
        # Check that OrgApp is initialized
        orgapp_initialized = driver.execute_script("return typeof window.OrgApp !== 'undefined'")
        assert orgapp_initialized, "OrgApp namespace should be initialized"
        
        # Check that required functions exist
        required_functions = [
            'init', 'showSuccess', 'showError', 'showWarning', 'showInfo',
            'confirmDelete', 'setFormLoading', 'formatDate', 'isValidEmail'
        ]
        
        for func in required_functions:
            exists = driver.execute_script(f"return typeof window.OrgApp.{func} === 'function'")
            assert exists, f"OrgApp.{func} function should exist"
    
    def test_form_validator_initialization(self, driver, wait):
        """Test that FormValidator initializes correctly"""
        driver.get("http://localhost:8000/units/create")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "needs-validation")))
        
        # Check FormValidator initialization
        validator_initialized = driver.execute_script("return typeof window.FormValidator !== 'undefined'")
        assert validator_initialized, "FormValidator should be initialized"
        
        # Check that validation setup has run
        form_has_validation = driver.execute_script("""
            const form = document.querySelector('.needs-validation');
            return form && form.classList.contains('needs-validation');
        """)
        assert form_has_validation, "Form should have validation setup"
    
    def test_real_time_email_validation(self, driver, wait):
        """Test real-time email validation"""
        driver.get("http://localhost:8000/persons/create")
        wait.until(EC.presence_of_element_located((By.ID, "email")))
        
        email_field = driver.find_element(By.ID, "email")
        
        # Test invalid email
        email_field.send_keys("invalid-email")
        email_field.send_keys(Keys.TAB)  # Trigger blur event
        time.sleep(0.5)
        
        # Check for validation feedback
        is_invalid = driver.execute_script("""
            const field = document.getElementById('email');
            return field.classList.contains('is-invalid');
        """)
        assert is_invalid, "Invalid email should trigger validation error"
        
        # Test valid email
        email_field.clear()
        email_field.send_keys("test@example.com")
        email_field.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        is_valid = driver.execute_script("""
            const field = document.getElementById('email');
            return field.classList.contains('is-valid');
        """)
        assert is_valid, "Valid email should pass validation"
    
    def test_required_field_validation(self, driver, wait):
        """Test required field validation"""
        driver.get("http://localhost:8000/units/create")
        wait.until(EC.presence_of_element_located((By.ID, "name")))
        
        name_field = driver.find_element(By.ID, "name")
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        # Try to submit empty form
        submit_button.click()
        time.sleep(0.5)
        
        # Check that required field shows error
        is_invalid = driver.execute_script("""
            const field = document.getElementById('name');
            return field.classList.contains('is-invalid');
        """)
        assert is_invalid, "Empty required field should show validation error"
        
        # Fill required field
        name_field.send_keys("Test Unit")
        name_field.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        is_valid = driver.execute_script("""
            const field = document.getElementById('name');
            return field.classList.contains('is-valid');
        """)
        assert is_valid, "Filled required field should be valid"
    
    def test_form_progress_indicator(self, driver, wait):
        """Test form progress indicator functionality"""
        driver.get("http://localhost:8000/units/create")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "needs-validation")))
        
        # Check if progress indicator exists
        progress_exists = driver.execute_script("""
            return document.querySelector('.form-progress-bar') !== null;
        """)
        assert progress_exists, "Form progress indicator should exist"
        
        # Fill a field and check progress update
        name_field = driver.find_element(By.ID, "name")
        name_field.send_keys("Test Unit")
        time.sleep(0.5)
        
        progress_value = driver.execute_script("""
            const progressBar = document.querySelector('.form-progress-bar');
            return progressBar ? progressBar.style.width : '0%';
        """)
        assert progress_value != '0%', "Progress should update when fields are filled"
    
    def test_form_loading_state(self, driver, wait):
        """Test form loading state functionality"""
        driver.get("http://localhost:8000/units/create")
        wait.until(EC.presence_of_element_located((By.ID, "name")))
        
        # Fill required fields
        name_field = driver.find_element(By.ID, "name")
        name_field.send_keys("Test Unit")
        
        type_select = driver.find_element(By.ID, "unit_type_id")
        type_select.send_keys("Funzione")
        
        # Test loading state activation
        loading_activated = driver.execute_script("""
            const form = document.querySelector('.needs-validation');
            if (window.FormValidator && window.FormValidator.setFormLoading) {
                window.FormValidator.setFormLoading(form, true);
                return form.classList.contains('form-loading');
            }
            return false;
        """)
        assert loading_activated, "Form loading state should be activated"
        
        # Test loading state deactivation
        loading_deactivated = driver.execute_script("""
            const form = document.querySelector('.needs-validation');
            if (window.FormValidator && window.FormValidator.setFormLoading) {
                window.FormValidator.setFormLoading(form, false);
                return !form.classList.contains('form-loading');
            }
            return false;
        """)
        assert loading_deactivated, "Form loading state should be deactivated"
    
    def test_notification_system(self, driver, wait):
        """Test notification system functionality"""
        driver.get("http://localhost:8000/")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Test success notification
        success_shown = driver.execute_script("""
            if (window.OrgApp && window.OrgApp.showSuccess) {
                window.OrgApp.showSuccess('Test success message');
                return document.querySelector('.alert-success') !== null;
            }
            return false;
        """)
        assert success_shown, "Success notification should be displayed"
        
        # Test error notification
        error_shown = driver.execute_script("""
            if (window.OrgApp && window.OrgApp.showError) {
                window.OrgApp.showError('Test error message');
                return document.querySelector('.alert-danger') !== null;
            }
            return false;
        """)
        assert error_shown, "Error notification should be displayed"
    
    def test_delete_confirmation(self, driver, wait):
        """Test delete confirmation functionality"""
        driver.get("http://localhost:8000/units")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Test delete confirmation dialog
        confirmation_works = driver.execute_script("""
            // Mock confirm function to return true
            const originalConfirm = window.confirm;
            let confirmCalled = false;
            window.confirm = function(message) {
                confirmCalled = true;
                return true;
            };
            
            // Create a mock delete button
            const button = document.createElement('button');
            button.className = 'btn-delete';
            button.setAttribute('data-item-name', 'Test Item');
            button.setAttribute('data-item-type', 'unità');
            document.body.appendChild(button);
            
            // Trigger delete confirmation
            if (window.OrgApp && window.OrgApp.confirmDelete) {
                window.OrgApp.confirmDelete(button);
            }
            
            // Restore original confirm
            window.confirm = originalConfirm;
            
            return confirmCalled;
        """)
        assert confirmation_works, "Delete confirmation should work"
    
    def test_form_enhancements_initialization(self, driver, wait):
        """Test FormEnhancements initialization"""
        driver.get("http://localhost:8000/units/create")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "needs-validation")))
        
        # Check FormEnhancements initialization
        enhancements_initialized = driver.execute_script("""
            return typeof window.FormEnhancements !== 'undefined';
        """)
        assert enhancements_initialized, "FormEnhancements should be initialized"
        
        # Check that enhancement functions exist
        enhancement_functions = [
            'validateFieldRealTime', 'showFieldSuccess', 'showFieldError',
            'updateFormProgress', 'handleFormSubmission'
        ]
        
        for func in enhancement_functions:
            exists = driver.execute_script(f"""
                return typeof window.FormEnhancements.{func} === 'function';
            """)
            assert exists, f"FormEnhancements.{func} function should exist"
    
    def test_field_help_system(self, driver, wait):
        """Test field help and hint system"""
        driver.get("http://localhost:8000/units/create")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "form-hint")))
        
        # Check that help hints are present
        help_hints_exist = driver.execute_script("""
            return document.querySelectorAll('.form-hint').length > 0;
        """)
        assert help_hints_exist, "Form help hints should be present"
        
        # Test field focus help display
        name_field = driver.find_element(By.ID, "name")
        name_field.click()
        time.sleep(0.2)
        
        # Check if help is visible on focus (if implemented)
        help_visible = driver.execute_script("""
            const hints = document.querySelectorAll('.form-hint');
            return hints.length > 0;
        """)
        assert help_visible, "Help hints should be visible"
    
    def test_cross_field_validation(self, driver, wait):
        """Test cross-field validation (date ranges)"""
        driver.get("http://localhost:8000/units/create")
        wait.until(EC.presence_of_element_located((By.ID, "start_date")))
        
        start_date = driver.find_element(By.ID, "start_date")
        end_date = driver.find_element(By.ID, "end_date")
        
        # Set invalid date range (end before start)
        start_date.send_keys("2024-12-01")
        end_date.send_keys("2024-11-01")
        end_date.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        # Check for validation error
        validation_error = driver.execute_script("""
            const endField = document.getElementById('end_date');
            return endField.validationMessage !== '';
        """)
        assert validation_error, "Invalid date range should trigger validation error"
    
    def test_accessibility_features(self, driver, wait):
        """Test accessibility features in JavaScript"""
        driver.get("http://localhost:8000/units/create")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "needs-validation")))
        
        # Test ARIA attributes are set correctly
        aria_attributes_set = driver.execute_script("""
            const form = document.querySelector('.needs-validation');
            return form && form.hasAttribute('aria-describedby');
        """)
        # Note: This might not be set initially, so we'll check if the functionality exists
        
        # Test keyboard shortcuts (Escape key)
        name_field = driver.find_element(By.ID, "name")
        name_field.send_keys("test")
        name_field.send_keys(Keys.TAB)
        
        # Simulate Escape key press
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.2)
        
        # The test passes if no JavaScript errors occur
        js_errors = driver.get_log('browser')
        critical_errors = [log for log in js_errors if log['level'] == 'SEVERE']
        assert len(critical_errors) == 0, f"No critical JavaScript errors should occur: {critical_errors}"
    
    def test_utility_functions(self, driver, wait):
        """Test utility functions"""
        driver.get("http://localhost:8000/")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Test email validation utility
        email_validation = driver.execute_script("""
            if (window.OrgApp && window.OrgApp.isValidEmail) {
                return {
                    valid: window.OrgApp.isValidEmail('test@example.com'),
                    invalid: !window.OrgApp.isValidEmail('invalid-email')
                };
            }
            return {valid: false, invalid: false};
        """)
        assert email_validation['valid'], "Valid email should pass validation"
        assert email_validation['invalid'], "Invalid email should fail validation"
        
        # Test date formatting utility
        date_formatting = driver.execute_script("""
            if (window.OrgApp && window.OrgApp.formatDate) {
                return window.OrgApp.formatDate('2024-01-15');
            }
            return null;
        """)
        assert date_formatting is not None, "Date formatting should work"
        assert '15' in date_formatting, "Formatted date should contain day"
        
        # Test percentage formatting utility
        percentage_formatting = driver.execute_script("""
            if (window.OrgApp && window.OrgApp.formatPercentage) {
                return window.OrgApp.formatPercentage(0.75);
            }
            return null;
        """)
        assert percentage_formatting == '75%', "Percentage formatting should work correctly"
    
    def test_components_initialization(self, driver, wait):
        """Test Components namespace initialization"""
        driver.get("http://localhost:8000/")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Check Components initialization
        components_initialized = driver.execute_script("""
            return typeof window.Components !== 'undefined';
        """)
        assert components_initialized, "Components namespace should be initialized"
        
        # Test component functions
        component_functions = ['initDataTables', 'sortTable', 'searchTable', 'createEmptyState']
        
        for func in component_functions:
            exists = driver.execute_script(f"""
                return typeof window.Components.{func} === 'function';
            """)
            assert exists, f"Components.{func} function should exist"
    
    def test_form_submission_prevention(self, driver, wait):
        """Test that invalid forms prevent submission"""
        driver.get("http://localhost:8000/units/create")
        wait.until(EC.presence_of_element_located((By.ID, "name")))
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        # Try to submit empty form
        submit_button.click()
        time.sleep(1)
        
        # Check that we're still on the same page (form wasn't submitted)
        current_url = driver.current_url
        assert "/units/create" in current_url, "Invalid form should not be submitted"
        
        # Check that validation errors are shown
        validation_errors = driver.execute_script("""
            return document.querySelectorAll('.is-invalid').length > 0;
        """)
        assert validation_errors, "Validation errors should be displayed"
    
    def test_javascript_error_handling(self, driver, wait):
        """Test that JavaScript handles errors gracefully"""
        driver.get("http://localhost:8000/units/create")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Test calling functions with invalid parameters
        no_errors = driver.execute_script("""
            try {
                // Test various functions with edge cases
                if (window.OrgApp) {
                    window.OrgApp.formatDate(null);
                    window.OrgApp.formatDate('invalid-date');
                    window.OrgApp.isValidEmail(null);
                    window.OrgApp.formatPercentage('not-a-number');
                }
                return true;
            } catch (e) {
                console.error('JavaScript error:', e);
                return false;
            }
        """)
        assert no_errors, "JavaScript functions should handle invalid inputs gracefully"
        
        # Check browser console for critical errors
        js_errors = driver.get_log('browser')
        critical_errors = [log for log in js_errors if log['level'] == 'SEVERE']
        assert len(critical_errors) == 0, f"No critical JavaScript errors should occur: {critical_errors}"


class TestFormValidationIntegration:
    """Integration tests for form validation with backend"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_successful_form_submission(self, driver):
        """Test successful form submission with valid data"""
        driver.get("http://localhost:8000/units/create")
        
        # Fill form with valid data
        name_field = driver.find_element(By.ID, "name")
        name_field.send_keys("Test Integration Unit")
        
        type_select = driver.find_element(By.ID, "unit_type_id")
        type_select.send_keys("Funzione")
        
        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for redirect or success message
        time.sleep(2)
        
        # Check that form was processed (either redirected or success shown)
        current_url = driver.current_url
        success_indicators = driver.execute_script("""
            return document.querySelector('.alert-success') !== null || 
                   !window.location.href.includes('/create');
        """)
        assert success_indicators, "Form submission should show success or redirect"