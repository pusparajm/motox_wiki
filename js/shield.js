/**
 * MotoX Wiki — client-side anti-scrape layer (public site only).
 * Session-random class names, CSS remapping, bot heuristics, honeypots.
 */
const MotoXShield = (() => {
  const KNOWN = [
    'active', 'ad-placeholder', 'ad-slot', 'adsbygoogle', 'bike-card', 'bike-grid', 'bike-header',
    'bike-make', 'bike-meta', 'bike-model', 'bike-oil', 'bike-subtitle', 'bike-title', 'bike-variant',
    'brand', 'brand-icon', 'breadcrumb', 'browse-pagination', 'browse-showing-count', 'container',
    'custom-section', 'empty-state', 'field-label', 'field-value', 'filter-bar', 'footer-text',
    'has-ad', 'has-sidebar', 'header-row', 'header-search', 'loading', 'nav-toggle', 'nav-toggle-bar',
    'oil-cap', 'oil-sep', 'oil-type', 'open', 'outline', 'page-content', 'page-item', 'page-layout',
    'page-list', 'result-meta', 'result-title', 'search-dropdown', 'search-no-results',
    'search-result-item', 'secondary', 'sidebar-ad', 'site-ad-bar', 'site-footer', 'site-footer-ad',
    'site-footer-inner', 'site-header', 'site-nav', 'site-top', 'spec-body', 'spec-field', 'spec-fields',
    'spec-section', 'spec-table', 'spec-table-wrap', 'sr-only', 'tag'
  ];

  const map = new Map();
  let session = '';
  let cssReady = null;
  let botFlag = false;

  function basePath() {
    const path = window.location.pathname;
    const parts = path.split('/').filter(Boolean);
    const depth = parts.length && parts[parts.length - 1].includes('.') ? parts.length - 1 : parts.length;
    return depth <= 1 ? './' : '../'.repeat(depth - 1);
  }

  const BASE = basePath();

  function hash(input) {
    let h = 2166136261;
    for (let i = 0; i < input.length; i++) {
      h ^= input.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return (h >>> 0).toString(36);
  }

  function obfName(semantic) {
    return `_mx${hash(session + semantic).slice(0, 9)}${hash(semantic + session).slice(0, 4)}`;
  }

  function initMap() {
    session = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
    KNOWN.forEach(name => map.set(name, obfName(name)));
    document.documentElement.dataset.mxSession = session.slice(-8);
  }

  function c(name) {
    return map.get(name) || name;
  }

  function cx(...names) {
    return names.map(n => c(n)).join(' ');
  }

  function escRx(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  async function injectCss() {
    const link = document.getElementById('mx-main-css') || document.querySelector('link[href*="main.css"]');
    const href = link?.getAttribute('href') || `${BASE}css/main.css`;
    const res = await fetch(href, { cache: 'no-store' });
    if (!res.ok) throw new Error('CSS load failed');
    let css = await res.text();

    const sorted = [...map.entries()].sort((a, b) => b[0].length - a[0].length);
    sorted.forEach(([sem, obf]) => {
      css = css.replace(new RegExp(`\\.${escRx(sem)}(?=[\\s,{.:>#\\[+~]|$)`, 'g'), `.${obf}`);
    });

    const tag = document.createElement('style');
    tag.id = 'mx-shield-css';
    tag.textContent = css;
    document.head.appendChild(tag);
    if (link) link.disabled = true;
  }

  function runDecoyVm() {
    const ops = [0x4a, 0x11, 0xff, 0x02, 0x9c, 0x31];
    let acc = 0;
    for (let i = 0; i < ops.length; i++) {
      acc = ((acc << 3) ^ ops[i]) >>> 0;
      acc = Math.imul(acc ^ session.charCodeAt(i % session.length || 0), 0x9e3779b1) >>> 0;
    }
    return acc;
  }

  function detectBot() {
    const ua = navigator.userAgent || '';
    if (navigator.webdriver) return true;
    if (window.document.documentElement.getAttribute('webdriver')) return true;
    if (/HeadlessChrome|Puppeteer|Playwright|PhantomJS|selenium|webdriver/i.test(ua)) return true;
    if (window.callPhantom || window._phantom || window.__nightmare) return true;
    if (window.outerWidth === 0 && window.outerHeight === 0) return true;
    return false;
  }

  function plantHoneypots() {
    const trap = document.createElement('div');
    trap.setAttribute('aria-hidden', 'true');
    trap.hidden = true;
    trap.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden;clip:rect(0,0,0,0)';
    trap.innerHTML = `<nav>
      <a href="${BASE}data/motorcycles-index.json" class="${c('bike-card')}" tabindex="-1">catalog</a>
      <a href="${BASE}data/search-index.json" class="${c('page-item')}" tabindex="-1">index</a>
    </nav>`;
    document.body.appendChild(trap);
  }

  function wrapHtml(html) {
    if (!html || botFlag) return html;
    const comment = `<!--${hash(html.length + session).slice(0, 12)}-->`;
    return comment + html + comment;
  }

  function mutateStaticShell() {
    document.querySelectorAll('[class]').forEach(el => {
      if (el.id === 'mx-shield-css') return;
      el.className = el.className.split(/\s+/).filter(Boolean).map(token => c(token)).join(' ');
    });
  }

  function rewriteRoot(root) {
    if (!root) return;
    root.querySelectorAll('[class]').forEach(el => {
      el.className = el.className.split(/\s+/).filter(Boolean).map(token => c(token)).join(' ');
    });
  }

  async function guardedFetch(url, init = {}) {
    if (botFlag) {
      return new Response('{}', { status: 403, headers: { 'Content-Type': 'application/json' } });
    }
    const headers = new Headers(init.headers || {});
    headers.set('X-MX-Client', hash(session + 'client'));
    headers.set('X-MX-Stamp', String(Date.now()));
    return fetch(url, { ...init, headers, credentials: init.credentials || 'same-origin' });
  }

  function bootstrap() {
    if (cssReady) return cssReady;
    document.documentElement.classList.add('mx-lock');
    initMap();
    botFlag = detectBot();
    runDecoyVm();
    plantHoneypots();

    cssReady = injectCss()
      .then(() => {
        mutateStaticShell();
        document.documentElement.classList.remove('mx-lock');
      })
      .catch(() => {
        document.documentElement.classList.remove('mx-lock');
      });

    return cssReady;
  }

  bootstrap();

  return {
    c,
    cx,
    bootstrap: () => cssReady || Promise.resolve(),
    wrapHtml,
    rewriteRoot,
    guardedFetch,
    isBot: () => botFlag,
    BASE
  };
})();
