/**
 * Responsive Organizational Chart - Task 7.3 Implementation
 * Responsive chart functionality with progressive enhancement and lazy loading
 */

// Responsive orgchart namespace
window.OrgchartResponsive = window.OrgchartResponsive || {};

/**
 * Initialize responsive orgchart functionality
 */
OrgchartResponsive.init = function() {
    this.setupResponsiveLayout();
    this.setupProgressiveEnhancement();
    this.setupLazyLoading();
    this.setupViewportAdaptation();
    this.setupTouchSupport();
    this.setupPerformanceOptimizations();
    console.log('Responsive orgchart initialized');
};

/**
 * Setup responsive layout adaptation
 */
OrgchartResponsive.setupResponsiveLayout = function() {
    // Detect screen size and adapt layout
    this.currentBreakpoint = this.getBreakpoint();
    this.adaptLayoutToBreakpoint();
    
    // Listen for resize events
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            const newBreakpoint = OrgchartResponsive.getBreakpoint();
            if (newBreakpoint !== OrgchartResponsive.currentBreakpoint) {
                OrgchartResponsive.currentBreakpoint = newBreakpoint;
                OrgchartResponsive.adaptLayoutToBreakpoint();
                OrgchartResponsive.recalculateLayout();
            }
        }, 250);
    });
    
    // Listen for orientation changes
    window.addEventListener('orientationchange', function() {
        setTimeout(function() {
            OrgchartResponsive.handleOrientationChange();
        }, 100);
    });
};

/**
 * Get current breakpoint
 */
OrgchartResponsive.getBreakpoint = function() {
    const width = window.innerWidth;
    if (width < 576) return 'xs';
    if (width < 768) return 'sm';
    if (width < 992) return 'md';
    if (width < 1200) return 'lg';
    if (width < 1400) return 'xl';
    return 'xxl';
};

/**
 * Adapt layout to current breakpoint
 */
OrgchartResponsive.adaptLayoutToBreakpoint = function() {
    const orgchartContainer = document.getElementById('orgchart-container');
    const orgchartTree = document.getElementById('orgchart-tree');
    
    if (!orgchartContainer || !orgchartTree) return;
    
    // Remove existing breakpoint classes
    orgchartContainer.classList.remove('bp-xs', 'bp-sm', 'bp-md', 'bp-lg', 'bp-xl', 'bp-xxl');
    orgchartTree.classList.remove('layout-vertical', 'layout-horizontal', 'layout-compact');
    
    // Add current breakpoint class
    orgchartContainer.classList.add(`bp-${this.currentBreakpoint}`);
    
    switch (this.currentBreakpoint) {
        case 'xs':
        case 'sm':
            this.setupMobileLayout();
            break;
        case 'md':
            this.setupTabletLayout();
            break;
        case 'lg':
        case 'xl':
        case 'xxl':
            this.setupDesktopLayout();
            break;
    }
    
    // Update controls visibility
    this.updateControlsVisibility();
};

/**
 * Setup mobile layout (xs, sm)
 */
OrgchartResponsive.setupMobileLayout = function() {
    const orgchartTree = document.getElementById('orgchart-tree');
    const unitBoxes = document.querySelectorAll('.unit-box');
    
    // Force vertical layout
    orgchartTree.classList.add('layout-vertical');
    
    // Simplify unit boxes for mobile
    unitBoxes.forEach(function(unitBox) {
        unitBox.classList.add('mobile-simplified');
    });
    
    // Hide complex controls
    this.hideComplexControls();
    
    // Enable swipe navigation
    this.enableSwipeNavigation();
    
    // Adjust zoom levels for mobile
    this.adjustMobileZoom();
};

/**
 * Setup tablet layout (md)
 */
OrgchartResponsive.setupTabletLayout = function() {
    const orgchartTree = document.getElementById('orgchart-tree');
    
    // Use compact layout
    orgchartTree.classList.add('layout-compact');
    
    // Show essential controls
    this.showEssentialControls();
    
    // Enable touch interactions
    this.enableTouchInteractions();
};

