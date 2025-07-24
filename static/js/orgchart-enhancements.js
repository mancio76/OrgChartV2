/**
 * Organizational Chart Enhancements - Task 7.2 Implementation
 * Enhanced unit type-specific rendering and interactions
 */

// Orgchart enhancements namespace
window.OrgchartEnhancements = window.OrgchartEnhancements || {};

/**
 * Initialize orgchart enhancements
 */
OrgchartEnhancements.init = function() {
    this.setupUnitInteractions();
    this.setupPersonInteractions();
    this.setupKeyboardNavigation();
    this.setupAccessibilityFeatures();
    this.setupAnimations();
    console.log('Orgchart enhancements initialized');
};

/**
 * Setup enhanced unit interactions
 */
OrgchartEnhancements.setupUnitInteractions = function() {
    const unitBoxes = document.querySelectorAll('.unit-box');
    
    unitBoxes.forEach(function(unitBox) {
        // Add hover effects for unit type differentiation
        unitBox.addEventListener('mouseenter', function() {
            this.classList.add('unit-hover');
            
            // Highlight connected units
            const unitId = this.closest('.tree-node').dataset.unitId;
            OrgchartEnhancements.highlightConnectedUnits(unitId);
        });
        
        unitBox.addEventListener('mouseleave', function() {
            this.classList.remove('unit-hover');
            
            // Remove highlights
            OrgchartEnhancements.clearHighlights();
        });
        
        // Add click handler for unit selection
        unitBox.addEventListener('click', function(e) {
            if (e.target.closest('.unit-actions') || e.target.closest('.person-actions')) {
                return; // Don't handle if clicking on action buttons
            }
            
            e.preventDefault();
            OrgchartEnhancements.selectUnit(this);
        });
        
        // Add double-click handler for quick navigation
        unitBox.addEventListener('dblclick', function(e) {
            e.preventDefault();
            const unitId = this.closest('.tree-node').dataset.unitId;
            window.location.href = `/units/${unitId}`;
        });
    });
};

/**
 * Setup enhanced person interactions
 */
OrgchartEnhancements.setupPersonInteractions = function() {
    const personItems = document.querySelectorAll('.person-item');
    
    personItems.forEach(function(personItem) {
        // Add hover effects
        personItem.addEventListener('mouseenter', function() {
            this.classList.add('person-hover');
            
            // Show additional person info tooltip
            OrgchartEnhancements.showPersonTooltip(this);
        });
        
        personItem.addEventListener('mouseleave', function() {
            this.classList.remove('person-hover');
            
            // Hide tooltip
            OrgchartEnhancements.hidePersonTooltip();
        });
        
        // Add click handler for person selection
        personItem.addEventListener('click', function(e) {
            if (e.target.closest('.person-actions')) {
                return; // Don't handle if clicking on action buttons
            }
            
            e.preventDefault();
            OrgchartEnhancements.selectPerson(this);
        });
    });
};

/**
 * Setup keyboard navigation
 */
OrgchartEnhancements.setupKeyboardNavigation = function() {
    let selectedUnit = null;
    let selectedPerson = null;
    
    document.addEventListener('keydown', function(e) {
        // Only handle if no input is focused
        if (document.activeElement.tagName === 'INPUT' || 
            document.activeElement.tagName === 'TEXTAREA' || 
            document.activeElement.contentEditable === 'true') {
            return;
        }
        
        switch(e.key) {
            case 'ArrowUp':
                e.preventDefault();
                OrgchartEnhancements.navigateUp();
                break;
                
            case 'ArrowDown':
                e.preventDefault();
                OrgchartEnhancements.navigateDown();
                break;
                
            case 'ArrowLeft':
                e.preventDefault();
                OrgchartEnhancements.navigateLeft();
                break;
                
            case 'ArrowRight':
                e.preventDefault();
                OrgchartEnhancements.navigateRight();
                break;
                
            case 'Enter':
                e.preventDefault();
                if (selectedUnit) {
                    const unitId = selectedUnit.dataset.unitId;
                    window.location.href = `/units/${unitId}`;
                }
                break;
                
            case 'Escape':
                e.preventDefault();
                OrgchartEnhancements.clearSelection();
                break;
                
            case 'f':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    OrgchartEnhancements.showSearchDialog();
                }
                break;
        }
    });
};

