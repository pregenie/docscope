/**
 * Dialog handlers for settings, scanning, etc.
 */

// Settings Dialog
class SettingsDialog {
    constructor() {
        this.modal = document.getElementById('settings-modal');
        this.additionalDirectories = [];
        this.setupEventListeners();
        this.loadSettings();
    }
    
    setupEventListeners() {
        // Settings button
        document.getElementById('settings-btn')?.addEventListener('click', () => {
            this.open();
        });
        
        // Select Origin button (new prominent button)
        document.getElementById('setting-select-origin-btn')?.addEventListener('click', () => {
            this.selectOrigin();
        });
        
        // Quick access buttons
        document.querySelectorAll('.quick-select').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const path = e.currentTarget.getAttribute('data-path');
                this.quickSelectPath(path);
            });
        });
        
        // Add directory button
        document.getElementById('add-directory-btn')?.addEventListener('click', () => {
            this.addAdditionalDirectory();
        });
        
        // Save button
        document.getElementById('settings-save')?.addEventListener('click', () => {
            this.saveSettings();
        });
        
        // Close button
        this.modal?.querySelector('.modal-close')?.addEventListener('click', () => {
            this.close();
        });
    }
    
    selectOrigin() {
        const currentPath = document.getElementById('setting-directory')?.value;
        
        // Open the directory picker with a callback
        window.directoryPicker.open((selectedPath) => {
            document.getElementById('setting-directory').value = selectedPath;
            // Remove readonly after selection
            document.getElementById('setting-directory').removeAttribute('readonly');
            
            // Show confirmation
            this.showToast(`Origin set to: ${selectedPath}`, 'success');
            
            // Optionally trigger an immediate scan
            if (confirm('Would you like to scan this directory now?')) {
                this.close();
                scanDialog.startScan(selectedPath);
            }
        }, currentPath);
    }
    
    async quickSelectPath(pathAlias) {
        // Expand the path alias (~/Documents, etc.)
        try {
            const response = await fetch(`/api/v1/filesystem/validate-path?path=${encodeURIComponent(pathAlias)}`);
            const data = await response.json();
            
            if (response.ok && data.exists && data.is_directory) {
                document.getElementById('setting-directory').value = data.path;
                document.getElementById('setting-directory').removeAttribute('readonly');
                this.showToast(`Origin set to: ${data.path}`, 'success');
                
                // Optionally trigger scan
                if (confirm('Would you like to scan this directory now?')) {
                    this.close();
                    scanDialog.startScan(data.path);
                }
            } else {
                this.showToast('Directory does not exist or is not accessible', 'error');
            }
        } catch (error) {
            console.error('Error validating path:', error);
            this.showToast('Failed to validate directory', 'error');
        }
    }
    
    addAdditionalDirectory() {
        window.directoryPicker.open((selectedPath) => {
            if (!this.additionalDirectories.includes(selectedPath)) {
                this.additionalDirectories.push(selectedPath);
                this.updateAdditionalDirectoriesList();
                this.showToast(`Added: ${selectedPath}`, 'success');
            } else {
                this.showToast('Directory already added', 'warning');
            }
        });
    }
    
    updateAdditionalDirectoriesList() {
        const container = document.getElementById('additional-directories-list');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.additionalDirectories.forEach((dir, index) => {
            const item = document.createElement('div');
            item.className = 'additional-directory-item';
            item.innerHTML = `
                <span class="directory-path">${dir}</span>
                <button class="btn-icon btn-small" onclick="settingsDialog.removeAdditionalDirectory(${index})" title="Remove">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            `;
            container.appendChild(item);
        });
    }
    
    removeAdditionalDirectory(index) {
        this.additionalDirectories.splice(index, 1);
        this.updateAdditionalDirectoriesList();
    }
    
    open() {
        this.modal?.classList.add('active');
    }
    
    close() {
        this.modal?.classList.remove('active');
    }
    
    browseDirectory() {
        const currentPath = document.getElementById('setting-directory')?.value;
        
        window.directoryPicker.open((selectedPath) => {
            document.getElementById('setting-directory').value = selectedPath;
        }, currentPath);
    }
    
    loadSettings() {
        // Load settings from localStorage
        const settings = JSON.parse(localStorage.getItem('docscope-settings') || '{}');
        
        if (settings.directory) {
            document.getElementById('setting-directory').value = settings.directory;
            document.getElementById('setting-directory').removeAttribute('readonly');
        }
        if (settings.additionalDirectories) {
            this.additionalDirectories = settings.additionalDirectories;
            this.updateAdditionalDirectoriesList();
        }
        if (settings.theme) {
            document.getElementById('setting-theme').value = settings.theme;
        }
        if (settings.resultsPerPage) {
            document.getElementById('setting-results').value = settings.resultsPerPage;
        }
        if (settings.fuzzySearch !== undefined) {
            document.getElementById('setting-fuzzy').checked = settings.fuzzySearch;
        }
        if (settings.autoScan !== undefined) {
            document.getElementById('setting-autoscan').checked = settings.autoScan;
        }
        if (settings.watchDirectories !== undefined) {
            const watchCheckbox = document.getElementById('setting-watch');
            if (watchCheckbox) {
                watchCheckbox.checked = settings.watchDirectories;
            }
        }
    }
    
    saveSettings() {
        const settings = {
            directory: document.getElementById('setting-directory')?.value || '',
            additionalDirectories: this.additionalDirectories,
            theme: document.getElementById('setting-theme')?.value || 'light',
            resultsPerPage: parseInt(document.getElementById('setting-results')?.value) || 20,
            fuzzySearch: document.getElementById('setting-fuzzy')?.checked || false,
            autoScan: document.getElementById('setting-autoscan')?.checked || false,
            watchDirectories: document.getElementById('setting-watch')?.checked || false,
            apiEndpoint: document.getElementById('setting-api')?.value || '/api/v1'
        };
        
        // Save to localStorage
        localStorage.setItem('docscope-settings', JSON.stringify(settings));
        
        // Apply theme
        if (settings.theme === 'dark') {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
        
        // Show success message
        this.showToast('Settings saved successfully', 'success');
        
        // Close dialog
        this.close();
        
        // If auto-scan is enabled and we have a directory, trigger a scan
        if (settings.autoScan && settings.directory) {
            scanDialog.startScan(settings.directory);
        }
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        container?.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Scan Dialog
class ScanDialog {
    constructor() {
        this.modal = document.getElementById('scan-dialog');
        this.isScanning = false;
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Scan button on browse page
        document.getElementById('scan-btn')?.addEventListener('click', () => {
            this.open();
        });
        
        // Browse button in scan dialog
        document.getElementById('scan-browse-btn')?.addEventListener('click', () => {
            this.browseDirectory();
        });
        
        // Start scan button
        document.getElementById('scan-start-btn')?.addEventListener('click', () => {
            this.startScan();
        });
        
        // Cancel button
        document.getElementById('scan-cancel-btn')?.addEventListener('click', () => {
            this.close();
        });
        
        // Close button
        this.modal?.querySelector('.modal-close')?.addEventListener('click', () => {
            this.close();
        });
    }
    
    open() {
        // Load default directory from settings
        const settings = JSON.parse(localStorage.getItem('docscope-settings') || '{}');
        if (settings.directory) {
            document.getElementById('scan-directory').value = settings.directory;
        }
        
        this.modal?.classList.add('active');
    }
    
    close() {
        if (!this.isScanning) {
            this.modal?.classList.remove('active');
        }
    }
    
    browseDirectory() {
        const currentPath = document.getElementById('scan-directory')?.value;
        
        window.directoryPicker.open((selectedPath) => {
            document.getElementById('scan-directory').value = selectedPath;
        }, currentPath);
    }
    
    async startScan(directory = null) {
        const scanDir = directory || document.getElementById('scan-directory')?.value;
        
        if (!scanDir) {
            this.showError('Please select a directory to scan');
            return;
        }
        
        // Get selected formats
        const formats = [];
        document.querySelectorAll('input[name="scan-format"]:checked').forEach(cb => {
            formats.push(cb.value);
        });
        
        if (formats.length === 0) {
            this.showError('Please select at least one file type');
            return;
        }
        
        // Get recursive option
        const recursive = document.getElementById('scan-recursive')?.checked || false;
        
        // Show progress
        this.showProgress(true);
        this.isScanning = true;
        
        // Disable buttons
        document.getElementById('scan-start-btn').disabled = true;
        document.getElementById('scan-cancel-btn').textContent = 'Close';
        
        try {
            // Start the scan
            const response = await fetch('/api/v1/scanner/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    path: scanDir,
                    recursive: recursive,
                    formats: formats
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.updateProgress(100, `Scan complete: ${data.documents_found || 0} documents found`);
                
                setTimeout(() => {
                    this.showProgress(false);
                    this.close();
                    
                    // Refresh the documents list if on browse page
                    if (document.getElementById('browse-page')?.classList.contains('active')) {
                        // Trigger refresh
                        document.getElementById('refresh-btn')?.click();
                    }
                    
                    // Show success message
                    settingsDialog.showToast(`Scan complete: ${data.documents_found || 0} documents indexed`, 'success');
                }, 2000);
            } else {
                throw new Error(data.detail || 'Scan failed');
            }
        } catch (error) {
            console.error('Scan error:', error);
            this.showError(error.message || 'Failed to scan directory');
            this.showProgress(false);
        } finally {
            this.isScanning = false;
            document.getElementById('scan-start-btn').disabled = false;
            document.getElementById('scan-cancel-btn').textContent = 'Cancel';
        }
    }
    
    showProgress(show) {
        const progressContainer = document.getElementById('scan-progress');
        if (progressContainer) {
            progressContainer.style.display = show ? 'block' : 'none';
        }
        
        if (!show) {
            this.updateProgress(0, 'Scanning...');
        }
    }
    
    updateProgress(percent, text) {
        const fill = document.getElementById('scan-progress-fill');
        const progressText = document.getElementById('scan-progress-text');
        
        if (fill) {
            fill.style.width = `${percent}%`;
        }
        if (progressText) {
            progressText.textContent = text;
        }
    }
    
    showError(message) {
        settingsDialog.showToast(message, 'error');
    }
}

// Initialize dialogs
const settingsDialog = new SettingsDialog();
const scanDialog = new ScanDialog();

// Check for auto-scan on load
window.addEventListener('DOMContentLoaded', () => {
    const settings = JSON.parse(localStorage.getItem('docscope-settings') || '{}');
    
    // Apply saved theme
    if (settings.theme === 'dark') {
        document.body.classList.add('dark-theme');
        document.getElementById('setting-theme').value = 'dark';
    }
    
    // Auto-scan if enabled
    if (settings.autoScan && settings.directory) {
        setTimeout(() => {
            console.log('Auto-scanning directory:', settings.directory);
            scanDialog.startScan(settings.directory);
        }, 1000);
    }
});