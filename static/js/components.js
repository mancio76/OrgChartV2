/**
 * Component-specific JavaScript functionality
 * Organigramma Web App
 */

// Components namespace
window.Components = window.Components || {};

/**
 * Initialize components
 */
Components.init = function() {
    this.initDataTables();
    this.initProgressCircles();
    this.initSkeletonLoaders();
    console.log('Components initialized');
};

/**
 * Initialize data tables
 */
Components.initDataTables = function() {
    const tables = document.querySelectorAll('.data-table table');
    
    tables.forEach(function(table) {
        // Add sorting functionality
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach(function(header) {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                Components.sortTable(table, header);
            });
        });
        
        // Add search functionality if search input exists
        const searchInput = document.querySelector(`[data-table-search="${table.id}"]`);
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                Components.searchTable(table, this.value);
            });
        }
    });
};

/**
 * Sort table by column
 */
Components.sortTable = function(table, header) {
    const columnIndex = Array.from(header.parentElement.children).indexOf(header);
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const isAscending = !header.classList.contains('sort-asc');
    
    // Remove existing sort classes
    header.parentElement.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add new sort class
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
    
    // Sort rows
    rows.sort(function(a, b) {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        // Try to parse as numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison
        return isAscending ? 
            aValue.localeCompare(bValue) : 
            bValue.localeCompare(aValue);
    });
    
    // Reorder rows in DOM
    rows.forEach(row => tbody.appendChild(row));
};

/**
 * Search table
 */
Components.searchTable = function(table, searchTerm) {
    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(function(row) {
        const text = row.textContent.toLowerCase();
        const matches = text.includes(term);
        row.style.display = matches ? '' : 'none';
    });
    
    // Show "no results" message if needed
    const visibleRows = tbody.querySelectorAll('tr:not([style*="display: none"])');
    let noResultsRow = tbody.querySelector('.no-results-row');
    
    if (visibleRows.length === 0 && searchTerm.trim()) {
        if (!noResultsRow) {
            noResultsRow = document.createElement('tr');
            noResultsRow.className = 'no-results-row';
            noResultsRow.innerHTML = `
                <td colspan="100%" class="text-center py-4 text-muted">
                    <i class="bi bi-search me-2"></i>
                    Nessun risultato trovato per "${searchTerm}"
                </td>
            `;
            tbody.appendChild(noResultsRow);
        }
    } else if (noResultsRow) {
        noResultsRow.remove();
    }
};

/**
 * Initialize progress circles
 */
Components.initProgressCircles = function() {
    const circles = document.querySelectorAll('.progress-circle[data-progress]');
    
    circles.forEach(function(circle) {
        const progress = parseInt(circle.dataset.progress) || 0;
        const degrees = (progress / 100) * 360;
        
        circle.style.background = `conic-gradient(
            var(--primary-color) ${degrees}deg,
            var(--light-color) ${degrees}deg
        )`;
        
        // Animate the progress
        let currentProgress = 0;
        const increment = progress / 50; // 50 steps
        
        const animate = function() {
            if (currentProgress < progress) {
                currentProgress += increment;
                const currentDegrees = (currentProgress / 100) * 360;
                circle.style.background = `conic-gradient(
                    var(--primary-color) ${currentDegrees}deg,
                    var(--light-color) ${currentDegrees}deg
                )`;
                requestAnimationFrame(animate);
            }
        };
        
        // Start animation when element is visible
        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    animate();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(circle);
    });
};

/**
 * Initialize skeleton loaders
 */
Components.initSkeletonLoaders = function() {
    const skeletons = document.querySelectorAll('.skeleton');
    
    // Remove skeleton class when content is loaded
    skeletons.forEach(function(skeleton) {
        if (skeleton.dataset.loaded === 'true') {
            skeleton.classList.remove('skeleton');
        }
    });
};

/**
 * Show loading skeleton
 */
Components.showSkeleton = function(element) {
    element.classList.add('skeleton');
    element.dataset.loaded = 'false';
};

/**
 * Hide loading skeleton
 */
Components.hideSkeleton = function(element) {
    element.classList.remove('skeleton');
    element.dataset.loaded = 'true';
};

/**
 * Create empty state
 */