/**
 * Setup accessibility features
 */
OrgchartEnhancements.setupAccessibilityFeatures = function() {
    const unitBoxes = document.querySelectorAll('.unit-box');
    
    unitBoxes.forEach(function(unitBox, index) {
        // Add ARIA attributes
        unitBox.setAttribute('role', 'button');
        unitBox.setAttribute('tabindex', index === 0 ? '0' : '-1');
        unitBox.setAttribute('aria-label', OrgchartEnhancements.getUnitAriaLabel(unitBox));
        
        // Add focus handlers
        unitBox.addEventListener('focus', function() {
            this.classList.add('unit-focused');
            OrgchartEnhancements.announceUnit(this);
        });
        
        unitBox.addEventListener('blur', function() {
            this.classList.remove('unit-focused');
        });
    });
    
    // Add live region for announcements
    const liveRegion = document.createElement('div');
    liveRegion.id = 'orgchart-announcements';
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'visually-hidden';
    document.body.appendChild(liveRegion);
};

/**
 * Setup animations
 */
OrgchartEnhancements.setupAnimations = function() {
    // Intersection Observer for unit animations
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('unit-visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '50px'
    });
    
    const unitBoxes = document.querySelectorAll('.unit-box');
    unitBoxes.forEach(function(unitBox) {
        observer.observe(unitBox);
    });
};

/**
 * Highlight connected units
 */
OrgchartEnhancements.highlightConnectedUnits = function(unitId) {
    const treeNode = document.querySelector(`[data-unit-id="${unitId}"]`);
    if (!treeNode) return;
    
    // Highlight parent
    const parentNode = treeNode.closest('.children-container')?.parentElement;
    if (parentNode && parentNode.classList.contains('tree-node')) {
        parentNode.querySelector('.unit-box')?.classList.add('unit-connected');
    }
    
    // Highlight children
    const childrenNodes = treeNode.querySelectorAll('.tree-node');
    childrenNodes.forEach(function(childNode) {
        if (childNode !== treeNode) {
            childNode.querySelector('.unit-box')?.classList.add('unit-connected');
        }
    });
};

/**
 * Clear highlights
 */
OrgchartEnhancements.clearHighlights = function() {
    const highlightedUnits = document.querySelectorAll('.unit-connected');
    highlightedUnits.forEach(function(unit) {
        unit.classList.remove('unit-connected');
    });
};

/**
 * Select unit
 */
OrgchartEnhancements.selectUnit = function(unitBox) {
    // Clear previous selection
    const previousSelected = document.querySelector('.unit-selected');
    if (previousSelected) {
        previousSelected.classList.remove('unit-selected');
    }
    
    // Select new unit
    unitBox.classList.add('unit-selected');
    unitBox.focus();
    
    // Update tabindex
    const allUnits = document.querySelectorAll('.unit-box');
    allUnits.forEach(function(unit) {
        unit.setAttribute('tabindex', unit === unitBox ? '0' : '-1');
    });
    
    // Announce selection
    OrgchartEnhancements.announceUnit(unitBox);
};

/**
 * Select person
 */
OrgchartEnhancements.selectPerson = function(personItem) {
    // Clear previous selection
    const previousSelected = document.querySelector('.person-selected');
    if (previousSelected) {
        previousSelected.classList.remove('person-selected');
    }
    
    // Select new person
    personItem.classList.add('person-selected');
    
    // Show person details
    OrgchartEnhancements.showPersonDetails(personItem);
};

/**
 * Show person tooltip
 */
OrgchartEnhancements.showPersonTooltip = function(personItem) {
    const personName = personItem.querySelector('.person-name')?.textContent;
    const personRole = personItem.querySelector('.person-role')?.textContent;
    
    if (!personName) return;
    
    // Create tooltip
    const tooltip = document.createElement('div');
    tooltip.id = 'person-tooltip';
    tooltip.className = 'person-tooltip';
    tooltip.innerHTML = `
        <div class="tooltip-content">
            <strong>${personName}</strong>
            ${personRole ? `<br><small>${personRole}</small>` : ''}
        </div>
    `;
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = personItem.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
    
    // Show tooltip
    setTimeout(() => {
        tooltip.classList.add('show');
    }, 100);
};

