/**
 * Signature/Stamp Uploader JavaScript
 * Handles file upload, preview, and API communication
 */

class SignatureUploader {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.loadCurrentSignature();
    }

    initializeElements() {
        // Main elements
        this.fileInput = document.getElementById('file-input');
        this.fileInputContainer = document.getElementById('file-input-container');
        this.previewContainer = document.getElementById('preview-container');
        this.previewImage = document.getElementById('preview-image');
        this.previewInfo = document.getElementById('preview-info');
        this.uploadBtn = document.getElementById('upload-btn');
        this.resetBtn = document.getElementById('reset-btn');
        this.deleteBtn = document.getElementById('delete-btn');
        this.downloadBtn = document.getElementById('download-btn');
        this.currentSignature = document.getElementById('current-signature');
        
        // Modals
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.successModal = document.getElementById('success-modal');
        this.errorModal = document.getElementById('error-modal');
        this.deleteModal = document.getElementById('delete-modal');
    }

    bindEvents() {
        // File input events
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop events
        this.fileInputContainer.addEventListener('click', () => this.fileInput.click());
        this.fileInputContainer.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.fileInputContainer.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.fileInputContainer.addEventListener('drop', (e) => this.handleDrop(e));
        
        // Button events
        this.uploadBtn.addEventListener('click', () => this.uploadSignature());
        this.resetBtn.addEventListener('click', () => this.resetForm());
        this.deleteBtn.addEventListener('click', () => this.showDeleteConfirmation());
        this.downloadBtn.addEventListener('click', () => this.downloadSignature());
    }

    async loadCurrentSignature() {
        try {
            const response = await fetch('/api/signature-stamp/my-signature/', {
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayCurrentSignature(data);
            } else if (response.status === 404) {
                // No signature found, keep default state
                this.displayCurrentSignature(null);
            }
        } catch (error) {
            console.error('Error loading current signature:', error);
        }
    }

    displayCurrentSignature(signatureData) {
        if (signatureData && signatureData.file) {
            this.currentSignature.innerHTML = `
                <img src="${signatureData.file}" alt="Current Signature" class="signature-preview-image">
                <div style="margin-top: 1rem;">
                    <p><strong>File:</strong> ${signatureData.file.split('/').pop()}</p>
                    <p><strong>Size:</strong> ${this.formatFileSize(signatureData.file_size)}</p>
                    <p><strong>Uploaded:</strong> ${new Date(signatureData.uploaded_at).toLocaleDateString()}</p>
                </div>
            `;
            
            // Show management buttons
            this.deleteBtn.style.display = 'inline-flex';
            this.downloadBtn.style.display = 'inline-flex';
        } else {
            this.currentSignature.innerHTML = `
                <div class="no-signature">
                    <p>No signature uploaded yet</p>
                    <p>Upload your signature to get started</p>
                </div>
            `;
            
            // Hide management buttons
            this.deleteBtn.style.display = 'none';
            this.downloadBtn.style.display = 'none';
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    handleDragOver(event) {
        event.preventDefault();
        this.fileInputContainer.classList.add('drag-over');
    }

    handleDragLeave(event) {
        event.preventDefault();
        this.fileInputContainer.classList.remove('drag-over');
    }

    handleDrop(event) {
        event.preventDefault();
        this.fileInputContainer.classList.remove('drag-over');
        
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    processFile(file) {
        if (this.validateFile(file)) {
            this.showPreview(file);
            this.uploadBtn.style.display = 'inline-flex';
            this.resetBtn.style.display = 'inline-flex';
        }
    }

    validateFile(file) {
        // Check file type
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Please select a valid image file (PNG, JPG, or JPEG).');
            return false;
        }

        // Check file size (2MB)
        const maxSize = 2 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showError('File size must be less than 2MB.');
            return false;
        }

        return true;
    }

    showPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.previewImage.src = e.target.result;
            this.previewContainer.style.display = 'block';
            
            // Show file info
            this.previewInfo.innerHTML = `
                <p><strong>File:</strong> ${file.name}</p>
                <p><strong>Size:</strong> ${this.formatFileSize(file.size)}</p>
                <p><strong>Type:</strong> ${file.type}</p>
            `;
        };
        reader.readAsDataURL(file);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async uploadSignature() {
        if (!this.fileInput.files[0]) return;

        this.showLoading(true);
        
        try {
            const formData = new FormData();
            formData.append('file', this.fileInput.files[0]);

            const response = await fetch('/api/signature-stamp/upload/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccess(result.message || 'Signature uploaded successfully!');
                this.resetForm();
                this.loadCurrentSignature();
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to upload signature.');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showError('An error occurred during upload.');
        } finally {
            this.showLoading(false);
        }
    }

    async deleteSignature() {
        try {
            const response = await fetch('/api/signature-stamp/delete/', {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.showSuccess('Signature deleted successfully!');
                this.loadCurrentSignature();
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to delete signature.');
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showError('An error occurred while deleting the signature.');
        }
    }

    downloadSignature() {
        // Get the current signature image and trigger download
        const signatureImg = this.currentSignature.querySelector('img');
        if (signatureImg) {
            const link = document.createElement('a');
            link.href = signatureImg.src;
            link.download = 'signature.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    resetForm() {
        this.fileInput.value = '';
        this.previewContainer.style.display = 'none';
        this.uploadBtn.style.display = 'none';
        this.resetBtn.style.display = 'none';
        this.fileInputContainer.classList.remove('drag-over');
    }

    showDeleteConfirmation() {
        this.deleteModal.style.display = 'flex';
    }

    confirmDelete() {
        this.deleteSignature();
        this.closeModal('delete-modal');
    }

    showLoading(show) {
        this.loadingOverlay.style.display = show ? 'flex' : 'none';
    }

    showSuccess(message) {
        document.getElementById('success-message').textContent = message;
        this.successModal.style.display = 'flex';
    }

    showError(message) {
        document.getElementById('error-message').textContent = message;
        this.errorModal.style.display = 'flex';
    }

    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }
}

// Global functions for modal interactions
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function confirmDelete() {
    if (window.signatureUploader) {
        window.signatureUploader.confirmDelete();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.signatureUploader = new SignatureUploader();
});
