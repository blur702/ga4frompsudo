/**
 * Main JavaScript file for GA4 Dashboard
 */

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    setupFormHandlers();
    setupFlashMessages();
    setupMobileMenu();
});

/**
 * Initialize Chart.js charts
 */
function initializeCharts() {
    // Find all chart containers
    const chartContainers = document.querySelectorAll('.chart-container');
    
    chartContainers.forEach(container => {
        const canvas = container.querySelector('canvas');
        if (!canvas) return;
        
        const chartType = container.dataset.chartType || 'line';
        const chartData = JSON.parse(container.dataset.chartData || '{}');
        const chartOptions = JSON.parse(container.dataset.chartOptions || '{}');
        
        // Set default options based on chart type
        const defaultOptions = getDefaultChartOptions(chartType);
        const mergedOptions = { ...defaultOptions, ...chartOptions };
        
        // Create chart
        new Chart(canvas, {
            type: chartType,
            data: chartData,
            options: mergedOptions
        });
    });
}

/**
 * Get default chart options based on chart type
 */
function getDefaultChartOptions(chartType) {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        }
    };
    
    switch (chartType) {
        case 'line':
            return {
                ...commonOptions,
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            };
            
        case 'bar':
            return {
                ...commonOptions,
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            };
            
        case 'pie':
        case 'doughnut':
            return {
                ...commonOptions,
                cutout: chartType === 'doughnut' ? '70%' : 0,
                plugins: {
                    ...commonOptions.plugins,
                    legend: {
                        position: 'right'
                    }
                }
            };
            
        default:
            return commonOptions;
    }
}

/**
 * Setup form handlers
 */
function setupFormHandlers() {
    // Date range picker initialization
    const dateRangePickers = document.querySelectorAll('.date-range-picker');
    dateRangePickers.forEach(picker => {
        if (typeof flatpickr !== 'undefined') {
            flatpickr(picker, {
                mode: 'range',
                dateFormat: 'Y-m-d',
                defaultDate: [picker.dataset.startDate, picker.dataset.endDate]
            });
        }
    });
    
    // Multi-select initialization
    const multiSelects = document.querySelectorAll('.multi-select');
    multiSelects.forEach(select => {
        if (typeof Choices !== 'undefined') {
            new Choices(select, {
                removeItemButton: true,
                searchEnabled: true,
                searchPlaceholderValue: 'Search...',
                placeholderValue: 'Select options',
                itemSelectText: 'Press to select'
            });
        }
    });
    
    // Form validation
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(form)) {
                event.preventDefault();
            }
        });
    });
}

/**
 * Validate form inputs
 */
function validateForm(form) {
    let isValid = true;
    
    // Find all required inputs
    const requiredInputs = form.querySelectorAll('[required]');
    
    requiredInputs.forEach(input => {
        // Clear previous error
        const errorElement = input.parentNode.querySelector('.error-message');
        if (errorElement) {
            errorElement.remove();
        }
        
        // Check if input is empty
        if (!input.value.trim()) {
            isValid = false;
            
            // Add error message
            const error = document.createElement('div');
            error.className = 'error-message text-red-500 text-sm mt-1';
            error.textContent = 'This field is required';
            input.parentNode.appendChild(error);
            
            // Add error styling
            input.classList.add('border-red-500');
        } else {
            input.classList.remove('border-red-500');
        }
    });
    
    return isValid;
}

/**
 * Setup flash messages
 */
function setupFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(message => {
        // Add close button functionality
        const closeButton = message.querySelector('svg[role="button"]');
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                message.remove();
            });
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
}

/**
 * Setup mobile menu toggle
 */
function setupMobileMenu() {
    const menuButton = document.querySelector('#mobile-menu-button');
    const mobileMenu = document.querySelector('#mobile-menu');
    
    if (menuButton && mobileMenu) {
        menuButton.addEventListener('click', function() {
            const expanded = menuButton.getAttribute('aria-expanded') === 'true';
            menuButton.setAttribute('aria-expanded', !expanded);
            mobileMenu.classList.toggle('hidden');
        });
    }
}

/**
 * Format number with thousands separator
 */
function formatNumber(number, decimalPlaces = 0) {
    if (number === null || number === undefined) {
        return '0';
    }
    
    try {
        if (decimalPlaces > 0) {
            return number.toLocaleString('en-US', {
                minimumFractionDigits: decimalPlaces,
                maximumFractionDigits: decimalPlaces
            });
        }
        return number.toLocaleString('en-US');
    } catch (e) {
        return number.toString();
    }
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Create and show a loading indicator
 */
function showLoading(container, message = 'Loading...') {
    const loadingElement = document.createElement('div');
    loadingElement.className = 'loading-container flex flex-col items-center justify-center p-8';
    loadingElement.innerHTML = `
        <div class="loading-indicator mb-2"></div>
        <p class="text-gray-600">${message}</p>
    `;
    
    container.innerHTML = '';
    container.appendChild(loadingElement);
}

/**
 * Remove loading indicator
 */
function hideLoading(container) {
    const loadingElement = container.querySelector('.loading-container');
    if (loadingElement) {
        loadingElement.remove();
    }
}

/**
 * Toggle property exclusion from global reports
 */
function togglePropertyExclusion(propertyId, button) {
    fetch(`/properties/${propertyId}/toggle_exclude`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update button text and class
            if (data.excluded) {
                button.textContent = 'Include';
                button.classList.remove('bg-red-600', 'hover:bg-red-700');
                button.classList.add('bg-green-600', 'hover:bg-green-700');
            } else {
                button.textContent = 'Exclude';
                button.classList.remove('bg-green-600', 'hover:bg-green-700');
                button.classList.add('bg-red-600', 'hover:bg-red-700');
            }
        }
    })
    .catch(error => {
        console.error('Error toggling property exclusion:', error);
    });
}