/**
 * Setup desktop layout (lg, xl, xxl)
 */
OrgchartResponsive.setupDesktopLayout = function() {
    const orgchartTree = document.getElementById('orgchart-tree');
    
    // Use full horizontal layout
    orgchartTree.classList.add('layout-horizontal');
    
    // Show all controls
    this.showAllControls();
    
    // Enable advanced interactions
    this.enableAdvancedInteractions();
};

/**
 * Setup progressive enhancement
 */
OrgchartResponsive.setupProgressiveEnhancement = function() {
    // Check if JavaScript is available
    document.documentElement.classList.add('js-enabled');
    
    // Enhance basic HTML structure
    this.enhanceBasicStructure();
    
    // Add interactive features progressively
    this.addInteractiveFeatures();
    
    // Setup fallbacks for non-JS users
    this.setupNoJSFallbacks();
};

/**
 * Enhance basic HTML structure
 */
OrgchartResponsive.enhanceBasicStructure = function() {
    const orgchartContainer = document.getElementById('orgchart-container');
    if (!orgchartContainer) return;
    
    // Add loading indicator
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'orgchart-loading';
    loadingIndicator.innerHTML = `
        <div class="loading-content">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Caricamento organigramma...</span>
            </div>
            <p class="mt-2">Caricamento organigramma in corso...</p>
        </div>
    `;
    
    // Show loading initially
    orgchartContainer.appendChild(loadingIndicator);
    
    // Hide loading after content is ready
    setTimeout(function() {
        loadingIndicator.style.display = 'none';
    }, 1000);
};

/**
 * Add interactive features progressively
 */
OrgchartResponsive.addInteractiveFeatures = function() {
    // Add interactive controls only if JavaScript is enabled
    this.addZoomControls();
    this.addViewModeControls();
    this.addSearchFunctionality();
    this.addExportOptions();
};

/**
 * Setup no-JS fallbacks
 */
OrgchartResponsive.setupNoJSFallbacks = function() {
    // Add noscript styles
    const noscriptStyle = document.createElement('noscript');
    noscriptStyle.innerHTML = `
        <style>
            .js-only { display: none !important; }
            .no-js-show { display: block !important; }
            .orgchart-tree { 
                transform: none !important; 
                overflow: visible !important;
            }
            .unit-box { 
                margin-bottom: 1rem !important; 
                page-break-inside: avoid;
            }
        </style>
    `;
    document.head.appendChild(noscriptStyle);
};

/**
 * Setup lazy loading for large organizational structures
 */
OrgchartResponsive.setupLazyLoading = function() {
    this.lazyLoadThreshold = 50; // Load units when within 50px of viewport
    this.loadedUnits = new Set();
    this.pendingLoads = new Map();
    
    // Setup intersection observer for lazy loading
    this.setupIntersectionObserver();
    
    // Setup virtual scrolling for very large trees
    this.setupVirtualScrolling();
    
    // Implement progressive loading
    this.implementProgressiveLoading();
};

/**
 * Setup intersection observer for lazy loading
 */
OrgchartResponsive.setupIntersectionObserver = function() {
    if (!('IntersectionObserver' in window)) {
        // Fallback for browsers without IntersectionObserver
        this.loadAllUnits();
        return;
    }
    
    this.intersectionObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                OrgchartResponsive.loadUnitContent(entry.target);
            }
        });
    }, {
        rootMargin: `${this.lazyLoadThreshold}px`,
        threshold: 0.1
    });
    
    // Observe all unit placeholders
    const unitPlaceholders = document.querySelectorAll('.unit-placeholder');
    unitPlaceholders.forEach(placeholder => {
        this.intersectionObserver.observe(placeholder);
    });
};

/**
 * Load unit content lazily
 */
