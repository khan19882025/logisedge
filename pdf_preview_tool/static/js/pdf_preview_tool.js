/**
 * PDF Preview Tool - Main JavaScript File
 * Handles PDF rendering, user interactions, and real-time updates
 */

class PDFPreviewTool {
    constructor() {
        this.currentDocument = null;
        this.currentSession = null;
        this.currentPage = 1;
        this.totalPages = 1;
        this.zoomLevel = 1.0;
        this.searchQuery = '';
        this.searchResults = [];
        this.currentSearchIndex = 0;
        this.isLoading = false;
        this.pdfDocument = null;
        this.pdfViewer = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeTooltips();
        this.loadUserSettings();
        this.setupRealTimeUpdates();
        
        // Check if we're on a preview page
        if (window.location.pathname.includes('/preview/')) {
            this.initializePDFViewer();
        }
    }
    
    setupEventListeners() {
        // Global event listeners
        document.addEventListener('DOMContentLoaded', () => {
            this.setupGlobalEvents();
        });
        
        // PDF viewer specific events
        this.setupPDFViewerEvents();
        
        // Search functionality
        this.setupSearchEvents();
        
        // Zoom controls
        this.setupZoomControls();
        
        // Navigation controls
        this.setupNavigationControls();
        
        // Print and download
        this.setupActionButtons();
    }
    
    setupGlobalEvents() {
        // Initialize tooltips
        this.initializeTooltips();
        
        // Setup form validation
        this.setupFormValidation();
        
        // Setup AJAX forms
        this.setupAJAXForms();
        
        // Setup document actions
        this.setupDocumentActions();
    }
    
