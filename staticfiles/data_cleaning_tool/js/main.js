// Data Cleaning Tool Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Data cleaning session progress tracking
    function updateProgress(progressBar, percentage) {
        if (progressBar) {
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
            
            // Update text if present
            const progressText = progressBar.parentElement.querySelector('.progress-text');
            if (progressText) {
                progressText.textContent = percentage + '%';
            }
        }
    }

    // Quick clean form validation
    const quickCleanForm = document.querySelector('#quick-clean-form');
    if (quickCleanForm) {
        quickCleanForm.addEventListener('submit', function(e) {
            const requiredFields = quickCleanForm.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                showAlert('Please fill in all required fields.', 'danger');
            }
        });
    }

    // Alert system
    function showAlert(message, type = 'info') {
        const alertContainer = document.querySelector('.messages') || document.querySelector('.container-fluid');
        if (alertContainer) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            alertContainer.insertBefore(alertDiv, alertContainer.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    // Data cleaning rule management
    const ruleToggleSwitches = document.querySelectorAll('.rule-toggle');
    ruleToggleSwitches.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const ruleId = this.dataset.ruleId;
            const isActive = this.checked;
            
            // Update rule status via AJAX
            updateRuleStatus(ruleId, isActive);
        });
    });

    function updateRuleStatus(ruleId, isActive) {
        fetch(`/utilities/data-cleaning/api/rules/${ruleId}/toggle/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                is_active: isActive
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`Rule ${isActive ? 'activated' : 'deactivated'} successfully.`, 'success');
            } else {
                showAlert('Failed to update rule status.', 'danger');
                // Revert toggle
                const toggle = document.querySelector(`[data-rule-id="${ruleId}"]`);
                if (toggle) {
                    toggle.checked = !isActive;
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('An error occurred while updating rule status.', 'danger');
            // Revert toggle
            const toggle = document.querySelector(`[data-rule-id="${ruleId}"]`);
            if (toggle) {
                toggle.checked = !isActive;
            }
        });
    }

    // Get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Session monitoring
    const sessionCards = document.querySelectorAll('.session-card');
    sessionCards.forEach(card => {
        card.addEventListener('click', function() {
            const sessionId = this.dataset.sessionId;
            if (sessionId) {
                window.location.href = `/utilities/data-cleaning/sessions/${sessionId}/`;
            }
        });
    });

    // Real-time updates for active sessions
    function updateActiveSessions() {
        const activeSessions = document.querySelectorAll('[data-session-status="active"]');
        activeSessions.forEach(session => {
            const sessionId = session.dataset.sessionId;
            const progressBar = session.querySelector('.progress-bar');
            
            if (progressBar && sessionId) {
                // Fetch current progress
                fetch(`/utilities/data-cleaning/api/sessions/${sessionId}/progress/`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.progress !== undefined) {
                            updateProgress(progressBar, data.progress);
                        }
                    })
                    .catch(error => console.error('Error fetching progress:', error));
            }
        });
    }

    // Update active sessions every 5 seconds
    setInterval(updateActiveSessions, 5000);

    // Initialize any charts or visualizations
    initializeCharts();
});

function initializeCharts() {
    // Chart initialization code can go here
    // This would be for any data visualization charts
    console.log('Data Cleaning Tool initialized successfully');
}
