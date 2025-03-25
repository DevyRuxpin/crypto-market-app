/**
 * Crypto Market Dashboard - Main JavaScript
 * Handles UI interactions, WebSocket connections, and API calls
 */

// Global variables
let socket;
let darkMode = localStorage.getItem('darkMode') === 'true';
let currentSymbol = 'BTCUSDT';
let currentInterval = '1h';
let chart;
let priceUpdateInterval;
let alertsCheckInterval;
let portfolioUpdateInterval;

// DOM elements
const priceTableBody = document.getElementById('price-table-body');
const cryptoChart = document.getElementById('crypto-chart');
const portfolioValue = document.getElementById('portfolio-value');
const darkModeToggle = document.getElementById('dark-mode-toggle');
const searchInput = document.getElementById('crypto-search');
const filterSelect = document.getElementById('crypto-filter');
const symbolSelect = document.getElementById('symbol-select');
const intervalSelect = document.getElementById('interval-select');
const alertsList = document.getElementById('alerts-list');
const watchlistSelect = document.getElementById('watchlist-select');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Apply dark mode if enabled
    if (darkMode) {
        document.body.classList.add('dark-mode');
    }
    
    // Initialize Socket.IO connection
    initializeSocket();
    
    // Initialize UI components
    initializeDarkModeToggle();
    initializeSearchAndFilter();
    initializeSymbolAndIntervalSelects();
    
    // Load initial data
    loadPrices();
    
    // If on portfolio page, initialize portfolio components
    if (document.getElementById('portfolio-container')) {
        initializePortfolioComponents();
    }
    
    // If on alerts page, initialize alerts components
    if (document.getElementById('alerts-container')) {
        initializeAlertsComponents();
    }
    
    // If on watchlist page, initialize watchlist components
    if (document.getElementById('watchlist-container')) {
        initializeWatchlistComponents();
    }
    
    // If chart exists on the page, initialize it
    if (cryptoChart) {
        initializeChart();
    }
    
    // Set up intervals for data updates
    setupDataUpdateIntervals();
});

// Initialize Socket.IO connection
function initializeSocket() {
    socket = io.connect(window.location.origin, {
        transports: ['websocket']
    });
    
    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
        
        // Join user-specific room for private notifications
        socket.emit('join_user_room');
        
        // Subscribe to ticker updates
        socket.emit('subscribe_ticker');
        
        // If chart exists, subscribe to kline updates for current symbol
        if (cryptoChart) {
            socket.emit('subscribe', {
                symbol: currentSymbol,
                interval: currentInterval
            });
        }
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket server');
    });
    
    socket.on('ticker_update', (data) => {
        updatePriceTable(data);
    });
    
    socket.on('kline_update', (data) => {
        if (chart && data.symbol === currentSymbol) {
            updateChart(data);
        }
    });
    
    socket.on('alert_triggered', (alert) => {
        showAlertNotification(alert);
    });
}

// Initialize dark mode toggle
function initializeDarkModeToggle() {
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            darkMode = !darkMode;
            document.body.classList.toggle('dark-mode', darkMode);
            localStorage.setItem('darkMode', darkMode);
            
            // Update server-side theme preference
            fetch('/api/theme/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            // Update chart theme if it exists
            if (chart) {
                updateChartTheme();
            }
        });
    }
}

// Initialize search and filter functionality
function initializeSearchAndFilter() {
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            filterCryptoTable();
        }, 300));
    }
    
    if (filterSelect) {
        filterSelect.addEventListener('change', () => {
            filterCryptoTable();
        });
    }
}

// Initialize symbol and interval select dropdowns
function initializeSymbolAndIntervalSelects() {
    if (symbolSelect) {
        symbolSelect.addEventListener('change', () => {
            currentSymbol = symbolSelect.value;
            if (chart) {
                // Unsubscribe from old symbol and subscribe to new one
                socket.emit('unsubscribe', {
                    symbol: currentSymbol,
                    interval: currentInterval
                });
                
                socket.emit('subscribe', {
                    symbol: currentSymbol,
                    interval: currentInterval
                });
                
                loadChartData();
            }
        });
    }
    
    if (intervalSelect) {
        intervalSelect.addEventListener('change', () => {
            currentInterval = intervalSelect.value;
            if (chart) {
                // Unsubscribe from old interval and subscribe to new one
                socket.emit('unsubscribe', {
                    symbol: currentSymbol,
                    interval: currentInterval
                });
                
                socket.emit('subscribe', {
                    symbol: currentSymbol,
                    interval: currentInterval
                });
                
                loadChartData();
            }
        });
    }
}

