// Bank Transfer Detail Page JavaScript

// Copy transfer number to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showAlert('Transfer number copied to clipboard!', 'success');
        }).catch(function(err) {
            showAlert('Failed to copy to clipboard', 'danger');
        });
    } else {
        // Fallback for older browsers
        var textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showAlert('Transfer number copied to clipboard!', 'success');
        } catch (err) {
            showAlert('Failed to copy to clipboard', 'danger');
        }
        document.body.removeChild(textArea);
    }
}

// Print transfer function
function printTransfer(transferId) {
    var url = '/accounting/bank-transfers/' + transferId + '/print/';
    window.open(url, '_blank');
}

// Initialize detail page functionality
$(document).ready(function() {
    // Add click handlers for action buttons
    $('.complete-btn').on('click', function() {
        var transferId = $(this).data('transfer-id');
        completeTransfer(transferId);
    });

    $('.cancel-btn').on('click', function() {
        var transferId = $(this).data('transfer-id');
        cancelTransfer(transferId);
    });

    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // Add keyboard shortcuts
    $(document).on('keydown', function(e) {
        // Ctrl+P to print
        if (e.ctrlKey && e.key === 'p') {
            e.preventDefault();
            var transferId = $('.complete-btn').data('transfer-id') || 
                           $('.cancel-btn').data('transfer-id');
            if (transferId) {
                printTransfer(transferId);
            }
        }
        
        // Ctrl+C to copy transfer number
        if (e.ctrlKey && e.key === 'c') {
            e.preventDefault();
            var transferNumber = $('.transfer-number').text();
            if (transferNumber) {
                copyToClipboard(transferNumber);
            }
        }
    });
}); 