/**
 * Hide person tooltip
 */
OrgchartEnhancements.hidePersonTooltip = function() {
    const tooltip = document.getElementById('person-tooltip');
    if (tooltip) {
        tooltip.classList.remove('show');
        setTimeout(() => {
            tooltip.remove();
        }, 200);
    }
};

/**
 * Get unit ARIA label
 */
OrgchartEnhancements.getUnitAriaLabel = function(unitBox) {
    const unitName = unitBox.querySelector('.unit-name')?.textContent || 'Unità senza nome';
    const unitType = unitBox.classList.contains('unit-function') ? 'Funzione' : 'Unità Organizzativa';
    const personCount = unitBox.querySelector('.unit-stat-badge.people')?.textContent?.replace(/\D/g, '') || '0';
    
    return `${unitType}: ${unitName}, ${personCount} persone`;
};

/**
 * Announce unit for screen readers
 */
OrgchartEnhancements.announceUnit = function(unitBox) {
    const liveRegion = document.getElementById('orgchart-announcements');
    if (liveRegion) {
        liveRegion.textContent = OrgchartEnhancements.getUnitAriaLabel(unitBox);
    }
};

/**
 * Navigation functions
 */
OrgchartEnhancements.navigateUp = function() {
    const selected = document.querySelector('.unit-selected') || document.querySelector('.unit-box');
    if (!selected) return;
    
    const currentNode = selected.closest('.tree-node');
    const parentContainer = currentNode.closest('.children-container');
    if (parentContainer) {
        const parentNode = parentContainer.parentElement;
        if (parentNode && parentNode.classList.contains('tree-node')) {
            const parentUnit = parentNode.querySelector('.unit-box');
            if (parentUnit) {
                OrgchartEnhancements.selectUnit(parentUnit);
            }
        }
    }
};

OrgchartEnhancements.navigateDown = function() {
    const selected = document.querySelector('.unit-selected') || document.querySelector('.unit-box');
    if (!selected) return;
    
    const currentNode = selected.closest('.tree-node');
    const childrenContainer = currentNode.querySelector('.children-container');
    if (childrenContainer) {
        const firstChild = childrenContainer.querySelector('.tree-node .unit-box');
        if (firstChild) {
            OrgchartEnhancements.selectUnit(firstChild);
        }
    }
};

OrgchartEnhancements.navigateLeft = function() {
    const selected = document.querySelector('.unit-selected') || document.querySelector('.unit-box');
    if (!selected) return;
    
    const currentNode = selected.closest('.tree-node');
    const parentContainer = currentNode.closest('.children-container');
    if (parentContainer) {
        const siblings = Array.from(parentContainer.children);
        const currentIndex = siblings.findIndex(sibling => sibling.contains(currentNode));
        if (currentIndex > 0) {
            const prevSibling = siblings[currentIndex - 1];
            const prevUnit = prevSibling.querySelector('.unit-box');
            if (prevUnit) {
                OrgchartEnhancements.selectUnit(prevUnit);
            }
        }
    }
};

OrgchartEnhancements.navigateRight = function() {
    const selected = document.querySelector('.unit-selected') || document.querySelector('.unit-box');
    if (!selected) return;
    
    const currentNode = selected.closest('.tree-node');
    const parentContainer = currentNode.closest('.children-container');
    if (parentContainer) {
        const siblings = Array.from(parentContainer.children);
        const currentIndex = siblings.findIndex(sibling => sibling.contains(currentNode));
        if (currentIndex < siblings.length - 1) {
            const nextSibling = siblings[currentIndex + 1];
            const nextUnit = nextSibling.querySelector('.unit-box');
            if (nextUnit) {
                OrgchartEnhancements.selectUnit(nextUnit);
            }
        }
    }
};

/**
 * Clear selection
 */
OrgchartEnhancements.clearSelection = function() {
    const selected = document.querySelector('.unit-selected');
    if (selected) {
        selected.classList.remove('unit-selected');
        selected.blur();
    }
    
    const selectedPerson = document.querySelector('.person-selected');
    if (selectedPerson) {
        selectedPerson.classList.remove('person-selected');
    }
    
    OrgchartEnhancements.clearHighlights();
};

/**
 * Show search dialog
 */
