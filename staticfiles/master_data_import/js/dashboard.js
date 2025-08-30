/**
 * Master Data Import Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize progress bars
    initializeProgressBars();
    
    // Initialize timeline animations
    initializeTimeline();
    
    // Add hover effects
    addHoverEffects();
});

function initializeProgressBars() {
    // Handle job progress bars
    const jobProgressBars = document.querySelectorAll('.progress-bar-job .progress-bar');
    jobProgressBars.forEach(bar => {
        const width = bar.getAttribute('data-width');
        if (width) {
            bar.style.width = width + '%';
        }
    });
    
    // Handle statistics progress bars
    const statProgressBars = document.querySelectorAll('.progress-bar-stat');
    statProgressBars.forEach(bar => {
        const completed = parseInt(bar.getAttribute('data-completed'));
        const total = parseInt(bar.getAttribute('data-total'));
        if (total > 0) {
            const percentage = Math.round((completed / total) * 100);
            bar.style.width = percentage + '%';
        }
    });
}

function initializeTimeline() {
    const timelineItems = document.querySelectorAll('.timeline-item');
    
    // Add animation delay to each timeline item
    timelineItems.forEach((item, index) => {
        item.style.animationDelay = (index * 0.1) + 's';
        item.classList.add('animate-slide-in');
    });
}

function addHoverEffects() {
    // Add hover effects to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Add hover effects to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Auto-refresh progress bars every 5 seconds
setInterval(function() {
    // Only refresh if the page is visible
    if (!document.hidden) {
        refreshProgressBars();
    }
}, 5000);

function refreshProgressBars() {
    // This function would typically make an AJAX call to get updated progress
    // For now, we'll just reinitialize the progress bars
    initializeProgressBars();
}

// Add smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add loading states for buttons
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function() {
        if (!this.classList.contains('btn-disabled')) {
            this.classList.add('loading');
            this.disabled = true;
            
            // Re-enable after a delay (adjust as needed)
            setTimeout(() => {
                this.classList.remove('loading');
                this.disabled = false;
            }, 2000);
        }
    });
});

// Export functions for external use
window.MasterDataImportDashboard = {
    initializeProgressBars,
    refreshProgressBars,
    initializeTimeline
};
