/* TechStore KE – main.js */

document.addEventListener('DOMContentLoaded', function () {

  // ── Navbar scroll effect ──────────────────────────────────
  const nav = document.getElementById('mainNav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.style.background = window.scrollY > 50
        ? 'rgba(13, 13, 20, 0.98)'
        : 'rgba(13, 13, 20, 0.95)';
    }, { passive: true });
  }

  // ── Auto-dismiss alerts ───────────────────────────────────
  document.querySelectorAll('.alert:not(.alert-danger)').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert && bsAlert.close();
    }, 4000);
  });

  // ── Add-to-cart AJAX for product listing pages ────────────
  document.querySelectorAll('.add-to-cart-form').forEach(form => {
    form.addEventListener('submit', function (e) {
      const btn = form.querySelector('button[type="submit"]');
      if (!btn) return;

      // Visual feedback: pulse the cart badge
      const badge = document.querySelector('.cart-badge');
      if (badge) {
        badge.style.transform = 'scale(1.4)';
        setTimeout(() => { badge.style.transform = 'scale(1)'; }, 200);
      }

      // Short button animation
      const origHTML = btn.innerHTML;
      btn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Added!';
      btn.disabled = true;
      setTimeout(() => {
        btn.innerHTML = origHTML;
        btn.disabled = false;
      }, 1500);
    });
  });

  // ── Smooth image error fallback ───────────────────────────
  document.querySelectorAll('img[data-fallback]').forEach(img => {
    img.addEventListener('error', function () {
      this.src = this.dataset.fallback;
    });
  });

  // ── Sticky filter form – preserve scroll position ─────────
  const filterForm = document.getElementById('filterForm');
  if (filterForm) {
    filterForm.addEventListener('submit', () => {
      sessionStorage.setItem('shopScrollY', window.scrollY);
    });
    const savedY = sessionStorage.getItem('shopScrollY');
    if (savedY) {
      window.scrollTo(0, parseInt(savedY));
      sessionStorage.removeItem('shopScrollY');
    }
  }

  // ── Qty input: prevent values below 1 ────────────────────
  document.querySelectorAll('.qty-input').forEach(input => {
    input.addEventListener('change', function () {
      if (parseInt(this.value) < 1) this.value = 1;
    });
  });

  // ── Tooltips ──────────────────────────────────────────────
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });

  // ── Cart badge counter update helper (used after AJAX) ────
  window.updateCartBadge = function (count) {
    document.querySelectorAll('.cart-badge').forEach(badge => {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    });
  };

});
