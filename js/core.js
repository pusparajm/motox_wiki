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

  const DEFAULT_SETTINGS = {
    site: {
      title: 'MotoX Wiki',
      footer: '© 2026 MotoX Wiki. Community-maintained motorcycle technical reference.'
    },
    navigation: [
      { label: 'Home', href: 'index.html' },
      { label: 'Browse', href: 'index.html#browse' },
      { label: 'Guides', href: 'guides/index.html' },
      { label: 'Pages', href: 'pages.html' }
    ],
    ads: { enabled: false, slots: [] },
    popular_models: { enabled: false, ids: [], page_size: 24 }
  };

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
    try {
      return await fetchJSON('settings.json');
    } catch {
      return structuredClone(DEFAULT_SETTINGS);
    }
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
    wireQuickSpecSync(root);
  }

  function initAdsense(root) {
    const scope = root || document;
    const ads = scope.querySelectorAll('ins.adsbygoogle:not([data-adsbygoogle-status])');
    if (!ads.length) return;
    window.adsbygoogle = window.adsbygoogle || [];
    ads.forEach(() => {
      try { window.adsbygoogle.push({}); } catch { /* AdSense may not be ready yet */ }
    });
  }

  function setContainerHtml(container, html) {
    if (!container) return;
    if (typeof MotoXShield !== 'undefined') {
      MotoXShield.setHtml(container, html);
    } else {
      container.innerHTML = html;
    }
    wireQuickSpecSync(container);
    initAdsense(container);
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
            const isActive = activePage && item.href === activePage;
            return `<a href="${BASE}${item.href.replace(/^\.\//, '')}" ${isActive ? `class="${mx('active')}"` : ''}>${shieldEnc(item.label)}</a>`;
          }).join('')}
        </nav>
        ${activePage === 'index.html' ? `
          <div class="${mx('header-intro')}">
            <span class="${mx('header-intro-title')}">Motorcycle Specifications Database</span>
            <span ${mxRef('header-meta')} class="${mx('header-intro-meta')}">413 models · 36 manufacturers · specs &amp; service data</span>
          </div>` : ''}
        <div class="${mx('header-search')}">
          <label data-mx-for="global-search" class="${mx('sr-only')}">Search motorcycles and pages</label>
          <input type="search" ${mxRef('global-search')} placeholder="Search specs, models…" autocomplete="off" role="combobox" aria-autocomplete="list" aria-expanded="false" data-mx-controls="search-dropdown" enterkeyhint="search">
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
        <span class="${mx('footer-text')}">${shieldEnc(site.footer || '')}${site.data_updated ? ` · Data updated ${shieldEnc(site.data_updated)}` : ''}</span>
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

  function renderSpecSection(key, section, options = {}) {
    if (!section) return '';

    let body = '';
    const fields = section.fields || [];
    const note = fields.find(f => f.key === 'note' && f.value);
    if (note) {
      body += `<p class="${mx('spec-note')}">${shieldEnc(note.value)}</p>`;
    }
    const rows = fields.filter(f => f.key !== 'note' && f.value);
    if (rows.length) {
      body += `<div class="${mx('spec-fields')}">${rows.map(f => `
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

    const openAttr = (options.defaultOpen ?? (key === 'general_specs' || key === 'overview' || key === 'service')) ? 'open' : '';
    const compactClass = options.compact ? ` ${mx('spec-section-compact')}` : '';
    const syncName = options.syncGroup ? ` name="${options.syncGroup}"` : '';

    return `
      <details class="${mx('spec-section')}${compactClass}"${syncName} ${openAttr}>
        <summary>${shieldEnc(section.label || key)}</summary>
        <div class="${mx('spec-body')}">${body}</div>
      </details>
    `;
  }

  function isQuickSpecKey(key) {
    return key === 'service' || key === 'engine_oil';
  }

  function quickSpecKeys(sections) {
    const keys = [];
    if (sections.service) keys.push('service');
    else if (sections.engine_oil) keys.push('engine_oil');
    return keys;
  }

  function renderQuickSpecRow(sections, quickKeys) {
    if (!quickKeys.length) return '';

    if (quickKeys.length === 1) {
      return renderSpecSection(quickKeys[0], sections[quickKeys[0]], { defaultOpen: true });
    }

    const syncGroup = typeof MotoXShield !== 'undefined'
      ? MotoXShield.quickSpecGroup()
      : 'mx-quick-spec';

    const cards = quickKeys.map(key => renderSpecSection(key, sections[key], {
      compact: true,
      defaultOpen: true,
      syncGroup
    }));

    return `<div class="${mx('spec-quick-row')}" data-mx-quick-spec-row>${cards.join('')}</div>`;
  }

  function wireQuickSpecSync(root) {
    if (!root) return;

    root.querySelectorAll('[data-mx-quick-spec-row]').forEach(row => {
      const details = [...row.querySelectorAll('details')];
      if (details.length < 2) return;

      const syncOpen = (source, open) => {
        details.forEach(other => {
          if (other !== source) other.open = open;
        });
      };

      details.forEach(el => {
        if (el.dataset.mxSyncWired) return;
        el.dataset.mxSyncWired = '1';

        el.addEventListener('toggle', () => {
          if (row.dataset.mxSyncLock) return;
          row.dataset.mxSyncLock = '1';
          syncOpen(el, el.open);
          delete row.dataset.mxSyncLock;
        });
      });
    });
  }

  function renderAllSpecSections(sections) {
    return `<div class="${mx('spec-section-grid')}">${Object.entries(sections)
      .map(([key, section]) => renderSpecSection(key, section))
      .join('')}</div>`;
  }

  function shieldWrap(html) {
    return typeof MotoXShield !== 'undefined' ? MotoXShield.wrapHtml(html) : html;
  }

  function aliasLabel(value) {
    return String(value || '')
      .split(' ')
      .filter(Boolean)
      .map(word => {
        if (/\d/.test(word)) return word.toUpperCase();
        return word.length <= 3 ? word.toUpperCase() : word.charAt(0).toUpperCase() + word.slice(1);
      })
      .join(' ');
  }

  const GENERIC_ALIASES = new Set([
    'harley', 'hd', 'enfield', 'royal enfield', 'guzzi', 'cf moto', 'qj motor',
    'qj', 'bmw motorrad', 'kawi', 'triumph motorcycles', 'indian motorcycle'
  ]);

  const ALIAS_NICKNAMES = new Set([
    'fireblade', 'busa', 'hayabusa', 'gixxer', 'goldwing', 'vstrom', 'tenere',
    'panigale', 'monster', 'multistrada', 'scrambler', 'bonneville', 'trident',
    'tiger', 'rocket', 'sportster', 'scout', 'chief', 'challenger', 'himalayan',
    'classic', 'hunter', 'meteor', 'interceptor', 'continental', 'cp2', 'cp3', 'gs', 'adv'
  ]);

  function aliasKey(value) {
    return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
  }

  function displayAliases(bike) {
    const modelKey = aliasKey(bike.model);
    return (bike.aliases || [])
      .filter(alias => !GENERIC_ALIASES.has(String(alias).toLowerCase()))
      .filter(alias => aliasKey(alias) !== modelKey)
      .map(alias => {
        const key = aliasKey(alias);
        let score = 0;
        if (String(alias).includes(' ')) score += 3;
        if (ALIAS_NICKNAMES.has(String(alias).toLowerCase())) score += 2;
        if (String(alias).length > 5) score += 1;
        if (key === modelKey) score -= 2;
        return { alias, score };
      })
      .sort((a, b) => b.score - a.score)
      .slice(0, 5)
      .map(item => aliasLabel(item.alias));
  }

  function getBikeFaq(bike) {
    const name = `${bike.make || ''} ${bike.model || ''}`.trim();
    const power = getGeneralField(bike, 'power');
    const torque = getGeneralField(bike, 'torque');
    const weight = getGeneralField(bike, 'weight');
    const seat = getGeneralField(bike, 'seat_height');
    const fuel = getGeneralField(bike, 'fuel_capacity');
    const top = getGeneralField(bike, 'top_speed');
    const oilCapacity = getServiceField(bike, 'oil_capacity');
    const oilGrade = getServiceField(bike, 'oil_grade');
    const faq = [];

    if (power) faq.push({ q: `How much power does the ${name} make?`, a: `The ${name} is rated at ${power}.` });
    if (torque) faq.push({ q: `What is the torque of the ${name}?`, a: `Manufacturer-claimed peak torque is ${torque}.` });
    if (seat) faq.push({ q: `What is the seat height of the ${name}?`, a: `The seat height is listed as ${seat}. Seat width and suspension sag also affect reach.` });
    if (weight) faq.push({ q: `How much does the ${name} weigh?`, a: `The kerb weight is listed as ${weight}.` });
    if (oilCapacity) faq.push({ q: `What engine oil does the ${name} take?`, a: `Engine oil capacity is ${oilCapacity}${oilGrade ? ` and the recommended grade is ${oilGrade}` : ''}. Confirm the exact fill procedure in the owner's or workshop manual.` });
    else if (oilGrade) faq.push({ q: `What engine oil grade does the ${name} use?`, a: `The recommended grade is ${oilGrade}. Confirm the exact fill procedure in the owner's or workshop manual.` });
    if (top) faq.push({ q: `What is the top speed of the ${name}?`, a: `The listed top speed is ${top}.` });
    if (fuel) faq.push({ q: `What is the fuel capacity of the ${name}?`, a: `Fuel capacity is listed as ${fuel}.` });

    return faq.slice(0, 6);
  }

  function renderBikeFaq(bike) {
    const faq = getBikeFaq(bike);
    if (!faq.length) return '';
    return `<section class="${mx('faq-section')}">
      <h2 class="${mx('section-heading')}">Frequently Asked Questions</h2>
      ${faq.map(item => `<div class="${mx('faq-item')}">
        <h3 class="${mx('faq-question')}">${shieldEnc(item.q)}</h3>
        <p class="${mx('faq-answer')}">${shieldEnc(item.a)}</p>
      </div>`).join('')}
    </section>`;
  }

  function renderRelatedGuides(bike) {
    const category = (bike.category || '').toLowerCase();
    const links = [
      ['guides/parts-fitment-codes.html', 'Parts and fitment codes'],
      ['guides/oil-capacity-chart.html', 'Motorcycle oil capacity chart'],
      ['guides/seat-height-chart.html', 'Motorcycle seat height chart'],
      ['guides/a2-motorcycles.html', 'A2 motorcycles'],
      ['guides/best-beginner-motorcycles.html', 'Best beginner motorcycles'],
      ['guides/torque-specs.html', 'Motorcycle torque specs']
    ];
    if (category === 'scooter') links.unshift(['guides/best-scooters.html', 'Best scooters']);
    else if (category === 'adventure' || category === 'dual sport') links.unshift(['guides/best-adventure-motorcycles.html', 'Best adventure motorcycles']);
    else if (category === 'cruiser') links.unshift(['guides/best-cruiser-motorcycles.html', 'Best cruiser motorcycles']);
    else if (category === 'commuter') links.unshift(['guides/best-commuter-motorcycles.html', 'Best commuter motorcycles']);
    else if (category === 'retro' || category === 'scrambler') links.unshift(['guides/best-retro-motorcycles.html', 'Best retro motorcycles']);
    if (String(bike.displacement || '').trim() === '—') links.unshift(['guides/best-electric-motorcycles.html', 'Best electric motorcycles']);

    const seen = new Set();
    const items = links.filter(([href, label]) => {
      if (seen.has(href)) return false;
      seen.add(href);
      return true;
    }).slice(0, 7);

    return `<section class="${mx('related-section')}">
      <h2 class="${mx('related-title')}">Related Guides</h2>
      <p class="${mx('home-guide-links')}">${items.map(([href, label]) => `<a href="${BASE}${href}">${shieldEnc(label)}</a>`).join('')}</p>
    </section>`;
  }

  function renderMotorcycleDetail(bike, settings) {
    const sections = bike.sections || {};
    const sectionHtml = renderAllSpecSections(sections);

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
            ${(bike.aliases || []).length ? `<p class="${mx('bike-alias')}"><strong>Also known as:</strong> ${shieldEnc(displayAliases(bike).join(', '))}</p>` : ''}
            ${renderHeroStats(bike)}
          </div>
          ${adTop ? `<div class="${mx('ad-slot')}">${adTop}</div>` : ''}
          <h2 class="${mx('section-heading')}">Specifications</h2>
          ${sectionHtml}
          ${adInArticle ? `<div class="${mx('ad-slot')}">${adInArticle}</div>` : ''}
          ${customHtml}
          ${renderBikeFaq(bike)}
          ${renderRelatedGuides(bike)}
          ${adBottom ? `<div class="${mx('ad-slot')}">${adBottom}</div>` : ''}
          ${(bike.sections?.service || bike.sections?.engine_oil) ? '' : `<p class="${mx('data-note')} ${mx('service-pending')}">Service data for this model is still being compiled. Use the owner's or workshop manual for oil capacity, fluid grades and torque values.</p>`}
          <p class="${mx('data-note')}">Specifications are manufacturer-claimed and can vary by model year and market. Always confirm service limits and torque values against the owner's or workshop manual before working on your motorcycle.</p>
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

  function fieldValue(section, key) {
    const fields = section?.fields || [];
    return fields.find(item => item.key === key)?.value || '';
  }

  function getGeneralField(bike, key) {
    if (!bike) return '';
    if (bike[key]) return bike[key];
    return fieldValue(bike.sections?.general_specs, key);
  }

  function getServiceField(bike, key) {
    if (!bike) return '';
    return fieldValue(bike.sections?.service, key) || fieldValue(bike.sections?.engine_oil, key);
  }

  function getOilField(bike, key) {
    const serviceKey = key === 'capacity' ? 'oil_capacity' : key === 'type' ? 'oil_grade' : key;
    const serviceValue = getServiceField(bike, serviceKey);
    if (serviceValue) return serviceValue;
    if (key === 'capacity') return bike.oil_capacity || '';
    if (key === 'type') return bike.oil_type || '';
    return fieldValue(bike.sections?.engine_oil, key);
  }

  function specHeadline(value) {
    if (!value) return '';
    return String(value).split('@')[0].replace(/\s+/g, ' ').trim();
  }

  function specCompact(value) {
    if (!value) return '';
    return String(value)
      .split('@')[0]
      .replace(/\([^)]*\)/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function numericSpec(value) {
    if (!value) return 0;
    const match = String(value).replace(/,/g, '').match(/-?\d+(?:\.\d+)?/);
    return match ? parseFloat(match[0]) : 0;
  }

  function getSpecNumber(bike, key) {
    return numericSpec(getGeneralField(bike, key));
  }

  function renderBikeCard(bike) {
    const power = getGeneralField(bike, 'power');
    const torque = getGeneralField(bike, 'torque');
    const weight = getGeneralField(bike, 'weight');
    const specParts = [];
    if (power) specParts.push(`<span class="${mx('bike-spec')}"><b>${shieldEnc(specCompact(power))}</b></span>`);
    if (torque) specParts.push(`<span class="${mx('bike-spec')}"><b>${shieldEnc(specCompact(torque))}</b></span>`);
    if (weight) specParts.push(`<span class="${mx('bike-spec')}"><b>${shieldEnc(specCompact(weight))}</b></span>`);
    const specsHtml = specParts.length
      ? `<div class="${mx('bike-specs')}">${specParts.join(`<span class="${mx('bike-spec-sep')}">·</span>`)}</div>`
      : '';

    const oilHtml = '';

    const parts = {
      make: `<span class="${mx('bike-make')}">${shieldEnc(bike.make)}</span>`,
      model: `<h3 class="${mx('bike-model')}">${shieldEnc(bike.model)}</h3>`,
      meta: `<span class="${mx('bike-meta')}">${[bike.year, bike.displacement].filter(Boolean).map(v => shieldEnc(v)).join(' · ')}</span>`,
      specs: specsHtml,
      oil: oilHtml
    };
    const href = `${BASE}motorcycle/${encodeURIComponent(bike.id)}.html`;

    if (typeof MotoXShield !== 'undefined') {
      return MotoXShield.cardHtml(href, parts, bike.id);
    }

    return `<a href="${href}" class="${mx('bike-card')}">${parts.make}${parts.model}${parts.meta}${parts.specs}${parts.oil}</a>`;
  }

  function renderHeroStats(bike) {
    const items = [
      ['Power', getGeneralField(bike, 'power')],
      ['Torque', getGeneralField(bike, 'torque')],
      ['Kerb Weight', getGeneralField(bike, 'weight')],
      ['Seat Height', getGeneralField(bike, 'seat_height')]
    ].filter(([, value]) => value);
    if (!items.length) return '';
    return `<div class="${mx('hero-stats')}">${items.map(([label, value]) => `
      <div class="${mx('hero-stat')}">
        <span class="${mx('hero-label')}">${shieldEnc(label)}</span>
        <span class="${mx('hero-value')}">${shieldEnc(value)}</span>
      </div>`).join('')}</div>`;
  }

  function renderRelatedModels(bike, motorcycles, limit = 6) {
    if (!bike || !motorcycles?.length) return '';
    const group = bike.model_group;
    const same = motorcycles.filter(m => m.id !== bike.id && ((group && m.model_group === group) || (m.make === bike.make && m.model === bike.model)));
    const pool = same.length ? same : motorcycles.filter(m => m.id !== bike.id && m.make === bike.make && m.category === bike.category);
    const related = pool.slice(0, limit);
    if (!related.length) return '';
    return `<section class="${mx('related-section')}">
      <h2 class="${mx('related-title')}">Related Models</h2>
      <div class="${mx('bike-grid')} ${mx('related-grid')}">${related.map(renderBikeCard).join('')}</div>
    </section>`;
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
    getOilField,
    getGeneralField,
    getBikeFaq,
    getServiceField,
    getSpecNumber,
    specHeadline,
    specCompact,
    renderBikeCard,
    renderHeroStats,
    renderRelatedModels,
    renderPageItem,
    renderSearchResult,
    ref,
    mxRef,
    renderAdSlot,
    escapeHtml,
    shieldEnc,
    finalizeContent,
    setContainerHtml,
    initAdsense,
    renderHeader,
    renderFooter,
    initLayout,
    renderSpecSection,
    renderMotorcycleDetail,
    mx,
    clearCache() { Object.keys(cache).forEach(k => delete cache[k]); }
  };
})();
