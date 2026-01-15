/**
 * DocScope API Client
 */

class API {
    constructor() {
        this.baseUrl = Config.api.baseUrl;
        this.headers = Config.api.headers;
        this.timeout = Config.api.timeout;
    }
    
    /**
     * Make an API request
     */
    async request(method, endpoint, data = null, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            method,
            headers: { ...this.headers, ...options.headers },
            ...options
        };
        
        if (data) {
            if (method === 'GET') {
                const params = new URLSearchParams(data);
                url += '?' + params.toString();
            } else {
                config.body = JSON.stringify(data);
            }
        }
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }
    
    // Document endpoints
    async getDocuments(params = {}) {
        return this.request('GET', '/documents', params);
    }
    
    async getDocument(id) {
        return this.request('GET', `/documents/${id}`);
    }
    
    async createDocument(data) {
        return this.request('POST', '/documents', data);
    }
    
    async updateDocument(id, data) {
        return this.request('PUT', `/documents/${id}`, data);
    }
    
    async deleteDocument(id) {
        return this.request('DELETE', `/documents/${id}`);
    }
    
    // Search endpoints
    async search(query, options = {}) {
        return this.request('POST', '/search', {
            query,
            limit: options.limit || Config.search.defaultLimit,
            offset: options.offset || 0,
            filters: options.filters,
            highlight: options.highlight !== false,
            facets: options.facets !== false,
            sort_by: options.sortBy
        });
    }
    
    async getSuggestions(query) {
        return this.request('GET', '/search/suggestions', { q: query });
    }
    
    async findSimilar(documentId, limit = 10) {
        return this.request('GET', `/search/similar/${documentId}`, { limit });
    }
    
    // Category endpoints
    async getCategories() {
        return this.request('GET', '/categories');
    }
    
    async getCategoryTree() {
        return this.request('GET', '/categories/tree');
    }
    
    async createCategory(data) {
        return this.request('POST', '/categories', data);
    }
    
    // Tag endpoints
    async getTags() {
        return this.request('GET', '/tags');
    }
    
    async getPopularTags(limit = 20) {
        return this.request('GET', '/tags/popular', { limit });
    }
    
    async getTagCloud() {
        return this.request('GET', '/tags/cloud');
    }
    
    async createTag(data) {
        return this.request('POST', '/tags', data);
    }
    
    // Scanner endpoints
    async scan(paths, options = {}) {
        return this.request('POST', '/scanner/scan', {
            paths,
            recursive: options.recursive !== false,
            incremental: options.incremental,
            since: options.since
        });
    }
    
    async getSupportedFormats() {
        return this.request('GET', '/scanner/formats');
    }
    
    // Statistics endpoints
    async getStats() {
        return this.request('GET', '/health/stats');
    }
    
    async getMetrics() {
        return this.request('GET', '/health/metrics');
    }
    
    // Export endpoint
    async exportDocuments(format, options = {}) {
        const response = await fetch(`${this.baseUrl}/export`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                format,
                query: options.query,
                category: options.category,
                tags: options.tags
            })
        });
        
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        
        return response.blob();
    }
}

// Create global API instance
const api = new API();