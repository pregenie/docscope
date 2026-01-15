/**
 * DocScope UI Components
 */

const Components = {
    /**
     * Create search result item
     */
    createSearchResult(result) {
        const item = document.createElement('div');
        item.className = 'result-item';
        item.dataset.documentId = result.document_id;
        
        const title = result.highlights && result.highlights.title 
            ? Utils.highlightText(result.title, result.highlights.title)
            : result.title;
        
        const snippet = result.highlights && result.highlights.content
            ? Utils.highlightText(result.snippet, result.highlights.content)
            : result.snippet;
        
        item.innerHTML = `
            <div class="result-title">${title}</div>
            <div class="result-path">${Utils.escapeHtml(result.path)}</div>
            <div class="result-snippet">${snippet}</div>
            <div class="result-meta">
                <span>Score: ${result.score.toFixed(2)}</span>
                ${result.format ? `<span>Format: ${result.format}</span>` : ''}
                ${result.category ? `<span>Category: ${result.category}</span>` : ''}
            </div>
        `;
        
        item.addEventListener('click', () => {
            this.showDocument(result.document_id);
        });
        
        return item;
    },
    
    /**
     * Create document card
     */
    createDocumentCard(doc) {
        const card = document.createElement('div');
        card.className = 'doc-card';
        card.dataset.documentId = doc.id;
        
        const icon = Utils.getFileIcon(doc.path);
        const date = Utils.formatRelativeTime(doc.modified_at);
        const size = Utils.formatFileSize(doc.size);
        
        card.innerHTML = `
            <div class="doc-card-title">
                <span>${icon}</span>
                ${Utils.escapeHtml(doc.title)}
            </div>
            <div class="doc-card-meta">
                ${date} • ${size}
            </div>
            <div class="doc-card-tags">
                ${doc.tags ? doc.tags.map(tag => 
                    `<span class="tag">${Utils.escapeHtml(tag)}</span>`
                ).join('') : ''}
            </div>
        `;
        
        card.addEventListener('click', () => {
            this.showDocument(doc.id);
        });
        
        return card;
    },
    
    /**
     * Create category tree item
     */
    createCategoryItem(category, level = 0) {
        const item = document.createElement('div');
        item.className = 'category-item';
        item.style.paddingLeft = `${level * 20 + 16}px`;
        
        item.innerHTML = `
            <span>${Utils.escapeHtml(category.name)}</span>
            <span class="category-count">(${category.document_count})</span>
        `;
        
        const container = document.createElement('div');
        container.appendChild(item);
        
        if (category.children && category.children.length > 0) {
            const childrenContainer = document.createElement('div');
            childrenContainer.className = 'category-children';
            
            category.children.forEach(child => {
                childrenContainer.appendChild(this.createCategoryItem(child, level + 1));
            });
            
            container.appendChild(childrenContainer);
            
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                childrenContainer.classList.toggle('collapsed');
                item.classList.toggle('collapsed');
            });
        } else {
            item.addEventListener('click', () => {
                this.filterByCategory(category.id);
            });
        }
        
        return container;
    },
    
    /**
     * Create tag cloud item
     */
    createTagItem(tag) {
        const item = document.createElement('span');
        item.className = 'tag';
        
        // Calculate size based on document count
        const minSize = 14;
        const maxSize = 24;
        const maxCount = 100;
        const size = minSize + (maxSize - minSize) * Math.min(tag.document_count / maxCount, 1);
        item.style.fontSize = `${size}px`;
        
        item.innerHTML = `
            ${Utils.escapeHtml(tag.name)}
            <span class="tag-count">${tag.document_count}</span>
        `;
        
        item.addEventListener('click', () => {
            this.filterByTag(tag.name);
        });
        
        return item;
    },
    
    /**
     * Create pagination
     */
    createPagination(currentPage, totalPages, onPageChange) {
        const container = document.createElement('div');
        container.className = 'pagination';
        
        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.className = 'pagination-item';
        prevBtn.innerHTML = '←';
        prevBtn.disabled = currentPage === 1;
        if (currentPage > 1) {
            prevBtn.addEventListener('click', () => onPageChange(currentPage - 1));
        }
        container.appendChild(prevBtn);
        
        // Page numbers
        const maxVisible = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);
        
        if (endPage - startPage < maxVisible - 1) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }
        
        if (startPage > 1) {
            const firstPage = this.createPageButton(1, currentPage, onPageChange);
            container.appendChild(firstPage);
            
            if (startPage > 2) {
                const dots = document.createElement('span');
                dots.className = 'pagination-dots';
                dots.textContent = '...';
                container.appendChild(dots);
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = this.createPageButton(i, currentPage, onPageChange);
            container.appendChild(pageBtn);
        }
        
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const dots = document.createElement('span');
                dots.className = 'pagination-dots';
                dots.textContent = '...';
                container.appendChild(dots);
            }
            
            const lastPage = this.createPageButton(totalPages, currentPage, onPageChange);
            container.appendChild(lastPage);
        }
        
        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.className = 'pagination-item';
        nextBtn.innerHTML = '→';
        nextBtn.disabled = currentPage === totalPages;
        if (currentPage < totalPages) {
            nextBtn.addEventListener('click', () => onPageChange(currentPage + 1));
        }
        container.appendChild(nextBtn);
        
        return container;
    },
    
    createPageButton(page, currentPage, onPageChange) {
        const btn = document.createElement('button');
        btn.className = 'pagination-item';
        if (page === currentPage) {
            btn.classList.add('active');
        }
        btn.textContent = page;
        btn.addEventListener('click', () => onPageChange(page));
        return btn;
    },
    
    /**
     * Show document in modal
     */
    async showDocument(documentId) {
        try {
            const doc = await api.getDocument(documentId);
            
            const modal = document.getElementById('doc-viewer');
            const title = document.getElementById('doc-title');
            const content = document.getElementById('doc-content');
            const metadata = document.getElementById('doc-metadata');
            
            title.textContent = doc.title;
            
            // Render content based on format
            if (doc.format === 'markdown') {
                content.innerHTML = Utils.parseMarkdown(doc.content);
            } else if (doc.format === 'html') {
                content.innerHTML = doc.content;
            } else {
                content.innerHTML = `<pre>${Utils.escapeHtml(doc.content)}</pre>`;
            }
            
            // Show metadata
            metadata.innerHTML = `
                <span>Path: ${doc.path}</span>
                <span>Format: ${doc.format}</span>
                <span>Size: ${Utils.formatFileSize(doc.size)}</span>
                <span>Modified: ${Utils.formatRelativeTime(doc.modified_at)}</span>
            `;
            
            modal.classList.add('active');
            
        } catch (error) {
            Toast.error(`Failed to load document: ${error.message}`);
        }
    },
    
    /**
     * Filter by category
     */
    filterByCategory(categoryId) {
        const searchPage = document.getElementById('search-page');
        const browseBtn = document.querySelector('[data-page="browse"]');
        
        // Switch to browse page
        browseBtn.click();
        
        // Apply filter
        Pages.loadDocuments({ category: categoryId });
    },
    
    /**
     * Filter by tag
     */
    filterByTag(tag) {
        const searchInput = document.getElementById('search-input');
        searchInput.value = `tags:${tag}`;
        Pages.performSearch();
    },
    
    /**
     * Create loading spinner
     */
    createLoadingSpinner() {
        const container = document.createElement('div');
        container.className = 'loading';
        container.innerHTML = '<div class="spinner"></div>';
        return container;
    },
    
    /**
     * Create empty state
     */
    createEmptyState(message = 'No items found') {
        const container = document.createElement('div');
        container.className = 'empty-state';
        container.innerHTML = `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" opacity="0.3">
                <circle cx="11" cy="11" r="8"/>
                <path d="m21 21-4.35-4.35"/>
            </svg>
            <p>${message}</p>
        `;
        return container;
    }
};

/**
 * Toast notifications
 */
const Toast = {
    show(message, type = 'info', duration = Config.ui.toastDuration) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'fadeOut 250ms ease';
            setTimeout(() => {
                container.removeChild(toast);
            }, 250);
        }, duration);
    },
    
    success(message) {
        this.show(message, 'success');
    },
    
    error(message) {
        this.show(message, 'error');
    },
    
    warning(message) {
        this.show(message, 'warning');
    },
    
    info(message) {
        this.show(message, 'info');
    }
};