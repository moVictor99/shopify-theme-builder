/* global.js — progressive enhancement custom elements. Vanilla, no globals. */

/**
 * <header-nav> — mobile menu toggle. Enhances the header markup rendered by
 * sections/header.liquid. Works without JS (nav is visible on desktop).
 */
class HeaderNav extends HTMLElement {
  connectedCallback() {
    this.toggle = this.querySelector('[data-header-toggle]');
    this.nav = this.querySelector('[data-header-nav]');
    if (!this.toggle || !this.nav) return;

    this.onToggle = this.onToggle.bind(this);
    this.onKeydown = this.onKeydown.bind(this);

    this.toggle.addEventListener('click', this.onToggle);
    this.addEventListener('keydown', this.onKeydown);
  }

  disconnectedCallback() {
    if (this.toggle) this.toggle.removeEventListener('click', this.onToggle);
    this.removeEventListener('keydown', this.onKeydown);
  }

  onToggle() {
    const open = this.toggle.getAttribute('aria-expanded') === 'true';
    this.setOpen(!open);
  }

  setOpen(open) {
    this.toggle.setAttribute('aria-expanded', String(open));
    this.nav.setAttribute('data-open', String(open));
    if (open) {
      const firstLink = this.nav.querySelector('a');
      if (firstLink) firstLink.focus();
    }
  }

  onKeydown(event) {
    if (event.key === 'Escape' && this.toggle.getAttribute('aria-expanded') === 'true') {
      this.setOpen(false);
      this.toggle.focus();
    }
  }
}

/**
 * <cart-drawer> — placeholder no-op enhancement so the element upgrades cleanly.
 * Real drawer logic arrives in a later phase.
 */
class CartDrawer extends HTMLElement {
  connectedCallback() {
    // Intentionally minimal for the skeleton phase.
  }
}

if (!customElements.get('header-nav')) customElements.define('header-nav', HeaderNav);
if (!customElements.get('cart-drawer')) customElements.define('cart-drawer', CartDrawer);

/* --- Quantity inputs: auto-submit the closest cart form on change --------- */
document.addEventListener('change', (event) => {
  const input = event.target;
  if (!(input instanceof HTMLElement) || !input.matches('[data-quantity-input]')) return;
  const form = input.closest('form');
  if (form && typeof form.requestSubmit === 'function') {
    form.requestSubmit();
  }
});

/* --- Reveal on scroll ----------------------------------------------------- */
(function initReveal() {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const elements = document.querySelectorAll('.reveal');
  if (!elements.length) return;

  if (reduceMotion || !('IntersectionObserver' in window)) {
    elements.forEach((el) => el.classList.add('is-visible'));
    return;
  }

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        obs.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -10% 0px' });

  elements.forEach((el) => observer.observe(el));
})();
