/**
 * DocScope Main Application
 */

class DocScopeApp {
    constructor() {
        this.currentTheme = Config.ui.theme;
        this.ws = null;
        this.wsReconnectAttempts = 0;
        
        this.init();
    }
    
    /**
     * Initialize application
     */
    async init() {
        // Load saved settings
        this.loadSettings();
        
        // Initialize theme
        this.setTheme(this.currentTheme);
        
        // Initialize navigation
        this.initNavigation();
        
        // Initialize pages
        Pages.initSearchPage();
        Pages.initBrowsePage();
        Pages.initCategoriesPage();
        Pages.initTagsPage();
        Pages.initStatsPage();
        
        // Initialize modals
        this.initModals();
        
        // Initialize WebSocket if enabled
        if (Config.features.websocket) {
            this.initWebSocket();
        }
        
        // Initialize theme toggle
        this.initThemeToggle();
        
        // Initialize settings
        this.initSettings();
        
        // Handle URL parameters
        this.handleUrlParams();
        
        // Show welcome message
        this.showWelcome();
    }
    
    /**
     * Initialize navigation
     */
    initNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                this.navigateToPage(page);
            });
        });
    }
    
    /**
     * Navigate to page
     */
    navigateToPage(pageName) {
        // Update nav active state
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === pageName);
        });
        
        // Hide all pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        
        // Show selected page
        const page = document.getElementById(`${pageName}-page`);
        if (page) {
            page.classList.add('active');
            Pages.currentPage = pageName;
            
            // Trigger page-specific actions
            switch(pageName) {
                case 'browse':
                    if (!page.dataset.loaded) {
                        Pages.loadDocuments();
                        page.dataset.loaded = 'true';
                    }
                    break;
                case 'categories':
                    if (!page.dataset.loaded) {
                        Pages.loadCategoryTree();
                        page.dataset.loaded = 'true';
                    }
                    break;
                case 'tags':
                    if (!page.dataset.loaded) {
                        Pages.loadTagCloud();
                        page.dataset.loaded = 'true';
                    }
                    break;
                case 'stats':
                    Pages.loadStatistics();
                    break;
            }
        }
    }
    
    /**
     * Initialize modals
     */
    initModals() {
        // Close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.closest('.modal').classList.remove('active');
            });
        });
        
        // Click outside to close
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });
        
        // Document viewer actions
        document.getElementById('doc-export').addEventListener('click', () => {
            this.exportDocument();
        });
        
        document.getElementById('doc-edit').addEventListener('click', () => {
            this.editDocument();
        });
        
        // Settings button
        document.getElementById('settings-btn').addEventListener('click', () => {
            document.getElementById('settings-modal').classList.add('active');
        });
        
        // Save settings button
        document.getElementById('settings-save').addEventListener('click', () => {
            this.saveSettings();
        });
    }
    
    /**
     * Initialize WebSocket connection
     */
    initWebSocket() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }
        
        try {
            this.ws = new WebSocket(Config.websocket.url);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.wsReconnectAttempts = 0;
                Toast.success('Connected to server');
                
                // Subscribe to updates
                this.ws.send(JSON.stringify({
                    type: 'subscribe',
                    topic: 'documents'
                }));
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                
                // Attempt reconnection
                if (this.wsReconnectAttempts < Config.websocket.maxReconnectAttempts) {
                    this.wsReconnectAttempts++;
                    setTimeout(() => {
                        this.initWebSocket();
                    }, Config.websocket.reconnectInterval);
                }
            };
            
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
        }
    }
    
    /**
     * Handle WebSocket message
     */
    handleWebSocketMessage(message) {
        switch(message.type) {
            case 'document_update':
                this.handleDocumentUpdate(message);
                break;
                
            case 'scan_progress':
                this.handleScanProgress(message);
                break;
                
            case 'notification':
                Toast.info(message.message);
                break;
                
            case 'pong':
                // Heartbeat response
                break;
                
            default:
                console.log('Unknown WebSocket message:', message);
        }
    }
    
    /**
     * Handle document update
     */
    handleDocumentUpdate(message) {
        // Refresh current page if needed
        if (Pages.currentPage === 'browse') {
            Pages.loadDocuments();
        }
        
        Toast.info(`Document ${message.action}: ${message.document_id}`);
    }
    
    /**
     * Handle scan progress
     */
    handleScanProgress(message) {
        Toast.info(`Scan progress: ${Math.round(message.progress * 100)}%`);
    }
    
    /**
     * Initialize theme toggle
     */
    initThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        
        themeToggle.addEventListener('click', () => {
            const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
            this.setTheme(newTheme);
        });
    }
    
    /**
     * Set theme
     */
    setTheme(theme) {
        this.currentTheme = theme;
        
        const themeLink = document.getElementById('theme-stylesheet');
        themeLink.href = `/static/css/themes/${theme}.css`;
        
        // Update toggle icon
        const sunIcon = document.querySelector('.icon-sun');
        const moonIcon = document.querySelector('.icon-moon');
        
        if (theme === 'dark') {
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'block';
        } else {
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
        }
        
        // Save preference
        localStorage.setItem(Config.storage.theme, theme);
    }
    
    /**
     * Initialize settings
     */
    initSettings() {
        // Load current settings into form
        document.getElementById('setting-theme').value = this.currentTheme;
        document.getElementById('setting-results').value = Config.ui.resultsPerPage;
        document.getElementById('setting-fuzzy').checked = Config.search.fuzzySearch;
        document.getElementById('setting-api').value = Config.api.baseUrl;
    }
    
    /**
     * Load settings
     */
    loadSettings() {
        const settings = Utils.retrieve(Config.storage.settings, {});
        
        if (settings.theme) {
            this.currentTheme = settings.theme;
        }
        
        if (settings.resultsPerPage) {
            Config.ui.resultsPerPage = settings.resultsPerPage;
        }
        
        if (settings.fuzzySearch !== undefined) {
            Config.search.fuzzySearch = settings.fuzzySearch;
        }
    }
    
    /**
     * Save settings
     */
    saveSettings() {
        const settings = {
            theme: document.getElementById('setting-theme').value,
            resultsPerPage: parseInt(document.getElementById('setting-results').value),
            fuzzySearch: document.getElementById('setting-fuzzy').checked,
            apiUrl: document.getElementById('setting-api').value
        };
        
        // Apply settings
        this.setTheme(settings.theme);
        Config.ui.resultsPerPage = settings.resultsPerPage;
        Config.search.fuzzySearch = settings.fuzzySearch;
        Config.api.baseUrl = settings.apiUrl;
        
        // Save to storage
        Utils.store(Config.storage.settings, settings);
        
        // Close modal
        document.getElementById('settings-modal').classList.remove('active');
        
        Toast.success('Settings saved');
    }
    
    /**
     * Handle URL parameters
     */
    handleUrlParams() {
        const params = Utils.getUrlParams();
        
        if (params.q) {
            // Search query in URL
            document.getElementById('search-input').value = params.q;
            Pages.performSearch(params.page || 1);
        }
        
        if (params.page) {
            // Page navigation
            const pageName = params.page;
            if (document.getElementById(`${pageName}-page`)) {
                this.navigateToPage(pageName);
            }
        }
    }
    
    /**
     * Export document
     */
    async exportDocument() {
        const modal = document.getElementById('doc-viewer');
        const title = document.getElementById('doc-title').textContent;
        
        try {
            const blob = await api.exportDocuments('markdown', {
                query: `title:"${title}"`
            });
            
            Utils.downloadBlob(blob, `${title}.md`);
            Toast.success('Document exported');
            
        } catch (error) {
            Toast.error(`Export failed: ${error.message}`);
        }
    }
    
    /**
     * Edit document
     */
    editDocument() {
        Toast.info('Document editing not implemented yet');
    }
    
    /**
     * Show welcome message
     */
    showWelcome() {
        const hasVisited = localStorage.getItem('docscope-visited');
        
        if (!hasVisited) {
            Toast.info('Welcome to DocScope! Start by searching for documentation or browsing documents.');
            localStorage.setItem('docscope-visited', 'true');
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DocScopeApp();
});