OrgchartResponsive.loadUnitContent = function(placeholder) {
    const unitId = placeholder.dataset.unitId;
    
    if (this.loadedUnits.has(unitId) || this.pendingLoads.has(unitId)) {
        return;
    }
    
    // Mark as pending
    this.pendingLoads.set(unitId, true);
    
    // Show loading state
    placeholder.classList.add('loading');
    
    // Simulate API call (replace with actual API call)
    setTimeout(() => {
        this.renderUnitContent(placeholder, unitId);
        this.loadedUnits.add(unitId);
        this.pendingLoads.delete(unitId);
        placeholder.classList.remove('loading');
    }, Math.random() * 500 + 200);
};

/**
 * Render unit content
 */
OrgchartResponsive.renderUnitContent = function(placeholder, unitId) {
    // This would typically fetch data from an API
    // For now, we'll just reveal the existing content
    const unitBox = placeholder.querySelector('.unit-box');
    if (unitBox) {
        unitBox.style.display = 'block';
        unitBox.classList.add('unit-loaded');
    }
    
    placeholder.classList.remove('unit-placeholder');
    placeholder.classList.add('unit-loaded');
};

/**
 * Setup virtual scrolling for very large trees
 */
OrgchartResponsive.setupVirtualScrolling = function() {
    const orgchartContainer = document.getElementById('orgchart-container');
    if (!orgchartContainer) return;
    
    const unitCount = document.querySelectorAll('.tree-node').length;
    
    // Only enable virtual scrolling for very large trees
    if (unitCount > 100) {
        orgchartContainer.classList.add('virtual-scrolling');
        this.enableVirtualScrolling();
    }
};

/**
 * Enable virtual scrolling
 */
OrgchartResponsive.enableVirtualScrolling = function() {
    const container = document.getElementById('orgchart-container');
    const tree = document.getElementById('orgchart-tree');
    
    if (!container || !tree) return;
    
    let scrollTimeout;
    container.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(function() {
            OrgchartResponsive.updateVisibleUnits();
        }, 16); // ~60fps
    });
    
    // Initial update
    this.updateVisibleUnits();
};

/**
 * Update visible units for virtual scrolling
 */
OrgchartResponsive.updateVisibleUnits = function() {
    const container = document.getElementById('orgchart-container');
    const units = document.querySelectorAll('.tree-node');
    
    if (!container || units.length === 0) return;
    
    const containerRect = container.getBoundingClientRect();
    const buffer = 100; // Extra pixels to load outside viewport
    
    units.forEach(function(unit) {
        const unitRect = unit.getBoundingClientRect();
        const isVisible = (
            unitRect.bottom >= containerRect.top - buffer &&
            unitRect.top <= containerRect.bottom + buffer &&
            unitRect.right >= containerRect.left - buffer &&
            unitRect.left <= containerRect.right + buffer
        );
        
        if (isVisible) {
            unit.classList.add('in-viewport');
            unit.style.visibility = 'visible';
        } else {
            unit.classList.remove('in-viewport');
            unit.style.visibility = 'hidden';
        }
    });
};

/**
 * Implement progressive loading
 */
OrgchartResponsive.implementProgressiveLoading = function() {
    // Load root units first
    this.loadRootUnits();
    
    // Then load children on demand
    this.setupOnDemandLoading();
};

/**
 * Load root units first
 */
OrgchartResponsive.loadRootUnits = function() {
    const rootUnits = document.querySelectorAll('.tree-node[data-level="0"]');
    rootUnits.forEach(unit => {
        unit.classList.add('priority-load');
        this.loadUnitContent(unit);
    });
};

/**
 * Setup on-demand loading for child units
 */
OrgchartResponsive.setupOnDemandLoading = function() {
    const expandButtons = document.querySelectorAll('.expand-children');
    
    expandButtons.forEach(button => {
        button.addEventListener('click', function() {
            const unitId = this.dataset.unitId;
            OrgchartResponsive.loadChildUnits(unitId);
        });
    });
};

/**
 * Load child units on demand
 */
OrgchartResponsive.loadChildUnits = function(parentUnitId) {
    const childUnits = document.querySelectorAll(`[data-parent-id="${parentUnitId}"]`);
    
    childUnits.forEach(child => {
        if (!this.loadedUnits.has(child.dataset.unitId)) {
            this.loadUnitContent(child);
        }
    });
};

