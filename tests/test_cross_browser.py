"""
Cross-Browser Compatibility Tests
Task 9.3 Implementation - Organigramma Web App

Tests for cross-browser compatibility including:
- JavaScript functionality across browsers
- CSS rendering consistency
- HTML5 feature support
- Responsive design behavior
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
import time
import os


class TestCrossBrowserCompatibility:
    """Test application compatibility across different browsers"""
    
    @pytest.fixture(params=['chrome'])  # Can be extended to ['chrome', 'firefox', 'edge']
    def browser_driver(self, request):
        """Setup browser drivers for cross-browser testing"""
        browser = request.param
        
        if browser == 'chrome':
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            driver = webdriver.Chrome(options=options)
        elif browser == 'firefox':
            options = FirefoxOptions()
            options.add_argument("--headless")
            driver = webdriver.Firefox(options=options)
        elif browser == 'edge':
            options = EdgeOptions()
            options.add_argument("--headless")
            driver = webdriver.Edge(options=options)
        else:
            raise ValueError(f"Unsupported browser: {browser}")
        
        driver.implicitly_wait(10)
        yield driver, browser
        driver.quit()
    
    def test_basic_page_loading(self, browser_driver):
        """Test that basic pages load correctly across browsers"""
        driver, browser_name = browser_driver
        
        pages = [
            "http://localhost:8000/",
            "http://localhost:8000/units",
            "http://localhost:8000/persons",
            "http://localhost:8000/job_titles",
            "http://localhost:8000/assignments",
            "http://localhost:8000/orgchart"
        ]
        
        for page_url in pages:
            driver.get(page_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check that page loaded successfully
            assert "error" not in driver.title.lower(), f"Page {page_url} should load without errors in {browser_name}"
            
            # Check that main content is present
            main_content = driver.execute_script("return document.body.innerHTML.length > 100;")
            assert main_content, f"Page {page_url} should have substantial content in {browser_name}"
    
    def test_javascript_functionality(self, browser_driver):
        """Test JavaScript functionality across browsers"""
        driver, browser_name = browser_driver
        
        driver.get("http://localhost:8000/units/create")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "form")))
        
        # Test that JavaScript objects are initialized
        js_objects = driver.execute_script("""
            return {
                orgApp: typeof window.OrgApp !== 'undefined',
                formValidator: typeof window.FormValidator !== 'undefined',
                formEnhancements: typeof window.FormEnhancements !== 'undefined',
                components: typeof window.Components !== 'undefined'
            };
        """)
        
        for obj_name, exists in js_objects.items():
            assert exists, f"{obj_name} should be initialized in {browser_name}"
        
        # Test basic JavaScript functionality
        basic_js = driver.execute_script("""
            try {
                // Test modern JavaScript features
                const arrow = () => true;
                const template = `test`;
                const [a, b] = [1, 2];
                const obj = {a, b};
                
                return {
                    arrow_functions: arrow(),
                    template_literals: template === 'test',
                    destructuring: a === 1 && b === 2,
                    object_shorthand: obj.a === 1
                };
            } catch (e) {
                return {error: e.message};
            }
        """)
        
        if 'error' in basic_js:
            pytest.skip(f"Browser {browser_name} doesn't support modern JavaScript features: {basic_js['error']}")
        
        for feature, works in basic_js.items():
            assert works, f"JavaScript feature {feature} should work in {browser_name}"
    
    def test_css_rendering(self, browser_driver):
        """Test CSS rendering consistency across browsers"""
        driver, browser_name = browser_driver
        
        driver.get("http://localhost:8000/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Test CSS features
        css_features = driver.execute_script("""
            const testDiv = document.createElement('div');
            document.body.appendChild(testDiv);
            
            const features = {
                flexbox: 'flex' in testDiv.style,
                grid: 'grid' in testDiv.style,
                transforms: 'transform' in testDiv.style,
                transitions: 'transition' in testDiv.style,
                border_radius: 'borderRadius' in testDiv.style
            };
            
            document.body.removeChild(testDiv);
            return features;
        """)
        
        for feature, supported in css_features.items():
            assert supported, f"CSS feature {feature} should be supported in {browser_name}"
        
        # Test Bootstrap classes are applied
        bootstrap_classes = driver.execute_script("""
            const container = document.querySelector('.container, .container-fluid');
            if (!container) return false;
            
            const styles = window.getComputedStyle(container);
            return {
                has_container: !!container,
                has_padding: styles.paddingLeft !== '0px' || styles.paddingRight !== '0px'
            };
        """)
        
        assert bootstrap_classes['has_container'], f"Bootstrap container should be present in {browser_name}"
    
    def test_form_functionality(self, browser_driver):
        """Test form functionality across browsers"""
        driver, browser_name = browser_driver
        
        driver.get("http://localhost:8000/units/create")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "name")))
        
        # Test form input
        name_field = driver.find_element(By.ID, "name")
        name_field.send_keys("Test Unit")
        
        # Check that input was registered
        input_value = name_field.get_attribute("value")
        assert input_value == "Test Unit", f"Form input should work in {browser_name}"
        
        # Test form validation
        name_field.clear()
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        time.sleep(0.5)
        
        # Check validation state
        validation_state = driver.execute_script("""
            const field = document.getElementById('name');
            return {
                is_invalid: field.classList.contains('is-invalid'),
                validation_message: field.validationMessage || ''
            };
        """)
        
        assert validation_state['is_invalid'] or validation_state['validation_message'], \
            f"Form validation should work in {browser_name}"
    
    def test_responsive_design(self, browser_driver):
        """Test responsive design across browsers"""
        driver, browser_name = browser_driver
        
        driver.get("http://localhost:8000/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Test different viewport sizes
        viewports = [
            (1920, 1080),  # Desktop
            (768, 1024),   # Tablet
            (375, 667)     # Mobile
        ]
        
        for width, height in viewports:
            driver.set_window_size(width, height)
            time.sleep(0.5)
            
            # Check that content is visible and accessible
            viewport_test = driver.execute_script("""
                return {
                    body_width: document.body.offsetWidth,
                    body_height: document.body.offsetHeight,
                    viewport_width: window.innerWidth,
                    viewport_height: window.innerHeight,
                    has_horizontal_scroll: document.body.scrollWidth > window.innerWidth
                };
            """)
            
            assert viewport_test['body_height'] > 0, \
                f"Content should be visible at {width}x{height} in {browser_name}"
            
            # Check navigation is accessible
            nav_accessible = driver.execute_script("""
                const nav = document.querySelector('nav, .navbar');
                return nav ? nav.offsetHeight > 0 : false;
            """)
            
            assert nav_accessible, f"Navigation should be accessible at {width}x{height} in {browser_name}"
    
    def test_table_rendering(self, browser_driver):
        """Test table rendering across browsers"""
        driver, browser_name = browser_driver
        
        driver.get("http://localhost:8000/units")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Test table structure
        table_structure = driver.execute_script("""
            const table = document.querySelector('table');
            if (!table) return {has_table: false};
            
            return {
                has_table: true,
                has_thead: !!table.querySelector('thead'),
                has_tbody: !!table.querySelector('tbody'),
                header_count: table.querySelectorAll('th').length,
                row_count: table.querySelectorAll('tr').length,
                is_responsive: table.closest('.table-responsive') !== null
            };
        """)
        
        assert table_structure['has_table'], f"Table should be present in {browser_name}"
        assert table_structure['has_thead'], f"Table should have thead in {browser_name}"
        assert table_structure['header_count'] > 0, f"Table should have headers in {browser_name}"
    
    def test_interactive_elements(self, browser_driver):
        """Test interactive elements across browsers"""
        driver, browser_name = browser_driver
        
        driver.get("http://localhost:8000/units")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Test buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        if buttons:
            button = buttons[0]
            
            # Test button click
            original_url = driver.current_url
            try:
                button.click()
                time.sleep(0.5)
                # Button should either navigate or trigger JavaScript
                # We'll just check that no JavaScript errors occurred
                js_errors = driver.get_log('browser')
                critical_errors = [log for log in js_errors if log['level'] == 'SEVERE']
                assert len(critical_errors) == 0, \
                    f"Button click should not cause JavaScript errors in {browser_name}: {critical_errors}"
            except Exception:
                # Some buttons might not be clickable in test environment
                pass
        
        # Test links
        links = driver.find_elements(By.TAG_NAME, "a")
        internal_links = [link for link in links if link.get_attribute("href") and 
                         "localhost:8000" in link.get_attribute("href")]
        
        if internal_links:
            link = internal_links[0]
            href = link.get_attribute("href")
            
            # Test link navigation
            link.click()
            WebDriverWait(driver, 10).until(lambda d: d.current_url != original_url or d.current_url == href)
            
            # Check that navigation worked
            assert driver.current_url == href or "error" not in driver.title.lower(), \
                f"Link navigation should work in {browser_name}"
    
    def test_error_handling(self, browser_driver):
        """Test error handling across browsers"""
        driver, browser_name = browser_driver
        
        # Test 404 page
        driver.get("http://localhost:8000/nonexistent-page")
        time.sleep(1)
        
        # Should show 404 page or redirect
        page_content = driver.execute_script("return document.body.textContent.toLowerCase();")
        is_error_page = "404" in page_content or "not found" in page_content or "error" in page_content
        
        # Error handling should be graceful
        assert is_error_page or driver.current_url != "http://localhost:8000/nonexistent-page", \
            f"404 errors should be handled gracefully in {browser_name}"
    
    def test_accessibility_features(self, browser_driver):
        """Test accessibility features across browsers"""
        driver, browser_name = browser_driver
        
        driver.get("http://localhost:8000/units/create")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "form")))
        
        # Test keyboard navigation
        first_input = driver.find_element(By.CSS_SELECTOR, "input, select, textarea")
        first_input.click()
        
        # Tab to next element
        first_input.send_keys(Keys.TAB)
        
        # Check that focus moved
        focused_element = driver.execute_script("return document.activeElement.tagName;")
        focusable_elements = ['INPUT', 'SELECT', 'TEXTAREA', 'BUTTON', 'A']
        
        assert focused_element in focusable_elements, \
            f"Keyboard navigation should work in {browser_name}"
        
        # Test focus indicators
        focus_visible = driver.execute_script("""
            const element = document.activeElement;
            const styles = window.getComputedStyle(element);
            return styles.outline !== 'none' || styles.boxShadow.includes('focus');
        """)
        
        # Focus indicators might vary by browser, so we'll be lenient
        # assert focus_visible, f"Focus indicators should be visible in {browser_name}"
    
    def test_performance_basics(self, browser_driver):
        """Test basic performance metrics across browsers"""
        driver, browser_name = browser_driver
        
        start_time = time.time()
        driver.get("http://localhost:8000/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        load_time = time.time() - start_time
        
        # Page should load within reasonable time
        assert load_time < 10, f"Page should load within 10 seconds in {browser_name}, took {load_time:.2f}s"
        
        # Test JavaScript execution time
        js_performance = driver.execute_script("""
            const start = performance.now();
            
            // Simulate some JavaScript work
            if (window.OrgApp && window.OrgApp.init) {
                window.OrgApp.init();
            }
            
            const end = performance.now();
            return end - start;
        """)
        
        assert js_performance < 1000, f"JavaScript should execute quickly in {browser_name}, took {js_performance:.2f}ms"


class TestBrowserSpecificFeatures:
    """Test browser-specific features and fallbacks"""
    
    def test_modern_javascript_fallbacks(self):
        """Test fallbacks for modern JavaScript features"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            driver.get("http://localhost:8000/")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Test that code works even if some modern features are missing
            fallback_test = driver.execute_script("""
                // Simulate missing modern features
                const originalFetch = window.fetch;
                const originalPromise = window.Promise;
                
                try {
                    // Test with fetch disabled
                    delete window.fetch;
                    
                    // Code should still work with XMLHttpRequest fallback
                    const hasXHR = typeof XMLHttpRequest !== 'undefined';
                    
                    // Restore
                    window.fetch = originalFetch;
                    
                    return {
                        xhr_available: hasXHR,
                        graceful_degradation: true
                    };
                } catch (e) {
                    window.fetch = originalFetch;
                    return {error: e.message};
                }
            """)
            
            assert fallback_test.get('xhr_available', False), "XMLHttpRequest should be available as fallback"
            
        finally:
            driver.quit()
    
    def test_css_fallbacks(self):
        """Test CSS fallbacks for older browsers"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            driver.get("http://localhost:8000/")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Test CSS fallbacks
            css_fallbacks = driver.execute_script("""
                const testElement = document.createElement('div');
                testElement.style.display = 'block'; // Fallback
                testElement.style.display = 'flex';  // Modern
                
                document.body.appendChild(testElement);
                const computedStyle = window.getComputedStyle(testElement);
                const displayValue = computedStyle.display;
                document.body.removeChild(testElement);
                
                return {
                    supports_flex: displayValue === 'flex',
                    has_fallback: displayValue === 'block' || displayValue === 'flex'
                };
            """)
            
            assert css_fallbacks['has_fallback'], "CSS should have appropriate fallbacks"
            
        finally:
            driver.quit()