    setupPDFViewerEvents() {
        // Page navigation
        const prevPageBtn = document.getElementById('prevPage');
        const nextPageBtn = document.getElementById('nextPage');
        const pageInput = document.getElementById('pageInput');
        
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', () => this.previousPage());
        }
        
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', () => this.nextPage());
        }
        
        if (pageInput) {
            pageInput.addEventListener('change', (e) => this.goToPage(parseInt(e.target.value)));
            pageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.goToPage(parseInt(e.target.value));
                }
            });
        }
        
        // Zoom controls
        const zoomInBtn = document.getElementById('zoomIn');
        const zoomOutBtn = document.getElementById('zoomOut');
        const zoomResetBtn = document.getElementById('zoomReset');
        
        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => this.zoomIn());
        }
        
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => this.zoomOut());
        }
        
        if (zoomResetBtn) {
            zoomResetBtn.addEventListener('click', () => this.resetZoom());
        }
        
        // Search controls
        const searchInput = document.getElementById('searchInput');
        const searchNextBtn = document.getElementById('searchNext');
        const searchPrevBtn = document.getElementById('searchPrev');
        const searchClearBtn = document.getElementById('searchClear');
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearchInput(e.target.value));
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchNext();
                }
            });
        }
        
        if (searchNextBtn) {
            searchNextBtn.addEventListener('click', () => this.searchNext());
        }
        
        if (searchPrevBtn) {
            searchPrevBtn.addEventListener('click', () => this.searchPrevious());
        }
        
        if (searchClearBtn) {
            searchClearBtn.addEventListener('click', () => this.clearSearch());
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Mouse wheel zoom
        const pdfContainer = document.getElementById('pdfContainer');
        if (pdfContainer) {
            pdfContainer.addEventListener('wheel', (e) => this.handleMouseWheel(e));
        }
    }
    
    setupSearchEvents() {
        // Global search functionality
        const globalSearchInput = document.querySelector('.global-search-input');
        if (globalSearchInput) {
            globalSearchInput.addEventListener('input', (e) => this.handleGlobalSearch(e.target.value));
        }
    }
    
    setupZoomControls() {
        // Zoom slider
        const zoomSlider = document.getElementById('zoomSlider');
        if (zoomSlider) {
            zoomSlider.addEventListener('input', (e) => this.setZoom(parseFloat(e.target.value)));
        }
        
        // Zoom buttons
        const zoomButtons = document.querySelectorAll('.zoom-btn');
        zoomButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const zoom = parseFloat(btn.dataset.zoom);
                this.setZoom(zoom);
            });
        });
    }
    
    setupNavigationControls() {
        // Thumbnail navigation
        const thumbnailContainer = document.getElementById('thumbnailContainer');
        if (thumbnailContainer) {
            thumbnailContainer.addEventListener('click', (e) => {
                if (e.target.classList.contains('thumbnail')) {
                    const page = parseInt(e.target.dataset.page);
                    this.goToPage(page);
                }
            });
        }
        
        // Page layout controls
        const layoutButtons = document.querySelectorAll('.layout-btn');
        layoutButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const layout = btn.dataset.layout;
                this.setPageLayout(layout);
            });
        });
    }
    
    setupActionButtons() {
        // Print button
        const printBtn = document.getElementById('printBtn');
        if (printBtn) {
            printBtn.addEventListener('click', () => this.printDocument());
        }
        
        // Download button
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadDocument());
        }
        
        // Email button
        const emailBtn = document.getElementById('emailBtn');
        if (emailBtn) {
            emailBtn.addEventListener('click', () => this.emailDocument());
        }
        
        // Share button
        const shareBtn = document.getElementById('shareBtn');
        if (shareBtn) {
            shareBtn.addEventListener('click', () => this.shareDocument());
        }
    }
    
    setupFormValidation() {
        // Form validation for document forms
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => this.validateForm(e, form));
        });
    }
    
    setupAJAXForms() {
        // AJAX form submissions
        const ajaxForms = document.querySelectorAll('.ajax-form');
        ajaxForms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleAJAXForm(e, form));
        });
    }
    
    setupDocumentActions() {
        // Document action buttons
        const actionButtons = document.querySelectorAll('.document-action');
        actionButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleDocumentAction(e, btn));
        });
    }
    
    // PDF Viewer Methods
    async initializePDFViewer() {
        try {
            this.isLoading = true;
            this.showLoadingIndicator();
            
            // Get document ID from URL
            const documentId = this.getDocumentIdFromURL();
            if (!documentId) {
                throw new Error('Document ID not found');
            }
            
            // Start preview session
            await this.startPreviewSession(documentId);
            
            // Load PDF document
            await this.loadPDFDocument(documentId);
            
            // Initialize viewer
            this.setupPDFViewer();
            
            // Load first page
            await this.loadPage(1);
            
            // Update UI
            this.updateUI();
            
        } catch (error) {
            console.error('Error initializing PDF viewer:', error);
            this.showError('Failed to initialize PDF viewer: ' + error.message);
        } finally {
            this.isLoading = false;
            this.hideLoadingIndicator();
        }
    }
    
    async loadPDFDocument(documentId) {
        try {
            // Fetch document info
            const response = await fetch(`/utilities/pdf-preview-tool/api/documents/${documentId}/info/`);
            if (!response.ok) {
                throw new Error('Failed to fetch document info');
            }
            
            const documentInfo = await response.json();
            this.currentDocument = documentInfo;
            this.totalPages = documentInfo.page_count;
            
            // Load PDF.js
            const pdfjsLib = window['pdfjs-dist/build/pdf'];
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
            
            // Load PDF document
            const loadingTask = pdfjsLib.getDocument(documentInfo.file_path);
            this.pdfDocument = await loadingTask.promise;
            
            // Update page count
            this.totalPages = this.pdfDocument.numPages;
            
        } catch (error) {
            console.error('Error loading PDF document:', error);
            throw error;
        }
    }
    
    setupPDFViewer() {
        const container = document.getElementById('pdfContainer');
        if (!container) return;
        
        // Create canvas for PDF rendering
        const canvas = document.createElement('canvas');
        canvas.id = 'pdfCanvas';
        canvas.style.width = '100%';
        canvas.style.height = 'auto';
        
        container.innerHTML = '';
        container.appendChild(canvas);
        
        this.pdfCanvas = canvas;
        this.pdfContext = canvas.getContext('2d');
    }
    
    async loadPage(pageNumber) {
        if (!this.pdfDocument || pageNumber < 1 || pageNumber > this.totalPages) {
            return;
        }
        
        try {
            this.isLoading = true;
            this.showLoadingIndicator();
            
            // Get page
            const page = await this.pdfDocument.getPage(pageNumber);
            
            // Calculate viewport
            const viewport = page.getViewport({ scale: this.zoomLevel });
            
            // Set canvas dimensions
            this.pdfCanvas.width = viewport.width;
            this.pdfCanvas.height = viewport.height;
            
            // Render page
            const renderContext = {
                canvasContext: this.pdfContext,
                viewport: viewport
            };
            
            await page.render(renderContext).promise;
            
            // Update current page
            this.currentPage = pageNumber;
            
            // Update UI
            this.updatePageInfo();
            
            // Log page view
            this.logPageView(pageNumber);
            
        } catch (error) {
            console.error('Error loading page:', error);
            this.showError('Failed to load page: ' + error.message);
        } finally {
            this.isLoading = false;
            this.hideLoadingIndicator();
        }
    }
    
    // Navigation Methods
    async previousPage() {
        if (this.currentPage > 1) {
            await this.goToPage(this.currentPage - 1);
        }
    }
    
    async nextPage() {
        if (this.currentPage < this.totalPages) {
            await this.goToPage(this.currentPage + 1);
        }
    }
    
    async goToPage(pageNumber) {
        if (pageNumber >= 1 && pageNumber <= this.totalPages && pageNumber !== this.currentPage) {
            await this.loadPage(pageNumber);
            
            // Update page input
            const pageInput = document.getElementById('pageInput');
            if (pageInput) {
                pageInput.value = pageNumber;
            }
            
            // Scroll to top
            window.scrollTo(0, 0);
        }
    }
    
    // Zoom Methods
    setZoom(zoomLevel) {
        this.zoomLevel = Math.max(0.25, Math.min(5.0, zoomLevel));
        
        // Update zoom slider
        const zoomSlider = document.getElementById('zoomSlider');
        if (zoomSlider) {
            zoomSlider.value = this.zoomLevel;
        }
        
        // Update zoom display
        const zoomDisplay = document.getElementById('zoomDisplay');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${Math.round(this.zoomLevel * 100)}%`;
        }
        
        // Reload current page with new zoom
        this.loadPage(this.currentPage);
        
        // Log zoom action
        this.logZoomAction(this.zoomLevel);
    }
    
    zoomIn() {
        this.setZoom(this.zoomLevel * 1.2);
    }
    
    zoomOut() {
        this.setZoom(this.zoomLevel / 1.2);
    }
    
    resetZoom() {
        this.setZoom(1.0);
    }
    
    // Search Methods
    async searchDocument(query) {
        if (!query.trim() || !this.pdfDocument) {
            return;
        }
        
        try {
            this.searchQuery = query;
            this.searchResults = [];
            this.currentSearchIndex = 0;
            
            // Search through all pages
            for (let pageNum = 1; pageNum <= this.totalPages; pageNum++) {
                const page = await this.pdfDocument.getPage(pageNum);
                const textContent = await page.getTextContent();
                
                const text = textContent.items.map(item => item.str).join(' ');
                const matches = this.findTextMatches(text, query);
                
                if (matches.length > 0) {
                    this.searchResults.push({
                        page: pageNum,
                        matches: matches
                    });
                }
            }
            
            // Update search UI
            this.updateSearchUI();
            
            // Log search action
            this.logSearchAction(query, this.searchResults.length);
            
            // Go to first result
            if (this.searchResults.length > 0) {
                this.goToSearchResult(0);
            }
            
        } catch (error) {
            console.error('Error searching document:', error);
            this.showError('Search failed: ' + error.message);
        }
    }
    
    findTextMatches(text, query) {
        const matches = [];
        const regex = new RegExp(query, 'gi');
        let match;
        
        while ((match = regex.exec(text)) !== null) {
            matches.push({
                index: match.index,
                text: match[0]
            });
        }
        
        return matches;
    }
    
    goToSearchResult(index) {
        if (index >= 0 && index < this.searchResults.length) {
            const result = this.searchResults[index];
            this.currentSearchIndex = index;
            
            // Go to page
            this.goToPage(result.page);
            
            // Highlight search result
            this.highlightSearchResult(result);
            
            // Update search UI
            this.updateSearchUI();
        }
    }
    
    searchNext() {
        if (this.searchResults.length > 0) {
            const nextIndex = (this.currentSearchIndex + 1) % this.searchResults.length;
            this.goToSearchResult(nextIndex);
        }
    }
    
    searchPrevious() {
        if (this.searchResults.length > 0) {
            const prevIndex = this.currentSearchIndex === 0 ? 
                this.searchResults.length - 1 : this.currentSearchIndex - 1;
            this.goToSearchResult(prevIndex);
        }
    }
    
    clearSearch() {
        this.searchQuery = '';
        this.searchResults = [];
        this.currentSearchIndex = 0;
        this.updateSearchUI();
        this.clearSearchHighlights();
    }
    
    // Action Methods
    async printDocument() {
        try {
            // Log print action
            this.logAction('print');
            
            // Open print dialog
            window.print();
            
        } catch (error) {
            console.error('Error printing document:', error);
            this.showError('Print failed: ' + error.message);
        }
    }
    
    async downloadDocument() {
        try {
            // Log download action
            this.logAction('download');
            
            // Create download link
            const link = document.createElement('a');
            link.href = this.currentDocument.file_path;
            link.download = this.currentDocument.title + '.pdf';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
        } catch (error) {
            console.error('Error downloading document:', error);
            this.showError('Download failed: ' + error.message);
        }
    }
    
    async emailDocument() {
        try {
            // Log email action
            this.logAction('email');
            
            // Open email modal
            this.openEmailModal();
            
        } catch (error) {
            console.error('Error emailing document:', error);
            this.showError('Email failed: ' + error.message);
        }
    }
    
    async shareDocument() {
        try {
            // Log share action
            this.logAction('share');
            
            // Check if Web Share API is supported
            if (navigator.share) {
                await navigator.share({
                    title: this.currentDocument.title,
                    text: this.currentDocument.description,
                    url: window.location.href
                });
            } else {
                // Fallback: copy URL to clipboard
                await navigator.clipboard.writeText(window.location.href);
                this.showSuccess('Link copied to clipboard');
            }
            
        } catch (error) {
            console.error('Error sharing document:', error);
            this.showError('Share failed: ' + error.message);
        }
    }
    
    // Utility Methods
    getDocumentIdFromURL() {
        const pathParts = window.location.pathname.split('/');
        const documentIndex = pathParts.indexOf('documents') + 1;
        return pathParts[documentIndex];
    }
    
    async startPreviewSession(documentId) {
        try {
            const response = await fetch(`/utilities/pdf-preview-tool/api/documents/${documentId}/start-session/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to start preview session');
            }
            
            const sessionData = await response.json();
            this.currentSession = sessionData;
            
        } catch (error) {
            console.error('Error starting preview session:', error);
            // Continue without session tracking
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    // UI Update Methods
    updateUI() {
        this.updatePageInfo();
        this.updateZoomInfo();
        this.updateSearchUI();
        this.updateThumbnails();
    }
    
    updatePageInfo() {
        const pageInfo = document.getElementById('pageInfo');
        if (pageInfo) {
            pageInfo.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
        }
        
        const pageInput = document.getElementById('pageInput');
        if (pageInput) {
            pageInput.value = this.currentPage;
        }
        
        // Update navigation buttons
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentPage <= 1;
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.currentPage >= this.totalPages;
        }
    }
    
    updateZoomInfo() {
        const zoomDisplay = document.getElementById('zoomDisplay');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${Math.round(this.zoomLevel * 100)}%`;
        }
        
        const zoomSlider = document.getElementById('zoomSlider');
        if (zoomSlider) {
            zoomSlider.value = this.zoomLevel;
        }
    }
    
    updateSearchUI() {
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            if (this.searchResults.length > 0) {
                searchResults.textContent = `${this.currentSearchIndex + 1} of ${this.searchResults.length} results`;
                searchResults.style.display = 'block';
            } else {
                searchResults.style.display = 'none';
            }
        }
        
        // Update search navigation buttons
        const searchNextBtn = document.getElementById('searchNext');
        const searchPrevBtn = document.getElementById('searchPrev');
        
        if (searchNextBtn) {
            searchNextBtn.disabled = this.searchResults.length === 0;
        }
        
        if (searchPrevBtn) {
            searchPrevBtn.disabled = this.searchResults.length === 0;
        }
    }
    
    updateThumbnails() {
        const thumbnailContainer = document.getElementById('thumbnailContainer');
        if (!thumbnailContainer) return;
        
        // Generate thumbnails for current page range
        this.generateThumbnails(thumbnailContainer);
    }
    
    async generateThumbnails(container) {
        // Implementation for generating page thumbnails
        // This would create small preview images for each page
    }
    
    // Event Handlers
    handleSearchInput(query) {
        // Debounce search input
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.searchDocument(query);
        }, 300);
    }
    
    handleGlobalSearch(query) {
        // Implement global search across all documents
        console.log('Global search:', query);
    }
    
    handleKeyboardShortcuts(e) {
        // Keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'f':
                    e.preventDefault();
                    document.getElementById('searchInput')?.focus();
                    break;
                case '=':
                    e.preventDefault();
                    this.zoomIn();
                    break;
                case '-':
                    e.preventDefault();
                    this.zoomOut();
                    break;
                case '0':
                    e.preventDefault();
                    this.resetZoom();
                    break;
            }
        } else {
            switch (e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousPage();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextPage();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.goToPage(1);
                    break;
                case 'End':
                    e.preventDefault();
                    this.goToPage(this.totalPages);
                    break;
            }
        }
    }
    
    handleMouseWheel(e) {
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            if (e.deltaY < 0) {
                this.zoomIn();
            } else {
                this.zoomOut();
            }
        }
    }
    
    // Form Handling
    validateForm(e, form) {
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        form.classList.add('was-validated');
    }
    
    async handleAJAXForm(e, form) {
        e.preventDefault();
        
        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: form.method,
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                this.handleFormSuccess(result, form);
            } else {
                throw new Error('Form submission failed');
            }
            
        } catch (error) {
            console.error('Error submitting form:', error);
            this.handleFormError(error, form);
        }
    }
    
    handleFormSuccess(result, form) {
        // Handle successful form submission
        this.showSuccess(result.message || 'Form submitted successfully');
        
        // Reset form if needed
        if (result.reset_form) {
            form.reset();
        }
        
        // Redirect if needed
        if (result.redirect_url) {
            window.location.href = result.redirect_url;
        }
    }
    
    handleFormError(error, form) {
        // Handle form submission error
        this.showError(error.message || 'Form submission failed');
    }
    
    // Document Actions
    handleDocumentAction(e, button) {
        e.preventDefault();
        
        const action = button.dataset.action;
        const documentId = button.dataset.documentId;
        
        switch (action) {
            case 'preview':
                window.location.href = `/utilities/pdf-preview-tool/documents/${documentId}/preview/`;
                break;
            case 'download':
                this.downloadDocumentById(documentId);
                break;
            case 'print':
                this.printDocumentById(documentId);
                break;
            case 'email':
                this.emailDocumentById(documentId);
                break;
            case 'delete':
                this.deleteDocument(documentId);
                break;
        }
    }
    
    // Logging Methods
    logPageView(pageNumber) {
        this.logAction('view_page', { page_number: pageNumber });
    }
    
    logZoomAction(zoomLevel) {
        this.logAction('zoom', { zoom_level: zoomLevel });
    }
    
    logSearchAction(query, resultCount) {
        this.logAction('search', { query: query, result_count: resultCount });
    }
    
    async logAction(actionType, details = {}) {
        if (!this.currentSession) return;
        
        try {
            await fetch(`/utilities/pdf-preview-tool/api/sessions/${this.currentSession.session_id}/log-action/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action_type: actionType,
                    details: details,
                    page_number: this.currentPage
                })
            });
        } catch (error) {
            console.error('Error logging action:', error);
        }
    }
    
    // UI Helper Methods
    showLoadingIndicator() {
        const indicator = document.getElementById('loadingIndicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
    }
    
    hideLoadingIndicator() {
        const indicator = document.getElementById('loadingIndicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to page
        const container = document.querySelector('.notifications-container') || document.body;
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    initializeTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    loadUserSettings() {
        // Load user's preview settings
        fetch('/utilities/pdf-preview-tool/api/user/settings/')
            .then(response => response.json())
            .then(settings => {
                this.applyUserSettings(settings);
            })
            .catch(error => {
                console.error('Error loading user settings:', error);
            });
    }
    
    applyUserSettings(settings) {
        // Apply user's default settings
        if (settings.default_zoom) {
            this.zoomLevel = settings.default_zoom;
        }
        
        if (settings.theme) {
            document.body.setAttribute('data-theme', settings.theme);
        }
        
        if (settings.sidebar_position) {
            this.setSidebarPosition(settings.sidebar_position);
        }
    }
    
    setSidebarPosition(position) {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.className = `sidebar sidebar-${position}`;
        }
    }
    
    setupRealTimeUpdates() {
        // Setup real-time updates for collaborative features
        // This could include WebSocket connections for real-time collaboration
    }
    
    // Cleanup
    destroy() {
        // Cleanup resources
        if (this.pdfDocument) {
            this.pdfDocument.destroy();
        }
        
        // End preview session
        if (this.currentSession) {
            this.endPreviewSession();
        }
    }
    
    async endPreviewSession() {
        if (!this.currentSession) return;
        
        try {
            await fetch(`/utilities/pdf-preview-tool/api/sessions/${this.currentSession.session_id}/end/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
        } catch (error) {
            console.error('Error ending preview session:', error);
        }
    }
}

// Initialize PDF Preview Tool when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.pdfPreviewTool = new PDFPreviewTool();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.pdfPreviewTool) {
        window.pdfPreviewTool.destroy();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PDFPreviewTool;
}
