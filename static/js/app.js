// static/js/app.js
/**
 * Crypto Market Dashboard - Main JavaScript
 * Handles UI interactions, WebSocket connections, and API calls
 */

// Global state
const CryptoApp = {
    // WebSocket connection
    socket: null,
    
    // User preferences
    preferences: {
        darkMode: localStorage.getItem('darkMode') === 'true',
        currency: 'USD'
    },
    
    // Active data
    activeSymbol: 'BTCUSDT',
    activeInterval: '1d',
    
    // Chart instances
    charts: {},
    
    // Initialize the application
    init() {
        // Apply theme based on saved preference
        this.applyTheme();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize Socket.IO connection
        this.initSocketConnection();
        
        // Load page-specific content
        this.loadPageContent();
    },
    
    // Apply dark/light theme
    applyTheme() {
        document.body.classList.toggle('dark-mode', this.preferences.darkMode);
        
        // Update charts if they exist
        for (const chartId in this.charts) {
            this.updateChartTheme(this.charts[chartId]);
        }
    },
    
    // Set up global event listeners
    setupEventListeners() {
        // Dark mode toggle
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) {
            darkModeToggle.addEventListener('click', () => {
                this.preferences.darkMode = !this.preferences.darkMode;
                localStorage.setItem('darkMode', this.preferences.darkMode);
                this.applyTheme();
                
                // Update server-side preference if user is logged in
                if (this.isUserLoggedIn()) {
                    this.updateUserSettings({ theme: this.preferences.darkMode ? 'dark' : 'light' });
                }
            });
        }
        
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const searchButton = document.getElementById('searchButton');
        
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => {
                this.handleSearch();
            }, 300));
        }
        
        if (searchButton) {
            searchButton.addEventListener('click', () => {
                this.handleSearch();
            });
        }
        
        // Symbol selector
        const symbolSelect = document.getElementById('symbol-select');
        if (symbolSelect) {
            symbolSelect.addEventListener('change', () => {
                this.activeSymbol = symbolSelect.value;
                this.loadChartData();
                
                // Update URL without reloading page
                const url = new URL(window.location);
                url.searchParams.set('symbol', this.activeSymbol);
                window.history.pushState({}, '', url);
            });
        }
        
        // Interval selector
        const intervalSelect = document.getElementById('interval-select');
        if (intervalSelect) {
            intervalSelect.addEventListener('change', () => {
                this.activeInterval = intervalSelect.value;
                this.loadChartData();
                
                // Update URL without reloading
                const url = new URL(window.location);
                url.searchParams.set('interval', this.activeInterval);
                window.history.pushState({}, '', url);
            });
        }
        
        // Portfolio actions
        this.setupPortfolioListeners();
        
        // Alert actions
        this.setupAlertListeners();
        
        // Watchlist actions
        this.setupWatchlistListeners();
    },
    
    // Initialize Socket.IO connection
    initSocketConnection() {
        // Check if Socket.IO is available
        if (typeof io !== 'undefined') {
            this.socket = io.connect(window.location.origin, {
                transports: ['websocket']
            });
            
            // Connection events
            this.socket.on('connect', () => {
                console.log('Connected to WebSocket server');
                
                // Subscribe to current symbol if on detail page
                if (document.getElementById('priceChart')) {
                    this.subscribeToSymbol(this.activeSymbol);
                }
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from WebSocket server');
            });
            
            // Price update handler
            this.socket.on('price_update', (data) => {
                this.handlePriceUpdate(data);
            });
            
            // Alert notification handler
            this.socket.on('alert_triggered', (alert) => {
                this.showAlertNotification(alert);
            });
        }
    },
    
    // Subscribe to price updates for a symbol
    subscribeToSymbol(symbol) {
        if (this.socket) {
            this.socket.emit('subscribe_price', { symbol });
            console.log(`Subscribed to ${symbol} price updates`);
        }
    },
    
    // Unsubscribe from price updates for a symbol
    unsubscribeFromSymbol(symbol) {
        if (this.socket) {
            this.socket.emit('unsubscribe_price', { symbol });
            console.log(`Unsubscribed from ${symbol} price updates`);
        }
    },
    
    // Load page-specific content
    loadPageContent() {
        // Dashboard page
        if (document.getElementById('crypto-list')) {
            this.loadCryptoPrices();
        }
        
        // Detail page
        if (document.getElementById('priceChart')) {
            this.initializePriceChart();
            this.loadChartData();
            this.loadMarketDepth();
            this.loadTechnicalIndicators();
        }
        
        // Portfolio page
        if (document.getElementById('portfolio-container')) {
            this.loadPortfolio();
        }
        
        // Alerts page
        if (document.getElementById('alerts-container')) {
            this.loadAlerts();
        }
        
        // Watchlist page
        if (document.getElementById('watchlist-container')) {
            this.loadWatchlists();
        }
    },
    
    // Load cryptocurrency prices for dashboard
    loadCryptoPrices() {
        const cryptoList = document.getElementById('crypto-list');
        const loadingIndicator = document.getElementById('loading-indicator');
        const errorMessage = document.getElementById('error-message');
        
        if (!cryptoList) return;
        
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        if (errorMessage) errorMessage.style.display = 'none';
        
        fetch('/api/prices')
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                this.renderCryptoList(data);
                if (loadingIndicator) loadingIndicator.style.display = 'none';
            })
            .catch(error => {
                console.error('Error loading prices:', error);
                if (errorMessage) errorMessage.style.display = 'block';
                if (loadingIndicator) loadingIndicator.style.display = 'none';
            });
    },
    
    // Render cryptocurrency list
    renderCryptoList(data) {
        const cryptoList = document.getElementById('crypto-list');
        const searchInput = document.getElementById('searchInput');
        const filterSelect = document.getElementById('filterSelect');
        
        if (!cryptoList) return;
        
        // Apply filters if they exist
        let filteredData = data;
        
        if (searchInput && searchInput.value) {
            const searchTerm = searchInput.value.toLowerCase();
            filteredData = filteredData.filter(crypto => 
                crypto.symbol.toLowerCase().includes(searchTerm)
            );
        }
        
        if (filterSelect && filterSelect.value !== 'all') {
            const filter = filterSelect.value;
            if (filter === 'usdt') {
                filteredData = filteredData.filter(crypto => crypto.symbol.endsWith('USDT'));
            } else if (filter === 'btc') {
                filteredData = filteredData.filter(crypto => crypto.symbol.endsWith('BTC'));
            }
        }
        
        // Clear existing content
        cryptoList.innerHTML = '';
        
        // Show "no results" message if filtered data is empty
        if (filteredData.length === 0) {
            cryptoList.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info">No cryptocurrencies match your search criteria.</div>
                </div>
            `;
            return;
        }
        
        // Create cards for each cryptocurrency
        filteredData.forEach(crypto => {
            const price = parseFloat(crypto.price);
            const formattedPrice = this.formatPrice(price);
            const baseSymbol = crypto.symbol.replace(/USDT$|BTC$/, '');
            
            const card = document.createElement('div');
            card.className = 'col-md-3 mb-4';
            card.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">${baseSymbol}</h5>
                        <p class="card-text crypto-price" data-symbol="${crypto.symbol}" data-price="${price}">
                            Price: ${formattedPrice}
                        </p>
                    </div>
                    <div class="card-footer bg-transparent border-top-0">
                        <a href="/crypto/${crypto.symbol}" class="btn btn-primary btn-sm stretched-link">View Details</a>
                    </div>
                </div>
            `;
            
            cryptoList.appendChild(card);
        });
    },
    
    // Initialize price chart
    initializePriceChart() {
        const chartCanvas = document.getElementById('priceChart');
        if (!chartCanvas) return;
        
        // Get Chart.js context
        const ctx = chartCanvas.getContext('2d');
        
        // Create chart instance
        this.charts.price = new Chart(ctx, {
            type: 'candlestick',
            data: {
                datasets: [{
                    label: this.activeSymbol,
                    data: []
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        },
                        adapters: {
                            date: {
                                locale: 'en-US'
                            }
                        }
                    },
                    y: {
                        position: 'right'
                    }
                },
                plugins: {
                    legend: {
                        display: true
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                animation: {
                    duration: 0 // Disable animation for better performance
                }
            }
        });
        
        // Apply theme to chart
        this.updateChartTheme(this.charts.price);
    },
    
    // Load chart data
    loadChartData() {
        if (!this.charts.price) return;
        
        const loadingElement = document.getElementById('chart-loading');
        const errorElement = document.getElementById('chart-error');
        
        if (loadingElement) loadingElement.style.display = 'block';
        if (errorElement) errorElement.style.display = 'none';
        
        fetch(`/api/klines/${this.activeSymbol}?interval=${this.activeInterval}`)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                // Format data for chart
                const chartData = data.map(candle => ({
                    x: new Date(candle.time),
                    o: candle.open,
                    h: candle.high,
                    l: candle.low,
                    c: candle.close
                }));
                
                // Update chart
                this.charts.price.data.datasets[0].data = chartData;
                this.charts.price.data.datasets[0].label = this.activeSymbol;
                this.charts.price.update();
                
                if (loadingElement) loadingElement.style.display = 'none';
            })
            .catch(error => {
                console.error('Error loading chart data:', error);
                if (errorElement) {
                    errorElement.style.display = 'block';
                    errorElement.textContent = 'Error loading chart data. Please try again later.';
                }
                if (loadingElement) loadingElement.style.display = 'none';
            });
    },
    
    // Handle price updates from WebSocket
    handlePriceUpdate(data) {
        const symbol = data.symbol;
        const price = parseFloat(data.price);
        
        // Update price displays
        document.querySelectorAll(`.crypto-price[data-symbol="${symbol}"]`).forEach(element => {
            const oldPrice = parseFloat(element.dataset.price || '0');
            
            // Update price
            element.textContent = `Price: ${this.formatPrice(price)}`;
            element.dataset.price = price;
            
            // Add animation class based on price change
            if (price > oldPrice) {
                element.classList.remove('price-down');
                element.classList.add('price-up');
            } else if (price < oldPrice) {
                element.classList.remove('price-up');
                element.classList.add('price-down');
            }
            
            // Remove animation classes after animation completes
            setTimeout(() => {
                element.classList.remove('price-up', 'price-down');
            }, 1000);
        });
        
        // Update current price on detail page
        const currentPriceElement = document.getElementById('current-price');
        if (currentPriceElement && symbol === this.activeSymbol) {
            currentPriceElement.textContent = this.formatPrice(price);
        }
    },
    
    // Setup portfolio-related event listeners
    setupPortfolioListeners() {
        // Add asset form
        const addAssetForm = document.getElementById('add-asset-form');
        if (addAssetForm) {
            addAssetForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addPortfolioAsset();
            });
        }
        
        // Edit asset buttons (delegated event)
        document.addEventListener('click', (e) => {
            if (e.target.closest('.edit-asset')) {
                const button = e.target.closest('.edit-asset');
                const assetId = button.dataset.assetId;
                this.openEditAssetModal(assetId);
            }
        });
        
        // Delete asset buttons (delegated event)
        document.addEventListener('click', (e) => {
            if (e.target.closest('.delete-asset')) {
                const button = e.target.closest('.delete-asset');
                const assetId = button.dataset.assetId;
                this.confirmDeleteAsset(assetId);
            }
        });
    },
    
    // Setup alert-related event listeners
    setupAlertListeners() {
        // Add alert form
        const addAlertForm = document.getElementById('add-alert-form');
        if (addAlertForm) {
            addAlertForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addAlert();
            });
        }
        
        // Alert action buttons (delegated events)
        document.addEventListener('click', (e) => {
            if (e.target.closest('.dismiss-alert')) {
                const button = e.target.closest('.dismiss-alert');
                this.updateAlertStatus(button.dataset.alertId, 'dismissed');
            } else if (e.target.closest('.reactivate-alert')) {
                const button = e.target.closest('.reactivate-alert');
                this.updateAlertStatus(button.dataset.alertId, 'active');
            } else if (e.target.closest('.delete-alert')) {
                const button = e.target.closest('.delete-alert');
                this.confirmDeleteAlert(button.dataset.alertId);
            }
        });
    },
    
    // Setup watchlist-related event listeners
    setupWatchlistListeners() {
        // Add to watchlist form
        const addToWatchlistForm = document.getElementById('add-to-watchlist-form');
        if (addToWatchlistForm) {
            addToWatchlistForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addToWatchlist();
            });
        }
        
        // Create watchlist form
        const createWatchlistForm = document.getElementById('create-watchlist-form');
        if (createWatchlistForm) {
            createWatchlistForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createWatchlist();
            });
        }
        
        // Watchlist selector
        const watchlistSelect = document.getElementById('watchlist-select');
        if (watchlistSelect) {
            watchlistSelect.addEventListener('change', () => {
                this.loadWatchlistSymbols(watchlistSelect.value);
            });
        }
        
        // Remove from watchlist buttons (delegated event)
        document.addEventListener('click', (e) => {
            if (e.target.closest('.remove-symbol')) {
                const button = e.target.closest('.remove-symbol');
                const symbol = button.dataset.symbol;
                const watchlistId = document.getElementById('watchlist-select').value;
                this.removeFromWatchlist(watchlistId, symbol);
            }
        });
    },
    
    // Format price based on magnitude
    formatPrice(price) {
        if (isNaN(price)) return '\$0.00';
        
        if (price >= 1000) {
            return `$${price.toFixed(2)}`;
        } else if (price >= 1) {
            return `$${price.toFixed(4)}`;
        } else if (price >= 0.01) {
            return `$${price.toFixed(6)}`;
        } else {
            return `$${price.toFixed(8)}`;
        }
    },
    
    // Update chart theme based on dark mode
    updateChartTheme(chart) {
        if (!chart) return;
        
        const isDark = this.preferences.darkMode;
        const textColor = isDark ? '#f5f5f5' : '#666';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
        
        chart.options.scales.x.ticks = { 
            color: textColor
        };
        chart.options.scales.y.ticks = { 
            color: textColor 
        };
        chart.options.scales.x.grid = { 
            color: gridColor 
        };
        chart.options.scales.y.grid = { 
            color: gridColor 
        };
        
        chart.update();
    },
    
    // Check if user is logged in
    isUserLoggedIn() {
        return document.querySelector('.navbar .dropdown-toggle[id="userDropdown"]') !== null;
    },
    
    // Update user settings
    updateUserSettings(settings) {
        fetch('/api/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            console.log('Settings updated successfully:', data);
        })
        .catch(error => {
            console.error('Error updating settings:', error);
            this.showToast('Error', 'Failed to update settings. Please try again.', 'danger');
        });
    },
    
    // Handle search
    handleSearch() {
        const searchInput = document.getElementById('searchInput');
        if (!searchInput) return;
        
        // Reload crypto prices with filtering
        this.loadCryptoPrices();
    },
    
    // Load portfolio data
    loadPortfolio() {
        fetch('/api/portfolio')
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                this.renderPortfolio(data);
            })
            .catch(error => {
                console.error('Error loading portfolio:', error);
                this.showToast('Error', 'Failed to load portfolio data. Please try again.', 'danger');
            });
    },
    
    // Render portfolio data
    renderPortfolio(data) {
        const holdingsTable = document.getElementById('holdings-table-body');
        const totalValue = document.getElementById('total-value');
        const totalInvested = document.getElementById('total-invested');
        const totalProfit = document.getElementById('total-profit');
        
        if (holdingsTable) {
            holdingsTable.innerHTML = '';
            
            if (data.items && data.items.length > 0) {
                data.items.forEach(item => {
                    const row = document.createElement('tr');
                    
                    const profitLoss = item.current_value - item.invested;
                    const profitLossPercent = item.invested > 0 ? (profitLoss / item.invested * 100) : 0;
                    const profitLossClass = profitLoss >= 0 ? 'text-success' : 'text-danger';
                    
                    row.innerHTML = `
                        <td>${item.symbol}</td>
                        <td>${item.quantity.toFixed(8)}</td>
                        <td>${this.formatPrice(item.purchase_price)}</td>
                        <td>${this.formatPrice(item.current_price)}</td>
                        <td>${this.formatPrice(item.current_value)}</td>
                        <td class="${profitLossClass}">
                            ${this.formatPrice(profitLoss)} (${profitLossPercent.toFixed(2)}%)
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary edit-asset" data-asset-id="${item.id}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-asset" data-asset-id="${item.id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    `;
                    
                    holdingsTable.appendChild(row);
                });
            } else {
                holdingsTable.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center">
                            You don't have any assets in your portfolio yet.
                            <button class="btn btn-sm btn-primary ms-3" data-bs-toggle="modal" data-bs-target="#add-asset-modal">
                                Add Your First Asset
                            </button>
                        </td>
                    </tr>
                `;
            }
        }
        
        // Update summary values
        if (totalValue && data.total_current_value !== undefined) {
            totalValue.textContent = this.formatPrice(data.total_current_value);
        }
        
        if (totalInvested && data.total_invested !== undefined) {
            totalInvested.textContent = this.formatPrice(data.total_invested);
        }
        
        if (totalProfit && data.total_profit_loss !== undefined) {
            const profitClass = data.total_profit_loss >= 0 ? 'text-success' : 'text-danger';
            totalProfit.className = profitClass;
            totalProfit.textContent = `${this.formatPrice(data.total_profit_loss)} (${data.total_profit_loss_percent.toFixed(2)}%)`;
        }
    },
    
    // Add portfolio asset
    addPortfolioAsset() {
        const symbol = document.getElementById('asset-symbol').value;
        const quantity = parseFloat(document.getElementById('asset-quantity').value);
        const price = parseFloat(document.getElementById('asset-price').value);
        const date = document.getElementById('asset-date').value || new Date().toISOString().split('T')[0];
        
        fetch('/api/portfolio/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbol: symbol,
                quantity: quantity,
                purchase_price: price,
                purchase_date: date
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('add-asset-modal'));
            if (modal) modal.hide();
            
            // Reload portfolio
            this.loadPortfolio();
            
            // Show success message
            this.showToast('Success', 'Asset added to portfolio successfully', 'success');
        })
        .catch(error => {
            console.error('Error adding asset:', error);
            this.showToast('Error', 'Failed to add asset. Please try again.', 'danger');
        });
    },
    
    // Open edit asset modal
    openEditAssetModal(assetId) {
        fetch(`/api/portfolio/item/${assetId}`)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(item => {
                // Populate form fields
                document.getElementById('edit-asset-id').value = assetId;
                document.getElementById('edit-asset-symbol').value = item.symbol;
                document.getElementById('edit-asset-quantity').value = item.quantity;
                document.getElementById('edit-asset-price').value = item.purchase_price;
                
                // Format date for input field
                const date = new Date(item.purchase_date);
                const formattedDate = date.toISOString().split('T')[0];
                document.getElementById('edit-asset-date').value = formattedDate;
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('edit-asset-modal'));
                modal.show();
            })
            .catch(error => {
                console.error('Error fetching asset details:', error);
                this.showToast('Error', 'Failed to load asset details. Please try again.', 'danger');
            });
    },
    
    // Update portfolio asset
    updatePortfolioAsset() {
        const assetId = document.getElementById('edit-asset-id').value;
        const quantity = parseFloat(document.getElementById('edit-asset-quantity').value);
        const price = parseFloat(document.getElementById('edit-asset-price').value);
        
        fetch(`/api/portfolio/update/${assetId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                quantity: quantity,
                purchase_price: price
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('edit-asset-modal'));
            if (modal) modal.hide();
            
            // Reload portfolio
            this.loadPortfolio();
            
            // Show success message
            this.showToast('Success', 'Asset updated successfully', 'success');
        })
        .catch(error => {
            console.error('Error updating asset:', error);
            this.showToast('Error', 'Failed to update asset. Please try again.', 'danger');
        });
    },
    
    // Confirm delete asset
    confirmDeleteAsset(assetId) {
        if (confirm('Are you sure you want to delete this asset from your portfolio?')) {
            this.deletePortfolioAsset(assetId);
        }
    },
    
    // Delete portfolio asset
    deletePortfolioAsset(assetId) {
        fetch(`/api/portfolio/delete/${assetId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Reload portfolio
            this.loadPortfolio();
            
            // Show success message
            this.showToast('Success', 'Asset deleted successfully', 'success');
        })
        .catch(error => {
            console.error('Error deleting asset:', error);
            this.showToast('Error', 'Failed to delete asset. Please try again.', 'danger');
        });
    },
    
    // Load alerts
    loadAlerts() {
        fetch('/api/alerts')
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                this.renderAlerts(data);
            })
            .catch(error => {
                console.error('Error loading alerts:', error);
                this.showToast('Error', 'Failed to load alerts. Please try again.', 'danger');
            });
    },
    
    // Render alerts
    renderAlerts(alerts) {
        const alertsList = document.getElementById('alerts-list');
        if (!alertsList) return;
        
        alertsList.innerHTML = '';
        
        if (alerts.length === 0) {
            alertsList.innerHTML = `
                <div class="alert alert-info">
                    You don't have any price alerts set. Create one below.
                </div>
            `;
            return;
        }
        
        alerts.forEach(alert => {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            
            const statusClass = alert.triggered ? 'warning' : 'success';
            const alertTypeText = alert.alert_type === 'above' ? 'Price Above' : 'Price Below';
            
            card.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5 class="card-title">${alert.symbol} Alert</h5>
                        <span class="badge bg-${statusClass}">
                            ${alert.triggered ? 'Triggered' : 'Active'}
                        </span>
                    </div>
                    <p class="card-text">
                        <strong>Condition:</strong> ${alertTypeText} ${this.formatPrice(alert.target_price)}<br>
                        <strong>Created:</strong> ${new Date(alert.created_at).toLocaleString()}
                        ${alert.triggered ? `<br><strong>Triggered:</strong> ${new Date(alert.triggered_at).toLocaleString()}` : ''}
                    </p>
                    <div class="btn-group">
                        ${alert.triggered ? 
                            `<button class="btn btn-sm btn-outline-secondary reset-alert" data-alert-id="${alert.id}">
                                Reset
                            </button>` : ''}
                        <button class="btn btn-sm btn-outline-danger delete-alert" data-alert-id="${alert.id}">
                            Delete
                        </button>
                    </div>
                </div>
            `;
            
            alertsList.appendChild(card);
        });
    },
    
    // Add alert
    addAlert() {
        const symbol = document.getElementById('alert-symbol').value;
        const alertType = document.getElementById('alert-type').value;
        const targetPrice = parseFloat(document.getElementById('alert-price').value);
        
        fetch('/api/alerts/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbol: symbol,
                alert_type: alertType,
                target_price: targetPrice
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('add-alert-modal'));
            if (modal) modal.hide();
            
            // Reload alerts
            this.loadAlerts();
            
            // Show success message
            this.showToast('Success', 'Alert created successfully', 'success');
        })
        .catch(error => {
            console.error('Error creating alert:', error);
            this.showToast('Error', 'Failed to create alert. Please try again.', 'danger');
        });
    },
    
    // Update alert status (reset)
    updateAlertStatus(alertId, status) {
        fetch(`/api/alerts/reset/${alertId}`, {
            method: 'PUT'
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Reload alerts
            this.loadAlerts();
            
            // Show success message
            this.showToast('Success', 'Alert reset successfully', 'success');
        })
        .catch(error => {
            console.error('Error resetting alert:', error);
            this.showToast('Error', 'Failed to reset alert. Please try again.', 'danger');
        });
    },
    
    // Confirm delete alert
    confirmDeleteAlert(alertId) {
        if (confirm('Are you sure you want to delete this alert?')) {
            this.deleteAlert(alertId);
        }
    },
    
    // Delete alert
    deleteAlert(alertId) {
        fetch(`/api/alerts/delete/${alertId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Reload alerts
            this.loadAlerts();
            
            // Show success message
            this.showToast('Success', 'Alert deleted successfully', 'success');
        })
        .catch(error => {
            console.error('Error deleting alert:', error);
            this.showToast('Error', 'Failed to delete alert. Please try again.', 'danger');
        });
    },
    
    // Show alert notification
    showAlertNotification(alert) {
        // Create notification
        this.showToast(
            'Price Alert Triggered',
            `Your ${alert.symbol} alert has been triggered. Price ${alert.alert_type === 'above' ? 'rose above' : 'fell below'} ${this.formatPrice(alert.target_price)}.`,
            'warning',
            10000 // Show for 10 seconds
        );
        
        // Play notification sound if available
        const notificationSound = document.getElementById('notification-sound');
        if (notificationSound) {
            notificationSound.play().catch(e => console.log('Could not play notification sound'));
        }
        
        // Update alerts list if on alerts page
        if (document.getElementById('alerts-list')) {
            this.loadAlerts();
        }
    },
    
    // Load watchlists
    loadWatchlists() {
        fetch('/api/watchlists')
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                this.renderWatchlists(data);
            })
            .catch(error => {
                console.error('Error loading watchlists:', error);
                this.showToast('Error', 'Failed to load watchlists. Please try again.', 'danger');
            });
    },
    
    // Render watchlists
    renderWatchlists(watchlists) {
        const watchlistSelect = document.getElementById('watchlist-select');
        if (!watchlistSelect) return;
        
        // Clear existing options except the placeholder
        while (watchlistSelect.options.length > 1) {
            watchlistSelect.remove(1);
        }
        
        if (watchlists.length === 0) {
            // Show message if no watchlists
            document.getElementById('watchlist-container').innerHTML = `
                <div class="alert alert-info">
                    You don't have any watchlists yet. Create one below.
                </div>
            `;
            return;
        }
        
        // Add options for each watchlist
        watchlists.forEach(watchlist => {
            const option = document.createElement('option');
            option.value = watchlist.id;
            option.textContent = watchlist.name;
            watchlistSelect.appendChild(option);
        });
        
        // Select first watchlist and load its symbols
        if (watchlists.length > 0) {
            watchlistSelect.value = watchlists[0].id;
            this.loadWatchlistSymbols(watchlists[0].id);
        }
    },
    
    // Load watchlist symbols
    loadWatchlistSymbols(watchlistId) {
        if (!watchlistId) return;
        
        fetch(`/api/watchlists/${watchlistId}`)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                this.renderWatchlistSymbols(data);
            })
            .catch(error => {
                console.error('Error loading watchlist symbols:', error);
                this.showToast('Error', 'Failed to load watchlist. Please try again.', 'danger');
            });
    },
    
    // Render watchlist symbols
    renderWatchlistSymbols(watchlist) {
        const symbolsContainer = document.getElementById('watchlist-symbols');
        if (!symbolsContainer) return;
        
        symbolsContainer.innerHTML = '';
        
        if (!watchlist.symbols || watchlist.symbols.length === 0) {
            symbolsContainer.innerHTML = `
                <div class="alert alert-info">
                    This watchlist is empty. Add symbols below.
                </div>
            `;
            return;
        }
        
        // Create table for symbols
        const table = document.createElement('table');
        table.className = 'table table-hover';
        
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Price</th>
                    <th>24h Change</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="watchlist-symbols-body"></tbody>
        `;
        
        symbolsContainer.appendChild(table);
        
        const tbody = document.getElementById('watchlist-symbols-body');
        
        // Add each symbol to the table
        watchlist.symbols.forEach(symbol => {
            const row = document.createElement('tr');
            
            // Calculate change class
            const changeClass = symbol.price_change_24h >= 0 ? 'text-success' : 'text-danger';
            const changeIcon = symbol.price_change_24h >= 0 ? '▲' : '▼';
            
            row.innerHTML = `
                <td>
                    <a href="/crypto/${symbol.symbol}" class="text-decoration-none">
                        ${symbol.symbol}
                    </a>
                </td>
                <td class="crypto-price" data-symbol="${symbol.symbol}" data-price="${symbol.price}">
                    ${this.formatPrice(symbol.price)}
                </td>
                <td class="${changeClass}">
                    ${changeIcon} ${Math.abs(symbol.price_change_24h).toFixed(2)}%
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-danger remove-symbol" data-symbol="${symbol.symbol}">
                        <i class="fas fa-times"></i> Remove
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
            
            // Subscribe to price updates
            this.subscribeToSymbol(symbol.symbol);
        });
    },
    
    // Create watchlist
    createWatchlist() {
        const name = document.getElementById('watchlist-name').value;
        
        fetch('/api/watchlists/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('create-watchlist-modal'));
            if (modal) modal.hide();
            
            // Clear form
            document.getElementById('watchlist-name').value = '';
            
            // Reload watchlists
            this.loadWatchlists();
            
            // Show success message
            this.showToast('Success', 'Watchlist created successfully', 'success');
        })
        .catch(error => {
            console.error('Error creating watchlist:', error);
            this.showToast('Error', 'Failed to create watchlist. Please try again.', 'danger');
        });
    },
    
    // Add to watchlist
    addToWatchlist() {
        const watchlistId = document.getElementById('watchlist-select-add').value;
        const symbol = document.getElementById('watchlist-symbol').value;
        
        fetch('/api/watchlists/add-symbol', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                watchlist_id: watchlistId,
                symbol: symbol
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('add-symbol-modal'));
            if (modal) modal.hide();
            
            // Clear form
            document.getElementById('watchlist-symbol').value = '';
            
            // Reload current watchlist
            const currentWatchlistId = document.getElementById('watchlist-select').value;
            this.loadWatchlistSymbols(currentWatchlistId);
            
            // Show success message
            this.showToast('Success', 'Symbol added to watchlist successfully', 'success');
        })
        .catch(error => {
            console.error('Error adding symbol to watchlist:', error);
            this.showToast('Error', 'Failed to add symbol. Please try again.', 'danger');
        });
    },
    
    // Remove from watchlist
    removeFromWatchlist(watchlistId, symbol) {
        fetch('/api/watchlists/remove-symbol', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                watchlist_id: watchlistId,
                symbol: symbol
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Reload current watchlist
            this.loadWatchlistSymbols(watchlistId);
            
            // Show success message
            this.showToast('Success', 'Symbol removed from watchlist', 'success');
        })
        .catch(error => {
            console.error('Error removing symbol from watchlist:', error);
            this.showToast('Error', 'Failed to remove symbol. Please try again.', 'danger');
        });
    },
    
    // Load market depth
    loadMarketDepth() {
        if (!document.getElementById('depthChart')) return;
        
        fetch(`/api/depth/${this.activeSymbol}`)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                this.renderMarketDepth(data);
            })
            .catch(error => {
                console.error('Error loading market depth:', error);
                document.getElementById('depth-error').style.display = 'block';
            });
    },
    
    // Render market depth
    renderMarketDepth(data) {
        const ctx = document.getElementById('depthChart').getContext('2d');
        
        if (this.charts.depth) {
            this.charts.depth.destroy();
        }
        
        // Prepare data
        const bids = data.bids.map(bid => ({
            x: parseFloat(bid[0]),
            y: parseFloat(bid[1])
        }));
        
        const asks = data.asks.map(ask => ({
            x: parseFloat(ask[0]),
            y: parseFloat(ask[1])
        }));
        
        // Create chart
        this.charts.depth = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [
                    {
                        label: 'Bids',
                        data: bids,
                        backgroundColor: 'rgba(0, 200, 0, 0.5)',
                        borderColor: 'rgba(0, 200, 0, 1)',
                        pointRadius: 3
                    },
                    {
                        label: 'Asks',
                        data: asks,
                        backgroundColor: 'rgba(200, 0, 0, 0.5)',
                        borderColor: 'rgba(200, 0, 0, 1)',
                        pointRadius: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Price'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Quantity'
                        }
                    }
                }
            }
        });
        
        // Apply theme to chart
        this.updateChartTheme(this.charts.depth);
    },
    
    // Load technical indicators
    loadTechnicalIndicators() {
        if (!document.getElementById('technical-indicators')) return;
        
        fetch(`/api/indicators/${this.activeSymbol}?interval=${this.activeInterval}`)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                this.renderTechnicalIndicators(data);
            })
            .catch(error => {
                console.error('Error loading technical indicators:', error);
                document.getElementById('indicators-error').style.display = 'block';
            });
    },
    
    // Render technical indicators
    renderTechnicalIndicators(data) {
        const container = document.getElementById('technical-indicators');
        if (!container) return;
        
        container.innerHTML = '';
        
        // Create indicator cards
        const createIndicatorCard = (title, value, interpretation) => {
            const card = document.createElement('div');
            card.className = 'col-md-4 mb-4';
            
            // Determine class based on interpretation
            let interpretationClass = 'text-info';
            if (interpretation.toLowerCase().includes('bullish')) {
                interpretationClass = 'text-success';
            } else if (interpretation.toLowerCase().includes('bearish')) {
                interpretationClass = 'text-danger';
            }
            
            card.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">${title}</h5>
                        <h3 class="card-text">${value}</h3>
                        <p class="${interpretationClass}">${interpretation}</p>
                    </div>
                </div>
            `;
            
            return card;
        };
        
        // Add RSI indicator
        container.appendChild(createIndicatorCard(
            'RSI (14)',
            data.rsi.toFixed(2),
            data.rsi > 70 ? 'Overbought - Bearish' : (data.rsi < 30 ? 'Oversold - Bullish' : 'Neutral')
        ));
        
        // Add MACD indicator
        container.appendChild(createIndicatorCard(
            'MACD',
            `${data.macd.toFixed(2)}`,
            data.macd > 0 ? 'Bullish Momentum' : 'Bearish Momentum'
        ));
        
        // Add Bollinger Bands
        container.appendChild(createIndicatorCard(
            'Bollinger Bands',
            `Width: ${data.bb_width.toFixed(2)}`,
            data.bb_width > 0.1 ? 'High Volatility' : 'Low Volatility'
        ));
    },
    
    // Show toast message
    showToast(title, message, type = 'info', duration = 5000) {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong>: ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Initialize and show toast
        const toastInstance = new bootstrap.Toast(toast, {
            autohide: true,
            delay: duration
        });
        
        toastInstance.show();
        
        // Remove toast from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },
    
    // Utility function for debouncing
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    CryptoApp.init();
});

