/* ============================================
   Chargebotic — Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

    // ---- Sticky Nav ----
    const nav = document.querySelector('.nav');
    if (nav) {
        window.addEventListener('scroll', () => {
            nav.classList.toggle('scrolled', window.scrollY > 40);
        }, { passive: true });
    }

    // ---- Mobile Hamburger ----
    const hamburger = document.querySelector('.nav-hamburger');
    const navLinks = document.querySelector('.nav-links');
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('open');
            navLinks.classList.toggle('open');
        });
        // Close on link click
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('open');
                navLinks.classList.remove('open');
            });
        });
    }

    // ---- Scroll Fade-In ----
    const fadeEls = document.querySelectorAll('.fade-in');
    if (fadeEls.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

        fadeEls.forEach(el => observer.observe(el));
    }

    // ---- Access Gate Modal ----
    const gateOverlay = document.getElementById('gate-overlay');
    const gateInput = document.getElementById('gate-input');
    const gateError = document.getElementById('gate-error');
    const gateEmailFallback = document.getElementById('gate-email-fallback');

    // Open gate
    document.querySelectorAll('[data-gate]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            if (gateOverlay) {
                gateOverlay.classList.add('active');
                if (gateInput) gateInput.focus();
            }
        });
    });

    // Close gate on overlay click
    if (gateOverlay) {
        gateOverlay.addEventListener('click', (e) => {
            if (e.target === gateOverlay) {
                gateOverlay.classList.remove('active');
            }
        });
    }

    // Check code
    window.checkGateCode = function() {
        if (!gateInput) return;
        const code = gateInput.value.trim().toUpperCase();
        if (code === 'SPARK') {
            window.location.href = 'deck/';
        } else {
            if (gateError) gateError.style.display = 'block';
            gateInput.style.borderColor = 'var(--color-error)';
            if (gateEmailFallback) gateEmailFallback.style.display = 'block';
        }
    };

    if (gateInput) {
        gateInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') window.checkGateCode();
        });
    }

    // Email fallback
    window.submitGateEmail = function() {
        const emailInput = document.getElementById('gate-email-input');
        if (!emailInput) return;
        const email = emailInput.value.trim();
        if (email && email.includes('@')) {
            if (gateEmailFallback) {
                gateEmailFallback.innerHTML = '<p style="color: var(--color-success); font-size: 13px; padding: 8px 0;">Thanks! We\'ll send you the access code shortly.</p>';
            }
            console.log('Access requested by:', email);
        }
    };

    // ---- Smooth scroll for anchor links ----
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
});