Components.createEmptyState = function(container, options = {}) {
    const defaults = {
        icon: 'inbox',
        title: 'Nessun elemento trovato',
        message: 'Non ci sono elementi da visualizzare.',
        actionText: null,
        actionUrl: null
    };
    
    const config = Object.assign(defaults, options);
    
    const emptyState = document.createElement('div');
    emptyState.className = 'empty-state';
    
    let actionHtml = '';
    if (config.actionText && config.actionUrl) {
        actionHtml = `
            <a href="${config.actionUrl}" class="btn btn-primary">
                <i class="bi bi-plus me-1"></i>${config.actionText}
            </a>
        `;
    }
    
    emptyState.innerHTML = `
        <div class="empty-icon">
            <i class="bi bi-${config.icon}"></i>
        </div>
        <h5>${config.title}</h5>
        <p>${config.message}</p>
        ${actionHtml}
    `;
    
    container.appendChild(emptyState);
    return emptyState;
};

/**
 * Create timeline item
 */
Components.createTimelineItem = function(data) {
    const item = document.createElement('div');
    item.className = `timeline-item ${data.type || ''}`;
    
    item.innerHTML = `
        <div class="timeline-content">
            <div class="timeline-header">
                <h6 class="timeline-title">${data.title}</h6>
                <span class="timeline-date">${data.date}</span>
            </div>
            <p class="mb-0">${data.description}</p>
            ${data.details ? `<div class="mt-2 small text-muted">${data.details}</div>` : ''}
        </div>
    `;
    
    return item;
};

/**
 * Update progress circle
 */
Components.updateProgressCircle = function(circle, newProgress) {
    const currentProgress = parseInt(circle.dataset.progress) || 0;
    circle.dataset.progress = newProgress;
    
    let progress = currentProgress;
    const increment = (newProgress - currentProgress) / 30; // 30 steps
    
    const animate = function() {
        if (Math.abs(progress - newProgress) > Math.abs(increment)) {
            progress += increment;
            const degrees = (progress / 100) * 360;
            circle.style.background = `conic-gradient(
                var(--primary-color) ${degrees}deg,
                var(--light-color) ${degrees}deg
            )`;
            circle.textContent = Math.round(progress) + '%';
            requestAnimationFrame(animate);
        } else {
            const degrees = (newProgress / 100) * 360;
            circle.style.background = `conic-gradient(
                var(--primary-color) ${degrees}deg,
                var(--light-color) ${degrees}deg
            )`;
            circle.textContent = newProgress + '%';
        }
    };
    
    animate();
};

/**
 * Create stat card
 */
Components.createStatCard = function(data) {
    const card = document.createElement('div');
    card.className = `stat-card ${data.type || 'primary'}`;
    
    card.innerHTML = `
        <div class="stat-icon">
            <i class="bi bi-${data.icon}"></i>
        </div>
        <div class="stat-value">${data.value}</div>
        <div class="stat-label">${data.label}</div>
        ${data.change ? `<div class="stat-change ${data.change > 0 ? 'text-success' : 'text-danger'} mt-1">
            <i class="bi bi-${data.change > 0 ? 'arrow-up' : 'arrow-down'} me-1"></i>
            ${Math.abs(data.change)}%
        </div>` : ''}
    `;
    
    return card;
};

/**
 * Animate counter
 */
Components.animateCounter = function(element, targetValue, duration = 1000) {
    const startValue = parseInt(element.textContent) || 0;
    const increment = (targetValue - startValue) / (duration / 16); // 60fps
    let currentValue = startValue;
    
    const animate = function() {
        if (Math.abs(currentValue - targetValue) > Math.abs(increment)) {
            currentValue += increment;
            element.textContent = Math.round(currentValue);
            requestAnimationFrame(animate);
        } else {
            element.textContent = targetValue;
        }
    };
    
    animate();
};

/**
 * Initialize when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    Components.init();
});

// Export for global use
window.createEmptyState = Components.createEmptyState;
window.createTimelineItem = Components.createTimelineItem;
window.updateProgressCircle = Components.updateProgressCircle;
window.createStatCard = Components.createStatCard;
window.animateCounter = Components.animateCounter;