// Initialize portfolio components
function initializePortfolioComponents() {
    const addHoldingForm = document.getElementById('add-holding-form');
    const createPortfolioForm = document.getElementById('create-portfolio-form');
    const portfolioSelect = document.getElementById('portfolio-select');
    
    if (addHoldingForm) {
        addHoldingForm.addEventListener('submit', (e) => {
            e.preventDefault();
            addHolding();
        });
    }
    
    if (createPortfolioForm) {
        createPortfolioForm.addEventListener('submit', (e) => {
            e.preventDefault();
            createPortfolio();
        });
    }
    
    if (portfolioSelect) {
        portfolioSelect.addEventListener('change', () => {
            loadPortfolioHoldings(portfolioSelect.value);
        });
        
        // Load initial portfolio holdings
        if (portfolioSelect.value) {
            loadPortfolioHoldings(portfolioSelect.value);
        }
    }
    
    // Load portfolios
    loadPortfolios();
}

// Initialize alerts components
function initializeAlertsComponents() {
    const createAlertForm = document.getElementById('create-alert-form');
    
    if (createAlertForm) {
        createAlertForm.addEventListener('submit', (e) => {
            e.preventDefault();
            createAlert();
        });
    }
    
    // Load alerts
    loadAlerts();
}

// Initialize watchlist components
function initializeWatchlistComponents() {
    const createWatchlistForm = document.getElementById('create-watchlist-form');
    const addToWatchlistForm = document.getElementById('add-to-watchlist-form');
    
    if (createWatchlistForm) {
        createWatchlistForm.addEventListener('submit', (e) => {
            e.preventDefault();
            createWatchlist();
        });
    }
    
    if (addToWatchlistForm) {
        addToWatchlistForm.addEventListener('submit', (e) => {
            e.preventDefault();
            addToWatchlist();
        });
    }
    
    if (watchlistSelect) {
        watchlistSelect.addEventListener('change', () => {
            loadWatchlistSymbols(watchlistSelect.value);
        });
        
        // Load initial watchlist symbols
        if (watchlistSelect.value) {
            loadWatchlistSymbols(watchlistSelect.value);
        }
    }
    
    // Load watchlists
    loadWatchlists();
}

// Initialize the price chart
function initializeChart() {
    const ctx = cryptoChart.getContext('2d');
    
    chart = new Chart(ctx, {
        type: 'candlestick',
        data: {
            datasets: [{
                label: currentSymbol,
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
                        unit: 'hour'
                    }
                },
                y: {
                    type: 'linear'
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
            }
        }
    });
    
    // Apply dark mode to chart if enabled
    if (darkMode) {
        updateChartTheme();
    }
    
    // Load initial chart data
    loadChartData();
}

// Update chart theme based on dark mode
function updateChartTheme() {
    if (!chart) return;
    
    const theme = darkMode ? {
        color: 'white',
        grid: {
            color: 'rgba(255, 255, 255, 0.1)'
        }
    } : {
        color: 'black',
        grid: {
            color: 'rgba(0, 0, 0, 0.1)'
        }
    };
    
    chart.options.scales.x.ticks = { color: theme.color };
    chart.options.scales.y.ticks = { color: theme.color };
    chart.options.scales.x.grid = { color: theme.grid.color };
    chart.options.scales.y.grid = { color: theme.grid.color };
    
    chart.update();
}

// Load cryptocurrency prices
function loadPrices() {
    fetch('/api/prices')
        .then(response => response.json())
        .then(data => {
            updatePriceTable(data);
        })
        .catch(error => {
            console.error('Error loading prices:', error);
        });
}

// Update the price table with new data
function updatePriceTable(data) {
    if (!priceTableBody) return;
    
    // Clear existing rows if this is a full update
    if (Array.isArray(data)) {
        priceTableBody.innerHTML = '';
        
        // Filter data based on search and filter criteria
        const filteredData = filterData(data);
        
        // Add rows for each cryptocurrency
        filteredData.forEach(item => {
            const row = createPriceTableRow(item);
            priceTableBody.appendChild(row);
        });
    }
    // If it's a single update, find and update just that row
    else if (data.symbol) {
        const existingRow = document.querySelector(`tr[data-symbol="${data.symbol}"]`);
        if (existingRow) {
            const priceCell = existingRow.querySelector('.price');
            const oldPrice = parseFloat(priceCell.dataset.price);
            const newPrice = parseFloat(data.price);
            
            priceCell.textContent = formatPrice(newPrice);
            priceCell.dataset.price = newPrice;
            
            // Add price change indicator
            if (newPrice > oldPrice) {
                priceCell.classList.remove('price-down');
                priceCell.classList.add('price-up');
            } else if (newPrice < oldPrice) {
                priceCell.classList.remove('price-up');
                priceCell.classList.add('price-down');
            }
            
            // Remove indicator after animation
            setTimeout(() => {
                priceCell.classList.remove('price-up', 'price-down');
            }, 1000);
        }
    }
}

