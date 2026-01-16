/**
 * DocScope Page Controllers
 */

const Pages = {
    currentPage: 'search',
    searchTimeout: null,
    currentSearchPage: 1,
    currentBrowsePage: 1,
    
    /**
     * Initialize search page
     */
    initSearchPage() {
        const searchInput = document.getElementById('search-input');
        const searchBtn = document.getElementById('search-btn');
        const filterFormat = document.getElementById('filter-format');
        const filterCategory = document.getElementById('filter-category');
        const filterSort = document.getElementById('filter-sort');
        
        // Search input handler with debounce
        searchInput.addEventListener('input', Utils.debounce(() => {
            if (searchInput.value.length >= Config.search.minQueryLength) {
                this.performSearch();
            }
        }, Config.search.debounceDelay));
        
        // Search button handler
        searchBtn.addEventListener('click', () => {
            this.performSearch();
        });
        
        // Enter key handler
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        // Filter handlers
        [filterFormat, filterCategory, filterSort].forEach(filter => {
            filter.addEventListener('change', () => {
                if (searchInput.value.length >= Config.search.minQueryLength) {
                    this.performSearch();
                }
            });
        });
        
        // Load categories
        this.loadCategories();
    },
    
    /**
     * Perform search
     */
    async performSearch(page = 1) {
        const searchInput = document.getElementById('search-input');
        const query = searchInput.value.trim();
        
        if (query.length < Config.search.minQueryLength) {
            return;
        }
        
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = '';
        resultsContainer.appendChild(Components.createLoadingSpinner());
        
        try {
            const filters = {};
            const filterFormat = document.getElementById('filter-format').value;
            const filterCategory = document.getElementById('filter-category').value;
            
            if (filterFormat) filters.format = filterFormat;
            if (filterCategory) filters.category = filterCategory;
            
            const sortBy = document.getElementById('filter-sort').value;
            const limit = Config.search.defaultLimit;
            const offset = (page - 1) * limit;
            
            const results = await api.search(query, {
                filters,
                sortBy,
                limit,
                offset
            });
            
            resultsContainer.innerHTML = '';
            
            if (results.results.length === 0) {
                resultsContainer.appendChild(
                    Components.createEmptyState('No results found for your search')
                );
                
                // Show suggestions if available
                if (results.suggestions && results.suggestions.length > 0) {
                    const suggestionsDiv = document.createElement('div');
                    suggestionsDiv.className = 'suggestions';
                    suggestionsDiv.innerHTML = `
                        <h3>Did you mean:</h3>
                        ${results.suggestions.map(s => 
                            `<a href="#" class="suggestion">${s}</a>`
                        ).join(' ')}
                    `;
                    resultsContainer.appendChild(suggestionsDiv);
                    
                    // Add click handlers for suggestions
                    suggestionsDiv.querySelectorAll('.suggestion').forEach(link => {
                        link.addEventListener('click', (e) => {
                            e.preventDefault();
                            searchInput.value = e.target.textContent;
                            this.performSearch();
                        });
                    });
                }
            } else {
                // Display results
                results.results.forEach(result => {
                    resultsContainer.appendChild(Components.createSearchResult(result));
                });
                
                // Add pagination if needed
                if (results.total > limit) {
                    const totalPages = Math.ceil(results.total / limit);
                    const pagination = Components.createPagination(
                        page,
                        totalPages,
                        (newPage) => this.performSearch(newPage)
                    );
                    resultsContainer.appendChild(pagination);
                }
                
                // Update URL
                Utils.updateUrlParams({ q: query, page: page > 1 ? page : null });
            }
            
            // Store search in recent searches
            this.addRecentSearch(query);
            
        } catch (error) {
            resultsContainer.innerHTML = '';
            resultsContainer.appendChild(
                Components.createEmptyState(`Search failed: ${error.message}`)
            );
            Toast.error(`Search failed: ${error.message}`);
        }
    },
    
    /**
     * Initialize browse page
     */
    initBrowsePage() {
        const refreshBtn = document.getElementById('refresh-btn');
        const scanBtn = document.getElementById('scan-btn');
        
        refreshBtn.addEventListener('click', () => {
            this.loadDocuments();
        });
        
        scanBtn.addEventListener('click', () => {
            this.showScanDialog();
        });
        
        // Load documents when page is shown
        this.loadDocuments();
    },
    
    /**
     * Load documents
     */
    async loadDocuments(filters = {}, page = 1) {
        const gridContainer = document.getElementById('document-grid');
        gridContainer.innerHTML = '';
        gridContainer.appendChild(Components.createLoadingSpinner());
        
        try {
            const limit = 24;
            const offset = (page - 1) * limit;
            
            const response = await api.getDocuments({
                ...filters,
                limit,
                offset
            });
            
            gridContainer.innerHTML = '';
            
            if (response.items.length === 0) {
                gridContainer.appendChild(
                    Components.createEmptyState('No documents found')
                );
            } else {
                response.items.forEach(doc => {
                    gridContainer.appendChild(Components.createDocumentCard(doc));
                });
                
                // Add pagination
                const paginationContainer = document.getElementById('pagination');
                paginationContainer.innerHTML = '';
                
                if (response.total > limit) {
                    const totalPages = Math.ceil(response.total / limit);
                    const pagination = Components.createPagination(
                        page,
                        totalPages,
                        (newPage) => this.loadDocuments(filters, newPage)
                    );
                    paginationContainer.appendChild(pagination);
                }
            }
            
        } catch (error) {
            gridContainer.innerHTML = '';
            gridContainer.appendChild(
                Components.createEmptyState(`Failed to load documents: ${error.message}`)
            );
            Toast.error(`Failed to load documents: ${error.message}`);
        }
    },
    
    /**
     * Initialize categories page
     */
    initCategoriesPage() {
        const addBtn = document.getElementById('add-category-btn');
        
        addBtn.addEventListener('click', () => {
            this.showAddCategoryDialog();
        });
        
        this.loadCategoryTree();
    },
    
    /**
     * Load category tree
     */
    async loadCategoryTree() {
        const treeContainer = document.getElementById('category-tree');
        treeContainer.innerHTML = '';
        treeContainer.appendChild(Components.createLoadingSpinner());
        
        try {
            console.log('Loading categories...');
            const categories = await api.getCategoryTree();
            console.log('Categories loaded:', categories);
            
            treeContainer.innerHTML = '';
            
            // Check if it's an array or has a nested structure
            const categoryList = Array.isArray(categories) ? categories : (categories.items || []);
            
            if (categoryList.length === 0) {
                treeContainer.appendChild(
                    Components.createEmptyState('No categories found. Click "Add Category" to create your first category.')
                );
            } else {
                categoryList.forEach(category => {
                    treeContainer.appendChild(Components.createCategoryItem(category));
                });
            }
            
        } catch (error) {
            console.error('Failed to load categories:', error);
            treeContainer.innerHTML = '';
            treeContainer.appendChild(
                Components.createEmptyState(`Failed to load categories: ${error.message}`)
            );
            Toast.error(`Failed to load categories: ${error.message}`);
        }
    },
    
    /**
     * Initialize tags page
     */
    initTagsPage() {
        const addBtn = document.getElementById('add-tag-btn');
        
        addBtn.addEventListener('click', () => {
            this.showAddTagDialog();
        });
        
        this.loadTagCloud();
    },
    
    /**
     * Load tag cloud
     */
    async loadTagCloud() {
        const cloudContainer = document.getElementById('tag-cloud');
        cloudContainer.innerHTML = '';
        cloudContainer.appendChild(Components.createLoadingSpinner());
        
        try {
            console.log('Loading tags...');
            const response = await api.getTagCloud();
            console.log('Tags loaded:', response);
            
            cloudContainer.innerHTML = '';
            
            // Handle both direct array and wrapped response
            const tagList = response.tags || response;
            
            if (!tagList || (Array.isArray(tagList) && tagList.length === 0)) {
                cloudContainer.appendChild(
                    Components.createEmptyState('No tags found. Tags will appear as documents are scanned and categorized.')
                );
            } else {
                tagList.forEach(tag => {
                    cloudContainer.appendChild(Components.createTagItem(tag));
                });
            }
            
        } catch (error) {
            console.error('Failed to load tags:', error);
            cloudContainer.innerHTML = '';
            cloudContainer.appendChild(
                Components.createEmptyState(`Failed to load tags: ${error.message}`)
            );
            Toast.error(`Failed to load tags: ${error.message}`);
        }
    },
    
    /**
     * Initialize statistics page
     */
    initStatsPage() {
        this.loadStatistics();
    },
    
    /**
     * Load statistics
     */
    async loadStatistics() {
        try {
            const stats = await api.getStats();
            
            // Update stat cards
            document.getElementById('stat-total-docs').textContent = 
                stats.documents.total.toLocaleString();
            document.getElementById('stat-categories').textContent = 
                stats.organization.categories.toLocaleString();
            document.getElementById('stat-tags').textContent = 
                stats.organization.tags.toLocaleString();
            
            const indexSize = stats.storage.total_size / (1024 * 1024);
            document.getElementById('stat-index-size').textContent = 
                `${indexSize.toFixed(1)} MB`;
            
            // Draw charts if chart library is available
            if (typeof Chart !== 'undefined' && Config.features.charts) {
                this.drawFormatChart(stats.documents.by_format);
                this.drawActivityChart(stats.recent);
            }
            
        } catch (error) {
            Toast.error(`Failed to load statistics: ${error.message}`);
        }
    },
    
    /**
     * Load categories for filter
     */
    async loadCategories() {
        try {
            const categories = await api.getCategories();
            const select = document.getElementById('filter-category');
            
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                select.appendChild(option);
            });
            
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    },
    
    /**
     * Add recent search
     */
    addRecentSearch(query) {
        const key = Config.storage.recentSearches;
        let searches = Utils.retrieve(key, []);
        
        // Remove if exists and add to front
        searches = searches.filter(s => s !== query);
        searches.unshift(query);
        
        // Keep only last 10
        searches = searches.slice(0, 10);
        
        Utils.store(key, searches);
    },
    
    /**
     * Show scan dialog
     */
    showScanDialog() {
        // Would show a dialog to configure and start scanning
        Toast.info('Scan dialog not implemented yet');
    },
    
    /**
     * Show add category dialog
     */
    showAddCategoryDialog() {
        // Would show a dialog to add a new category
        Toast.info('Add category dialog not implemented yet');
    },
    
    /**
     * Show add tag dialog
     */
    showAddTagDialog() {
        // Would show a dialog to add a new tag
        Toast.info('Add tag dialog not implemented yet');
    },
    
    /**
     * Draw format chart
     */
    drawFormatChart(data) {
        // Would draw a chart using Chart.js or similar
        console.log('Format chart data:', data);
    },
    
    /**
     * Draw activity chart
     */
    drawActivityChart(data) {
        // Would draw a chart using Chart.js or similar
        console.log('Activity chart data:', data);
    }
};