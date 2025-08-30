// Documentation JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-resize textarea for content
    const contentTextarea = document.querySelector('#id_content');
    if (contentTextarea) {
        contentTextarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Set initial height
        contentTextarea.style.height = 'auto';
        contentTextarea.style.height = (contentTextarea.scrollHeight) + 'px';
    }
    
    // Confirm delete action
    const deleteButtons = document.querySelectorAll('.btn-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this documentation? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Search functionality for documentation list
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('tbody tr');
            
            tableRows.forEach(row => {
                const title = row.querySelector('td:first-child').textContent.toLowerCase();
                if (title.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Auto-save draft functionality (optional)
    let autoSaveTimer;
    const form = document.querySelector('form');
    if (form && contentTextarea) {
        contentTextarea.addEventListener('input', function() {
            clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(function() {
                // Save draft to localStorage
                const draft = {
                    title: document.querySelector('#id_title').value,
                    content: contentTextarea.value,
                    timestamp: new Date().toISOString()
                };
                localStorage.setItem('documentation_draft', JSON.stringify(draft));
                
                // Show auto-save indicator
                showAutoSaveIndicator();
            }, 2000); // Auto-save after 2 seconds of inactivity
        });
    }
    
    // Load draft on page load
    if (form && !form.querySelector('input[name="pk"]')) { // Only for new documents
        const draft = localStorage.getItem('documentation_draft');
        if (draft) {
            const draftData = JSON.parse(draft);
            const titleField = document.querySelector('#id_title');
            if (titleField && !titleField.value) {
                titleField.value = draftData.title || '';
            }
            if (contentTextarea && !contentTextarea.value) {
                contentTextarea.value = draftData.content || '';
                contentTextarea.style.height = 'auto';
                contentTextarea.style.height = (contentTextarea.scrollHeight) + 'px';
            }
        }
    }
    
    // Clear draft when form is submitted
    if (form) {
        form.addEventListener('submit', function() {
            localStorage.removeItem('documentation_draft');
        });
    }
});

function showAutoSaveIndicator() {
    // Create or update auto-save indicator
    let indicator = document.getElementById('auto-save-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'auto-save-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s;
        `;
        document.body.appendChild(indicator);
    }
    
    indicator.textContent = 'Draft saved';
    indicator.style.opacity = '1';
    
    setTimeout(() => {
        indicator.style.opacity = '0';
    }, 2000);
} 