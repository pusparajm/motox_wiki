/**
 * MotoX Wiki — client-side search (no external dependencies)
 */
const MotoXSearch = (() => {
  function mx(name) {
    return typeof MotoXShield !== 'undefined' ? MotoXShield.c(name) : name;
  }

  let index = [];
  let indexPromise = null;
  let debounceTimer = null;
  let searchSettings = { minChars: 2, maxResults: 20 };

  function buildIndex(motorcycles, pages) {
    const items = [];

    motorcycles.forEach(bike => {
      items.push({
        type: 'motorcycle',
        id: bike.id,
        title: MotoX.formatBikeTitle(bike),
        meta: [bike.region, bike.category, bike.displacement].filter(Boolean).join(' · ') || 'Motorcycle',
        url: `motorcycle.html?id=${encodeURIComponent(bike.id)}`,
        searchText: flattenBike(bike)
      });
    });

    pages.forEach(page => {
      items.push({
        type: 'page',
        id: page.id,
        title: page.title,
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
      bike.summary, ...(bike.tags || [])
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
    const q = query.toLowerCase();
    const title = item.title.toLowerCase();
    const text = item.searchText;

    let score = 0;
    if (title === q) score += 100;
    else if (title.startsWith(q)) score += 50;
    else if (title.includes(q)) score += 30;

    const words = q.split(/\s+/).filter(Boolean);
    words.forEach(word => {
      if (title.includes(word)) score += 10;
      if (text.includes(word)) score += 5;
    });

    if (text.includes(q)) score += 15;
    return score;
  }

  function search(query, maxResults = searchSettings.maxResults) {
    if (!query || query.length < searchSettings.minChars) return [];
    return index
      .map(item => ({ ...item, score: scoreItem(item, query) }))
      .filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, maxResults);
  }

  async function ensureIndex() {
    if (index.length) return index;
    if (!indexPromise) {
      indexPromise = (async () => {
        try {
          index = await MotoX.loadSearchIndex();
        } catch {
          const { motorcycles, pages, settings } = await MotoX.loadAllSearchData();
          searchSettings = {
            minChars: settings.search?.minChars || 2,
            maxResults: settings.search?.maxResults || 20
          };
          index = buildIndex(motorcycles, pages);
        }
        return index;
      })();
    }
    return indexPromise;
  }

  function renderResults(results, dropdown, base) {
    if (!results.length) {
      dropdown.innerHTML = `<div class="${mx('search-no-results')}">No results found</div>`;
      dropdown.classList.add(mx('open'));
      return;
    }

    dropdown.innerHTML = results.map(r => `
      <a href="${base}${r.url}" class="${mx('search-result-item')}" role="option">
        <div class="${mx('result-title')}">${MotoX.escapeHtml(r.title)}</div>
        <div class="${mx('result-meta')}">${r.type === 'motorcycle' ? '🏍 ' : '📄 '}${MotoX.escapeHtml(r.meta)}</div>
      </a>
    `).join('');
    dropdown.classList.add(mx('open'));
  }

  function closeDropdown(dropdown) {
    dropdown.classList.remove(mx('open'));
    dropdown.innerHTML = '';
  }

  async function init(options = {}) {
    const input = document.getElementById('global-search');
    const dropdown = document.getElementById('search-dropdown');
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
      if (q.length < searchSettings.minChars) {
        closeDropdown(dropdown);
        input.setAttribute('aria-expanded', 'false');
        return;
      }
      const results = search(q, searchSettings.maxResults);
      renderResults(results, dropdown, MotoX.BASE);
      input.setAttribute('aria-expanded', 'true');
    }

    input.addEventListener('focus', () => {
      if (lazy) ensureIndex();
    });

    input.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(runSearch, 150);
    });

    input.addEventListener('keydown', e => {
      if (e.key === 'Escape') {
        closeDropdown(dropdown);
        input.blur();
      }
      if (e.key === 'Enter') {
        const q = input.value.trim();
        if (q.length >= searchSettings.minChars) {
          window.location.href = `${MotoX.BASE}search.html?q=${encodeURIComponent(q)}`;
        }
      }
    });

    document.addEventListener('click', e => {
      if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        closeDropdown(dropdown);
        input.setAttribute('aria-expanded', 'false');
      }
    });
  }

  return { init, search, buildIndex, ensureIndex };
})();
