/**
 * MotoX Wiki — shared utilities, data loading, ads, and navigation
 */
const MotoX = (() => {
  const BASE = getBasePath();

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
    const res = await fetch(url, { cache: 'no-store' });
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
      <div class="container">
        <div class="header-row">
          <a href="${BASE}index.html" class="brand">
            <span class="brand-icon">⚙</span>
            <span>${escapeHtml(site.title || 'MotoX Wiki')}</span>
          </a>
          <button type="button" class="nav-toggle" aria-label="Toggle navigation" aria-expanded="false" aria-controls="site-nav">
            <span class="nav-toggle-bar"></span>
            <span class="nav-toggle-bar"></span>
            <span class="nav-toggle-bar"></span>
          </button>
        </div>
        <nav id="site-nav" class="site-nav" aria-label="Main navigation">
          ${nav.map(item => {
            const isActive = activePage && (item.href === activePage || item.href.includes(activePage));
            return `<a href="${BASE}${item.href.replace(/^\.\//, '')}" ${isActive ? 'class="active"' : ''}>${escapeHtml(item.label)}</a>`;
          }).join('')}
        </nav>
        <div class="header-search">
          <label for="global-search" class="sr-only">Search motorcycles and pages</label>
          <input type="search" id="global-search" placeholder="Search specs, models…" autocomplete="off" aria-expanded="false" aria-controls="search-dropdown" enterkeyhint="search">
          <div id="search-dropdown" class="search-dropdown" role="listbox"></div>
        </div>
      </div>
    `;

    initMobileNav(container);
  }

  function initMobileNav(header) {
    const toggle = header.querySelector('.nav-toggle');
    const nav = header.querySelector('#site-nav');
    if (!toggle || !nav) return;

    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });

    nav.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });

    document.addEventListener('click', e => {
      if (!header.contains(e.target)) {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  function renderAdBar(settings) {
    const header = document.getElementById('site-header');
    if (!header) return;

    let wrapper = header.parentElement;
    if (!wrapper.classList.contains('site-top')) {
      wrapper = document.createElement('div');
      wrapper.className = 'site-top';
      header.parentNode.insertBefore(wrapper, header);
      wrapper.appendChild(header);
    }

    let bar = document.getElementById('site-ad-bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'site-ad-bar';
      bar.className = 'site-ad-bar';
      wrapper.appendChild(bar);
    }

    const content = settings.ads ? renderAdSlot(settings.ads, 'header-banner') : '';
    bar.innerHTML = content;
    bar.classList.toggle('has-ad', !!content);
  }

  function renderFooter(container, settings) {
    if (!container) return;
    const site = settings.site || {};
    const footerAd = settings.ads ? renderAdSlot(settings.ads, 'footer-banner') : '';
    container.innerHTML = `
      ${footerAd ? `<div class="site-footer-ad">${footerAd}</div>` : ''}
      <div class="container site-footer-inner">
        <span class="footer-text">${escapeHtml(site.footer || '')}</span>
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
      body = `<div class="spec-fields">${section.fields.map(f => `
        <div class="spec-field">
          <span class="field-label">${escapeHtml(f.label)}</span>
          <span class="field-value">${escapeHtml(f.value)}</span>
        </div>
      `).join('')}</div>`;
    }

    if (section.table && section.table.length) {
      const headers = Object.keys(section.table[0]);
      const labels = {
        component: 'Component', torque: 'Torque', notes: 'Notes',
        name: 'Name', thread: 'Thread', length: 'Length', head: 'Head', 
      };
      body += `<div class="spec-table-wrap" tabindex="0" aria-label="Scrollable table">
        <table class="spec-table">
        <thead><tr>${headers.map(h => `<th>${escapeHtml(labels[h] || h)}</th>`).join('')}</tr></thead>
        <tbody>${section.table.map(row => `
          <tr>${headers.map(h => `<td>${escapeHtml(row[h] || '')}</td>`).join('')}</tr>
        `).join('')}</tbody>
      </table></div>`;
    }

    return `
      <details class="spec-section" ${key === 'engine_oil' || key === 'torque_specs' ? 'open' : ''}>
        <summary>${escapeHtml(section.label || key)}</summary>
        <div class="spec-body">${body}</div>
      </details>
    `;
  }

  function renderMotorcycleDetail(bike, settings) {
    const sections = bike.sections || {};
    const sectionHtml = Object.entries(sections).map(([key, sec]) => renderSpecSection(key, sec)).join('');

    const customHtml = (bike.custom_sections || []).map(cs => `
      <div class="custom-section">
        <h3>${escapeHtml(cs.title)}</h3>
        <div>${cs.content}</div>
      </div>
    `).join('');

    const adTop = settings ? renderAdSlot(settings.ads, 'content-top') : '';
    const adBottom = settings ? renderAdSlot(settings.ads, 'content-bottom') : '';
    const adInArticle = settings ? renderAdSlot(settings.ads, 'in-article') : '';
    const sidebarAd = settings ? renderAdSlot(settings.ads, 'sidebar') : '';

    return `
      <div class="page-layout has-sidebar">
        <main>
          <div class="bike-header">
            <div class="breadcrumb"><a href="${BASE}index.html">Home</a> / <a href="${BASE}index.html#browse">Browse</a> / ${escapeHtml(bike.make)} ${escapeHtml(bike.model)}</div>
            <h1 class="bike-title">${escapeHtml(formatBikeTitle(bike))}</h1>
            <p class="bike-subtitle">${escapeHtml(bike.category || '')}${bike.category && bike.displacement ? ' · ' : ''}${escapeHtml(bike.displacement || '')}</p>
            ${bike.summary ? `<p>${escapeHtml(bike.summary)}</p>` : ''}
          </div>
          ${adTop ? `<div class="ad-slot">${adTop}</div>` : ''}
          ${sectionHtml}
          ${adInArticle ? `<div class="ad-slot">${adInArticle}</div>` : ''}
          ${customHtml}
          ${adBottom ? `<div class="ad-slot">${adBottom}</div>` : ''}
        </main>
        <aside class="sidebar-ad">${sidebarAd}</aside>
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
    if (capacity) oilParts.push(`<span class="oil-cap">${escapeHtml(capacity)}</span>`);
    if (oilType) oilParts.push(`<span class="oil-type">${escapeHtml(oilType)}</span>`);
    const oilHtml = oilParts.length
      ? `<div class="bike-oil">${oilParts.join('<span class="oil-sep"> · </span>')}</div>`
      : '';

    return `
      <a href="${BASE}motorcycle.html?id=${encodeURIComponent(bike.id)}" class="bike-card">
        <span class="bike-make">${escapeHtml(bike.make)}</span>
        <h3 class="bike-model">${escapeHtml(bike.model)}${bikeVariantLabel(bike) ? ` <span class="bike-variant">(${escapeHtml(bikeVariantLabel(bike))})</span>` : ''}</h3>
        <span class="bike-meta">${escapeHtml(bike.displacement || '')}${bike.category ? ` · ${escapeHtml(bike.category)}` : ''}</span>
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
    clearCache() { Object.keys(cache).forEach(k => delete cache[k]); }
  };
})();