OrgchartEnhancements.showSearchDialog = function() {
    // Create search modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'orgchart-search-modal';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Cerca nell'Organigramma</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <input type="text" class="form-control" id="orgchart-search-input" placeholder="Cerca unità o persone...">
                    <div id="search-results" class="mt-3"></div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Focus search input
    modal.addEventListener('shown.bs.modal', function() {
        document.getElementById('orgchart-search-input').focus();
    });
    
    // Setup search functionality
    const searchInput = document.getElementById('orgchart-search-input');
    searchInput.addEventListener('input', OrgchartEnhancements.performSearch);
    
    // Cleanup on hide
    modal.addEventListener('hidden.bs.modal', function() {
        modal.remove();
    });
};

/**
 * Perform search
 */
OrgchartEnhancements.performSearch = function(e) {
    const query = e.target.value.toLowerCase().trim();
    const resultsContainer = document.getElementById('search-results');
    
    if (query.length < 2) {
        resultsContainer.innerHTML = '';
        return;
    }
    
    const results = [];
    
    // Search units
    const unitBoxes = document.querySelectorAll('.unit-box');
    unitBoxes.forEach(function(unitBox) {
        const unitName = unitBox.querySelector('.unit-name')?.textContent.toLowerCase();
        const unitShortName = unitBox.querySelector('.unit-short-name')?.textContent.toLowerCase();
        
        if (unitName?.includes(query) || unitShortName?.includes(query)) {
            const unitId = unitBox.closest('.tree-node').dataset.unitId;
            results.push({
                type: 'unit',
                name: unitBox.querySelector('.unit-name')?.textContent,
                shortName: unitBox.querySelector('.unit-short-name')?.textContent,
                unitType: unitBox.classList.contains('unit-function') ? 'Funzione' : 'Unità Org.',
                element: unitBox,
                id: unitId
            });
        }
    });
    
    // Search persons
    const personItems = document.querySelectorAll('.person-item');
    personItems.forEach(function(personItem) {
        const personName = personItem.querySelector('.person-name')?.textContent.toLowerCase();
        const personRole = personItem.querySelector('.person-role')?.textContent.toLowerCase();
        
        if (personName?.includes(query) || personRole?.includes(query)) {
            results.push({
                type: 'person',
                name: personItem.querySelector('.person-name')?.textContent,
                role: personItem.querySelector('.person-role')?.textContent,
                element: personItem
            });
        }
    });
    
    // Display results
    if (results.length === 0) {
        resultsContainer.innerHTML = '<p class="text-muted">Nessun risultato trovato</p>';
    } else {
        resultsContainer.innerHTML = results.map(result => {
            if (result.type === 'unit') {
                return `
                    <div class="search-result-item" onclick="OrgchartEnhancements.selectSearchResult('${result.id}', 'unit')">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-${result.unitType === 'Funzione' ? 'building' : 'diagram-2'} me-2"></i>
                            <div>
                                <strong>${result.name}</strong>
                                ${result.shortName ? `<small class="text-muted ms-2">(${result.shortName})</small>` : ''}
                                <br><small class="text-muted">${result.unitType}</small>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                return `
                    <div class="search-result-item" onclick="OrgchartEnhancements.selectSearchResult('${result.name}', 'person')">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-person me-2"></i>
                            <div>
                                <strong>${result.name}</strong>
                                <br><small class="text-muted">${result.role}</small>
                            </div>
                        </div>
                    </div>
                `;
            }
        }).join('');
    }
};

/**
 * Select search result
 */
OrgchartEnhancements.selectSearchResult = function(id, type) {
    // Close modal
    const modal = document.getElementById('orgchart-search-modal');
    const bsModal = bootstrap.Modal.getInstance(modal);
    bsModal.hide();
    
    if (type === 'unit') {
        const unitBox = document.querySelector(`[data-unit-id="${id}"] .unit-box`);
        if (unitBox) {
            OrgchartEnhancements.selectUnit(unitBox);
            unitBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    } else {
        const personItem = Array.from(document.querySelectorAll('.person-name'))
            .find(el => el.textContent === id)?.closest('.person-item');
        if (personItem) {
            OrgchartEnhancements.selectPerson(personItem);
            personItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    OrgchartEnhancements.init();
});

// Export for global use
window.OrgchartEnhancements = OrgchartEnhancements;