// Global JavaScript functions and utilities

// Format currency with appropriate precision
function formatCurrency(value, currency = 'USD') {
    const num = parseFloat(value);
    
    if (isNaN(num)) {
        return 'N/A';
    }
    
    // Format based on magnitude
    let options;
    if (num >= 1000) {
        options = { style: 'currency', currency, minimumFractionDigits: 2, maximumFractionDigits: 2 };
    } else if (num >= 1) {
        options = { style: 'currency', currency, minimumFractionDigits: 2, maximumFractionDigits: 4 };
    } else if (num >= 0.01) {
        options = { style: 'currency', currency, minimumFractionDigits: 4, maximumFractionDigits: 6 };
    } else {
        options = { style: 'currency', currency, minimumFractionDigits: 6, maximumFractionDigits: 8 };
    }
    
    return new Intl.NumberFormat('en-US', options).format(num);
}

// Format percentage values
function formatPercent(value) {
    const num = parseFloat(value);
    
    if (isNaN(num)) {
        return 'N/A';
    }
    
    return new Intl.NumberFormat('en-US', { 
        style: 'percent', 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2,
        signDisplay: 'exceptZero'
    }).format(num / 100);
}

// Format large numbers with K, M, B suffixes
function formatNumber(value) {
    const num = parseFloat(value);
    
    if (isNaN(num)) {
        return 'N/A';
    }
    
    if (num >= 1000000000) {
        return (num / 1000000000).toFixed(2) + 'B';
    } else if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(2) + 'K';
    } else {
        return num.toFixed(2);
    }
}

// Detect price direction for styling
function getPriceChangeClass(change) {
    const num = parseFloat(change);
    
    if (isNaN(num)) {
        return '';
    }
    
    return num > 0 ? 'price-up' : num < 0 ? 'price-down' : '';
}

// Handle API errors
function handleApiError(error, elementId) {
    console.error('API Error:', error);
    
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">Error!</h4>
                <p>There was a problem loading data: ${error.message}</p>
                <hr>
                <p class="mb-0">Please try again later or contact support if the problem persists.</p>
            </div>
        `;
    }
}

// Add event listener for dark mode toggle if it exists
document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    
    if (darkModeToggle) {
        // Check for saved theme preference or use device preference
        const savedTheme = localStorage.getItem('theme') || 
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
            
        // Apply saved theme
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-mode');
            darkModeToggle.checked = true;
        }
        
        // Add toggle event listener
        darkModeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark');
            } else {
                document.body.classList.remove('dark-mode');
                localStorage.setItem('theme', 'light');
            }
        });
    }
});
