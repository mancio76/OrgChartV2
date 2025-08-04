/**
 * Theme Accessibility and Performance Enhancements
 * Provides client-side accessibility features and performance optimizations for the theme system
 */

class ThemeAccessibility {
    constructor() {
        this.highContrastMode = false;
        this.reducedMotion = false;
        this.lazyLoadObserver = null;
        this.performanceMetrics = {
            cssLoadTime: 0,
            themeRenderTime: 0,
            lazyLoadCount: 0
        };
        
        this.init();
    }
    
    /**
     * Initialize accessibility features
     */
    init() {
        this.detectUserPreferences();
        this.setupHighContrastToggle();
        this.setupKeyboardNavigation();
        this.setupLazyLoading();
        this.setupPerformanceMonitoring();
        this.addSkipLinks();
        
        console.log('Theme accessibility features initialized');
    }
    
    /**
     * Detect user accessibility preferences
     */
    detectUserPreferences() {
        // Check for reduced motion preference
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.reducedMotion = true;
            document.body.classList.add('reduced-motion');
            console.log('Reduced motion preference detected');
        }
        
        // Check for high contrast preference
        if (window.matchMedia && window.matchMedia('(prefers-contrast: high)').matches) {
            this.enableHighContrast();
            console.log('High contrast preference detected');
        }
        
