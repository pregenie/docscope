/**
 * Directory Picker Dialog
 * Provides a file browser interface for selecting directories
 */

class DirectoryPicker {
    constructor() {
        this.modal = document.getElementById('directory-picker');
        this.currentPath = null;
        this.selectedPath = null;
        this.callback = null;
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Modal controls
        const closeBtn = this.modal.querySelector('.modal-close');
        const cancelBtn = document.getElementById('directory-cancel-btn');
        const selectBtn = document.getElementById('directory-select-btn');
        
        closeBtn?.addEventListener('click', () => this.close());
        cancelBtn?.addEventListener('click', () => this.close());
        selectBtn?.addEventListener('click', () => this.selectDirectory());
        
        // Navigation controls
        const goBtn = document.getElementById('directory-go-btn');
        const homeBtn = document.getElementById('directory-home-btn');
        const pathInput = document.getElementById('directory-path-input');
        
        goBtn?.addEventListener('click', () => {
            const path = pathInput.value.trim();
            if (path) {
                this.navigateTo(path);
            }
        });
        
        homeBtn?.addEventListener('click', () => {
            this.navigateToHome();
        });
        
        pathInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const path = pathInput.value.trim();
                if (path) {
                    this.navigateTo(path);
                }
            }
        });
        
        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }
    
    async open(callback, initialPath = null) {
        this.callback = callback;
        this.modal.classList.add('active');
        
        // Load initial directory
        if (initialPath) {
            await this.navigateTo(initialPath);
        } else {
            await this.navigateToHome();
        }
    }
    
    close() {
        this.modal.classList.remove('active');
        this.currentPath = null;
        this.selectedPath = null;
        this.callback = null;
    }
    
    selectDirectory() {
        if (this.callback && this.currentPath) {
            this.callback(this.currentPath);
            this.close();
        }
    }
    
    async navigateToHome() {
        try {
            const response = await fetch('/api/v1/filesystem/browse');
            const data = await response.json();
            
            if (response.ok) {
                this.displayDirectory(data);
            } else {
                this.showError('Failed to load home directory');
            }
        } catch (error) {
            console.error('Error navigating to home:', error);
            this.showError('Failed to load home directory');
        }
    }
    
    async navigateTo(path) {
        try {
            const response = await fetch(`/api/v1/filesystem/browse?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayDirectory(data);
            } else {
                this.showError(data.detail || 'Failed to load directory');
            }
        } catch (error) {
            console.error('Error navigating to path:', error);
            this.showError('Failed to load directory');
        }
    }
    
    displayDirectory(data) {
        this.currentPath = data.current_path;
        this.selectedPath = data.current_path;
        
        // Update path input
        const pathInput = document.getElementById('directory-path-input');
        if (pathInput) {
            pathInput.value = data.current_path;
        }
        
        // Update breadcrumb
        this.updateBreadcrumb(data.current_path, data.separator);
        
        // Display directory listing
        this.displayListing(data.items, data.parent_path);
    }
    
    updateBreadcrumb(path, separator) {
        const breadcrumb = document.getElementById('directory-breadcrumb');
        if (!breadcrumb) return;
        
        const parts = path.split(separator).filter(p => p);
        let currentPath = separator === '\\' ? '' : '/';
        
        breadcrumb.innerHTML = '';
        
        // Add root
        const rootSpan = document.createElement('span');
        rootSpan.className = 'breadcrumb-item';
        rootSpan.textContent = separator === '\\' ? 'C:\\' : '/';
        rootSpan.onclick = () => this.navigateTo(currentPath);
        breadcrumb.appendChild(rootSpan);
        
        // Add path parts
        parts.forEach((part, index) => {
            if (separator === '\\' && index === 0) {
                currentPath = part + separator;
            } else {
                currentPath += (currentPath.endsWith(separator) ? '' : separator) + part;
            }
            
            const sep = document.createElement('span');
            sep.className = 'breadcrumb-separator';
            sep.textContent = ' › ';
            breadcrumb.appendChild(sep);
            
            const span = document.createElement('span');
            span.className = 'breadcrumb-item';
            span.textContent = part;
            
            const pathCopy = currentPath;
            span.onclick = () => this.navigateTo(pathCopy);
            
            breadcrumb.appendChild(span);
        });
    }
    
    displayListing(items, parentPath) {
        const listing = document.getElementById('directory-listing');
        if (!listing) return;
        
        listing.innerHTML = '';
        
        // Add parent directory if available
        if (parentPath) {
            const parentDiv = this.createListingItem({
                name: '..',
                path: parentPath,
                type: 'directory',
                is_readable: true
            }, true);
            listing.appendChild(parentDiv);
        }
        
        // Add directory items
        items.forEach(item => {
            const itemDiv = this.createListingItem(item);
            listing.appendChild(itemDiv);
        });
        
        if (items.length === 0 && !parentPath) {
            listing.innerHTML = '<div class="no-items">Empty directory</div>';
        }
    }
    
    createListingItem(item, isParent = false) {
        const div = document.createElement('div');
        div.className = 'directory-item';
        
        if (!item.is_readable) {
            div.classList.add('disabled');
        }
        
        // Icon
        const icon = document.createElement('span');
        icon.className = 'directory-item-icon';
        
        if (item.type === 'directory') {
            icon.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M10 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2h-8l-2-2z"/>
                </svg>
            `;
        } else {
            icon.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
            `;
        }
        
        // Name
        const name = document.createElement('span');
        name.className = 'directory-item-name';
        name.textContent = isParent ? 'Parent Directory' : item.name;
        
        // Size (for files)
        const size = document.createElement('span');
        size.className = 'directory-item-size';
        if (item.type === 'file' && item.size !== null) {
            size.textContent = this.formatFileSize(item.size);
        }
        
        div.appendChild(icon);
        div.appendChild(name);
        div.appendChild(size);
        
        // Click handler
        if (item.type === 'directory' && item.is_readable) {
            div.onclick = () => this.navigateTo(item.path);
            div.style.cursor = 'pointer';
        }
        
        return div;
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    showError(message) {
        const listing = document.getElementById('directory-listing');
        if (listing) {
            listing.innerHTML = `<div class="error-message">${message}</div>`;
        }
    }
}

// Initialize directory picker
const directoryPicker = new DirectoryPicker();

// Export for use in other modules
window.directoryPicker = directoryPicker;