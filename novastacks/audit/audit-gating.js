(function() {
  'use strict';

  var urlParams = new URLSearchParams(window.location.search);
  var unlockToken = urlParams.get('unlock');

  function unlockReport() {
    var gatedSections = document.querySelectorAll('.gated-section');
    gatedSections.forEach(function(section) {
      section.classList.add('unlocked');
    });
    sessionStorage.setItem('audit-unlocked', 'true');

    if (typeof gtag !== 'undefined') {
      gtag('event', 'audit_unlocked', {
        'event_category': 'conversion',
        'event_label': window.location.pathname
      });
    }
  }

  function showUnlockError() {
    var banner = document.createElement('div');
    banner.className = 'fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-red-600 text-white px-6 py-3 rounded-lg shadow-xl font-mono text-sm';
    banner.style.transform = 'translateX(-50%)';
    banner.textContent = 'Invalid unlock token. Please check your email for the correct link.';
    document.body.appendChild(banner);
    setTimeout(function() { banner.remove(); }, 5000);
  }

  document.addEventListener('DOMContentLoaded', function() {
    // Check session storage first
    if (sessionStorage.getItem('audit-unlocked') === 'true') {
      unlockReport();
      return;
    }

    // Check URL token
    if (unlockToken) {
      var expectedToken = window.AUDIT_UNLOCK_TOKEN || '';
      if (unlockToken === expectedToken) {
        unlockReport();
      } else {
        showUnlockError();
      }
    }

    // Track scroll depth
    var scrollTracked = {};
    window.addEventListener('scroll', function() {
      var pct = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
      [25, 50, 75, 100].forEach(function(depth) {
        if (pct >= depth && !scrollTracked[depth]) {
          scrollTracked[depth] = true;
          if (typeof gtag !== 'undefined') {
            gtag('event', 'scroll', { event_category: 'audit_engagement', event_label: depth + '%' });
          }
        }
      });
    });

    // Track CTA clicks
    document.querySelectorAll('a[href*="calendar.app.google"]').forEach(function(link) {
      link.addEventListener('click', function() {
        if (typeof gtag !== 'undefined') {
          gtag('event', 'cta_click', { event_category: 'conversion', event_label: 'book_discovery_call' });
        }
      });
    });

    // Track gated section views
    if ('IntersectionObserver' in window) {
      var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting && typeof gtag !== 'undefined') {
            gtag('event', 'gated_section_view', {
              event_category: 'audit_engagement',
              event_label: entry.target.getAttribute('data-section-id') || 'unknown'
            });
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.3 });

      document.querySelectorAll('.gated-section').forEach(function(section) {
        observer.observe(section);
      });
    }
  });
})();