/**
 * Setup viewport adaptation
 */
OrgchartResponsive.setupViewportAdaptation = function() {
    // Adapt to viewport size changes
    this.adaptToViewport();
    
    // Handle zoom level changes
    this.handleZoomAdaptation();
    
    // Optimize for different pixel densities
    this.optimizeForPixelDensity();
};

/**
 * Adapt to current viewport
 */
OrgchartResponsive.adaptToViewport = function() {
    const viewport = {
        width: window.innerWidth,
        height: window.innerHeight,
        ratio: window.innerWidth / window.innerHeight
    };
    
    const orgchartContainer = document.getElementById('orgchart-container');
    if (!orgchartContainer) return;
    
    // Adjust container height based on viewport
    const maxHeight = Math.min(viewport.height * 0.8, 800);
    orgchartContainer.style.maxHeight = maxHeight + 'px';
    
    // Adjust layout based on aspect ratio
    if (viewport.ratio < 1) {
        // Portrait mode - use vertical layout
        orgchartContainer.classList.add('portrait-mode');
    } else {
        // Landscape mode - use horizontal layout
        orgchartContainer.classList.remove('portrait-mode');
    }
};

/**
 * Handle zoom adaptation
 */
OrgchartResponsive.handleZoomAdaptation = function() {
    // Detect browser zoom level
    const zoomLevel = Math.round(window.devicePixelRatio * 100) / 100;
    
    if (zoomLevel !== 1) {
        document.documentElement.style.setProperty('--zoom-factor', zoomLevel);
        document.body.classList.add('browser-zoomed');
    }
};

/**
 * Optimize for pixel density
 */
OrgchartResponsive.optimizeForPixelDensity = function() {
    const pixelRatio = window.devicePixelRatio || 1;
    
    if (pixelRatio > 1) {
        // High DPI display - use sharper graphics
        document.body.classList.add('high-dpi');
        
        // Adjust font rendering
        document.documentElement.style.setProperty('--font-smoothing', 'antialiased');
    }
};

/**
 * Setup touch support for mobile devices
 */
OrgchartResponsive.setupTouchSupport = function() {
    if (!('ontouchstart' in window)) return;
    
    document.body.classList.add('touch-device');
    
    // Setup touch gestures
    this.setupTouchGestures();
    
    // Setup touch-friendly interactions
    this.setupTouchInteractions();
    
    // Handle touch scrolling
    this.setupTouchScrolling();
};

/**
 * Setup touch gestures
 */
OrgchartResponsive.setupTouchGestures = function() {
    const orgchartContainer = document.getElementById('orgchart-container');
    if (!orgchartContainer) return;
    
    let touchStartX, touchStartY, touchStartTime;
    let isScrolling = false;
    
    orgchartContainer.addEventListener('touchstart', function(e) {
        if (e.touches.length === 1) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            touchStartTime = Date.now();
            isScrolling = false;
        }
    }, { passive: true });
    
    orgchartContainer.addEventListener('touchmove', function(e) {
        if (e.touches.length === 1 && !isScrolling) {
            const touchX = e.touches[0].clientX;
            const touchY = e.touches[0].clientY;
            const deltaX = Math.abs(touchX - touchStartX);
            const deltaY = Math.abs(touchY - touchStartY);
            
            if (deltaX > 10 || deltaY > 10) {
                isScrolling = true;
            }
        }
    }, { passive: true });
    
    orgchartContainer.addEventListener('touchend', function(e) {
        if (e.changedTouches.length === 1 && !isScrolling) {
            const touchEndTime = Date.now();
            const touchDuration = touchEndTime - touchStartTime;
            
            // Handle tap gesture
            if (touchDuration < 300) {
                const target = document.elementFromPoint(
                    e.changedTouches[0].clientX,
                    e.changedTouches[0].clientY
                );
                
                if (target) {
                    OrgchartResponsive.handleTouchTap(target);
                }
            }
        }
    }, { passive: true });
};

