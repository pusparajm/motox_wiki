/**
 * MotoX Wiki — client-side anti-scrape layer (public site only).
 * Session-random class/id names, CSS remapping, bot heuristics, honeypots,
 * dynamic HTML structure (dead markup, encoded text, parser traps).
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
    'search-result-item', 'secondary', 'shell', 'sidebar-ad', 'site-ad-bar', 'site-footer',
    'site-footer-ad', 'site-footer-inner', 'site-header', 'site-nav', 'site-top', 'spec-body',
    'spec-field', 'spec-fields', 'spec-section', 'spec-table', 'spec-table-wrap', 'sr-only', 'tag'
  ];

  const DEAD_SNIPPETS = [
    '<div class="{c}" data-mx-dead hidden aria-hidden="true"><span>{t}</span></div>',
    '<template data-mx-dead><nav><a href="{b}data/export.json">{t}</a></nav></template>',
    '<span class="{c}" data-mx-decoy aria-hidden="true" hidden></span>',
    '<i data-mx-dead hidden aria-hidden="true">{t}</i>',
    '<b data-mx-dead hidden aria-hidden="true">{t}</b>'
  ];

  const TRAP_SNIPPETS = [
    'trap:close </div></main></article></body>',
    'trap:table </tr></td></table>',
    'trap:form <form><p></form></p>',
    'trap:dup class="{c}" class="{c2}"'
  ];

  const DECOY_WORDS = [
    'Torque', 'Oil capacity', 'Fork seal', 'Fastener', 'Displacement', 'Catalog', 'Index', 'Export'
  ];

  const map = new Map();
  const idMap = new Map();
  const refCache = new Map();
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

  function sessionRoll(seed) {
    return parseInt(hash(session + seed).slice(0, 8), 36);
  }

  function pick(list, seed) {
    return list[sessionRoll(seed) % list.length];
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

  function idFor(refName) {
    if (!idMap.has(refName)) idMap.set(refName, obfName(`ref-${refName}`));
    return idMap.get(refName);
  }

  function mxRef(name) {
    return `data-mx-ref="${name}"`;
  }

  function ref(name) {
    if (refCache.has(name)) return refCache.get(name);
    const el = document.querySelector(`[data-mx-ref="${name}"]`);
    if (el) refCache.set(name, el);
    return el;
  }

  function variant(seed, count) {
    return sessionRoll(seed) % count;
  }

  function escRx(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function escAttr(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/</g, '&lt;');
  }

  function xorEncode(text) {
    if (!text) return '';
    const bytes = new TextEncoder().encode(String(text));
    let hex = '';
    for (let i = 0; i < bytes.length; i++) {
      hex += (bytes[i] ^ session.charCodeAt(i % session.length || 0)).toString(16).padStart(2, '0');
    }
    return hex;
  }

  function xorDecode(payload) {
    if (!payload || payload.length % 2 !== 0) return '';
    try {
      const bytes = new Uint8Array(payload.length / 2);
      for (let i = 0; i < bytes.length; i++) {
        const byte = parseInt(payload.slice(i * 2, i * 2 + 2), 16);
        if (Number.isNaN(byte)) return '';
        bytes[i] = byte ^ session.charCodeAt(i % session.length || 0);
      }
      return new TextDecoder().decode(bytes);
    } catch {
      return '';
    }
  }

  function enc(text) {
    if (!text || botFlag) return text || '';
    const payload = xorEncode(String(text));
    return `<span data-mx-enc="${escAttr(payload)}" hidden aria-hidden="true"></span>`;
  }

  function decodeEncElements(root) {
    if (!root) return;
    root.querySelectorAll('[data-mx-enc]').forEach(el => {
      const payload = el.getAttribute('data-mx-enc') || '';
      el.textContent = xorDecode(payload);
      el.removeAttribute('data-mx-enc');
      el.removeAttribute('hidden');
      el.removeAttribute('aria-hidden');
    });
  }

  function removeDeadNodes(root) {
    if (!root) return;
    root.querySelectorAll('[data-mx-dead]').forEach(el => el.remove());
  }

  function deadMarkup(seed) {
    const word = DECOY_WORDS[sessionRoll(seed + 'w') % DECOY_WORDS.length];
    const tpl = pick(DEAD_SNIPPETS, seed);
    return tpl
      .replace(/\{c\}/g, c('bike-card'))
      .replace(/\{c2\}/g, c('page-item'))
      .replace(/\{b\}/g, BASE)
      .replace(/\{t\}/g, word);
  }

  function parserTrapText(seed) {
    const word = DECOY_WORDS[sessionRoll(seed + 't') % DECOY_WORDS.length];
    return pick(TRAP_SNIPPETS, seed + 'trap')
      .replace(/\{c\}/g, c('spec-field'))
      .replace(/\{c2\}/g, c('tag'))
      .replace(/\{t\}/g, word);
  }

  function weaveDynamicStructure(html) {
    return html;
  }

  function injectDomNoise(root, seedBase) {
    if (!root || botFlag) return;
    const count = 1 + (sessionRoll(seedBase) % 2);
    for (let i = 0; i < count; i++) {
      const trap = document.createElement('div');
      trap.setAttribute('data-mx-dead', '');
      trap.hidden = true;
      trap.setAttribute('aria-hidden', 'true');
      trap.textContent = parserTrapText(`${seedBase}-dom${i}`);
      root.insertBefore(trap, root.firstChild);

      const decoy = document.createElement('span');
      decoy.className = c('tag');
      decoy.setAttribute('data-mx-decoy', hash(`${seedBase}-dec${i}`).slice(0, 10));
      decoy.hidden = true;
      decoy.setAttribute('aria-hidden', 'true');
      root.appendChild(decoy);
    }
  }

  function cardHtml(href, parts, seed) {
    const card = c('bike-card');
    const shell = c('shell');
    const body = c('spec-body');
    const v = variant(seed, 4);
    let inner;

    switch (v) {
      case 1:
        inner = `<div class="${shell}"><div class="${body}">${parts.make}${parts.model}${parts.meta}${parts.oil}</div></div>`;
        break;
      case 2:
        inner = `${parts.meta}${parts.make}${parts.model}${parts.oil}`;
        break;
      case 3:
        inner = `<div class="${shell}">${parts.make}${parts.model}</div><div class="${body}">${parts.meta}${parts.oil}</div>`;
        break;
      default:
        inner = `${parts.make}${parts.model}${parts.meta}${parts.oil}`;
    }

    return `<a href="${escAttr(href)}" class="${card}">${inner}</a>`;
  }

  function searchResultHtml(href, parts, seed) {
    const item = c('search-result-item');
    const shell = c('shell');
    const v = variant(seed, 3);
    let inner;

    switch (v) {
      case 1:
        inner = `<div class="${shell}"><div class="${c('result-title')}">${parts.title}</div><div class="${c('result-meta')}">${parts.meta}</div></div>`;
        break;
      case 2:
        inner = `<div class="${c('result-meta')}">${parts.meta}</div><div class="${c('result-title')}">${parts.title}</div>`;
        break;
      default:
        inner = `<div class="${c('result-title')}">${parts.title}</div><div class="${c('result-meta')}">${parts.meta}</div>`;
    }

    return `<a href="${escAttr(href)}" class="${item}" role="option">${inner}</a>`;
  }

  function pageItemHtml(href, parts, seed) {
    const item = c('page-item');
    const shell = c('shell');
    const v = variant(seed, 3);
    let inner;

    switch (v) {
      case 1:
        inner = `<div class="${shell}"><h3>${parts.title}</h3><p>${parts.meta}</p></div>`;
        break;
      case 2:
        inner = `<p>${parts.meta}</p><h3>${parts.title}</h3>`;
        break;
      default:
        inner = `<h3>${parts.title}</h3><p>${parts.meta}</p>`;
    }

    return `<a href="${escAttr(href)}" class="${item}">${inner}</a>`;
  }

  function mutateRefsIn(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-mx-ref]').forEach(el => {
      const name = el.getAttribute('data-mx-ref');
      if (!name) return;
      el.id = idFor(name);
      refCache.set(name, el);
      el.removeAttribute('data-mx-ref');
    });
  }

  function wireAriaRefsIn(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-mx-controls]').forEach(el => {
      const name = el.getAttribute('data-mx-controls');
      const target = ref(name);
      if (target?.id) el.setAttribute('aria-controls', target.id);
    });
    scope.querySelectorAll('[data-mx-for]').forEach(label => {
      const name = label.getAttribute('data-mx-for');
      const target = ref(name);
      if (target?.id) label.setAttribute('for', target.id);
    });
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
    return weaveDynamicStructure(html);
  }

  function mutateStaticShell() {
    document.querySelectorAll('[class]').forEach(el => {
      if (el.id === 'mx-shield-css') return;
      el.className = el.className.split(/\s+/).filter(Boolean).map(token => c(token)).join(' ');
    });
    mutateRefsIn(document);
    wireAriaRefsIn(document);
  }

  function rewriteRoot(root) {
    if (!root) return;
    root.querySelectorAll('[class]').forEach(el => {
      el.className = el.className.split(/\s+/).filter(Boolean).map(token => c(token)).join(' ');
    });
  }

  function finalizeRoot(root) {
    if (!root || botFlag) return;
    decodeEncElements(root);
    injectDomNoise(root, hash(String(root.getAttribute?.('data-mx-ref') || root.id || root.childElementCount) + session));
    removeDeadNodes(root);
    mutateRefsIn(root);
    wireAriaRefsIn(root);
    rewriteRoot(root);
  }

  function setHtml(el, html) {
    if (!el) return;
    el.innerHTML = wrapHtml(html);
    finalizeRoot(el);
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
    enc,
    ref,
    mxRef,
    idFor,
    variant,
    cardHtml,
    pageItemHtml,
    searchResultHtml,
    bootstrap: () => cssReady || Promise.resolve(),
    wrapHtml,
    rewriteRoot,
    finalizeRoot,
    setHtml,
    guardedFetch,
    isBot: () => botFlag,
    BASE
  };
})();