// Create a row for the price table
function createPriceTableRow(item) {
    const row = document.createElement('tr');
    row.dataset.symbol = item.symbol;
    
    // Extract base symbol (remove USDT suffix)
    const baseSymbol = item.symbol.replace('USDT', '');
    
    row.innerHTML = `
        <td>
            <img src="https://cryptoicons.org/api/icon/${baseSymbol.toLowerCase()}/30" 
                 onerror="this.src='/static/img/generic-crypto.png'" 
                 alt="${baseSymbol}" class="crypto-icon">
            ${baseSymbol}
        </td>
        <td class="price" data-price="${item.price}">${formatPrice(item.price)}</td>
        <td>
            <button class="btn btn-sm btn-outline-primary add-to-watchlist" 
                    data-symbol="${baseSymbol}">
                <i class="fas fa-star"></i>
            </button>
            <button class="btn btn-sm btn-outline-info view-detail" 
                    data-symbol="${baseSymbol}">
                <i class="fas fa-chart-line"></i>
            </button>
        </td>
    `;
    
    // Add event listeners for the buttons
    const watchlistBtn = row.querySelector('.add-to-watchlist');
    const detailBtn = row.querySelector('.view-detail');
    
    watchlistBtn.addEventListener('click', () => {
        addToDefaultWatchlist(baseSymbol);
    });
    
    detailBtn.addEventListener('click', () => {
        window.location.href = `/crypto/${baseSymbol}`;
    });
    
    return row;
}

// Filter data based on search and filter criteria
function filterData(data) {
    let filteredData = [...data];
    
    // Apply search filter if search input exists and has a value
    if (searchInput && searchInput.value) {
        const searchTerm = searchInput.value.toLowerCase();
        filteredData = filteredData.filter(item => 
            item.symbol.toLowerCase().includes(searchTerm)
        );
    }
    
        // Apply dropdown filter if filter select exists and has a value
    if (filterSelect && filterSelect.value !== 'all') {
        if (filterSelect.value === 'major') {
            // Filter to only show major cryptocurrencies
            const majorSymbols = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'MATIC', 'LINK', 'LTC', 'UNI', 'ATOM', 'AVAX', 'SHIB'];
            filteredData = filteredData.filter(item => {
                const baseSymbol = item.symbol.replace('USDT', '');
                return majorSymbols.includes(baseSymbol);
            });
        } else if (filterSelect.value === 'usd') {
            // Filter to only show USD pairs
            filteredData = filteredData.filter(item => item.symbol.endsWith('USDT'));
        }
    }
    
    return filteredData;
}

// Filter the crypto table based on search and filter inputs
function filterCryptoTable() {
    loadPrices(); // Reload prices with filters applied
}

// Load chart data for the selected symbol and interval
function loadChartData() {
    if (!chart) return;
    
    fetch(`/api/klines?symbol=${currentSymbol}&interval=${currentInterval}`)
        .then(response => response.json())
        .then(data => {
            // Format data for the chart
            const chartData = data.map(candle => ({
                x: new Date(candle.openTime),
                o: parseFloat(candle.open),
                h: parseFloat(candle.high),
                l: parseFloat(candle.low),
                c: parseFloat(candle.close)
            }));
            
            // Update chart data
            chart.data.datasets[0].data = chartData;
            chart.data.datasets[0].label = currentSymbol;
            chart.options.scales.x.time.unit = getTimeUnitForInterval(currentInterval);
            chart.update();
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
        });
}

// Update chart with new candle data
function updateChart(data) {
    if (!chart) return;
    
    // Convert WebSocket data to chart format
    const candle = {
        x: new Date(data.kline.startTime),
        o: parseFloat(data.kline.open),
        h: parseFloat(data.kline.high),
        l: parseFloat(data.kline.low),
        c: parseFloat(data.kline.close)
    };
    
    // Find if this candle already exists in the data
    const dataIndex = chart.data.datasets[0].data.findIndex(item => 
        item.x.getTime() === candle.x.getTime()
    );
    
    // Update existing candle or add new one
    if (dataIndex >= 0) {
        chart.data.datasets[0].data[dataIndex] = candle;
    } else {
        chart.data.datasets[0].data.push(candle);
        
        // Remove oldest candle if we have too many
        if (chart.data.datasets[0].data.length > 100) {
            chart.data.datasets[0].data.shift();
        }
    }
    
    chart.update();
}

