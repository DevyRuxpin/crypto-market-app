document.addEventListener('DOMContentLoaded', function() {
    // Get the symbol from the page
    const symbolTitle = document.getElementById('symbol-title');
    const currentPrice = document.getElementById('current-price');
    const priceChange = document.getElementById('price-change');
    const high24h = document.getElementById('24h-high');
    const low24h = document.getElementById('24h-low');
    const volume24h = document.getElementById('24h-volume');
    const trades24h = document.getElementById('24h-trades');
    const baseAsset = document.getElementById('base-asset');
    const quoteAsset = document.getElementById('quote-asset');
    const statusElement = document.getElementById('status');
    const chartLoading = document.getElementById('chart-loading');
    const chartError = document.getElementById('chart-error');
    const depthLoading = document.getElementById('depth-loading');
    const rsiValue = document.getElementById('rsi-value');
    const rsiProgress = document.getElementById('rsi-progress');
    const sma20 = document.getElementById('sma-20');
    const sma50 = document.getElementById('sma-50');
    const ema12 = document.getElementById('ema-12');
    const ema26 = document.getElementById('ema-26');
    
    // Chart instances
    let priceChart = null;
    let depthChart = null;
    
    // Current interval
    let currentInterval = '1d';
    
    // Initialize
    loadSymbolInfo();
    load24hTicker();
    fetchKlines(currentInterval);
    fetchMarketDepth();
    setupIntervalButtons();
    
    // Socket.io setup for real-time updates
    const socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to WebSocket server');
        // Subscribe to ticker updates for this symbol
        socket.emit('subscribe', `ticker_${symbol.toLowerCase()}`);
        // Subscribe to kline updates
        socket.emit('subscribe', `kline_${symbol.toLowerCase()}_${currentInterval}`);
    });
    
    socket.on(`ticker_${symbol.toLowerCase()}`, function(data) {
        updateTickerData(data);
    });
    
    socket.on(`kline_${symbol.toLowerCase()}_${currentInterval}`, function(data) {
        updateKlineData(data);
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from WebSocket server');
    });
    
    // Functions
    function loadSymbolInfo() {
        fetch(`/api/symbol-info/${symbol}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data || !data.symbols || data.symbols.length === 0) {
                    console.error('No symbol info received');
                    return;
                }
                
                const symbolInfo = data.symbols[0];
                baseAsset.textContent = symbolInfo.baseAsset;
                quoteAsset.textContent = symbolInfo.quoteAsset;
                statusElement.textContent = symbolInfo.status;
                
                // Add base/quote asset to title for clarity
                symbolTitle.textContent = `${symbol} (${symbolInfo.baseAsset}/${symbolInfo.quoteAsset})`;
            })
            .catch(error => {
                console.error('Error fetching symbol info:', error);
                baseAsset.textContent = 'Error loading data';
                quoteAsset.textContent = 'Error loading data';
                statusElement.textContent = 'Unknown';
            });
    }
    
    function load24hTicker() {
        fetch(`/api/ticker/${symbol}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data || !data.symbol) {
                    console.error('No ticker data received');
                    return;
                }
                
                updateTickerDisplay(data);
            })
            .catch(error => {
                console.error('Error fetching 24h ticker:', error);
                currentPrice.textContent = 'Error loading data';
                priceChange.innerHTML = '<span>Error loading data</span>';
            });
    }
    
    function updateTickerDisplay(data) {
        // Update current price
        const price = parseFloat(data.lastPrice);
        currentPrice.textContent = formatPrice(price);
        
        // Update price change
        const priceChangePercent = parseFloat(data.priceChangePercent);
        const priceChangeValue = parseFloat(data.priceChange);
        const changeClass = priceChangePercent >= 0 ? 'price-up' : 'price-down';
        const changeSign = priceChangePercent >= 0 ? '+' : '';
        priceChange.innerHTML = `24h Change: <span class="${changeClass}">${changeSign}${priceChangePercent.toFixed(2)}% (${formatPrice(priceChangeValue)})</span>`;
        
        // Update 24h stats
        high24h.textContent = formatPrice(parseFloat(data.highPrice));
        low24h.textContent = formatPrice(parseFloat(data.lowPrice));
        volume24h.textContent = formatVolume(parseFloat(data.volume));
        trades24h.textContent = data.count.toLocaleString();
    }
    
    function updateTickerData(data) {
        // Update from WebSocket data
        if (data.e === '24hrTicker' && data.s === symbol) {
            const tickerData = {
                symbol: data.s,
                lastPrice: data.c,
                priceChange: data.p,
                priceChangePercent: data.P,
                highPrice: data.h,
                lowPrice: data.l,
                volume: data.v,
                count: data.n
            };
            updateTickerDisplay(tickerData);
        }
    }
    
    function fetchKlines(interval) {
        showChartLoading(true);
        showChartError(false);
        
        fetch(`/api/klines/${symbol}?interval=${interval}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data || data.length === 0) {
                    showChartError(true, 'No chart data available');
                    return;
                }
                
                // Create price chart
                createPriceChart(data, interval);
                
                // Calculate and display technical indicators
                calculateIndicators(data);
            })
            .catch(error => {
                console.error('Error fetching klines:', error);
                showChartError(true, error.message);
            })
            .finally(() => {
                showChartLoading(false);
            });
    }
    
    function createPriceChart(klines, interval) {
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        // Format data for Chart.js
        const labels = klines.map(k => new Date(k.time).toLocaleString());
        const prices = klines.map(k => k.close);
        const volumes = klines.map(k => k.volume);
        
        // Destroy previous chart if it exists
        if (priceChart) {
            priceChart.destroy();
        }
        
        // Create new chart
        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: `${symbol} Price`,
                        data: prices,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Volume',
                        data: volumes,
                        borderColor: 'rgb(153, 102, 255)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        type: 'bar',
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: `Time (${interval})`
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Price'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        title: {
                            display: true,
                            text: 'Volume'
                        }
                    }
                }
            }
        });
    }
    
    function updateKlineData(data) {
        // Update chart with real-time kline data
        if (priceChart && data.k.i === currentInterval && data.s === symbol) {
            const kline = data.k;
            const candle = {
                time: kline.t,
                open: parseFloat(kline.o),
                high: parseFloat(kline.h),
                low: parseFloat(kline.l),
                close: parseFloat(kline.c),
                volume: parseFloat(kline.v)
            };
            
            // Check if this is a new candle or update to existing one
            const lastIndex = priceChart.data.labels.length - 1;
            const lastTime = new Date(candle.time).toLocaleString();
            
            if (lastIndex >= 0 && priceChart.data.labels[lastIndex] === lastTime) {
                // Update existing candle
                priceChart.data.datasets[0].data[lastIndex] = candle.close;
                priceChart.data.datasets[1].data[lastIndex] = candle.volume;
            } else {
                // Add new candle
                priceChart.data.labels.push(lastTime);
                priceChart.data.datasets[0].data.push(candle.close);
                priceChart.data.datasets[1].data.push(candle.volume);
                
                // Remove oldest candle if we have too many
                if (priceChart.data.labels.length > 100) {
                    priceChart.data.labels.shift();
                    priceChart.data.datasets[0].data.shift();
                    priceChart.data.datasets[1].data.shift();
                }
            }
            
            priceChart.update();
            
            // Recalculate indicators with new data
            const prices = priceChart.data.datasets[0].data;
            calculateIndicatorsFromPrices(prices);
        }
    }
    
    function fetchMarketDepth() {
        depthLoading.style.display = 'block';
        
        fetch(`/api/depth/${symbol}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data || (!data.bids && !data.asks)) {
                    console.error('No market depth data received');
                    return;
                }
                
                createDepthChart(data);
            })
            .catch(error => {
                console.error('Error fetching market depth:', error);
            })
            .finally(() => {
                depthLoading.style.display = 'none';
            });
    }
    
    function createDepthChart(depthData) {
        const ctx = document.getElementById('depthChart').getContext('2d');
        
        // Format data for Chart.js
        const bids = depthData.bids.slice(0, 20).map(b => ({ price: parseFloat(b[0]), quantity: parseFloat(b[1]) }));
        const asks = depthData.asks.slice(0, 20).map(a => ({ price: parseFloat(a[0]), quantity: parseFloat(a[1]) }));
        
        // Sort by price
        bids.sort((a, b) => b.price - a.price);
        asks.sort((a, b) => a.price - b.price);
        
        const bidPrices = bids.map(b => b.price);
        const bidQuantities = bids.map(b => b.quantity);
        const askPrices = asks.map(a => a.price);
        const askQuantities = asks.map(a => a.quantity);
        
        // Destroy previous chart if it exists
        if (depthChart) {
            depthChart.destroy();
        }
        
        // Create new chart
        depthChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [...bidPrices.reverse(), ...askPrices],
                datasets: [
                    {
                        label: 'Bids',
                        data: [...bidQuantities.reverse(), ...Array(askPrices.length).fill(null)],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        pointRadius: 0,
                        fill: true
                    },
                    {
                        label: 'Asks',
                        data: [...Array(bidPrices.length).fill(null), ...askQuantities],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        pointRadius: 0,
                        fill: true
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
    }
    
    function calculateIndicators(klines) {
        const closePrices = klines.map(k => k.close);
        calculateIndicatorsFromPrices(closePrices);
    }
    
    function calculateIndicatorsFromPrices(prices) {
        // Calculate RSI
        fetch(`/api/technical/rsi/${symbol}?period=14`)
            .then(response => response.json())
            .then(data => {
                if (data && data.rsi !== null) {
                    updateRSI(data.rsi);
                }
            })
            .catch(error => console.error('Error fetching RSI:', error));
        
        // Calculate Moving Averages
        fetch(`/api/technical/ma/${symbol}`)
            .then(response => response.json())
            .then(data => {
                if (data) {
                    sma20.textContent = data.sma20 ? formatPrice(data.sma20) : 'N/A';
                    sma50.textContent = data.sma50 ? formatPrice(data.sma50) : 'N/A';
                    ema12.textContent = data.ema12 ? formatPrice(data.ema12) : 'N/A';
                    ema26.textContent = data.ema26 ? formatPrice(data.ema26) : 'N/A';
                }
            })
            .catch(error => console.error('Error fetching moving averages:', error));
    }
    
    function updateRSI(rsiValue) {
        // Update RSI value
        const rsiElement = document.getElementById('rsi-value');
        const rsiProgress = document.getElementById('rsi-progress');
        
        if (rsiElement && rsiProgress) {
            rsiElement.textContent = rsiValue.toFixed(2);
            rsiProgress.style.width = `${rsiValue}%`;
            rsiProgress.textContent = rsiValue.toFixed(2);
            
            // Color based on RSI value
            if (rsiValue >= 70) {
                rsiProgress.classList.remove('bg-primary', 'bg-warning');
                rsiProgress.classList.add('bg-danger');
            } else if (rsiValue <= 30) {
                rsiProgress.classList.remove('bg-primary', 'bg-danger');
                rsiProgress.classList.add('bg-success');
            } else {
                rsiProgress.classList.remove('bg-danger', 'bg-success');
                rsiProgress.classList.add('bg-primary');
            }
        }
    }
    
    function setupIntervalButtons() {
        const intervalButtons = document.querySelectorAll('.interval-btn');
        
        intervalButtons.forEach(button => {
            button.addEventListener('click', function() {
                const interval = this.getAttribute('data-interval');
                
                // Update active button
                intervalButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // Update socket subscription
                socket.emit('unsubscribe', `kline_${symbol.toLowerCase()}_${currentInterval}`);
                currentInterval = interval;
                socket.emit('subscribe', `kline_${symbol.toLowerCase()}_${currentInterval}`);
                
                // Fetch new data
                fetchKlines(interval);
            });
        });
    }
    
    function formatPrice(price) {
        if (price >= 1000) {
            return `$${price.toFixed(2)}`;
        } else if (price >= 1) {
            return `$${price.toFixed(4)}`;
        } else if (price >= 0.01) {
            return `$${price.toFixed(6)}`;
        } else {
            return `$${price.toFixed(8)}`;
        }
    }
    
    function formatVolume(volume) {
        if (volume >= 1000000000) {
            return `${(volume / 1000000000).toFixed(2)}B`;
        } else if (volume >= 1000000) {
            return `${(volume / 1000000).toFixed(2)}M`;
        } else if (volume >= 1000) {
            return `${(volume / 1000).toFixed(2)}K`;
        } else {
            return volume.toFixed(2);
        }
    }
    
    function showChartLoading(show) {
        chartLoading.style.display = show ? 'block' : 'none';
        document.getElementById('priceChart').style.display = show ? 'none' : 'block';
    }
    
    function showChartError(show, message = 'Error loading chart data') {
        chartError.classList.toggle('d-none', !show);
        chartError.textContent = message;
    }
});
