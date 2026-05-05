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

  document.querySelectorAll('[data-qty-step]').forEach(button => {
    button.addEventListener('click', function () {
      const form = this.closest('form');
      const target = this.dataset.qtyTarget
        ? document.querySelector(this.dataset.qtyTarget)
        : form && form.querySelector('[name=quantity]');
      if (!target) return;

      const step = parseInt(this.dataset.qtyStep, 10);
      step < 0 ? target.stepDown() : target.stepUp();
      target.dispatchEvent(new Event('change', { bubbles: true }));

      if (this.dataset.submitForm === 'true' && form) {
        form.submit();
      }
    });
  });

  document.querySelectorAll('[data-submit-on-change], [data-auto-submit]').forEach(input => {
    input.addEventListener('change', function () {
      const form = this.closest('form');
      if (form) form.submit();
    });
  });

  document.querySelectorAll('[data-sort-url]').forEach(select => {
    select.addEventListener('change', function () {
      const url = new URL(window.location.href);
      url.searchParams.set('sort', this.value);
      window.location.href = url.toString();
    });
  });

  document.querySelectorAll('[data-print-document]').forEach(button => {
    button.addEventListener('click', () => window.print());
  });

  document.querySelectorAll('.star-label').forEach(label => {
    label.addEventListener('click', function () {
      const val = parseInt(this.dataset.val, 10);
      document.querySelectorAll('.star-label').forEach((starLabel, index) => {
        const icon = starLabel.querySelector('i');
        if (icon) icon.classList.toggle('text-warning', index < val);
      });
    });
  });

  document.querySelectorAll('[data-payment-wait]').forEach(waitPanel => {
    const statusUrl = waitPanel.dataset.statusUrl;
    const confirmationUrl = waitPanel.dataset.confirmationUrl;
    const csrfToken = waitPanel.dataset.csrfToken;
    let attempts = 0;
    const maxAttempts = 24;

    const statusText = document.getElementById('statusText');
    const successMsg = document.getElementById('successMsg');
    const failMsg = document.getElementById('failMsg');
    const actions = document.getElementById('actions');
    const receiptText = document.getElementById('receiptText');

    function checkStatus() {
      fetch(statusUrl, { method: 'POST', headers: { 'X-CSRFToken': csrfToken } })
        .then(response => response.json())
        .then(data => {
          if (data.paid) {
            if (statusText) statusText.textContent = 'Payment confirmed!';
            if (successMsg) successMsg.classList.remove('d-none');
            if (failMsg) failMsg.classList.add('d-none');
            if (actions) actions.classList.add('d-none');
            if (data.receipt && receiptText) receiptText.textContent = 'Receipt: ' + data.receipt;
            setTimeout(() => { window.location.href = confirmationUrl; }, 2500);
            return;
          }

          if (data.status === 'failed' || data.status === 'cancelled') {
            if (failMsg) failMsg.classList.remove('d-none');
            if (statusText) statusText.textContent = 'Payment failed.';
            return;
          }

          attempts++;
          if (attempts < maxAttempts) {
            if (statusText) statusText.textContent = `Waiting... (${attempts * 5}s elapsed)`;
            setTimeout(checkStatus, 5000);
          } else if (statusText) {
            statusText.textContent = 'Timed out. Please check your M-Pesa or retry.';
          }
        })
        .catch(() => {
          attempts++;
          if (attempts < maxAttempts) setTimeout(checkStatus, 5000);
        });
    }

    setTimeout(checkStatus, 5000);
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
