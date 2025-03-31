// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Dark mode toggle
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            
            // Save preference via API if user is logged in
            if (isUserLoggedIn()) {
                const isDarkMode = document.body.classList.contains('dark-mode');
                updateUserSettings({ theme: isDarkMode ? 'dark' : 'light' });
            }
        });
    }
    
    // Initialize Socket.IO if available
    initializeSocketIO();
});

// Check if user is logged in
function isUserLoggedIn() {
    // This is a simple check - you might want to use a more robust method
    return document.querySelector('.navbar .dropdown-toggle[id="userDropdown"]') !== null;
}

// Update user settings
function updateUserSettings(settings) {
    fetch('/api/settings', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Settings updated successfully:', data);
    })
    .catch(error => {
        console.error('Error updating settings:', error);
        showToast('Error', 'Failed to update settings. Please try again.', 'danger');
    });
}

// Initialize Socket.IO
function initializeSocketIO() {
    // Check if Socket.IO is loaded
    if (typeof io !== 'undefined') {
        // Connect to the Socket.IO server
        const socket = io();
        
        // Store socket in window for global access
        window.cryptoSocket = socket;
        
        // Connection event handlers
        socket.on('connect', () => {
            console.log('Connected to WebSocket server');
        });
        
        socket.on('disconnect', () => {
            console.log('Disconnected from WebSocket server');
        });
        
        // Set up price update handlers
        socket.on('price_update', (data) => {
            handlePriceUpdate(data);
        });
    }
}

function handlePriceUpdate(data) {
    const symbol = data.symbol;
    const price = parseFloat(data.price);
    
    // Update price displays for this symbol
    const priceElements = document.querySelectorAll(`.crypto-price[data-symbol="${symbol}"]`);
    priceElements.forEach(element => {
        // Store previous price for color animation
        const prevPrice = parseFloat(element.dataset.price || '0');
        
        // Update price
        element.textContent = formatCurrency(price);
        element.dataset.price = price;
        
        // Add color animation based on price change
        if (price > prevPrice) {
            element.classList.remove('price-down');
            element.classList.add('price-up');
        } else if (price < prevPrice) {
            element.classList.remove('price-up');
            element.classList.add('price-down');
        }
        
        // Remove animation classes after animation completes
        setTimeout(() => {
            element.classList.remove('price-up', 'price-down');
        }, 1000);
    });
    
    // Update charts if available
    const priceChart = window.priceChart;
    if (priceChart && priceChart.symbol === symbol) {
        // Add new price point to chart
        const now = new Date();
        priceChart.data.labels.push(formatTime(now));
        priceChart.data.datasets[0].data.push(price);
        
        // Remove oldest data point if we have more than 100
        if (priceChart.data.labels.length > 100) {
            priceChart.data.labels.shift();
            priceChart.data.datasets[0].data.shift();
        }
        
        priceChart.update();
    }
}


// Subscribe to price updates for a symbol
function subscribeToPriceUpdates(symbol) {
    if (window.cryptoSocket) {
        window.cryptoSocket.emit('subscribe_price', { symbol: symbol });
    }
}

// Unsubscribe from price updates for a symbol
function unsubscribeFromPriceUpdates(symbol) {
    if (window.cryptoSocket) {
        window.cryptoSocket.emit('unsubscribe_price', { symbol: symbol });
    }
}

// Format currency values
function formatCurrency(value) {
    if (value >= 1000) {
        return '$' + value.toFixed(2);
    } else if (value >= 1) {
        return '$' + value.toFixed(4);
    } else if (value >= 0.01) {
        return '$' + value.toFixed(6);
    } else {
        return '$' + value.toFixed(8);
    }
}

// Format time for charts
function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Show toast notification
function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast bg-${type} text-white`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.setAttribute('id', toastId);
    
    toast.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">${title}</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();
    
    // Remove from DOM after hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}
