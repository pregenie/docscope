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
        
        // Initialize single page app
        Pages.initSearchPage();
        Pages.loadStatistics();  // Load stats on startup
        
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
     * Initialize navigation (removed - single page now)
     */
    initNavigation() {
        // No longer needed - single page app
    }
    
    /**
     * Navigate to page (removed - single page now)
     */
    navigateToPage(pageName) {
        // No longer needed - single page app
        // Everything is on the search page now
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
                
            case 'scan_update':
                // Real-time scan updates
                this.handleScanUpdate(message);
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
     * Handle real-time scan updates
     */
    handleScanUpdate(message) {
        // Update the scanned counter
        if (message.scanned !== undefined) {
            const scannedEl = document.getElementById('stat-scanned');
            if (scannedEl) {
                scannedEl.textContent = message.scanned.toLocaleString();
                // Add pulse animation
                scannedEl.parentElement.classList.add('pulse');
                setTimeout(() => {
                    scannedEl.parentElement.classList.remove('pulse');
                }, 300);
            }
        }
        
        // Update documents count
        if (message.documents !== undefined) {
            document.getElementById('stat-total-docs').textContent = message.documents.toLocaleString();
        }
        
        // Update categories count
        if (message.categories !== undefined) {
            document.getElementById('stat-categories').textContent = message.categories.toLocaleString();
        }
        
        // Update tags count
        if (message.tags !== undefined) {
            document.getElementById('stat-tags').textContent = message.tags.toLocaleString();
        }
        
        // Update index size
        if (message.indexSize !== undefined) {
            const sizeInMB = (message.indexSize / (1024 * 1024)).toFixed(1);
            document.getElementById('stat-index-size').textContent = `${sizeInMB} MB`;
        }
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
        const settings = JSON.parse(localStorage.getItem('docscope-settings') || '{}');
        
        if (!hasVisited) {
            localStorage.setItem('docscope-visited', 'true');
            
            // Check if origin is set
            if (!settings.directory) {
                // First time user - prompt to set origin
                setTimeout(() => {
                    Toast.info('Welcome to DocScope! Let\'s start by selecting your documentation folder.');
                    settingsDialog.open();
                }, 500);
            } else {
                Toast.info('Welcome to DocScope! Start by searching for documentation or browsing documents.');
            }
        } else if (!settings.directory) {
            // Returning user but no origin set
            Toast.info('Please select a documentation folder to get started.');
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DocScopeApp();
});