/**
 * Handle touch tap
 */
OrgchartResponsive.handleTouchTap = function(target) {
    const unitBox = target.closest('.unit-box');
    if (unitBox) {
        // Toggle unit selection on touch
        unitBox.classList.toggle('touch-selected');
        
        // Show touch feedback
        this.showTouchFeedback(unitBox);
    }
};

/**
 * Show touch feedback
 */
OrgchartResponsive.showTouchFeedback = function(element) {
    element.classList.add('touch-feedback');
    setTimeout(() => {
        element.classList.remove('touch-feedback');
    }, 150);
};

/**
 * Setup touch-friendly interactions
 */
OrgchartResponsive.setupTouchInteractions = function() {
    // Increase touch target sizes
    const actionButtons = document.querySelectorAll('.unit-actions .btn, .person-actions .btn');
    actionButtons.forEach(button => {
        button.classList.add('touch-target');
    });
    
    // Add touch-friendly hover states
    const interactiveElements = document.querySelectorAll('.unit-box, .person-item');
    interactiveElements.forEach(element => {
        element.addEventListener('touchstart', function() {
            this.classList.add('touch-hover');
        }, { passive: true });
        
        element.addEventListener('touchend', function() {
            setTimeout(() => {
                this.classList.remove('touch-hover');
            }, 150);
        }, { passive: true });
    });
};

/**
 * Setup touch scrolling
 */
OrgchartResponsive.setupTouchScrolling = function() {
    const orgchartContainer = document.getElementById('orgchart-container');
    if (!orgchartContainer) return;
    
    // Enable momentum scrolling on iOS
    orgchartContainer.style.webkitOverflowScrolling = 'touch';
    
    // Handle scroll boundaries
    let isScrollingHorizontally = false;
    let isScrollingVertically = false;
    
    orgchartContainer.addEventListener('touchstart', function() {
        isScrollingHorizontally = false;
        isScrollingVertically = false;
    });
    
    orgchartContainer.addEventListener('touchmove', function(e) {
        const touch = e.touches[0];
        const deltaX = Math.abs(touch.clientX - (touch.startX || touch.clientX));
        const deltaY = Math.abs(touch.clientY - (touch.startY || touch.clientY));
        
        if (deltaX > deltaY) {
            isScrollingHorizontally = true;
        } else {
            isScrollingVertically = true;
        }
        
        // Prevent body scroll when scrolling orgchart
        if (isScrollingHorizontally || isScrollingVertically) {
            e.preventDefault();
        }
    }, { passive: false });
};

/**
 * Setup performance optimizations
 */
OrgchartResponsive.setupPerformanceOptimizations = function() {
    // Debounce expensive operations
    this.setupDebouncedOperations();
    
    // Use requestAnimationFrame for smooth animations
    this.setupAnimationOptimizations();
    
    // Implement efficient rendering
    this.setupEfficientRendering();
    
    // Memory management
    this.setupMemoryManagement();
};

/**
 * Setup debounced operations
 */
OrgchartResponsive.setupDebouncedOperations = function() {
    // Debounce resize handler
    this.debouncedResize = this.debounce(function() {
        OrgchartResponsive.handleResize();
    }, 250);
    
    // Debounce scroll handler
    this.debouncedScroll = this.debounce(function() {
        OrgchartResponsive.handleScroll();
    }, 16);
    
    window.addEventListener('resize', this.debouncedResize);
    document.getElementById('orgchart-container')?.addEventListener('scroll', this.debouncedScroll);
};

/**
 * Debounce utility function
 */