// Get appropriate time unit for chart based on interval
function getTimeUnitForInterval(interval) {
    switch (interval) {
        case '1m':
        case '3m':
        case '5m':
        case '15m':
        case '30m':
            return 'minute';
        case '1h':
        case '2h':
        case '4h':
        case '6h':
        case '8h':
        case '12h':
            return 'hour';
        case '1d':
        case '3d':
            return 'day';
        case '1w':
            return 'week';
        case '1M':
            return 'month';
        default:
            return 'hour';
    }
}

// Load user portfolios
function loadPortfolios() {
    fetch('/api/portfolio')
        .then(response => response.json())
        .then(data => {
            // Update portfolio select dropdown
            if (document.getElementById('portfolio-select')) {
                const select = document.getElementById('portfolio-select');
                select.innerHTML = '';
                
                data.forEach(portfolio => {
                    const option = document.createElement('option');
                    option.value = portfolio.id;
                    option.textContent = portfolio.name;
                    select.appendChild(option);
                });
                
                // Load holdings for the selected portfolio
                if (select.value) {
                    loadPortfolioHoldings(select.value);
                }
            }
            
            // Update portfolio summary if on dashboard
            if (document.getElementById('portfolio-summary')) {
                updatePortfolioSummary(data);
            }
        })
        .catch(error => {
            console.error('Error loading portfolios:', error);
        });
}

// Load holdings for a specific portfolio
function loadPortfolioHoldings(portfolioId) {
    fetch(`/api/portfolio/${portfolioId}`)
        .then(response => response.json())
        .then(data => {
            // Update holdings table
            const holdingsTable = document.getElementById('holdings-table-body');
            if (holdingsTable) {
                holdingsTable.innerHTML = '';
                
                data.holdings.forEach(holding => {
                    const row = document.createElement('tr');
                    row.dataset.holdingId = holding.id;
                    
                    // Calculate profit/loss percentage
                    const costBasis = holding.amount * holding.price_per_unit;
                    const currentValue = holding.current_value;
                    const profitLoss = currentValue - costBasis;
                    const profitLossPercent = costBasis > 0 ? (profitLoss / costBasis) * 100 : 0;
                    
                    row.innerHTML = `
                        <td>${holding.symbol}</td>
                        <td>${formatNumber(holding.amount)}</td>
                        <td>${formatPrice(holding.price_per_unit)}</td>
                        <td>${formatPrice(holding.current_price)}</td>
                        <td>${formatPrice(currentValue)}</td>
                        <td class="${profitLoss >= 0 ? 'text-success' : 'text-danger'}">
                            ${formatPrice(profitLoss)} (${formatNumber(profitLossPercent)}%)
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary edit-holding" 
                                    data-holding-id="${holding.id}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-holding" 
                                    data-holding-id="${holding.id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    `;
                    
                    holdingsTable.appendChild(row);
                });
                
                // Add event listeners for edit and delete buttons
                document.querySelectorAll('.edit-holding').forEach(button => {
                    button.addEventListener('click', () => {
                        const holdingId = button.dataset.holdingId;
                        openEditHoldingModal(portfolioId, holdingId);
                    });
                });
                
                document.querySelectorAll('.delete-holding').forEach(button => {
                    button.addEventListener('click', () => {
                        const holdingId = button.dataset.holdingId;
                        deleteHolding(portfolioId, holdingId);
                    });
                });
            }
            
            // Update portfolio performance metrics
            updatePortfolioMetrics(data.performance);
        })
        .catch(error => {
            console.error('Error loading portfolio holdings:', error);
        });
}

// Update portfolio summary on dashboard
function updatePortfolioSummary(portfolios) {
    const summaryContainer = document.getElementById('portfolio-summary');
    if (!summaryContainer) return;
    
    summaryContainer.innerHTML = '';
    
    // Calculate total value across all portfolios
    let totalValue = 0;
    let totalInvested = 0;
    
    portfolios.forEach(portfolio => {
        totalValue += portfolio.performance.current_value;
        totalInvested += portfolio.performance.total_invested;
    });
    
    const totalProfitLoss = totalValue - totalInvested;
    const totalProfitLossPercent = totalInvested > 0 ? (totalProfitLoss / totalInvested) * 100 : 0;
    
    // Create summary card
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
        <div class="card-body">
            <h5 class="card-title">Portfolio Summary</h5>
            <div class="row">
                <div class="col-md-4">
                    <p class="card-text">Total Value: ${formatPrice(totalValue)}</p>
                </div>
                <div class="col-md-4">
                    <p class="card-text">Total Invested: ${formatPrice(totalInvested)}</p>
                </div>
                <div class="col-md-4">
                    <p class="card-text ${totalProfitLoss >= 0 ? 'text-success' : 'text-danger'}">
                        Profit/Loss: ${formatPrice(totalProfitLoss)} (${formatNumber(totalProfitLossPercent)}%)
                    </p>
                </div>
            </div>
        </div>
    `;
    
    summaryContainer.appendChild(card);
    
    // Create cards for individual portfolios
    portfolios.forEach(portfolio => {
        const portfolioCard = document.createElement('div');
        portfolioCard.className = 'card mt-3';
        
        const profitLoss = portfolio.performance.profit_loss;
        const profitLossPercent = portfolio.performance.profit_loss_percent;
        
        portfolioCard.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${portfolio.name}</h5>
                <div class="row">
                    <div class="col-md-4">
                        <p class="card-text">Value: ${formatPrice(portfolio.performance.current_value)}</p>
                    </div>
                    <div class="col-md-4">
                        <p class="card-text">Invested: ${formatPrice(portfolio.performance.total_invested)}</p>
                    </div>
                    <div class="col-md-4">
                        <p class="card-text ${profitLoss >= 0 ? 'text-success' : 'text-danger'}">
                            Profit/Loss: ${formatPrice(profitLoss)} (${formatNumber(profitLossPercent)}%)
                        </p>
                    </div>
                </div>
                <a href="/portfolio?id=${portfolio.id}" class="btn btn-sm btn-primary">View Details</a>
            </div>
        `;
        
        summaryContainer.appendChild(portfolioCard);
    });
}

