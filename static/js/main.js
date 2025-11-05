// Art Auction Website - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add fade-in animation to cards on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card').forEach(card => {
        observer.observe(card);
    });

    // Smooth scroll for anchor links
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

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('input[type="number"][name*="price"], input[type="number"][name*="bid"]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
    });

    // Confirm before placing bid
    const bidForms = document.querySelectorAll('form[action*="place_bid"]');
    bidForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const bidAmount = this.querySelector('input[name="bid_amount"]').value;
            const confirmMessage = `Are you sure you want to place a bid of $${parseFloat(bidAmount).toFixed(2)}?`;
            
            if (!confirm(confirmMessage)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Image lazy loading
    const images = document.querySelectorAll('img[data-src]');
    const imageOptions = {
        threshold: 0,
        rootMargin: '0px 0px 300px 0px'
    };

    const imageObserver = new IntersectionObserver(function(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                imageObserver.unobserve(img);
            }
        });
    }, imageOptions);

    images.forEach(img => imageObserver.observe(img));

    // Search form enhancement
    const searchForm = document.getElementById('filterForm');
    if (searchForm) {
        // Add loading state
        searchForm.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Searching...';
                submitBtn.disabled = true;
            }
        });

        // Price range validation
        const minPrice = searchForm.querySelector('input[name="min_price"]');
        const maxPrice = searchForm.querySelector('input[name="max_price"]');
        
        if (minPrice && maxPrice) {
            maxPrice.addEventListener('change', function() {
                if (minPrice.value && parseFloat(this.value) < parseFloat(minPrice.value)) {
                    alert('Maximum price cannot be less than minimum price');
                    this.value = '';
                }
            });
        }
    }

    // Countdown timer update function
    window.updateAllCountdowns = function() {
        const countdowns = document.querySelectorAll('[data-end-time]');
        countdowns.forEach(countdown => {
            const endTime = new Date(countdown.dataset.endTime).getTime();
            const now = new Date().getTime();
            const timeLeft = endTime - now;
            
            if (timeLeft > 0) {
                const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
                const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
                
                let timeString = '';
                if (days > 0) timeString += days + 'd ';
                if (hours > 0 || days > 0) timeString += hours + 'h ';
                timeString += minutes + 'm';
                
                countdown.textContent = timeString;
                
                // Add urgency styling
                if (timeLeft < 3600000) { // Less than 1 hour
                    countdown.classList.add('text-danger', 'fw-bold');
                }
            } else {
                countdown.textContent = 'Ended';
                countdown.classList.add('text-muted');
            }
        });
    };

    // Update countdowns every minute
    if (document.querySelector('[data-end-time]')) {
        updateAllCountdowns();
        setInterval(updateAllCountdowns, 60000);
    }

    // File upload preview enhancement
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'No file selected';
            const fileSize = this.files[0]?.size;
            
            // Update label if exists
            const label = this.nextElementSibling;
            if (label && label.tagName === 'LABEL') {
                label.textContent = fileName;
            }
            
            // Check file size
            if (fileSize && fileSize > 16 * 1024 * 1024) {
                alert('File size must be less than 16MB');
                this.value = '';
            }
        });
    });

    // Add to favorites functionality (placeholder)
    document.querySelectorAll('.btn-favorite').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            this.classList.toggle('active');
            const icon = this.querySelector('i');
            if (icon) {
                icon.classList.toggle('bi-heart');
                icon.classList.toggle('bi-heart-fill');
            }
        });
    });

    // Print functionality for receipts
    window.printAuctionReceipt = function(auctionId) {
        window.print();
    };

    // Check auction status periodically
    function checkAuctionStatus() {
        fetch('/api/check_auction_status')
            .then(response => response.json())
            .then(data => {
                console.log('Auction status checked');
            })
            .catch(error => {
                console.error('Error checking auction status:', error);
            });
    }

    // Check auction status every 5 minutes
    setInterval(checkAuctionStatus, 300000);

    // Mobile menu enhancement
    const navToggler = document.querySelector('.navbar-toggler');
    if (navToggler) {
        navToggler.addEventListener('click', function() {
            document.body.classList.toggle('menu-open');
        });
    }

    // Accessibility enhancements
    // Add keyboard navigation for cards
    document.querySelectorAll('.auction-card').forEach(card => {
        card.setAttribute('tabindex', '0');
        card.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                this.click();
            }
        });
    });

    // Form validation feedback
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Copy to clipboard functionality
    window.copyToClipboard = function(text) {
        navigator.clipboard.writeText(text).then(function() {
            const toast = document.createElement('div');
            toast.className = 'toast position-fixed bottom-0 end-0 m-3';
            toast.innerHTML = `
                <div class="toast-body">
                    <i class="bi bi-check-circle text-success"></i> Copied to clipboard!
                </div>
            `;
            document.body.appendChild(toast);
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
            
            setTimeout(() => {
                toast.remove();
            }, 3000);
        });
    };

    // Debug mode for development
    if (window.location.hostname === 'localhost') {
        console.log('Art Auction Website - Debug Mode');
        console.log('Page loaded:', new Date().toISOString());
    }
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
});

// Service worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Uncomment to enable service worker
        // navigator.serviceWorker.register('/sw.js');
    });
}
