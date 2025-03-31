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
    let lastFetchTime = 0;
    // InitializeMIT_INTERVAL = 60000; // 1 minute
    fetchCryptocurrencies();
    // Initialize
    // Event listenersies();
    searchInput.addEventListener('input', debounce(handleSearch, 300));
    searchButton.addEventListener('click', handleSearch);
    sortByNameBtn.addEventListener('click', () => handleSort('symbol'));
    sortByPriceBtn.addEventListener('click', () => handleSort('price'));
    pairFilterRadios.forEach(radio => {ck', () => handleSort('symbol'));
        radio.addEventListener('change', handleFilterChange);('price'));
    });rFilterRadios.forEach(radio => {
        radio.addEventListener('change', handleFilterChange);
    // Functions
    async function fetchCryptocurrencies() {
        showLoading(true);ons
        showError(false);currencies() {wait fetch('/api/prices');
ency data');
        try {
            const response = await fetch('/api/prices'); Skipping fetch.');
            if (!response.ok) throw new Error('Failed to fetch cryptocurrency data');            return;        } catch (error) {
            const data = await response.json();

            if (!data || data.length === 0) {
                showNoResults(true);
                cryptoList.innerHTML = '<div class="alert alert-info">No cryptocurrencies available.</div>';
                return;            showLoading(true);    function renderCryptoList(data) {
            }/prices');isting content
ok) throw new Error(`HTTP error! status: ${response.status}`);
            allCryptos = data.map(crypto => ({
                ...crypto, = '<div class="alert alert-info">No data available</div>';
                parsedPrice: parseFloat(crypto.price)            if (!data || data.length === 0) {            return;
            }));e);
t.innerHTML = '<div class="alert alert-info">No cryptocurrencies available.</div>';
            applyFilterAndSort();
        } catch (error) {ment('div');
            console.error('Error fetching cryptocurrency data:', error); mb-4';
            showError(true);ap(crypto => ({
        } finally {       ...crypto,       <div class="card h-100">
            showLoading(false);           parsedPrice: parseFloat(crypto.price)               <div class="card-body text-center">
        }        }));                    <h5 class="card-title">${crypto.symbol}</h5>
    }to.price)}</p>
    );s="card-text">24h Change: ${crypto.price_change_24h.toFixed(2)}%</p>
    function applyFilterAndSort() {
        // Step 1: Apply filter fetching prices:', error);
        filteredCryptos = allCryptos.filter(crypto => {
            // Apply pair filter);
            if (currentFilter === 'usdt' && !crypto.symbol.endsWith('USDT')) {howLoading(false);
                return false;
            }
            if (currentFilter === 'btc' && !crypto.symbol.endsWith('BTC')) {ce(price) {
                return false; applyFilterAndSort() {ormat price based on its magnitude
            }
            
            // Apply search termter) {
            if (searchTerm && !crypto.symbol.toLowerCase().includes(searchTerm.toLowerCase())) {f (currentFilter === 'usdt' && !crypto.symbol.endsWith('USDT')) {eturn `$${price.toFixed(4)}`;
                return false;    return false;se if (price >= 0.01) {
            }d(6)}`;
             if (currentFilter === 'btc' && !crypto.symbol.endsWith('BTC')) {lse {
            return true;        return false;    return `$${price.toFixed(8)}`;
        });
        
        // Step 2: Apply sort
        filteredCryptos.sort((a, b) => {e().includes(searchTerm.toLowerCase())) {
            if (currentSort.field === 'symbol') {
                return currentSort.direction === 'asc' 
                    ? a.symbol.localeCompare(b.symbol)
                    : b.symbol.localeCompare(a.symbol);
            } else if (currentSort.field === 'price') {
                return currentSort.direction === 'asc'
                    ? a.parsedPrice - b.parsedPriceep 2: Apply sorturrentSort.field === field) {
                    : b.parsedPrice - a.parsedPrice;os.sort((a, b) => {rt.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } if (currentSort.field === 'symbol') {lse {
            return 0;        return currentSort.direction === 'asc'     currentSort.field = field;
        });bol)
        bol.localeCompare(a.symbol);
        // Step 3: Render filtered and sorted list       } else if (currentSort.field === 'price') {   
        renderCryptoList();            return currentSort.direction === 'asc'    // Update button active states
    }ce - b.parsedPriceoggle('active', field === 'symbol');
    
    function renderCryptoList() {
        // Show no results message if no cryptos match the filter
        if (filteredCryptos.length === 0) {
            showNoResults(true);
            cryptoList.innerHTML = '';/ Step 3: Render filtered and sorted listion handleFilterChange(event) {
            return;renderCryptoList();currentFilter = event.target.value;
        }
        
        showNoResults(false);
        ults message if no cryptos match the filterng(show) {
        // Build HTML for crypto listif (filteredCryptos.length === 0) {loadingIndicator.style.display = show ? 'block' : 'none';
        let html = '';
        
        filteredCryptos.forEach(crypto => {return; showError(show) {
            const formattedPrice = formatPrice(crypto.parsedPrice);ggle('d-none', !show);
            
            html += `
                <div class="col-md-3 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">${crypto.symbol}</h5>
                            <p class="card-text">Price: ${formattedPrice}</p>
                        </div>
                        <div class="card-footer bg-transparent border-top-0">
                            <a href="/crypto/${crypto.symbol}" class="btn btn-primary btn-sm stretched-link">View Details</a>t);
                        </div>lass="col-md-3 mb-4">setTimeout(() => func.apply(this, args), delay);
                    </div>      <div class="card h-100">
                </div>             <div class="card-body">
            `;                    <h5 class="card-title">${crypto.symbol}</h5>
        });="card-text">Price: ${formattedPrice}</p>                        </div>                        <div class="card-footer bg-transparent border-top-0">                            <a href="/crypto/${crypto.symbol}" class="btn btn-primary btn-sm stretched-link">View Details</a>                        </div>                    </div>                </div>            `;        });                cryptoList.innerHTML = html;    }        function formatPrice(price) {        // Format price based on its magnitude        if (price >= 1000) {            return `$${price.toFixed(2)}`;        } else if (price >= 1) {            return `$${price.toFixed(4)}`;        } else if (price >= 0.01) {            return `$${price.toFixed(6)}`;        } else {            return `$${price.toFixed(8)}`;        }    }        function handleSearch() {        searchTerm = searchInput.value.trim();        applyFilterAndSort();    }        function handleSort(field) {        // Toggle sort direction if clicking the same field        if (currentSort.field === field) {            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';        } else {            currentSort.field = field;            currentSort.direction = 'asc';        }                // Update button active states        sortByNameBtn.classList.toggle('active', field === 'symbol');        sortByPriceBtn.classList.toggle('active', field === 'price');                applyFilterAndSort();    }        function handleFilterChange(event) {        currentFilter = event.target.value;        applyFilterAndSort();    }        function showLoading(show) {        loadingIndicator.style.display = show ? 'block' : 'none';    }        function showError(show) {        errorMessage.classList.toggle('d-none', !show);    }        function showNoResults(show) {        noResults.classList.toggle('d-none', !show);    }
        
        cryptoList.innerHTML = html;function debounce(func, delay) {
    }
    
    function formatPrice(price) {eout);
        // Format price based on its magnitudec.apply(this, args), delay);
        if (price >= 1000) {
            return `$${price.toFixed(2)}`;
        } else if (price >= 1) {
            return `$${price.toFixed(4)}`;        } else if (price >= 0.01) {            return `$${price.toFixed(6)}`;        } else {            return `$${price.toFixed(8)}`;        }    }        function handleSearch() {        searchTerm = searchInput.value.trim();        applyFilterAndSort();    }        function handleSort(field) {        // Toggle sort direction if clicking the same field        if (currentSort.field === field) {            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';        } else {            currentSort.field = field;            currentSort.direction = 'asc';        }                // Update button active states        sortByNameBtn.classList.toggle('active', field === 'symbol');        sortByPriceBtn.classList.toggle('active', field === 'price');                applyFilterAndSort();    }        function handleFilterChange(event) {        currentFilter = event.target.value;        applyFilterAndSort();    }        function showLoading(show) {        const loadingIndicator = document.getElementById('crypto-loading');        loadingIndicator.style.display = show ? 'block' : 'none';    }        function showError(show) {        const errorMessage = document.getElementById('error-message');        errorMessage.style.display = show ? 'block' : 'none';    }        function showNoResults(show) {        noResults.classList.toggle('d-none', !show);    }    function debounce(func, delay) {        let timeout;        return function (...args) {            clearTimeout(timeout);            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    }
});
