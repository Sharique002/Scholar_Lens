/**
 * Main JavaScript File for Scholar Lens
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Menu Toggle
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    
    if (mobileBtn && navLinks) {
        mobileBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            const hamburger = mobileBtn.querySelector('.hamburger');
            if (navLinks.classList.contains('active')) {
                hamburger.style.backgroundColor = 'transparent';
                hamburger.style.setProperty('--before-transform', 'rotate(45deg) translate(5px, 5px)');
                hamburger.style.setProperty('--after-transform', 'rotate(-45deg) translate(5px, -5px)');
            } else {
                hamburger.style.backgroundColor = '';
                hamburger.style.setProperty('--before-transform', 'none');
                hamburger.style.setProperty('--after-transform', 'none');
            }
        });
    }

    // 2. Dropdown Toggle for Navigation
    const dropdowns = document.querySelectorAll('.nav-dropdown');
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        if (toggle) {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                // Close others
                dropdowns.forEach(d => {
                    if (d !== dropdown) d.classList.remove('active');
                });
                dropdown.classList.toggle('active');
            });
        }
    });

    // Close dropdowns on outside click
    document.addEventListener('click', () => {
        dropdowns.forEach(d => d.classList.remove('active'));
    });

    // 3. Alerts Auto-Dismiss
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector('.close-alert');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            });
        }
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (document.body.contains(alert)) {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    });

    // 4. Tabs Switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const tabsContainer = btn.closest('.tabs-container') || document;
            
            // Remove active class from all buttons and contents in this container
            tabsContainer.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            tabsContainer.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked button and target content
            btn.classList.add('active');
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });

    // 5. Confirm Delete Dialogs
    const confirmBtns = document.querySelectorAll('[data-confirm]');
    confirmBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const message = btn.getAttribute('data-confirm') || 'Are you sure you want to perform this action?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // 6. Initialize Score Rings
    const scoreRings = document.querySelectorAll('.score-ring');
    scoreRings.forEach(ring => {
        const score = parseFloat(ring.getAttribute('data-score') || 0);
        const percentage = score * 100; // Assuming score is 0-1 or 0-100? If 0-100:
        const pct = score <= 1 ? score * 100 : score;
        ring.style.setProperty('--score', `${pct}%`);
        
        // Change color based on score
        if (pct >= 80) ring.style.setProperty('--primary', 'var(--success)');
        else if (pct >= 50) ring.style.setProperty('--primary', 'var(--warning)');
        else ring.style.setProperty('--primary', 'var(--danger)');
    });

    // 7. File Input Preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            const label = input.nextElementSibling;
            if (label && label.classList.contains('custom-file-label')) {
                const fileName = e.target.files[0] ? e.target.files[0].name : 'Choose file...';
                label.textContent = fileName;
            }
        });
    });

    // 9. Interactive Mouse Parallax for Hero Floating Books
    const heroCard = document.querySelector('.hero-pop-card');
    const floatingBooks = document.querySelectorAll('.floating-book');
    if (heroCard && floatingBooks.length > 0) {
        heroCard.addEventListener('mousemove', (e) => {
            const rect = heroCard.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            
            floatingBooks.forEach((book, index) => {
                const depth = (index + 1) * 14;
                const rotateOffset = index === 0 ? -18 : (index === 1 ? 16 : 34);
                book.style.transform = `translate(${x * depth}px, ${y * depth}px) rotate(${rotateOffset + x * 6}deg)`;
            });
        });

        heroCard.addEventListener('mouseleave', () => {
            floatingBooks.forEach((book, index) => {
                const rotateOffset = index === 0 ? -18 : (index === 1 ? 16 : 34);
                book.style.transform = `rotate(${rotateOffset}deg)`;
            });
        });
    }

    // 10. Sticky Navbar Blur on Scroll
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 20) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
});

// CSRF Token Helper for AJAX
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
