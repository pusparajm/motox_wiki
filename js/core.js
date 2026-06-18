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

  function renderHeader(container, settings, activePage) {
    if (!container) return;
    const site = settings.site || {};
    const nav = settings.navigation || [];

    container.innerHTML = `
      <div class="${mx('container')}">
        <div class="${mx('header-row')}">
          <a href="${BASE}index.html" class="${mx('brand')}">
            <span class="${mx('brand-icon')}">⚙</span>
            <span>${escapeHtml(site.title || 'MotoX Wiki')}</span>
          </a>
          <button type="button" class="${mx('nav-toggle')}" ${mxHook('nav-toggle')} aria-label="Toggle navigation" aria-expanded="false" aria-controls="site-nav">
            <span class="${mx('nav-toggle-bar')}"></span>
            <span class="${mx('nav-toggle-bar')}"></span>
            <span class="${mx('nav-toggle-bar')}"></span>
          </button>
        </div>
        <nav id="site-nav" class="${mx('site-nav')}" aria-label="Main navigation">
          ${nav.map(item => {
            const isActive = activePage && (item.href === activePage || item.href.includes(activePage));
            return `<a href="${BASE}${item.href.replace(/^\.\//, '')}" ${isActive ? `class="${mx('active')}"` : ''}>${escapeHtml(item.label)}</a>`;
          }).join('')}
        </nav>
        <div class="${mx('header-search')}">
          <label for="global-search" class="${mx('sr-only')}">Search motorcycles and pages</label>
          <input type="search" id="global-search" placeholder="Search specs, models…" autocomplete="off" aria-expanded="false" aria-controls="search-dropdown" enterkeyhint="search">
          <div id="search-dropdown" class="${mx('search-dropdown')}" role="listbox"></div>
        </div>
      </div>
    `;

    initMobileNav(container);
  }

  function initMobileNav(header) {
    const toggle = header.querySelector('[data-mx-hook="nav-toggle"]');
    const nav = header.querySelector('#site-nav');
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
    const header = document.getElementById('site-header');
    if (!header) return;

    let wrapper = header.parentElement;
    if (!wrapper.classList.contains(mx('site-top'))) {
      wrapper = document.createElement('div');
      wrapper.className = mx('site-top');
      header.parentNode.insertBefore(wrapper, header);
      wrapper.appendChild(header);
    }

    let bar = document.getElementById('site-ad-bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'site-ad-bar';
      bar.className = mx('site-ad-bar');
      wrapper.appendChild(bar);
    }

    const content = settings.ads ? renderAdSlot(settings.ads, 'header-banner') : '';
    bar.innerHTML = content;
    bar.classList.toggle(mx('has-ad'), !!content);
  }

  function renderFooter(container, settings) {
    if (!container) return;
    const site = settings.site || {};
    const footerAd = settings.ads ? renderAdSlot(settings.ads, 'footer-banner') : '';
    container.innerHTML = `
      ${footerAd ? `<div class="${mx('site-footer-ad')}">${footerAd}</div>` : ''}
      <div class="${mx('container')} ${mx('site-footer-inner')}">
        <span class="${mx('footer-text')}">${escapeHtml(site.footer || '')}</span>
      </div>
    `;
  }

  function initLayout(activePage) {
    return loadSettings().then(settings => {
      renderHeader(document.getElementById('site-header'), settings, activePage);
      renderAdBar(settings);
      renderFooter(document.getElementById('site-footer'), settings);
      return settings;
    });
  }

  function renderSpecSection(key, section) {
    if (!section) return '';

    let body = '';
    if (section.fields && section.fields.length) {
      body = `<div class="${mx('spec-fields')}">${section.fields.map(f => `
        <div class="${mx('spec-field')}">
          <span class="${mx('field-label')}">${escapeHtml(f.label)}</span>
          <span class="${mx('field-value')}">${escapeHtml(f.value)}</span>
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
        <thead><tr>${headers.map(h => `<th>${escapeHtml(labels[h] || h)}</th>`).join('')}</tr></thead>
        <tbody>${section.table.map(row => `
          <tr>${headers.map(h => `<td>${escapeHtml(row[h] || '')}</td>`).join('')}</tr>
        `).join('')}</tbody>
      </table></div>`;
    }

    return shieldWrap(`
      <details class="${mx('spec-section')}" ${key === 'engine_oil' || key === 'torque_specs' ? 'open' : ''}>
        <summary>${escapeHtml(section.label || key)}</summary>
        <div class="${mx('spec-body')}">${body}</div>
      </details>
    `);
  }

  function shieldWrap(html) {
    return typeof MotoXShield !== 'undefined' ? MotoXShield.wrapHtml(html) : html;
  }

  function renderMotorcycleDetail(bike, settings) {
    const sections = bike.sections || {};
    const sectionHtml = Object.entries(sections).map(([key, sec]) => renderSpecSection(key, sec)).join('');

    const customHtml = (bike.custom_sections || []).map(cs => shieldWrap(`
      <div class="${mx('custom-section')}">
        <h3>${escapeHtml(cs.title)}</h3>
        <div>${cs.content}</div>
      </div>
    `)).join('');

    const adTop = settings ? renderAdSlot(settings.ads, 'content-top') : '';
    const adBottom = settings ? renderAdSlot(settings.ads, 'content-bottom') : '';
    const adInArticle = settings ? renderAdSlot(settings.ads, 'in-article') : '';
    const sidebarAd = settings ? renderAdSlot(settings.ads, 'sidebar') : '';

    return shieldWrap(`
      <div class="${mx('page-layout')} ${mx('has-sidebar')}">
        <main>
          <div class="${mx('bike-header')}">
            <div class="${mx('breadcrumb')}"><a href="${BASE}index.html">Home</a> / <a href="${BASE}index.html#browse">Browse</a> / ${escapeHtml(bike.make)} ${escapeHtml(bike.model)}</div>
            <h1 class="${mx('bike-title')}">${escapeHtml(formatBikeTitle(bike))}</h1>
            <p class="${mx('bike-subtitle')}">${escapeHtml(bike.category || '')}${bike.category && bike.displacement ? ' · ' : ''}${escapeHtml(bike.displacement || '')}</p>
            ${bike.summary ? `<p>${escapeHtml(bike.summary)}</p>` : ''}
          </div>
          ${adTop ? `<div class="${mx('ad-slot')}">${adTop}</div>` : ''}
          ${sectionHtml}
          ${adInArticle ? `<div class="${mx('ad-slot')}">${adInArticle}</div>` : ''}
          ${customHtml}
          ${adBottom ? `<div class="${mx('ad-slot')}">${adBottom}</div>` : ''}
        </main>
        <aside class="${mx('sidebar-ad')}">${sidebarAd}</aside>
      </div>
    `);
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
    if (capacity) oilParts.push(`<span class="${mx('oil-cap')}">${escapeHtml(capacity)}</span>`);
    if (oilType) oilParts.push(`<span class="${mx('oil-type')}">${escapeHtml(oilType)}</span>`);
    const oilHtml = oilParts.length
      ? `<div class="${mx('bike-oil')}">${oilParts.join(`<span class="${mx('oil-sep')}"> · </span>`)}</div>`
      : '';

    return `
      <a href="${BASE}motorcycle.html?id=${encodeURIComponent(bike.id)}" class="${mx('bike-card')}">
        <span class="${mx('bike-make')}">${escapeHtml(bike.make)}</span>
        <h3 class="${mx('bike-model')}">${escapeHtml(bike.model)}${bikeVariantLabel(bike) ? ` <span class="${mx('bike-variant')}">(${escapeHtml(bikeVariantLabel(bike))})</span>` : ''}</h3>
        <span class="${mx('bike-meta')}">${escapeHtml(bike.displacement || '')}${bike.category ? ` · ${escapeHtml(bike.category)}` : ''}</span>
        ${oilHtml}
      </a>
    `;
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
    renderAdSlot,
    escapeHtml,
    renderHeader,
    renderFooter,
    initLayout,
    renderSpecSection,
    renderMotorcycleDetail,
    mx,
    clearCache() { Object.keys(cache).forEach(k => delete cache[k]); }
  };
})();
