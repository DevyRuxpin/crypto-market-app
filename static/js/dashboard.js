document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const cryptoList = document.getElementById('crypto-list');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessage = document.getElementById('error-message');
    const noResults = document.getElementById('no-results');
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const sortByNameBtn = document.getElementById('sortByName');
    const sortByPriceBtn = document.getElementById('sortByPrice');
    const pairFilterRadios = document.querySelectorAll('input[name="pairFilter"]');
    
    // State variables
    let allCryptos = [];
    let filteredCryptos = [];
    let currentSort = { field: 'symbol', direction: 'asc' };
    let currentFilter = 'all';
    let searchTerm = '';
    
    // Initialize
    fetchCryptocurrencies();
    
    // Event listeners
    searchInput.addEventListener('input', debounce(handleSearch, 300));
    searchButton.addEventListener('click', handleSearch);
    sortByNameBtn.addEventListener('click', () => handleSort('symbol'));
    sortByPriceBtn.addEventListener('click', () => handleSort('price'));
    pairFilterRadios.forEach(radio => {
        radio.addEventListener('change', handleFilterChange);
    });
    
    // Functions
    async function fetchCryptocurrencies() {
        try {
            showLoading(true);
            const response = await fetch('/api/prices');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            console.log(`Received ${data.length} cryptocurrencies from API`);
                
            if (!data || data.length === 0) {
                showNoResults(true);
                return;
            }
                
            // Store all cryptos and add parsed price
            allCryptos = data.map(crypto => ({
                ...crypto,
                parsedPrice: parseFloat(crypto.price)
            }));
                
            // Apply initial filter and sort
            applyFilterAndSort();
        } catch (error) {
            console.error('Error fetching prices:', error);
            showError(true);
        } finally {
            showLoading(false);
        }
    }
    
    function applyFilterAndSort() {
        // Step 1: Apply filter
        filteredCryptos = allCryptos.filter(crypto => {
            // Apply pair filter
            if (currentFilter === 'usdt' && !crypto.symbol.endsWith('USDT')) {
                return false;
            }
            if (currentFilter === 'btc' && !crypto.symbol.endsWith('BTC')) {
                return false;
            }
            
            // Apply search term
            if (searchTerm && !crypto.symbol.toLowerCase().includes(searchTerm.toLowerCase())) {
                return false;
            }
            
            return true;
        });
        
        // Step 2: Apply sort
        filteredCryptos.sort((a, b) => {
            if (currentSort.field === 'symbol') {
                return currentSort.direction === 'asc' 
                    ? a.symbol.localeCompare(b.symbol)
                    : b.symbol.localeCompare(a.symbol);
            } else if (currentSort.field === 'price') {
                return currentSort.direction === 'asc'
                    ? a.parsedPrice - b.parsedPrice
                    : b.parsedPrice - a.parsedPrice;
            }
            return 0;
        });
        
        // Step 3: Render filtered and sorted list
        renderCryptoList();
    }
    
    function renderCryptoList() {
        // Show no results message if no cryptos match the filter
        if (filteredCryptos.length === 0) {
            showNoResults(true);
            cryptoList.innerHTML = '';
            return;
        }
        
        showNoResults(false);
        
        // Build HTML for crypto list
        let html = '';
        
        filteredCryptos.forEach(crypto => {
            const formattedPrice = formatPrice(crypto.parsedPrice);
            
            html += `
                <div class="col-md-3 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">${crypto.symbol}</h5>
                            <p class="card-text">Price: ${formattedPrice}</p>
                        </div>
                        <div class="card-footer bg-transparent border-top-0">
                            <a href="/crypto/${crypto.symbol}" class="btn btn-primary btn-sm stretched-link">View Details</a>
                        </div>
                    </div>
                </div>
            `;
        });
        
        cryptoList.innerHTML = html;
    }
    
    function formatPrice(price) {
        // Format price based on its magnitude
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
    
    function handleSearch() {
        searchTerm = searchInput.value.trim();
        applyFilterAndSort();
    }
    
    function handleSort(field) {
        // Toggle sort direction if clicking the same field
        if (currentSort.field === field) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.direction = 'asc';
        }
        
        // Update button active states
        sortByNameBtn.classList.toggle('active', field === 'symbol');
        sortByPriceBtn.classList.toggle('active', field === 'price');
        
        applyFilterAndSort();
    }
    
    function handleFilterChange(event) {
        currentFilter = event.target.value;
        applyFilterAndSort();
    }
    
    function showLoading(show) {
        loadingIndicator.style.display = show ? 'block' : 'none';
    }
    
    function showError(show) {
        errorMessage.classList.toggle('d-none', !show);
    }
    
    function showNoResults(show) {
        noResults.classList.toggle('d-none', !show);
    }

    function debounce(func, delay) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    }
});
