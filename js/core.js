/**
 * MotoX Wiki — shared utilities, data loading, ads, and navigation
 */
const MotoX = (() => {
  const BASE = getBasePath();

  function mx(name) {
    return typeof MotoXShield !== 'undefined' ? MotoXShield.c(name) : name;
  }

  function mxHook(name) {
    return `data-mx-hook="${name}"`;
  }

  function mxRef(name) {
    return typeof MotoXShield !== 'undefined' ? MotoXShield.mxRef(name) : `data-mx-ref="${name}"`;
  }

  function ref(name) {
    if (typeof MotoXShield !== 'undefined') return MotoXShield.ref(name);
    return document.querySelector(`[data-mx-ref="${name}"]`) || document.getElementById(name);
  }

  function getBasePath() {
    const path = window.location.pathname;
    const parts = path.split('/').filter(Boolean);
    if (parts.length <= 1) return './';
    const depth = parts[parts.length - 1].includes('.') ? parts.length - 1 : parts.length;
    return depth <= 1 ? './' : '../'.repeat(depth - 1);
  }

  const cache = {};

  async function fetchJSON(file) {
    if (cache[file]) return structuredClone(cache[file]);
    const url = `${BASE}data/${file}`;
    const fetchFn = typeof MotoXShield !== 'undefined' ? MotoXShield.guardedFetch.bind(MotoXShield) : fetch;
    const res = await fetchFn(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`Failed to load ${file}`);
    const data = await res.json();
    cache[file] = data;
    return structuredClone(data);
  }

  async function loadSettings() {
    return fetchJSON('settings.json');
  }

  async function loadMotorcycleIndex() {
    const data = await fetchJSON('motorcycles-index.json');
    return (data.motorcycles || []).filter(m => m.published !== false);
  }

  async function loadMotorcycle(id) {
    if (!id) return null;
    const data = await fetchJSON(`motorcycles/${encodeURIComponent(id)}.json`);
    const bike = data.motorcycle || data;
    return bike?.published === false ? null : bike;
  }

  async function loadPopularSummaries(settings) {
    const popular = settings?.popular_models;
    if (!popular || popular.enabled === false) return [];

    const ids = popular.ids || [];
    if (!ids.length) return [];

    const summaryMap = new Map();

    try {
      const cached = await fetchJSON('popular-summaries.json');
      (cached.motorcycles || []).forEach(m => summaryMap.set(m.id, m));
    } catch { /* optional cache file */ }

    if (ids.some(id => !summaryMap.has(id))) {
      const index = await loadMotorcycleIndex();
      index.forEach(m => summaryMap.set(m.id, m));
    }

    return ids.map(id => summaryMap.get(id)).filter(Boolean);
  }

  async function loadPagesIndex() {
    const data = await fetchJSON('pages-index.json');
    return (data.pages || [])
      .filter(p => p.published !== false)
      .sort((a, b) => (a.order || 0) - (b.order || 0));
  }

  async function loadPage(slug) {
    if (!slug) return null;
    const data = await fetchJSON(`pages/${encodeURIComponent(slug)}.json`);
    const page = data.page || data;
    return page?.published === false ? null : page;
  }

  async function loadSearchIndex() {
    const data = await fetchJSON('search-index.json');
    return data.items || [];
  }

  /** @deprecated Use loadMotorcycleIndex or loadMotorcycle for public pages. */
  async function loadMotorcycles() {
    try {
      return await loadMotorcycleIndex();
    } catch {
      const data = await fetchJSON('motorcycles.json');
      return (data.motorcycles || []).filter(m => m.published !== false);
    }
  }

  /** @deprecated Use loadPagesIndex or loadPage for public pages. */
  async function loadPages() {
    try {
      return await loadPagesIndex();
    } catch {
      const data = await fetchJSON('pages.json');
      return (data.pages || []).filter(p => p.published !== false).sort((a, b) => (a.order || 0) - (b.order || 0));
    }
  }

  async function loadAllSearchData() {
    const [motorcycles, pages, settings] = await Promise.all([
      loadMotorcycles(),
      loadPages(),
      loadSettings()
    ]);
    return { motorcycles, pages, settings };
  }

  function getMotorcycleById(motorcycles, id) {
    return motorcycles.find(m => m.id === id);
  }

  function getPageBySlug(pages, slug) {
    return pages.find(p => p.slug === slug || p.id === slug);
  }

  function renderAdSlot(slots, slotId) {
    if (!slots || !slots.enabled) return '';
    const slot = (slots.slots || []).find(s => s.id === slotId && s.enabled);
    if (!slot) return '';
    if (slot.type === 'adsense' && slot.client && slot.slotId) {
      return `<ins class="adsbygoogle" style="display:block" data-ad-client="${escapeHtml(slot.client)}" data-ad-slot="${escapeHtml(slot.slotId)}" data-ad-format="auto" data-full-width-responsive="true"></ins>`;
    }
    return slot.content || '';
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function shieldEnc(str) {
    if (!str) return '';
    return typeof MotoXShield !== 'undefined' ? MotoXShield.enc(str) : escapeHtml(str);
  }

  function finalizeContent(root) {
    if (typeof MotoXShield !== 'undefined') MotoXShield.finalizeRoot(root);
  }

  function setContainerHtml(container, html) {
    if (!container) return;
    if (typeof MotoXShield !== 'undefined') {
      MotoXShield.setHtml(container, html);
    } else {
      container.innerHTML = html;
    }
  }

  function renderHeader(container, settings, activePage) {
    if (!container) return;
    const site = settings.site || {};
    const nav = settings.navigation || [];

    setContainerHtml(container, `
      <div class="${mx('container')}">
        <div class="${mx('header-row')}">
          <a href="${BASE}index.html" class="${mx('brand')}">
            <span class="${mx('brand-icon')}">⚙</span>
            <span>${shieldEnc(site.title || 'MotoX Wiki')}</span>
          </a>
          <button type="button" class="${mx('nav-toggle')}" ${mxHook('nav-toggle')} aria-label="Toggle navigation" aria-expanded="false" data-mx-controls="site-nav">
            <span class="${mx('nav-toggle-bar')}"></span>
            <span class="${mx('nav-toggle-bar')}"></span>
            <span class="${mx('nav-toggle-bar')}"></span>
          </button>
        </div>
        <nav ${mxRef('site-nav')} class="${mx('site-nav')}" aria-label="Main navigation">
          ${nav.map(item => {
            const isActive = activePage && (item.href === activePage || item.href.includes(activePage));
            return `<a href="${BASE}${item.href.replace(/^\.\//, '')}" ${isActive ? `class="${mx('active')}"` : ''}>${shieldEnc(item.label)}</a>`;
          }).join('')}
        </nav>
        <div class="${mx('header-search')}">
          <label data-mx-for="global-search" class="${mx('sr-only')}">Search motorcycles and pages</label>
          <input type="search" ${mxRef('global-search')} placeholder="Search specs, models…" autocomplete="off" aria-expanded="false" data-mx-controls="search-dropdown" enterkeyhint="search">
          <div ${mxRef('search-dropdown')} class="${mx('search-dropdown')}" role="listbox"></div>
        </div>
      </div>
    `);

    initMobileNav(container);
  }

  function initMobileNav(header) {
    const toggle = header.querySelector('[data-mx-hook="nav-toggle"]');
    const nav = ref('site-nav');
    if (!toggle || !nav) return;

    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle(mx('open'));
      toggle.setAttribute('aria-expanded', String(open));
    });

    nav.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        nav.classList.remove(mx('open'));
        toggle.setAttribute('aria-expanded', 'false');
      });
    });

    document.addEventListener('click', e => {
      if (!header.contains(e.target)) {
        nav.classList.remove(mx('open'));
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  function renderAdBar(settings) {
    const header = ref('site-header');
    if (!header) return;

    let wrapper = header.parentElement;
    if (!wrapper.classList.contains(mx('site-top'))) {
      wrapper = document.createElement('div');
      wrapper.className = mx('site-top');
      header.parentNode.insertBefore(wrapper, header);
      wrapper.appendChild(header);
    }

    let bar = ref('site-ad-bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.setAttribute('data-mx-ref', 'site-ad-bar');
      bar.className = mx('site-ad-bar');
      wrapper.appendChild(bar);
      if (typeof MotoXShield !== 'undefined') bar.id = MotoXShield.idFor('site-ad-bar');
    }

    const content = settings.ads ? renderAdSlot(settings.ads, 'header-banner') : '';
    bar.innerHTML = content;
    bar.classList.toggle(mx('has-ad'), !!content);
  }

  function renderFooter(container, settings) {
    if (!container) return;
    const site = settings.site || {};
    const footerAd = settings.ads ? renderAdSlot(settings.ads, 'footer-banner') : '';
    setContainerHtml(container, `
      ${footerAd ? `<div class="${mx('site-footer-ad')}">${footerAd}</div>` : ''}
      <div class="${mx('container')} ${mx('site-footer-inner')}">
        <span class="${mx('footer-text')}">${shieldEnc(site.footer || '')}</span>
      </div>
    `);
  }

  function initLayout(activePage) {
    return loadSettings().then(settings => {
      renderHeader(ref('site-header'), settings, activePage);
      renderAdBar(settings);
      renderFooter(ref('site-footer'), settings);
      return settings;
    });
  }

  function renderSpecSection(key, section) {
    if (!section) return '';

    let body = '';
    if (section.fields && section.fields.length) {
      body = `<div class="${mx('spec-fields')}">${section.fields.map(f => `
        <div class="${mx('spec-field')}">
          <span class="${mx('field-label')}">${shieldEnc(f.label)}</span>
          <span class="${mx('field-value')}">${shieldEnc(f.value)}</span>
        </div>
      `).join('')}</div>`;
    }

    if (section.table && section.table.length) {
      const headers = Object.keys(section.table[0]);
      const labels = {
        component: 'Component', torque: 'Torque', notes: 'Notes',
        name: 'Name', thread: 'Thread', length: 'Length', head: 'Head', 
      };
      body += `<div class="${mx('spec-table-wrap')}" tabindex="0" aria-label="Scrollable table">
        <table class="${mx('spec-table')}">
        <thead><tr>${headers.map(h => `<th>${shieldEnc(labels[h] || h)}</th>`).join('')}</tr></thead>
        <tbody>${section.table.map(row => `
          <tr>${headers.map(h => `<td>${shieldEnc(row[h] || '')}</td>`).join('')}</tr>
        `).join('')}</tbody>
      </table></div>`;
    }

    return `
      <details class="${mx('spec-section')}" ${key === 'engine_oil' || key === 'torque_specs' ? 'open' : ''}>
        <summary>${shieldEnc(section.label || key)}</summary>
        <div class="${mx('spec-body')}">${body}</div>
      </details>
    `;
  }

  function shieldWrap(html) {
    return typeof MotoXShield !== 'undefined' ? MotoXShield.wrapHtml(html) : html;
  }

  function renderMotorcycleDetail(bike, settings) {
    const sections = bike.sections || {};
    const sectionHtml = Object.entries(sections).map(([key, sec]) => renderSpecSection(key, sec)).join('');

    const customHtml = (bike.custom_sections || []).map(cs => `
      <div class="${mx('custom-section')}">
        <h3>${shieldEnc(cs.title)}</h3>
        <div>${cs.content}</div>
      </div>
    `).join('');

    const adTop = settings ? renderAdSlot(settings.ads, 'content-top') : '';
    const adBottom = settings ? renderAdSlot(settings.ads, 'content-bottom') : '';
    const adInArticle = settings ? renderAdSlot(settings.ads, 'in-article') : '';
    const sidebarAd = settings ? renderAdSlot(settings.ads, 'sidebar') : '';

    return `
      <div class="${mx('page-layout')} ${mx('has-sidebar')}">
        <main>
          <div class="${mx('bike-header')}">
            <div class="${mx('breadcrumb')}"><a href="${BASE}index.html">Home</a> / <a href="${BASE}index.html#browse">Browse</a> / ${shieldEnc(bike.make)} ${shieldEnc(bike.model)}</div>
            <h1 class="${mx('bike-title')}">${shieldEnc(formatBikeTitle(bike))}</h1>
            <p class="${mx('bike-subtitle')}">${shieldEnc(bike.category || '')}${bike.category && bike.displacement ? ' · ' : ''}${shieldEnc(bike.displacement || '')}</p>
            ${bike.summary ? `<p>${shieldEnc(bike.summary)}</p>` : ''}
          </div>
          ${adTop ? `<div class="${mx('ad-slot')}">${adTop}</div>` : ''}
          ${sectionHtml}
          ${adInArticle ? `<div class="${mx('ad-slot')}">${adInArticle}</div>` : ''}
          ${customHtml}
          ${adBottom ? `<div class="${mx('ad-slot')}">${adBottom}</div>` : ''}
        </main>
        <aside class="${mx('sidebar-ad')}">${sidebarAd}</aside>
      </div>
    `;
  }

  function bikeVariantLabel(bike) {
    return [bike.year, bike.region].filter(Boolean).join(', ');
  }

  function formatBikeTitle(bike) {
    const name = `${bike.make || ''} ${bike.model || ''}`.trim();
    const variant = bikeVariantLabel(bike);
    return variant ? `${name} (${variant})` : name;
  }

  function getPopularMotorcycles(motorcycles, settings) {
    const popular = settings?.popular_models;
    if (!popular || popular.enabled === false) return [];
    const bikeMap = new Map(motorcycles.map(m => [m.id, m]));
    return (popular.ids || []).map(id => bikeMap.get(id)).filter(Boolean);
  }

  function getPopularPageSize(settings) {
    const size = parseInt(settings?.popular_models?.page_size, 10);
    return Number.isFinite(size) && size > 0 ? size : 8;
  }

  function getOilField(bike, key) {
    if (key === 'capacity' && bike.oil_capacity) return bike.oil_capacity;
    if (key === 'type' && bike.oil_type) return bike.oil_type;
    const fields = bike.sections?.engine_oil?.fields || [];
    const field = fields.find(item => item.key === key);
    return field?.value || '';
  }

  function renderBikeCard(bike) {
    const capacity = getOilField(bike, 'capacity');
    const oilType = getOilField(bike, 'type');
    const oilParts = [];
    if (capacity) oilParts.push(`<span class="${mx('oil-cap')}">${shieldEnc(capacity)}</span>`);
    if (oilType) oilParts.push(`<span class="${mx('oil-type')}">${shieldEnc(oilType)}</span>`);
    const oilHtml = oilParts.length
      ? `<div class="${mx('bike-oil')}">${oilParts.join(`<span class="${mx('oil-sep')}"> · </span>`)}</div>`
      : '';

    const parts = {
      make: `<span class="${mx('bike-make')}">${shieldEnc(bike.make)}</span>`,
      model: `<h3 class="${mx('bike-model')}">${shieldEnc(bike.model)}${bikeVariantLabel(bike) ? ` <span class="${mx('bike-variant')}">(${shieldEnc(bikeVariantLabel(bike))})</span>` : ''}</h3>`,
      meta: `<span class="${mx('bike-meta')}">${shieldEnc(bike.displacement || '')}${bike.category ? ` · ${shieldEnc(bike.category)}` : ''}</span>`,
      oil: oilHtml
    };
    const href = `${BASE}motorcycle.html?id=${encodeURIComponent(bike.id)}`;

    if (typeof MotoXShield !== 'undefined') {
      return MotoXShield.cardHtml(href, parts, bike.id);
    }

    return `<a href="${href}" class="${mx('bike-card')}">${parts.make}${parts.model}${parts.meta}${parts.oil}</a>`;
  }

  function renderSearchResult(url, title, meta, seed) {
    const parts = {
      title: shieldEnc(title),
      meta: shieldEnc(meta)
    };

    if (typeof MotoXShield !== 'undefined') {
      return MotoXShield.searchResultHtml(url, parts, seed || title);
    }

    return `<a href="${url}" class="${mx('search-result-item')}" role="option"><div class="${mx('result-title')}">${parts.title}</div><div class="${mx('result-meta')}">${parts.meta}</div></a>`;
  }
  function renderPageItem(url, title, meta, seed) {
    const parts = {
      title: shieldEnc(title),
      meta: shieldEnc(meta)
    };

    if (typeof MotoXShield !== 'undefined') {
      return MotoXShield.pageItemHtml(url, parts, seed || title);
    }

    return `<a href="${url}" class="${mx('page-item')}"><h3>${parts.title}</h3><p>${parts.meta}</p></a>`;
  }

  return {
    BASE,
    fetchJSON,
    loadSettings,
    loadMotorcycleIndex,
    loadMotorcycle,
    loadPopularSummaries,
    loadPagesIndex,
    loadPage,
    loadSearchIndex,
    loadMotorcycles,
    loadPages,
    loadAllSearchData,
    getMotorcycleById,
    getPageBySlug,
    getPopularMotorcycles,
    getPopularPageSize,
    bikeVariantLabel,
    formatBikeTitle,
    renderBikeCard,
    renderPageItem,
    renderSearchResult,
    ref,
    mxRef,
    renderAdSlot,
    escapeHtml,
    shieldEnc,
    finalizeContent,
    setContainerHtml,
    renderHeader,
    renderFooter,
    initLayout,
    renderSpecSection,
    renderMotorcycleDetail,
    mx,
    clearCache() { Object.keys(cache).forEach(k => delete cache[k]); }
  };
})();