// Update portfolio performance metrics
function updatePortfolioMetrics(performance) {
    const metricsContainer = document.getElementById('portfolio-metrics');
    if (!metricsContainer) return;
    
    const totalValue = performance.current_value;
    const totalInvested = performance.total_invested;
    const profitLoss = performance.profit_loss;
    const profitLossPercent = performance.profit_loss_percent;
    
    metricsContainer.innerHTML = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Portfolio Performance</h5>
                <div class="row">
                    <div class="col-md-6">
                        <p class="card-text">Current Value: ${formatPrice(totalValue)}</p>
                        <p class="card-text">Total Invested: ${formatPrice(totalInvested)}</p>
                    </div>
                    <div class="col-md-6">
                        <p class="card-text ${profitLoss >= 0 ? 'text-success' : 'text-danger'}">
                            Profit/Loss: ${formatPrice(profitLoss)}
                        </p>
                        <p class="card-text ${profitLoss >= 0 ? 'text-success' : 'text-danger'}">
                            Profit/Loss %: ${formatNumber(profitLossPercent)}%
                        </p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Add a new holding to a portfolio
function addHolding() {
    const portfolioId = document.getElementById('portfolio-id').value;
    const symbol = document.getElementById('holding-symbol').value;
    const amount = document.getElementById('holding-amount').value;
    const price = document.getElementById('holding-price').value;
    const date = document.getElementById('holding-date').value;
    
    fetch(`/api/portfolio/${portfolioId}/holdings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: symbol,
            amount: amount,
            price_per_unit: price,
            date: date
        })
    })
    .then(response => response.json())
    .then(data => {
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('add-holding-modal'));
        modal.hide();
        
        // Reload portfolio holdings
        loadPortfolioHoldings(portfolioId);
        
        // Show success message
        showToast('Holding added successfully', 'success');
    })
    .catch(error => {
        console.error('Error adding holding:', error);
        showToast('Error adding holding', 'danger');
    });
}

// Create a new portfolio
function createPortfolio() {
    const name = document.getElementById('portfolio-name').value;
    
    fetch('/api/portfolio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name
        })
    })
    .then(response => response.json())
    .then(data => {
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('create-portfolio-modal'));
        modal.hide();
        
        // Reload portfolios
        loadPortfolios();
        
        // Show success message
        showToast('Portfolio created successfully', 'success');
    })
    .catch(error => {
        console.error('Error creating portfolio:', error);
        showToast('Error creating portfolio', 'danger');
    });
}

// Open the edit holding modal
function openEditHoldingModal(portfolioId, holdingId) {
    fetch(`/api/portfolio/${portfolioId}`)
        .then(response => response.json())
        .then(data => {
            const holding = data.holdings.find(h => h.id === holdingId);
            if (holding) {
                document.getElementById('edit-holding-id').value = holdingId;
                document.getElementById('edit-portfolio-id').value = portfolioId;
                document.getElementById('edit-holding-symbol').value = holding.symbol;
                document.getElementById('edit-holding-amount').value = holding.amount;
                document.getElementById('edit-holding-price').value = holding.price_per_unit;
                
                // Open the modal
                const modal = new bootstrap.Modal(document.getElementById('edit-holding-modal'));
                modal.show();
                
                // Set up the form submission
                                document.getElementById('edit-holding-form').addEventListener('submit', function(e) {
                    e.preventDefault();
                    updateHolding();
                });
            }
        })
        .catch(error => {
            console.error('Error getting holding details:', error);
        });
}

// Update an existing holding
function updateHolding() {
    const holdingId = document.getElementById('edit-holding-id').value;
    const portfolioId = document.getElementById('edit-portfolio-id').value;
    const amount = document.getElementById('edit-holding-amount').value;
    const price = document.getElementById('edit-holding-price').value;
    
    fetch(`/api/portfolio/${portfolioId}/holdings/${holdingId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            amount: amount,
            price_per_unit: price
        })
    })
    .then(response => response.json())
    .then(data => {
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('edit-holding-modal'));
        modal.hide();
        
        // Reload portfolio holdings
        loadPortfolioHoldings(portfolioId);
        
        // Show success message
        showToast('Holding updated successfully', 'success');
    })
    .catch(error => {
        console.error('Error updating holding:', error);
        showToast('Error updating holding', 'danger');
    });
}

