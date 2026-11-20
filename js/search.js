/**
 * MotoX Wiki — client-side search with token matching, aliases and fuzzy fallback
 */
const MotoXSearch = (() => {
  function mx(name) {
    return typeof MotoXShield !== 'undefined' ? MotoXShield.c(name) : name;
  }

  const SUGGESTIONS = [
    'CBR 600',
    'Fireblade',
    'Hayabusa',
    'MT-07',
    'Ninja 400',
    'Royal Enfield Classic 350',
    'Himalayan 450',
    'Panigale V4',
    'Gold Wing',
    'ZX-10R'
  ];

  let index = [];
  let indexPromise = null;
  let debounceTimer = null;
  let searchSettings = { minChars: 2, maxResults: 20 };
  let activeResults = [];
  let activeIndex = -1;
  const distanceCache = new Map();

  function normalize(value) {
    return String(value || '')
      .toLowerCase()
      .replace(/&/g, ' and ')
      .replace(/([a-z])([0-9])/g, '$1 $2')
      .replace(/([0-9])([a-z])/g, '$1 $2')
      .replace(/[^a-z0-9]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function tokens(value) {
    return normalize(value).split(' ').filter(Boolean);
  }

  function editDistance(a, b) {
    if (a === b) return 0;
    if (Math.abs(a.length - b.length) > 2) return 3;
    const key = `${a}|${b}`;
    if (distanceCache.has(key)) return distanceCache.get(key);
    const rows = [];
    for (let i = 0; i <= a.length; i++) rows.push([i]);
    for (let j = 1; j <= b.length; j++) rows[0][j] = j;
    for (let i = 1; i <= a.length; i++) {
      for (let j = 1; j <= b.length; j++) {
        rows[i][j] = Math.min(
          rows[i - 1][j] + 1,
          rows[i][j - 1] + 1,
          rows[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)
        );
      }
    }
    const result = rows[a.length][b.length];
    if (distanceCache.size > 4000) distanceCache.clear();
    distanceCache.set(key, result);
    return result;
  }

  function matchTokens(haystack, queryTokens, allowFuzzy = false) {
    if (!queryTokens.length) return 0;
    let matched = 0;

    for (const qt of queryTokens) {
      if (haystack.includes(qt)) {
        matched += 1;
        continue;
      }
      if (qt.length >= 2 && haystack.some(token => token.startsWith(qt))) {
        matched += 0.85;
        continue;
      }
      if (!allowFuzzy || qt.length < 4) continue;

      let best = 0;
      for (const token of haystack) {
        if (Math.abs(token.length - qt.length) > 2) continue;
        const distance = editDistance(token, qt);
        const allowed = qt.length >= 7 ? 2 : 1;
        if (distance <= allowed) {
          best = Math.max(best, distance === 1 ? 0.75 : 0.6);
        }
      }
      matched += best;
    }

    return matched / queryTokens.length;
  }

  function prepareItem(item) {
    const title = normalize(item.title);
    const model = normalize(item.model);
    const aliases = normalize([...(item.aliases || []), ...(item.tags || [])].join(' '));
    const text = normalize(item.searchText || '');
    return {
      ...item,
      _title: title,
      _titleTokens: title.split(' ').filter(Boolean),
      _model: model,
      _modelTokens: model.split(' ').filter(Boolean),
      _make: normalize(item.make),
      _aliases: aliases,
      _aliasTokens: aliases.split(' ').filter(Boolean),
      _text: text,
      _textTokens: text.split(' ').filter(Boolean),
      _group: normalize(item.model_group)
    };
  }

  function buildIndex(motorcycles, pages) {
    const items = [];

    motorcycles.forEach(bike => {
      const title = MotoX.formatBikeTitle(bike);
      const meta = [bike.region, bike.category, bike.displacement].filter(Boolean).join(' · ') || 'Motorcycle';
      items.push({
        type: 'motorcycle',
        id: bike.id,
        title,
        make: bike.make,
        model: bike.model,
        model_group: bike.model_group || '',
        aliases: bike.tags || [],
        meta,
        power: MotoX.getGeneralField(bike, 'power'),
        weight: MotoX.getGeneralField(bike, 'weight'),
        url: `motorcycle.html?id=${encodeURIComponent(bike.id)}`,
        searchText: flattenBike(bike)
      });
    });

    pages.forEach(page => {
      items.push({
        type: 'page',
        id: page.id,
        title: page.title,
        make: '',
        model: '',
        model_group: '',
        aliases: [],
        meta: page.summary || 'Wiki page',
        url: `pages.html?slug=${encodeURIComponent(page.slug || page.id)}`,
        searchText: `${page.title} ${page.summary || ''} ${stripHtml(page.content || '')}`
      });
    });

    return items;
  }

  function flattenBike(bike) {
    const parts = [
      bike.make, bike.model, bike.year, bike.region, bike.category, bike.displacement,
      bike.summary, bike.power, bike.torque, bike.weight, bike.engine, ...(bike.tags || [])
    ];

    const sections = bike.sections || {};
    Object.values(sections).forEach(sec => {
      if (sec.label) parts.push(sec.label);
      (sec.fields || []).forEach(f => parts.push(f.label, f.value));
      (sec.table || []).forEach(row => parts.push(...Object.values(row)));
    });

    (bike.custom_sections || []).forEach(cs => {
      parts.push(cs.title, stripHtml(cs.content || ''));
    });

    return parts.filter(Boolean).join(' ').toLowerCase();
  }

  function stripHtml(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent || '';
  }

  function scoreItem(item, query) {
    const q = normalize(query);
    if (!q) return 0;
    const queryTokens = q.split(' ').filter(Boolean);
    let score = 0;

    const title = item._title;
    const model = item._model;
    const aliases = item._aliases;
    const text = item._text;

    if (title === q) score += 300;
    else if (title.startsWith(q)) score += 160;
    else if (title.includes(q)) score += 110;

    if (model === q) score += 260;
    else if (model.startsWith(q)) score += 140;
    else if (model.includes(q)) score += 90;

    if (aliases.includes(q)) score += 180;
    if (text.includes(q)) score += 40;
    if (item._make === q) score += 60;
    if (item._group && item._group.includes(q)) score += 30;

    const titleCoverage = matchTokens(item._titleTokens, queryTokens, false);
    const modelCoverage = matchTokens(item._modelTokens, queryTokens, false);
    const aliasCoverage = matchTokens(item._aliasTokens, queryTokens, false);
    const textCoverage = matchTokens(item._textTokens, queryTokens, false);

    score += titleCoverage * 100;
    score += modelCoverage * 90;
    score += aliasCoverage * 80;
    score += textCoverage * 35;

    if (score < 90) {
      const fuzzyAlias = matchTokens(item._aliasTokens, queryTokens, true);
      const fuzzyTitle = matchTokens(item._titleTokens, queryTokens, true);
      const fuzzyModel = matchTokens(item._modelTokens, queryTokens, true);
      score += fuzzyAlias * 65 + fuzzyTitle * 45 + fuzzyModel * 35;
    }

    if (item.type === 'motorcycle') score += 5;
    return score;
  }

  function search(query, maxResults = searchSettings.maxResults) {
    const normalized = normalize(query);
    if (!normalized || normalized.length < searchSettings.minChars) return [];

    const scored = [];
    for (const item of index) {
      const score = scoreItem(item, query);
      if (score > 0) scored.push({ ...item, score });
    }

    scored.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      if (a.type !== b.type) return a.type === 'motorcycle' ? -1 : 1;
      return a.title.localeCompare(b.title);
    });

    const topScore = scored[0]?.score || 0;
    const minimum = Math.max(35, topScore * 0.3);
    return scored.filter(item => item.score >= minimum).slice(0, maxResults);
  }

  function matches(query, text) {
    const q = normalize(query);
    if (!q) return true;
    const haystack = normalize(text).split(' ').filter(Boolean);
    return q.split(' ').filter(Boolean).every(qt =>
      haystack.some(token => token === qt || token.startsWith(qt))
    );
  }

  function suggestions(limit = 6) {
    return SUGGESTIONS.slice(0, limit);
  }

  function renderSuggestions() {
    return `<div class="${mx('search-suggestions')}">${suggestions(6).map(s => `
      <button type="button" class="${mx('search-suggestion')}" data-search-suggestion="${MotoX.escapeHtml(s)}">${MotoX.escapeHtml(s)}</button>
    `).join('')}</div>`;
  }

  function renderResults(results, dropdown, base, query) {
    activeResults = results;
    activeIndex = -1;

    if (!results.length) {
      dropdown.innerHTML = `<div class="${mx('search-no-results')}">
        <strong>No results for “${MotoX.escapeHtml(query)}”</strong>
        <p class="${mx('search-tip')}">Try a model name, nickname or engine size — for example “CBR 600”, “Fireblade” or “Busa”.</p>
        ${renderSuggestions()}
      </div>`;
      dropdown.classList.add(mx('open'));
      if (typeof MotoXShield !== 'undefined') MotoXShield.finalizeRoot(dropdown);
      return;
    }

    dropdown.innerHTML = results.map(r => {
      const extras = [r.meta, r.power].filter(Boolean).join(' · ');
      return MotoX.renderSearchResult(`${base}${r.url}`, r.title, `${r.type === 'motorcycle' ? '🏍 ' : '📄 '}${extras}`, r.title);
    }).join('');
    dropdown.classList.add(mx('open'));
    if (typeof MotoXShield !== 'undefined') MotoXShield.finalizeRoot(dropdown);
  }

  function closeDropdown(dropdown) {
    dropdown.classList.remove(mx('open'));
    dropdown.innerHTML = '';
    activeResults = [];
    activeIndex = -1;
  }

  function setActive(dropdown, nextIndex) {
    const items = [...dropdown.querySelectorAll('[role="option"]')];
    if (!items.length) return -1;
    if (nextIndex < 0) nextIndex = items.length - 1;
    if (nextIndex >= items.length) nextIndex = 0;
    items.forEach((el, i) => {
      const active = i === nextIndex;
      el.classList.toggle('is-active', active);
      el.setAttribute('aria-selected', String(active));
      if (active) el.scrollIntoView({ block: 'nearest' });
    });
    activeIndex = nextIndex;
    return nextIndex;
  }

  async function ensureIndex() {
    if (index.length) return index;
    if (!indexPromise) {
      indexPromise = (async () => {
        try {
          index = (await MotoX.loadSearchIndex()).map(prepareItem);
        } catch {
          const { motorcycles, pages, settings } = await MotoX.loadAllSearchData();
          searchSettings = {
            minChars: settings.search?.minChars || 2,
            maxResults: settings.search?.maxResults || 20
          };
          index = buildIndex(motorcycles, pages).map(prepareItem);
        }
        return index;
      })();
    }
    return indexPromise;
  }

  async function init(options = {}) {
    const input = MotoX.ref('global-search');
    const dropdown = MotoX.ref('search-dropdown');
    if (!input || !dropdown) return;

    const lazy = options.lazy !== false;
    if (!lazy) {
      await ensureIndex();
    }

    if (options.settings) {
      searchSettings = {
        minChars: options.settings.search?.minChars || 2,
        maxResults: options.settings.search?.maxResults || 20
      };
    }

    async function runSearch() {
      await ensureIndex();
      const q = input.value.trim();
      if (normalize(q).length < searchSettings.minChars) {
        closeDropdown(dropdown);
        input.setAttribute('aria-expanded', 'false');
        return;
      }
      const results = search(q, searchSettings.maxResults);
      renderResults(results, dropdown, MotoX.BASE, q);
      input.setAttribute('aria-expanded', 'true');
    }

    input.addEventListener('focus', () => {
      if (lazy) ensureIndex();
    });

    input.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(runSearch, 140);
    });

    input.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        closeDropdown(dropdown);
        input.setAttribute('aria-expanded', 'false');
        input.blur();
        return;
      }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        if (!dropdown.classList.contains(mx('open'))) return;
        e.preventDefault();
        const delta = e.key === 'ArrowDown' ? 1 : -1;
        setActive(dropdown, activeIndex + delta);
        return;
      }
      if (e.key === 'Enter') {
        if (activeIndex >= 0) {
          const items = dropdown.querySelectorAll('[role="option"]');
          const active = items[activeIndex];
          if (active) {
            e.preventDefault();
            window.location.href = active.getAttribute('href');
            return;
          }
        }
        const q = input.value.trim();
        if (normalize(q).length >= searchSettings.minChars) {
          window.location.href = `${MotoX.BASE}search.html?q=${encodeURIComponent(q)}`;
        }
      }
    });

    dropdown.addEventListener('click', e => {
      const suggestion = e.target.closest('[data-search-suggestion]');
      if (!suggestion) return;
      e.preventDefault();
      input.value = suggestion.getAttribute('data-search-suggestion') || '';
      runSearch();
      input.focus();
    });

    document.addEventListener('click', e => {
      if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        closeDropdown(dropdown);
        input.setAttribute('aria-expanded', 'false');
      }
    });
  }

  return { init, search, matches, buildIndex, ensureIndex, suggestions, normalize };
})();