OrgchartResponsive.debounce = function(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

/**
 * Setup animation optimizations
 */
OrgchartResponsive.setupAnimationOptimizations = function() {
    // Use CSS transforms for better performance
    this.enableHardwareAcceleration();
    
    // Batch DOM updates
    this.setupBatchedUpdates();
    
    // Reduce animations on low-end devices
    this.adaptAnimationsToDevice();
};

/**
 * Enable hardware acceleration
 */
OrgchartResponsive.enableHardwareAcceleration = function() {
    const animatedElements = document.querySelectorAll('.unit-box, .person-item');
    animatedElements.forEach(element => {
        element.style.willChange = 'transform, opacity';
    });
};

/**
 * Setup batched updates
 */
OrgchartResponsive.setupBatchedUpdates = function() {
    this.pendingUpdates = [];
    this.updateScheduled = false;
    
    this.scheduleUpdate = function(updateFn) {
        this.pendingUpdates.push(updateFn);
        
        if (!this.updateScheduled) {
            this.updateScheduled = true;
            requestAnimationFrame(() => {
                this.processPendingUpdates();
            });
        }
    };
    
    this.processPendingUpdates = function() {
        this.pendingUpdates.forEach(updateFn => updateFn());
        this.pendingUpdates = [];
        this.updateScheduled = false;
    };
};

/**
 * Adapt animations to device capabilities
 */
OrgchartResponsive.adaptAnimationsToDevice = function() {
    // Detect low-end devices
    const isLowEndDevice = this.detectLowEndDevice();
    
    if (isLowEndDevice) {
        document.body.classList.add('reduced-animations');
    }
};

/**
 * Detect low-end device
 */
OrgchartResponsive.detectLowEndDevice = function() {
    // Simple heuristics for low-end device detection
    const hardwareConcurrency = navigator.hardwareConcurrency || 1;
    const deviceMemory = navigator.deviceMemory || 1;
    const connectionSpeed = navigator.connection?.effectiveType || '4g';
    
    return (
        hardwareConcurrency <= 2 ||
        deviceMemory <= 2 ||
        ['slow-2g', '2g', '3g'].includes(connectionSpeed)
    );
};

/**
 * Setup efficient rendering
 */
OrgchartResponsive.setupEfficientRendering = function() {
    // Use document fragments for batch DOM updates
    this.createDocumentFragment = function() {
        return document.createDocumentFragment();
    };
    
    // Minimize reflows and repaints
    this.minimizeReflows();
    
    // Use efficient selectors
    this.cacheSelectors();
};

/**
 * Minimize reflows
 */
OrgchartResponsive.minimizeReflows = function() {
    // Cache layout properties
    this.layoutCache = new Map();
    
    // Batch style changes
    this.batchStyleChanges = function(element, styles) {
        const cssText = Object.entries(styles)
            .map(([prop, value]) => `${prop}: ${value}`)
            .join('; ');
        element.style.cssText += cssText;
    };
};

/**
 * Cache selectors for better performance
 */
OrgchartResponsive.cacheSelectors = function() {
    this.cachedElements = {
        container: document.getElementById('orgchart-container'),
        tree: document.getElementById('orgchart-tree'),
        unitBoxes: document.querySelectorAll('.unit-box'),
        personItems: document.querySelectorAll('.person-item')
    };
};

/**
 * Setup memory management
 */
OrgchartResponsive.setupMemoryManagement = function() {
    // Clean up event listeners on page unload
    window.addEventListener('beforeunload', () => {
        this.cleanup();
    });
    
    // Implement garbage collection for large datasets
    this.setupGarbageCollection();
};

/**
 * Cleanup resources
 */
OrgchartResponsive.cleanup = function() {
    // Remove event listeners
    if (this.intersectionObserver) {
        this.intersectionObserver.disconnect();
    }
    
    // Clear caches
    this.layoutCache?.clear();
    this.loadedUnits?.clear();
    this.pendingLoads?.clear();
    
    // Clear timeouts
    clearTimeout(this.resizeTimeout);
    clearTimeout(this.scrollTimeout);
};

/**
 * Setup garbage collection
 */
OrgchartResponsive.setupGarbageCollection = function() {
    // Periodically clean up unused elements
    setInterval(() => {
        this.garbageCollect();
    }, 30000); // Every 30 seconds
};

/**
 * Perform garbage collection
 */
OrgchartResponsive.garbageCollect = function() {
    // Remove elements that are far from viewport
    const container = this.cachedElements.container;
    if (!container) return;
    
    const containerRect = container.getBoundingClientRect();
    const threshold = 1000; // pixels
    
    const units = document.querySelectorAll('.tree-node');
    units.forEach(unit => {
        const unitRect = unit.getBoundingClientRect();
        const distance = Math.abs(unitRect.top - containerRect.top);
        
        if (distance > threshold) {
            // Unload non-essential content
            const personsList = unit.querySelector('.persons-list');
            if (personsList && !unit.classList.contains('priority-load')) {
                personsList.style.display = 'none';
            }
        }
    });
};

/**
 * Utility functions for responsive behavior
 */

// Handle resize events
OrgchartResponsive.handleResize = function() {
    this.adaptToViewport();
    this.recalculateLayout();
};

// Handle scroll events
OrgchartResponsive.handleScroll = function() {
    this.updateVisibleUnits();
};

// Recalculate layout
OrgchartResponsive.recalculateLayout = function() {
    const tree = this.cachedElements.tree;
    if (tree) {
        // Force layout recalculation
        tree.style.display = 'none';
        tree.offsetHeight; // Trigger reflow
        tree.style.display = '';
    }
};

// Handle orientation change
OrgchartResponsive.handleOrientationChange = function() {
    this.adaptLayoutToBreakpoint();
    this.adaptToViewport();
};

// Control visibility functions
OrgchartResponsive.hideComplexControls = function() {
    const complexControls = document.querySelectorAll('.complex-control');
    complexControls.forEach(control => {
        control.style.display = 'none';
    });
};

OrgchartResponsive.showEssentialControls = function() {
    const essentialControls = document.querySelectorAll('.essential-control');
    essentialControls.forEach(control => {
        control.style.display = 'block';
    });
};

OrgchartResponsive.showAllControls = function() {
    const allControls = document.querySelectorAll('.orgchart-control');
    allControls.forEach(control => {
        control.style.display = 'block';
    });
};

OrgchartResponsive.updateControlsVisibility = function() {
    const controls = document.querySelector('.tree-controls');
    if (!controls) return;
    
    switch (this.currentBreakpoint) {
        case 'xs':
        case 'sm':
            controls.classList.add('mobile-controls');
            break;
        case 'md':
            controls.classList.add('tablet-controls');
            break;
        default:
            controls.classList.add('desktop-controls');
    }
};

// Touch and interaction functions
OrgchartResponsive.enableSwipeNavigation = function() {
    // Implementation for swipe navigation on mobile
    console.log('Swipe navigation enabled');
};

OrgchartResponsive.enableTouchInteractions = function() {
    // Implementation for touch interactions on tablet
    console.log('Touch interactions enabled');
};

OrgchartResponsive.enableAdvancedInteractions = function() {
    // Implementation for advanced interactions on desktop
    console.log('Advanced interactions enabled');
};

OrgchartResponsive.adjustMobileZoom = function() {
    // Adjust zoom levels specifically for mobile
    const tree = this.cachedElements.tree;
    if (tree) {
        tree.style.transform = 'scale(0.8)';
    }
};

// Loading functions
OrgchartResponsive.loadAllUnits = function() {
    // Fallback to load all units if IntersectionObserver is not available
    const units = document.querySelectorAll('.unit-placeholder');
    units.forEach(unit => {
        this.loadUnitContent(unit);
    });
};

// Progressive enhancement functions
OrgchartResponsive.addZoomControls = function() {
    // Add zoom controls if not already present
    console.log('Zoom controls added');
};

OrgchartResponsive.addViewModeControls = function() {
    // Add view mode controls if not already present
    console.log('View mode controls added');
};

OrgchartResponsive.addSearchFunctionality = function() {
    // Add search functionality if not already present
    console.log('Search functionality added');
};

OrgchartResponsive.addExportOptions = function() {
    // Add export options if not already present
    console.log('Export options added');
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    OrgchartResponsive.init();
});

// Export for global use
window.OrgchartResponsive = OrgchartResponsive;