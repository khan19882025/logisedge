// Manual Backup Dashboard JavaScript
class ManualBackupDashboard {
    constructor() {
        this.currentBackupType = null;
        this.backupInProgress = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.loadRecentBackups();
    }

    setupEventListeners() {
        // Modal close functionality
        const closeButtons = document.querySelectorAll('.close');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => this.closeModal(button.closest('.modal')));
        });

        // Close modal when clicking outside
        window.addEventListener('click', (event) => {
            if (event.target.classList.contains('modal')) {
                this.closeModal(event.target);
            }
        });

        // Form submission
        const backupForm = document.getElementById('backup-form');
        if (backupForm) {
            backupForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.confirmBackup();
            });
        }
    }

    loadDashboardData() {
        // Load last backup time
        this.updateLastBackupTime();
        
        // Load storage usage
        this.updateStorageUsage();
        
        // Load next scheduled backup
        this.updateNextBackupTime();
    }

    updateLastBackupTime() {
        const lastBackupElement = document.getElementById('last-backup-time');
        if (lastBackupElement) {
            // In a real application, this would fetch from the backend
            const lastBackup = localStorage.getItem('lastBackupTime');
            if (lastBackup) {
                lastBackupElement.textContent = new Date(lastBackup).toLocaleString();
            } else {
                lastBackupElement.textContent = 'Not available';
            }
        }
    }

    updateStorageUsage() {
        const storageElement = document.getElementById('storage-used');
        if (storageElement) {
            // In a real application, this would fetch from the backend
            const storageUsed = localStorage.getItem('storageUsed') || '0';
            storageElement.textContent = `${storageUsed} GB`;
        }
    }

    updateNextBackupTime() {
        const nextBackupElement = document.getElementById('next-backup-time');
        if (nextBackupElement) {
            // In a real application, this would fetch from the backend
            const nextBackup = localStorage.getItem('nextBackupTime');
            if (nextBackup) {
                nextBackupElement.textContent = new Date(nextBackup).toLocaleString();
            } else {
                nextBackupElement.textContent = 'Not scheduled';
            }
        }
    }

    loadRecentBackups() {
        const backupList = document.getElementById('recent-backups-list');
        if (!backupList) return;

        // In a real application, this would fetch from the backend
        const recentBackups = this.getMockRecentBackups();
        
        backupList.innerHTML = recentBackups.map(backup => `
            <div class="backup-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${backup.name}</strong>
                        <div style="color: #666; font-size: 0.9rem; margin-top: 0.25rem;">
                            ${backup.description}
                        </div>
                        <div style="color: #888; font-size: 0.8rem; margin-top: 0.25rem;">
                            Created: ${new Date(backup.created).toLocaleString()}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span class="status-badge ${backup.status}">${backup.status}</span>
                        <div style="color: #666; font-size: 0.9rem; margin-top: 0.25rem;">
                            ${backup.size}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    getMockRecentBackups() {
        return [
            {
                name: 'MANUAL_20250810_1930_SystemMaintenance',
                description: 'Pre-maintenance backup before system updates',
                created: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
                status: 'success',
                size: '2.3 GB'
            },
            {
                name: 'PREDEPLOY_20250810_1500_ERPUpdate',
                description: 'Pre-deployment backup for ERP system update',
                created: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
                status: 'success',
                size: '2.1 GB'
            },
            {
                name: 'POSTDEPLOY_20250809_2200_ERPUpdate',
                description: 'Post-deployment backup after ERP system update',
                created: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
                status: 'success',
                size: '2.2 GB'
            }
        ];
    }

    initiateBackup(type) {
        this.currentBackupType = type;
        this.showBackupModal();
    }

    showBackupModal() {
        const modal = document.getElementById('backup-modal');
        if (modal) {
            modal.style.display = 'block';
            
            // Pre-fill reason based on type
            const reasonField = document.getElementById('backup-reason');
            if (reasonField) {
                switch (this.currentBackupType) {
                    case 'general':
                        reasonField.value = 'General system backup';
                        break;
                    case 'predepLOY':
                        reasonField.value = 'Pre-deployment backup';
                        break;
                    case 'postdeploy':
                        reasonField.value = 'Post-deployment backup';
                        break;
                }
            }
        }
    }

    closeModal(modal) {
        if (modal) {
            modal.style.display = 'none';
        }
    }

    confirmBackup() {
        const form = document.getElementById('backup-form');
        const formData = new FormData(form);
        
        // Validate required fields
        const reason = formData.get('reason');
        if (!reason.trim()) {
            alert('Please provide a backup reason');
            return;
        }

        // Close the backup modal
        this.closeModal(document.getElementById('backup-modal'));
        
        // Start the backup process
        this.startBackupProcess(formData);
    }

    startBackupProcess(formData) {
        this.backupInProgress = true;
        this.showProgressModal();
        
        // Simulate backup process
        this.simulateBackupSteps();
        
        // In a real application, this would make an AJAX call to start the backup
        console.log('Starting backup with data:', Object.fromEntries(formData));
    }

    showProgressModal() {
        const modal = document.getElementById('progress-modal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    simulateBackupSteps() {
        const steps = [
            { id: 'step-1', text: 'Preparing backup environment', duration: 2000 },
            { id: 'step-2', text: 'Backing up databases', duration: 5000 },
            { id: 'step-3', text: 'Backing up files', duration: 4000 },
            { id: 'step-4', text: 'Generating checksums', duration: 2000 },
            { id: 'step-5', text: 'Encrypting backup', duration: 3000 },
            { id: 'step-6', text: 'Storing backup', duration: 4000 },
            { id: 'step-7', text: 'Verifying integrity', duration: 3000 }
        ];

        let currentStep = 0;
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        const executeStep = () => {
            if (currentStep >= steps.length) {
                this.completeBackup();
                return;
            }

            const step = steps[currentStep];
            
            // Update progress bar
            const progress = ((currentStep + 1) / steps.length) * 100;
            if (progressFill) progressFill.style.width = progress + '%';
            
            // Update progress text
            if (progressText) progressText.textContent = step.text;
            
            // Update step status
            this.updateStepStatus(step.id, 'active');
            
            // Mark previous step as completed
            if (currentStep > 0) {
                this.updateStepStatus(steps[currentStep - 1].id, 'completed');
            }

            currentStep++;
            
            // Move to next step after duration
            setTimeout(executeStep, step.duration);
        };

        executeStep();
    }

    updateStepStatus(stepId, status) {
        const stepElement = document.getElementById(stepId);
        if (stepElement) {
            stepElement.className = `step ${status}`;
        }
    }

    completeBackup() {
        // Update progress to 100%
        const progressFill = document.getElementById('progress-fill');
        if (progressFill) progressFill.style.width = '100%';
        
        const progressText = document.getElementById('progress-text');
        if (progressText) progressText.textContent = 'Backup completed successfully!';
        
        // Update last backup time
        localStorage.setItem('lastBackupTime', new Date().toISOString());
        
        // Close progress modal after a delay
        setTimeout(() => {
            this.closeModal(document.getElementById('progress-modal'));
            this.backupInProgress = false;
            
            // Show success message
            this.showSuccessMessage();
            
            // Refresh dashboard data
            this.loadDashboardData();
            this.loadRecentBackups();
        }, 2000);
    }

    showSuccessMessage() {
        // Create and show a success notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideInRight 0.3s ease;
        `;
        notification.innerHTML = `
            <i class="fas fa-check-circle" style="margin-right: 0.5rem;"></i>
            Backup completed successfully!
        `;
        
        document.body.appendChild(notification);
        
        // Remove notification after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    showBackupHistory() {
        alert('Backup History feature - This would show a detailed list of all backups with filtering and search capabilities.');
    }

    showRestoreOptions() {
        alert('Restore Options feature - This would show available restore points and allow selection of backup to restore from.');
    }

    showAuditLog() {
        alert('Audit Log feature - This would show a comprehensive log of all backup operations, including timestamps, operators, and verification results.');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ManualBackupDashboard();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

// Export for use in other modules
window.ManualBackupDashboard = ManualBackupDashboard;
