/**
 * Dialog handlers for settings, scanning, etc.
 */

// Settings Dialog
class SettingsDialog {
    constructor() {
        this.modal = document.getElementById('settings-modal');
        this.setupEventListeners();
        this.loadSettings();
    }
    
    setupEventListeners() {
        // Settings button
        document.getElementById('settings-btn')?.addEventListener('click', () => {
            this.open();
        });
        
        // Browse button in settings
        document.getElementById('setting-browse-btn')?.addEventListener('click', () => {
            this.browseDirectory();
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
    }
    
    saveSettings() {
        const settings = {
            directory: document.getElementById('setting-directory')?.value || '',
            theme: document.getElementById('setting-theme')?.value || 'light',
            resultsPerPage: parseInt(document.getElementById('setting-results')?.value) || 20,
            fuzzySearch: document.getElementById('setting-fuzzy')?.checked || false,
            autoScan: document.getElementById('setting-autoscan')?.checked || false,
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