// Delete a holding
function deleteHolding(portfolioId, holdingId) {
    if (confirm('Are you sure you want to delete this holding?')) {
        fetch(`/api/portfolio/${portfolioId}/holdings/${holdingId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                // Reload portfolio holdings
                loadPortfolioHoldings(portfolioId);
                
                // Show success message
                showToast('Holding deleted successfully', 'success');
            } else {
                throw new Error('Failed to delete holding');
            }
        })
        .catch(error => {
            console.error('Error deleting holding:', error);
            showToast('Error deleting holding', 'danger');
        });
    }
}

// Load alerts
function loadAlerts() {
    fetch('/api/alerts')
        .then(response => response.json())
        .then(data => {
            // Update alerts list
            if (alertsList) {
                alertsList.innerHTML = '';
                
                if (data.length === 0) {
                    alertsList.innerHTML = '<div class="alert alert-info">No alerts set. Create one below.</div>';
                } else {
                    data.forEach(alert => {
                        const alertCard = createAlertCard(alert);
                        alertsList.appendChild(alertCard);
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error loading alerts:', error);
        });
}

// Create an alert card element
function createAlertCard(alert) {
    const card = document.createElement('div');
    card.className = 'card mb-3';
    card.dataset.alertId = alert.id;
    
    const statusClass = alert.status === 'active' ? 'success' : 
                       (alert.status === 'triggered' ? 'warning' : 'secondary');
    
    const alertTypeText = alert.alert_type === 'price_above' ? 'Price Above' : 
                         (alert.alert_type === 'price_below' ? 'Price Below' : 'Price Change');
    
    card.innerHTML = `
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
                <h5 class="card-title">${alert.name || `${alert.symbol} Alert`}</h5>
                <span class="badge bg-${statusClass}">${alert.status}</span>
            </div>
            <p class="card-text">
                <strong>Symbol:</strong> ${alert.symbol}<br>
                <strong>Condition:</strong> ${alertTypeText} ${formatPrice(alert.target_value)}<br>
                <strong>Created:</strong> ${new Date(alert.created_at).toLocaleString()}
            </p>
            <div class="btn-group">
                ${alert.status === 'active' ? 
                  `<button class="btn btn-sm btn-outline-secondary dismiss-alert" data-alert-id="${alert.id}">
                      Dismiss
                  </button>` : 
                  (alert.status === 'dismissed' ? 
                   `<button class="btn btn-sm btn-outline-success reactivate-alert" data-alert-id="${alert.id}">
                       Reactivate
                   </button>` : '')}
                <button class="btn btn-sm btn-outline-danger delete-alert" data-alert-id="${alert.id}">
                    Delete
                </button>
            </div>
        </div>
    `;
    
    // Add event listeners for the buttons
    const dismissBtn = card.querySelector('.dismiss-alert');
    const reactivateBtn = card.querySelector('.reactivate-alert');
    const deleteBtn = card.querySelector('.delete-alert');
    
    if (dismissBtn) {
        dismissBtn.addEventListener('click', () => {
            updateAlertStatus(alert.id, 'dismissed');
        });
    }
    
    if (reactivateBtn) {
        reactivateBtn.addEventListener('click', () => {
            updateAlertStatus(alert.id, 'active');
        });
    }
    
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            deleteAlert(alert.id);
        });
    }
    
    return card;
}

// Create a new price alert
function createAlert() {
    const symbol = document.getElementById('alert-symbol').value;
    const alertType = document.getElementById('alert-type').value;
    const targetValue = document.getElementById('alert-value').value;
    const name = document.getElementById('alert-name').value;
    
    fetch('/api/alerts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: symbol,
            alert_type: alertType,
            target_value: targetValue,
            name: name
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset the form
        document.getElementById('create-alert-form').reset();
        
        // Reload alerts
        loadAlerts();
        
        // Show success message
        showToast('Alert created successfully', 'success');
    })
    .catch(error => {
        console.error('Error creating alert:', error);
        showToast('Error creating alert', 'danger');
    });
}

// Update an alert's status
function updateAlertStatus(alertId, status) {
    fetch(`/api/alerts/${alertId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reload alerts
        loadAlerts();
        
        // Show success message
        const action = status === 'active' ? 'reactivated' : 'dismissed';
        showToast(`Alert ${action} successfully`, 'success');
    })
    .catch(error => {
        console.error('Error updating alert:', error);
        showToast('Error updating alert', 'danger');
    });
}

// Delete an alert
function deleteAlert(alertId) {
    if (confirm('Are you sure you want to delete this alert?')) {
        fetch(`/api/alerts/${alertId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                // Reload alerts
                loadAlerts();
                
                // Show success message
                showToast('Alert deleted successfully', 'success');
            } else {
                throw new Error('Failed to delete alert');
            }
        })
        .catch(error => {
            console.error('Error deleting alert:', error);
            showToast('Error deleting alert', 'danger');
        });
    }
}

// Show alert notification
function showAlertNotification(alert) {
    // Create a toast notification
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">Price Alert Triggered</strong>
            <small>${new Date().toLocaleTimeString()}</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            <p><strong>${alert.name || `${alert.symbol} Alert`}</strong></p>
            <p>Your price alert for ${alert.symbol} has been triggered.</p>
            <a href="/alerts" class="btn btn-sm btn-primary">View Alerts</a>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Play notification sound
    playNotificationSound();
}

// Play a notification sound
function playNotificationSound() {
    const audio = new Audio('/static/sounds/notification.mp3');
    audio.play();
}

// Load watchlists
function loadWatchlists() {
    fetch('/api/watchlists')
        .then(response => response.json())
        .then(data => {
            // Update watchlist select dropdown
            if (watchlistSelect) {
                watchlistSelect.innerHTML = '';
                
                data.forEach(watchlist => {
                    const option = document.createElement('option');
                    option.value = watchlist.id;
                    option.textContent = `${watchlist.name} (${watchlist.count})`;
                    watchlistSelect.appendChild(option);
                });
                
                // Load symbols for the selected watchlist
                if (watchlistSelect.value) {
                    loadWatchlistSymbols(watchlistSelect.value);
                }
            }
        })
        .catch(error => {
            console.error('Error loading watchlists:', error);
        });
}

// Load symbols for a specific watchlist
function loadWatchlistSymbols(watchlistId) {
    fetch(`/api/watchlists/${watchlistId}`)
        .then(response => response.json())
        .then(data => {
            // Update watchlist symbols
            const symbolsContainer = document.getElementById('watchlist-symbols');
            if (symbolsContainer) {
                symbolsContainer.innerHTML = '';
                
                if (data.symbols.length === 0) {
                    symbolsContainer.innerHTML = '<div class="alert alert-info">No symbols in this watchlist. Add some below.</div>';
                } else {
                    data.symbols.forEach(symbol => {
                        const symbolCard = createWatchlistSymbolCard(symbol, watchlistId);
                        symbolsContainer.appendChild(symbolCard);
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error loading watchlist symbols:', error);
        });
}

// Create a watchlist symbol card
function createWatchlistSymbolCard(symbol, watchlistId) {
    const card = document.createElement('div');
    card.className = 'card mb-2';
    
    card.innerHTML = `
        <div class="card-body d-flex justify-content-between align-items-center">
            <div>
                <img src="https://cryptoicons.org/api/icon/${symbol.toLowerCase()}/30" 
                     onerror="this.src='/static/img/generic-crypto.png'" 
                     alt="${symbol}" class="crypto-icon me-2">
                <span>${symbol}</span>
            </div>
            <div>
                <a href="/crypto/${symbol}" class="btn btn-sm btn-outline-info me-2">
                    <i class="fas fa-chart-line"></i> View
                </a>
                <button class="btn btn-sm btn-outline-danger remove-symbol" data-symbol="${symbol}">
                    <i class="fas fa-times"></i> Remove
                </button>
            </div>
        </div>
    `;
    
    // Add event listener for the remove button
    const removeBtn = card.querySelector('.remove-symbol');
    removeBtn.addEventListener('click', () => {
        removeFromWatchlist(watchlistId, symbol);
    });
    
    return card;
}

// Create a new watchlist
function createWatchlist() {
    const name = document.getElementById('watchlist-name').value;
    
    fetch('/api/watchlists', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset the form
        document.getElementById('create-watchlist-form').reset();
        
        // Reload watchlists
        loadWatchlists();
        
        // Show success message
        showToast('Watchlist created successfully', 'success');
    })
    .catch(error => {
        console.error('Error creating watchlist:', error);
        showToast('Error creating watchlist', 'danger');
    });
}

// Add a symbol to a watchlist
function addToWatchlist() {
    const watchlistId = document.getElementById('watchlist-select').value;
    const symbol = document.getElementById('symbol-input').value;
    
    if (!watchlistId || !symbol) {
        showToast('Please select a watchlist and enter a symbol', 'warning');
        return;
    }
    
    fetch(`/api/watchlists/${watchlistId}/symbols`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: symbol
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reset the symbol input
        document.getElementById('symbol-input').value = '';
        
        // Reload watchlist symbols
        loadWatchlistSymbols(watchlistId);
        
        // Update watchlist select options
        loadWatchlists();
        
        // Show success message
        showToast('Symbol added to watchlist', 'success');
    })
    .catch(error => {
        console.error('Error adding symbol to watchlist:', error);
        showToast('Error adding symbol to watchlist', 'danger');
    });
}

// Add a symbol to the default watchlist (quick action)
function addToDefaultWatchlist(symbol) {
    // First, get the user's watchlists
    fetch('/api/watchlists')
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                // Use the first watchlist as the default
                const defaultWatchlistId = data[0].id;
                
                // Add the symbol to the default watchlist
                fetch(`/api/watchlists/${defaultWatchlistId}/symbols`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        symbol: symbol
                    })
                })
                .then(response => response.json())
                .then(data => {
                    showToast(`${symbol} added to watchlist`, 'success');
                })
                .catch(error => {
                    console.error('Error adding symbol to watchlist:', error);
                    showToast('Error adding symbol to watchlist', 'danger');
                });
            } else {
                showToast('No watchlist found. Create one first.', 'warning');
            }
        })
        .catch(error => {
            console.error('Error getting watchlists:', error);
            showToast('Error getting watchlists', 'danger');
        });
}

// Remove a symbol from a watchlist
function removeFromWatchlist(watchlistId, symbol) {
    fetch(`/api/watchlists/${watchlistId}/symbols`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: symbol
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reload watchlist symbols
        loadWatchlistSymbols(watchlistId);
        
        // Update watchlist select options
        loadWatchlists();
        
        // Show success message
        showToast('Symbol removed from watchlist', 'success');
    })
    .catch(error => {
        console.error('Error removing symbol from watchlist:', error);
        showToast('Error removing symbol from watchlist', 'danger');
    });
}

// Setup intervals for data updates
function setupDataUpdateIntervals() {
    // Update prices every 10 seconds
    priceUpdateInterval = setInterval(() => {
        loadPrices();
    }, 10000);
    
    // Check for alerts every minute
    alertsCheckInterval = setInterval(() => {
        if (document.getElementById('alerts-list')) {
            loadAlerts();
        }
    }, 60000);
    
    // Update portfolio data every 5 minutes
    portfolioUpdateInterval = setInterval(() => {
        if (document.getElementById('portfolio-container')) {
            const portfolioId = document.getElementById('portfolio-select').value;
            if (portfolioId) {
                loadPortfolioHoldings(portfolioId);
            }
        }
    }, 300000);
}

// Format a price value with appropriate decimals
function formatPrice(price) {
    const numPrice = parseFloat(price);
    if (isNaN(numPrice)) return '$0.00';
    
    if (numPrice < 0.01) {
        return '$' + numPrice.toFixed(8);
    } else if (numPrice < 1) {
        return '$' + numPrice.toFixed(6);
    } else if (numPrice < 10) {
        return '$' + numPrice.toFixed(4);
    } else if (numPrice < 1000) {
        return '$' + numPrice.toFixed(2);
    } else {
        return '$' + numPrice.toLocaleString('en-US', { maximumFractionDigits: 2 });
    }
}

// Format a number with appropriate decimals
function formatNumber(num) {
    const numValue = parseFloat(num);
    if (isNaN(numValue)) return '0';
    
    if (numValue < 0.01) {
        return numValue.toFixed(8);
    } else if (numValue < 1) {
        return numValue.toFixed(6);
    } else if (numValue < 10) {
        return numValue.toFixed(4);
    } else if (numValue < 1000) {
        return numValue.toFixed(2);
    } else {
        return numValue.toLocaleString('en-US', { maximumFractionDigits: 2 });
    }
}

// Show a toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast bg-${type} text-white`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-body">
            ${message}
            <button type="button" class="btn-close btn-close-white ms-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    // Remove the toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Debounce function to limit how often a function can be called
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Clean up intervals when the page is unloaded
window.addEventListener('beforeunload', () => {
    clearInterval(priceUpdateInterval);
    clearInterval(alertsCheckInterval);
    clearInterval(portfolioUpdateInterval);
});


        
