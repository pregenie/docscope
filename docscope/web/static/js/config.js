/**
 * DocScope Configuration
 */

const Config = {
    // API Configuration
    api: {
        baseUrl: window.location.origin + '/api/v1',
        timeout: 30000,
        headers: {
            'Content-Type': 'application/json'
        }
    },
    
    // Search Configuration
    search: {
        debounceDelay: 300,
        minQueryLength: 2,
        defaultLimit: 20,
        maxLimit: 100,
        fuzzySearch: true,
        highlightResults: true
    },
    
    // UI Configuration
    ui: {
        theme: localStorage.getItem('theme') || 'light',
        resultsPerPage: parseInt(localStorage.getItem('resultsPerPage') || '20'),
        animationDuration: 250,
        toastDuration: 5000
    },
    
    // WebSocket Configuration
    websocket: {
        url: `ws://${window.location.host}/api/v1/ws/connect`,
        reconnectInterval: 5000,
        maxReconnectAttempts: 5
    },
    
    // Storage Keys
    storage: {
        theme: 'docscope-theme',
        settings: 'docscope-settings',
        recentSearches: 'docscope-recent-searches',
        favorites: 'docscope-favorites'
    },
    
    // Feature Flags
    features: {
        websocket: true,
        liveSearch: true,
        markdown: true,
        syntaxHighlighting: true,
        export: true,
        charts: true
    }
};

// Freeze configuration to prevent modifications
Object.freeze(Config);