        // Check for color scheme preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.classList.add('dark-mode-preferred');
        }
        
        // Listen for preference changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
                this.reducedMotion = e.matches;
                document.body.classList.toggle('reduced-motion', e.matches);
            });
            
            window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
                if (e.matches) {
                    this.enableHighContrast();
                } else {
                    this.disableHighContrast();
                }
            });
        }
    }
    
    /**
     * Setup high contrast mode toggle
     */
    setupHighContrastToggle() {
        // Create high contrast toggle button
        const toggleButton = document.createElement('button');
        toggleButton.id = 'high-contrast-toggle';
        toggleButton.className = 'btn btn-outline-secondary btn-sm position-fixed';
        toggleButton.style.cssText = 'bottom: 1rem; right: 1rem; z-index: 1050;';
        toggleButton.innerHTML = '<i class="bi bi-circle-half"></i> <span class="sr-only">Attiva/Disattiva Alto Contrasto</span>';
        toggleButton.setAttribute('aria-label', 'Attiva o disattiva modalità alto contrasto');
        toggleButton.setAttribute('title', 'Modalità Alto Contrasto');
        
        toggleButton.addEventListener('click', () => {
            this.toggleHighContrast();
        });
        
        // Add to page
        document.body.appendChild(toggleButton);
        
        // Check for saved preference
        const savedPreference = localStorage.getItem('theme-high-contrast');
        if (savedPreference === 'true') {
            this.enableHighContrast();
        }
    }
    
    /**
     * Toggle high contrast mode
     */
    toggleHighContrast() {
        if (this.highContrastMode) {
            this.disableHighContrast();
        } else {
            this.enableHighContrast();
        }
    }
    
    /**
     * Enable high contrast mode
     */
    enableHighContrast() {
        this.highContrastMode = true;
        document.body.classList.add('high-contrast');
        
        // Update all themed elements
        const themedElements = document.querySelectorAll('.unit-themed, .unit-box');
        themedElements.forEach(element => {
            element.classList.add('high-contrast');
        });
        
        // Save preference
        localStorage.setItem('theme-high-contrast', 'true');
        
        // Update toggle button
        const toggleButton = document.getElementById('high-contrast-toggle');
        if (toggleButton) {
            toggleButton.classList.add('active');
            toggleButton.setAttribute('aria-pressed', 'true');
        }
        
        console.log('High contrast mode enabled');
    }
    
    /**
     * Disable high contrast mode
     */
    disableHighContrast() {
        this.highContrastMode = false;
        document.body.classList.remove('high-contrast');
        
        // Update all themed elements
        const themedElements = document.querySelectorAll('.unit-themed, .unit-box');
        themedElements.forEach(element => {
            element.classList.remove('high-contrast');
        });
        
        // Save preference
        localStorage.setItem('theme-high-contrast', 'false');
        
        // Update toggle button
        const toggleButton = document.getElementById('high-contrast-toggle');
        if (toggleButton) {
            toggleButton.classList.remove('active');
            toggleButton.setAttribute('aria-pressed', 'false');
        }
        
        console.log('High contrast mode disabled');
    }
    
    /**
     * Setup enhanced keyboard navigation
     */
    setupKeyboardNavigation() {
        // Add keyboard event listeners for themed elements
        document.addEventListener('keydown', (e) => {
            // Handle Enter and Space for themed elements
            if ((e.key === 'Enter' || e.key === ' ') && e.target.classList.contains('unit-themed')) {
                e.preventDefault();
                e.target.click();
            }
            
            // Handle Escape to close any open modals or dropdowns
            if (e.key === 'Escape') {
                const activeElement = document.activeElement;
                if (activeElement && activeElement.blur) {
                    activeElement.blur();
                }
            }
            
            // Handle high contrast toggle with Ctrl+Alt+H
            if (e.ctrlKey && e.altKey && e.key === 'h') {
                e.preventDefault();
                this.toggleHighContrast();
            }
        });
        
        // Ensure all themed elements are focusable
        const themedElements = document.querySelectorAll('.unit-themed, .unit-box');
        themedElements.forEach(element => {
            if (!element.hasAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }
            
            // Add role if not present
            if (!element.hasAttribute('role')) {
                element.setAttribute('role', 'button');
            }
        });
    }
    
    /**
     * Setup lazy loading for theme data in large orgcharts
     */
    setupLazyLoading() {
        if (!('IntersectionObserver' in window)) {
            console.warn('IntersectionObserver not supported, lazy loading disabled');
            return;
        }
        
        this.lazyLoadObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadThemeData(entry.target);
                    this.lazyLoadObserver.unobserve(entry.target);
                    this.performanceMetrics.lazyLoadCount++;
                }
            });
        }, {
            rootMargin: '50px',
            threshold: 0.1
        });
        
        // Observe elements marked for lazy loading
        const lazyElements = document.querySelectorAll('[data-lazy-theme]');
        lazyElements.forEach(element => {
            this.lazyLoadObserver.observe(element);
        });
        
        console.log(`Lazy loading setup for ${lazyElements.length} elements`);
    }
    
    /**
     * Load theme data for a lazy-loaded element
     */
    async loadThemeData(element) {
        const themeId = element.getAttribute('data-lazy-theme');
        if (!themeId) return;
        
        try {
            const startTime = performance.now();
            
            // Show loading indicator
            element.classList.add('theme-loading');
            
            // Fetch theme data
            const response = await fetch(`/api/themes/${themeId}/lazy`);
            if (!response.ok) throw new Error('Failed to load theme data');
            
            const themeData = await response.json();
            
            // Apply theme data to element
            this.applyThemeData(element, themeData);
            
            // Remove loading indicator
            element.classList.remove('theme-loading');
            element.classList.add('theme-loaded');
            
            const loadTime = performance.now() - startTime;
            console.log(`Lazy loaded theme ${themeId} in ${loadTime.toFixed(2)}ms`);
            
        } catch (error) {
            console.error('Error lazy loading theme data:', error);
            element.classList.remove('theme-loading');
            element.classList.add('theme-error');
        }
    }
    
    /**
     * Apply theme data to an element
     */
    applyThemeData(element, themeData) {
        // Apply CSS class
        if (themeData.css_class_name) {
            element.classList.add(themeData.css_class_name);
        }
        
        // Apply CSS custom properties
        if (themeData.primary_color) {
            element.style.setProperty('--unit-primary', themeData.primary_color);
        }
        if (themeData.secondary_color) {
            element.style.setProperty('--unit-secondary', themeData.secondary_color);
        }
        if (themeData.text_color) {
            element.style.setProperty('--unit-text', themeData.text_color);
        }
        if (themeData.computed_border_color) {
            element.style.setProperty('--unit-border', themeData.computed_border_color);
        }
        if (themeData.border_width) {
            element.style.setProperty('--unit-border-width', `${themeData.border_width}px`);
        }
        
        // Update icon if present
        const iconElement = element.querySelector('.bi');
        if (iconElement && themeData.icon_class) {
            iconElement.className = `bi bi-${themeData.icon_class}`;
        }
        
        // Update badge text if present
        const badgeElement = element.querySelector('.badge');
        if (badgeElement && themeData.display_label) {
            badgeElement.textContent = themeData.display_label;
        }
    }
    
    /**
     * Setup performance monitoring
     */
    setupPerformanceMonitoring() {
        // Monitor CSS load time
        const cssLinks = document.querySelectorAll('link[rel="stylesheet"][href*="themes"]');
        cssLinks.forEach(link => {
            const startTime = performance.now();
            link.addEventListener('load', () => {
                this.performanceMetrics.cssLoadTime = performance.now() - startTime;
                console.log(`Theme CSS loaded in ${this.performanceMetrics.cssLoadTime.toFixed(2)}ms`);
            });
        });
        
        // Monitor theme rendering time
        const startTime = performance.now();
        document.addEventListener('DOMContentLoaded', () => {
            this.performanceMetrics.themeRenderTime = performance.now() - startTime;
            console.log(`Theme rendering completed in ${this.performanceMetrics.themeRenderTime.toFixed(2)}ms`);
        });
        
        // Report performance metrics
        setTimeout(() => {
            this.reportPerformanceMetrics();
        }, 5000);
    }
    
    /**
     * Add skip links for accessibility
     */
    addSkipLinks() {
        const pageHeader = document.querySelector('page-header');
        const skipLinksContainer = document.createElement('div');
        skipLinksContainer.className = 'skip-links';
        skipLinksContainer.innerHTML = `
            <a href="#main-content" class="skip-link">Salta al contenuto principale</a>
            <a href="#navigation" class="skip-link">Salta alla navigazione</a>
            <a href="#orgchart" class="skip-link">Salta all'organigramma</a>
        `;
        
        document.body.insertBefore(skipLinksContainer, pageHeader ?? document.body.firstChild);
    }
    
    /**
     * Report performance metrics
     */
    reportPerformanceMetrics() {
        const metrics = {
            ...this.performanceMetrics,
            timestamp: Date.now(),
            userAgent: navigator.userAgent,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            accessibility: {
                highContrastMode: this.highContrastMode,
                reducedMotion: this.reducedMotion
            }
        };
        
        console.log('Theme Performance Metrics:', metrics);
        
        // Send metrics to server if analytics endpoint exists
        if (window.location.pathname.includes('/themes/')) {
            fetch('/api/themes/performance-metrics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(metrics)
            }).catch(error => {
                console.warn('Failed to send performance metrics:', error);
            });
        }
    }
    
    /**
     * Get current accessibility status
     */
    getAccessibilityStatus() {
        return {
            highContrastMode: this.highContrastMode,
            reducedMotion: this.reducedMotion,
            keyboardNavigation: true,
            lazyLoadingEnabled: !!this.lazyLoadObserver,
            performanceMetrics: this.performanceMetrics
        };
    }
    
    /**
     * Validate color contrast for a theme
     */
    validateColorContrast(primaryColor, textColor) {
        try {
            const primary = this.hexToRgb(primaryColor);
            const text = this.hexToRgb(textColor);
            
            if (!primary || !text) return null;
            
            const contrastRatio = this.calculateContrastRatio(primary, text);
            
            return {
                ratio: Math.round(contrastRatio * 100) / 100,
                wcagAA: contrastRatio >= 4.5,
                wcagAAA: contrastRatio >= 7.0,
                level: contrastRatio >= 7.0 ? 'AAA' : contrastRatio >= 4.5 ? 'AA' : 'Fail'
            };
        } catch (error) {
            console.error('Error validating color contrast:', error);
            return null;
        }
    }
    
    /**
     * Convert hex color to RGB
     */
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
    
    /**
     * Calculate WCAG contrast ratio
     */
    calculateContrastRatio(rgb1, rgb2) {
        const luminance1 = this.getLuminance(rgb1);
        const luminance2 = this.getLuminance(rgb2);
        
        const brightest = Math.max(luminance1, luminance2);
        const darkest = Math.min(luminance1, luminance2);
        
        return (brightest + 0.05) / (darkest + 0.05);
    }
    
    /**
     * Calculate relative luminance
     */
    getLuminance(rgb) {
        const rsRGB = rgb.r / 255;
        const gsRGB = rgb.g / 255;
        const bsRGB = rgb.b / 255;
        
        const r = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
        const g = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
        const b = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);
        
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    }
}

// Initialize theme accessibility when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeAccessibility = new ThemeAccessibility();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeAccessibility;
}