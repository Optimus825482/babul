/* ============================================================
   BABUL - Frontend JavaScript
   Vanilla JS - Framework gerektirmez
   ============================================================ */

const API_BASE = window.location.origin + '/api';

// ============================================================
// STATE
// ============================================================
let allBrands = [];
let allYears = [];
let isSearching = false;
let liveSearchTimer = null;
let newsSlideIndex = 0;
let watchlist = [];
let currentResults = [];
let currentQuery = {};
let currentPage = 1;
const RESULTS_PER_PAGE = 8;

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    // Splash screen: min 1.8s göster, sonra kapat
    const splash = document.getElementById('splash-screen');
    const hideSplash = () => { if (splash) splash.classList.add('is-hidden'); };
    setTimeout(hideSplash, 1800);

    loadWatchlist();
    loadNews();
    loadMarketSnapshot();
    loadBrands();
    loadYears();
    renderWatchlist();
    updateDashboard();
});

// ============================================================
// FILTER DRAWER (Mobile)
// ============================================================
function toggleFilterDrawer() {
    const sidebar = document.getElementById('search-sidebar');
    const backdrop = document.getElementById('filter-backdrop');
    if (!sidebar) return;
    const isOpen = sidebar.classList.contains('is-open');
    sidebar.classList.toggle('is-open', !isOpen);
    if (backdrop) backdrop.classList.toggle('hidden', isOpen);
    document.body.style.overflow = isOpen ? '' : 'hidden';
}

// ============================================================
// API ÇAĞRILARI
// ============================================================

async function loadBrands() {
    try {
        const res = await fetch(API_BASE + '/brands');
        const data = await res.json();
        allBrands = data.brands || [];
        const sel = document.getElementById('brand-select');
        sel.innerHTML = '<option value="">Marka Seçin</option>';
        allBrands.forEach(b => {
            const opt = document.createElement('option');
            opt.value = b;
            opt.textContent = b;
            sel.appendChild(opt);
        });
    } catch (e) {
        console.error('Markalar yüklenemedi:', e);
    }
}

async function loadModels(brand) {
    const sel = document.getElementById('model-select');
    sel.innerHTML = '<option value="">Yükleniyor...</option>';
    sel.disabled = true;

    try {
        const res = await fetch(API_BASE + '/models/' + encodeURIComponent(brand));
        const data = await res.json();
        const models = data.models || [];
        sel.innerHTML = '<option value="">Model Seçin</option>';
        models.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            sel.appendChild(opt);
        });
        sel.disabled = false;
    } catch (e) {
        sel.innerHTML = '<option value="">Model bulunamadı</option>';
        console.error('Modeller yüklenemedi:', e);
    }
    validateForm();
}

async function loadYears() {
    try {
        const res = await fetch(API_BASE + '/years');
        const data = await res.json();
        allYears = data.years || [];
        const sel = document.getElementById('year-select');
        sel.innerHTML = '<option value="">Yıl Seçin</option>';
        allYears.forEach(y => {
            const opt = document.createElement('option');
            opt.value = y;
            opt.textContent = y;
            sel.appendChild(opt);
        });
    } catch (e) {
        console.error('Yıllar yüklenemedi:', e);
    }
}

async function loadNews() {
    const track = document.getElementById('news-track');
    if (!track) return;

    try {
        const res = await fetch(API_BASE + '/news?limit=12');
        const data = await res.json();
        const items = data.items || [];

        if (!items.length) {
            renderNewsFallback();
            return;
        }

        newsSlideIndex = 0;
        track.style.transform = 'translateX(0)';
        track.innerHTML = items.map((item, index) => `
            <article class="news-card ${index === 0 ? 'is-active' : ''}" onclick="window.open('${escapeHtml(item.url)}', '_blank')">
                ${item.imageUrl ? `<img class="news-image" src="${escapeHtml(item.imageUrl)}" alt="${escapeHtml(item.title)}" loading="lazy" onerror="this.remove()">` : ''}
                <div class="news-content">
                    <span>${escapeHtml(item.source)} · ${escapeHtml(formatNewsDate(item.publishedAt))}</span>
                    <h4>${escapeHtml(item.title)}</h4>
                    <p>${escapeHtml(item.summary || 'Haberi okumak için karta tıkla.')}</p>
                </div>
            </article>
        `).join('');
    } catch (e) {
        console.error('Haberler yüklenemedi:', e);
        renderNewsFallback();
    }
}

async function loadMarketSnapshot() {
    try {
        const res = await fetch(API_BASE + '/market');
        const data = await res.json();
        renderMarketRates(data.rates || []);
        renderLoanRates(data.loanRates || {});
    } catch (e) {
        console.error('Piyasa verisi yüklenemedi:', e);
        renderMarketRates([]);
        renderLoanRates({});
    }
}

function renderMarketRates(rates) {
    const container = document.getElementById('market-rates');
    if (!container) return;

    if (!rates.length) {
        container.innerHTML = '<p class="muted-line">Kur bilgisi alınamadı.</p>';
        return;
    }

    container.innerHTML = rates.map(rate => {
        const val = rate.selling || rate.buying || '-';
        const symbol = rate.symbol || '';
        const unit = rate.unit || '';
        const dir = rate.direction || 'neutral';
        const pct = rate.change_pct;

        let arrowHtml = '';
        if (dir === 'up') {
            const pctStr = pct != null ? ` +${pct}%` : '';
            arrowHtml = `<span class="rate-up">↑${pctStr}</span>`;
        } else if (dir === 'down') {
            const pctStr = pct != null ? ` ${pct}%` : '';
            arrowHtml = `<span class="rate-down">↓${pctStr}</span>`;
        }

        const unitLabel = unit ? `<span class="rate-unit">${escapeHtml(unit)}</span> ` : '';
        return `<div class="market-row">
            <span>${escapeHtml(rate.label)}</span>
            <div class="market-val-group">
                <strong>${unitLabel}${escapeHtml(val)} ${escapeHtml(symbol)}</strong>
                ${arrowHtml}
            </div>
        </div>`;
    }).join('');
}

function renderLoanRates(loanData) {
    const container = document.getElementById('loan-rates');
    const link = document.getElementById('loan-source-link');
    if (!container) return;

    const rates = loanData.rates || [];
    if (!rates.length) {
        container.innerHTML = '<p class="muted-line">' + escapeHtml(loanData.note || 'Faiz oranı alınamadı.') + '</p>';
        if (link) link.classList.add('hidden');
        return;
    }

    container.innerHTML = rates.map(rate => `
        <div class="market-row">
            <span>${escapeHtml(rate.label)}</span>
            <strong>${escapeHtml(rate.value)}</strong>
        </div>
    `).join('') + '<p class="muted-line">' + escapeHtml(loanData.source || '') + '</p>';

    if (link && loanData.url) {
        link.href = loanData.url;
        link.classList.remove('hidden');
    }
}

function renderNewsFallback() {
    const track = document.getElementById('news-track');
    if (!track) return;

    newsSlideIndex = 0;
    track.style.transform = 'translateX(0)';
    track.innerHTML = `
        <article class="news-card is-active">
            <div class="news-content">
                <span>BABUL</span>
                <h4>Haber akışı şu anda alınamadı</h4>
                <p>Kaynaklar geçici olarak yanıt vermiyor olabilir. Dashboard açık kaldıkça tekrar yenileyebilirsin.</p>
            </div>
        </article>
    `;
}

async function searchListings() {
    const brand = document.getElementById('brand-select').value;
    const model = document.getElementById('model-select').value;
    const year = document.getElementById('year-select').value;
    const filters = collectSearchFilters();

    if (!brand || !model || !year) {
        showToast('Lütfen tüm alanları doldurun', 'warning');
        return;
    }

    if (isSearching) return;
    isSearching = true;

    showLoading(brand, model, year);

    try {
        const res = await fetch(API_BASE + '/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ brand, model, year, ...filters })
        });
        const data = await res.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        stopLiveSearch(data.results || []);
        renderResults(data.results || [], data.query || {});
        updateSearchSidebar(data.results || []);

        if (data.warnings && data.warnings.length > 0) {
            showToast('Bazı kaynaklarda hata oluştu', 'warning');
        }

        const count = data.count || 0;
        if (count > 0) {
            showToast(count + ' ilan bulundu!', 'success');
        } else {
            showToast('İlan bulunamadı', 'warning');
        }

    } catch (err) {
        console.error('Arama hatası:', err);
        stopLiveSearch([]);
        showError('Sunucuya bağlanılamadı. Lütfen backend\'in çalıştığından emin olun.');
    } finally {
        isSearching = false;
    }
}

// ============================================================
// EVENT HANDLERS
// ============================================================

function onBrandChange() {
    const brand = document.getElementById('brand-select').value;
    const modelSel = document.getElementById('model-select');

    if (brand) {
        loadModels(brand);
    } else {
        modelSel.innerHTML = '<option value="">Önce Marka Seçin</option>';
        modelSel.disabled = true;
    }
    validateForm();
}

function validateForm() {
    const brand = document.getElementById('brand-select').value;
    const model = document.getElementById('model-select').value;
    const year = document.getElementById('year-select').value;
    const btn = document.getElementById('search-btn');
    const missing = [brand, model, year].filter(Boolean).length;
    btn.disabled = missing !== 3;

    const readiness = document.getElementById('form-readiness');
    if (readiness) {
        readiness.textContent = missing === 3 ? 'Aramaya hazır' : (3 - missing) + ' seçim gerekli';
        readiness.classList.toggle('is-ready', missing === 3);
    }
}

function showView(viewName) {
    document.querySelectorAll('.app-view').forEach(view => {
        view.classList.toggle('hidden', view.id !== viewName + '-view');
    });
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('is-active', tab.dataset.view === viewName);
    });
    if (viewName === 'watchlist') renderWatchlist();
    if (viewName === 'kredi') renderKrediRateInfo();
}

function moveNewsSlide(direction) {
    const slides = Array.from(document.querySelectorAll('.news-card'));
    if (!slides.length) return;
    newsSlideIndex = (newsSlideIndex + direction + slides.length) % slides.length;
    slides.forEach((slide, index) => {
        slide.classList.toggle('is-active', index === newsSlideIndex);
    });
    const track = document.getElementById('news-track');
    if (track) {
        track.style.transform = 'translateX(' + (-newsSlideIndex * 100) + '%)';
    }
}

function selectVehicleType(button) {
    document.querySelectorAll('.vehicle-type-card').forEach(card => {
        card.classList.toggle('is-active', card === button);
    });

    const bodySelect = document.getElementById('body-select');
    if (bodySelect) {
        bodySelect.value = button.dataset.bodyType || '';
    }
}

// Yıl select değişimi
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('year-select').addEventListener('change', validateForm);
});

function resetForm() {
    document.getElementById('brand-select').value = '';
    const modelSel = document.getElementById('model-select');
    modelSel.innerHTML = '<option value="">Önce Marka Seçin</option>';
    modelSel.disabled = true;
    document.getElementById('year-select').value = '';
    [
        'transmission-select',
        'fuel-select',
        'body-select',
        'color-select',
        'condition-select',
        'damage-select',
        'paint-change-select'
    ].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    document.querySelectorAll('.vehicle-type-card').forEach(card => {
        card.classList.toggle('is-active', card.dataset.bodyType === '');
    });
    [
        'price-min-input',
        'price-max-input',
        'km-min-input',
        'km-max-input'
    ].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    document.getElementById('search-btn').disabled = true;

    // UI sıfırla
    document.getElementById('empty-state').classList.remove('hidden');
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('error-state').classList.add('hidden');
    document.getElementById('stats-bar').classList.add('hidden');
    document.getElementById('results-grid').classList.add('hidden');
    document.getElementById('pagination-bar').classList.add('hidden');
    document.getElementById('no-results').classList.add('hidden');
    currentResults = [];
    currentQuery = {};
    currentPage = 1;
    updatePagination();
    stopLiveSearch([]);
}

function collectSearchFilters() {
    return {
        transmission: getValue('transmission-select'),
        fuelType: getValue('fuel-select'),
        bodyType: getValue('body-select'),
        color: getValue('color-select'),
        vehicleCondition: getValue('condition-select'),
        heavyDamage: getValue('damage-select'),
        paintChange: getValue('paint-change-select'),
        priceMin: getValue('price-min-input'),
        priceMax: getValue('price-max-input'),
        kmMin: getValue('km-min-input'),
        kmMax: getValue('km-max-input')
    };
}

// ============================================================
// UI RENDER
// ============================================================

function showLoading(brand, model, year) {
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('loading-state').classList.remove('hidden');
    document.getElementById('error-state').classList.add('hidden');
    document.getElementById('stats-bar').classList.add('hidden');
    const grid = document.getElementById('results-grid');
    grid.classList.remove('hidden');
    grid.innerHTML = '';
    document.getElementById('pagination-bar').classList.add('hidden');
    document.getElementById('no-results').classList.add('hidden');
    startLiveSearch(brand, model, year);
}

function showError(msg) {
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('error-state').classList.remove('hidden');
    document.getElementById('stats-bar').classList.add('hidden');
    document.getElementById('results-grid').classList.add('hidden');
    document.getElementById('pagination-bar').classList.add('hidden');
    document.getElementById('no-results').classList.add('hidden');
    document.getElementById('error-message').textContent = msg;
}

function renderResults(results, query) {
    currentResults = results || [];
    currentQuery = query || {};
    currentPage = 1;

    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('error-state').classList.add('hidden');

    if (!results || results.length === 0) {
        document.getElementById('no-results').classList.remove('hidden');
        document.getElementById('stats-bar').classList.add('hidden');
        document.getElementById('results-grid').classList.add('hidden');
        document.getElementById('pagination-bar').classList.add('hidden');
        updatePagination();
        return;
    }

    // Stats Bar
    const priceStats = calculatePriceStats(results);
    const sourceBreakdown = calculateSourceBreakdown(results);
    const statsBar = document.getElementById('stats-bar');
    statsBar.classList.remove('hidden');
    document.getElementById('result-count').textContent = results.length + ' ilan';
    document.getElementById('avg-price').textContent = formatPrice(priceStats.avg);
    document.getElementById('min-price').textContent = formatPrice(priceStats.min);
    document.getElementById('max-price').textContent = formatPrice(priceStats.max);
    document.getElementById('source-breakdown').textContent = sourceBreakdown;
    document.getElementById('search-query-badge').textContent =
        (query.brand || '') + ' ' + (query.model || '') + ' ' + (query.year || '');

    // List
    const grid = document.getElementById('results-grid');
    grid.classList.remove('hidden');
    grid.innerHTML = '';

    renderCurrentPage(true);
}

function renderCurrentPage(animated) {
    const grid = document.getElementById('results-grid');
    if (!grid) return;

    const start = (currentPage - 1) * RESULTS_PER_PAGE;
    const pageItems = currentResults.slice(start, start + RESULTS_PER_PAGE);
    grid.innerHTML = '';

    if (animated) {
        revealResults(pageItems, grid, start);
    } else {
        pageItems.forEach((item, index) => {
            grid.appendChild(createListingCard(item, start + index));
        });
    }

    updatePagination();
}

function changeResultsPage(direction) {
    const totalPages = getTotalPages();
    currentPage = Math.min(Math.max(currentPage + direction, 1), totalPages);
    renderCurrentPage(false);
}

function getTotalPages() {
    return Math.max(Math.ceil(currentResults.length / RESULTS_PER_PAGE), 1);
}

function updatePagination() {
    const bar = document.getElementById('pagination-bar');
    const info = document.getElementById('pagination-info');
    const prev = document.getElementById('prev-page-btn');
    const next = document.getElementById('next-page-btn');
    const totalPages = getTotalPages();

    if (!bar || !info || !prev || !next) return;

    const hasResults = currentResults.length > 0;
    bar.classList.toggle('hidden', !hasResults || totalPages <= 1);
    info.textContent = 'Sayfa ' + currentPage + ' / ' + totalPages;
    prev.disabled = currentPage <= 1;
    next.disabled = currentPage >= totalPages;
    setText('side-page-info', hasResults ? currentPage + ' / ' + totalPages : '-');
}

function updateSearchSidebar(results) {
    const priceStats = calculatePriceStats(results);
    setText('side-search-status', results.length ? 'Sonuçlandı' : 'Sonuç yok');
    setText('side-last-count', results.length + ' ilan');
    setText('side-last-avg', formatPrice(priceStats.avg));
}

function startLiveSearch(brand, model, year) {
    stopLiveSearch([]);

    const title = document.getElementById('live-search-title');
    const events = document.getElementById('scan-events');
    const progress = document.getElementById('scan-progress-bar');
    const foundCount = document.getElementById('live-found-count');
    const arabamStatus = document.getElementById('source-arabam-status');
    const sahibindenStatus = document.getElementById('source-sahibinden-status');
    const arabamCard = document.getElementById('source-arabam-card');
    const sahibindenCard = document.getElementById('source-sahibinden-card');

    if (!title || !events || !progress) return;

    const steps = [
        { pct: 12, title: brand + ' ' + model + ' için arama hazırlanıyor', event: 'Arama parametreleri hazırlandı', arabam: 'Bağlantı hazırlanıyor', sahibinden: 'Sırada bekliyor', count: 0 },
        { pct: 28, title: 'arabam.com taranıyor', event: 'arabam.com arama isteği gönderildi', arabam: 'Sayfalar taranıyor', sahibinden: 'Sırada bekliyor', count: 0 },
        { pct: 46, title: 'İlk ilan sinyalleri işleniyor', event: 'Fiyat ve lokasyon alanları normalize ediliyor', arabam: 'İlan detayları okunuyor', sahibinden: 'Hazırlanıyor', count: 1 },
        { pct: 62, title: 'sahibinden.com taranıyor', event: 'sahibinden.com arama isteği gönderildi', arabam: 'Tamamlanıyor', sahibinden: 'Sayfalar taranıyor', count: 2 },
        { pct: 78, title: 'Kaynaklar birleştiriliyor', event: 'Tekrarlı kayıtlar ve fiyat metrikleri hazırlanıyor', arabam: 'Tamamlandı', sahibinden: 'İlan detayları okunuyor', count: 3 },
        { pct: 90, title: year + ' sonuçları sıralanıyor', event: 'Kartlar ekrana akmaya hazırlanıyor', arabam: 'Tamamlandı', sahibinden: 'Tamamlanıyor', count: 4 }
    ];

    events.innerHTML = '';
    progress.style.width = '4%';
    foundCount.textContent = '0';
    arabamCard.classList.add('is-active');
    sahibindenCard.classList.remove('is-active');

    let index = 0;
    const applyStep = () => {
        const step = steps[Math.min(index, steps.length - 1)];
        title.textContent = step.title;
        progress.style.width = step.pct + '%';
        foundCount.textContent = step.count;
        arabamStatus.textContent = step.arabam;
        sahibindenStatus.textContent = step.sahibinden;
        sahibindenCard.classList.toggle('is-active', step.pct >= 55);
        appendScanEvent(step.event);
        index += 1;
    };

    applyStep();
    liveSearchTimer = setInterval(applyStep, 950);
}

function stopLiveSearch(results) {
    if (liveSearchTimer) {
        clearInterval(liveSearchTimer);
        liveSearchTimer = null;
    }

    const progress = document.getElementById('scan-progress-bar');
    const foundCount = document.getElementById('live-found-count');
    const title = document.getElementById('live-search-title');
    if (progress) progress.style.width = results.length ? '100%' : '92%';
    if (foundCount) foundCount.textContent = results.length;
    if (title && results.length) title.textContent = 'Sonuçlar ekrana aktarılıyor';
}

function appendScanEvent(text) {
    const events = document.getElementById('scan-events');
    if (!events) return;

    const item = document.createElement('div');
    item.className = 'scan-event';
    item.textContent = text;
    events.prepend(item);

    while (events.children.length > 4) {
        events.lastChild.remove();
    }
}

function revealResults(results, grid, offset = 0) {
    let index = 0;
    const tick = () => {
        if (index >= results.length) return;
        const card = createListingCard(results[index], offset + index);
        grid.appendChild(card);
        index += 1;
        setText('live-found-count', index);
        setTimeout(tick, index < 8 ? 120 : 45);
    };
    tick();
}

function createListingCard(item, index) {
    const card = document.createElement('div');
    card.className = 'listing-card animate-fade-in stagger-' + Math.min(index + 1, 8);
    card.onclick = () => {
        if (item.detailUrl) {
            window.open(item.detailUrl, '_blank');
        }
    };

    const sourceClass = item.source === 'arabam.com' ? 'source-arabam' : 'source-sahibinden';
    const sourceLabel = item.source === 'arabam.com' ? 'arabam.com' : 'sahibinden.com';
    const imgUrl = item.imageUrl || 'https://placehold.co/400x250/e2e8f0/94a3b8?text=Arac+Resmi';

    card.innerHTML = `
        <div class="listing-image-wrapper">
            <img class="listing-image" src="${escapeHtml(imgUrl)}" alt="${escapeHtml(item.title || item.modelName || 'Araç')}"
                 onerror="this.src='https://placehold.co/400x250/e2e8f0/94a3b8?text=Arac+Resmi'" loading="lazy">
            <div class="absolute top-3 right-3">
                <span class="source-badge ${sourceClass}">${sourceLabel}</span>
            </div>
        </div>
        <div class="p-4">
            <h3 class="text-sm font-bold text-slate-800 leading-tight mb-1" style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.5em;">
                ${escapeHtml(item.title || item.modelName || 'İlan Başlığı')}
            </h3>
            ${item.modelName && item.title ? `<p class="text-xs text-slate-400 mb-2">${escapeHtml(item.modelName)}</p>` : '<div class="mb-2"></div>'}
            <div class="flex items-center justify-between mb-3">
                <span class="text-lg font-extrabold text-blue-700">${escapeHtml(item.price || 'Fiyat Yok')}</span>
                ${item.year ? `<span class="year-badge">${escapeHtml(item.year)}</span>` : ''}
            </div>
            <div class="flex items-center justify-between text-xs text-slate-400">
                <span class="flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
                    ${escapeHtml(item.location || 'Belirtilmemiş')}
                </span>
                ${item.date ? `<span class="flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
                    ${escapeHtml(item.date)}
                </span>` : ''}
            </div>
            <button class="watch-btn" onclick="event.stopPropagation(); addListingToWatchlistFromPayload('${encodeURIComponent(JSON.stringify(item))}')">
                Takibe al
            </button>
        </div>
    `;

    return card;
}

function addListingToWatchlistFromPayload(payload) {
    addListingToWatchlist(JSON.parse(decodeURIComponent(payload)));
}

function loadWatchlist() {
    try {
        watchlist = JSON.parse(localStorage.getItem('babul.watchlist') || '[]');
    } catch {
        watchlist = [];
    }
}

function saveWatchlist() {
    localStorage.setItem('babul.watchlist', JSON.stringify(watchlist));
    updateDashboard();
}

function addListingToWatchlist(item) {
    const entry = {
        id: item.detailUrl || item.title || Date.now().toString(),
        type: 'listing',
        title: item.title || item.modelName || 'Araç ilanı',
        meta: [item.price, item.location, item.year, item.source].filter(Boolean).join(' · '),
        createdAt: new Date().toISOString()
    };
    upsertWatchItem(entry);
}

function addCurrentCriteriaToWatchlist() {
    const brand = document.getElementById('brand-select').value;
    const model = document.getElementById('model-select').value;
    const year = document.getElementById('year-select').value;
    if (!brand || !model || !year) {
        showToast('Önce marka, model ve yıl seç', 'warning');
        return;
    }
    upsertWatchItem({
        id: 'criteria:' + [brand, model, year].join(':'),
        type: 'criteria',
        title: brand + ' ' + model + ' ' + year,
        meta: 'Kriter takibi · belirli aralıklarla izlenebilir',
        createdAt: new Date().toISOString()
    });
}

function addCriteriaFromForm() {
    const brand = document.getElementById('watch-brand').value.trim();
    const model = document.getElementById('watch-model').value.trim();
    const year = document.getElementById('watch-year').value.trim();
    const km = document.getElementById('watch-km').value.trim();
    if (!brand) {
        showToast('En az marka gir', 'warning');
        return;
    }
    upsertWatchItem({
        id: 'criteria:' + [brand, model, year, km].join(':'),
        type: 'criteria',
        title: [brand, model, year].filter(Boolean).join(' '),
        meta: ['Kriter takibi', km ? 'Maks. ' + km + ' km' : 'km filtresi yok'].join(' · '),
        createdAt: new Date().toISOString()
    });
}

function upsertWatchItem(entry) {
    if (!watchlist.some(item => item.id === entry.id)) {
        watchlist.unshift(entry);
        saveWatchlist();
        renderWatchlist();
        showToast('Takip listesine eklendi', 'success');
    } else {
        showToast('Bu kayıt zaten takipte', 'warning');
    }
}

function removeWatchItem(id) {
    id = decodeURIComponent(id);
    watchlist = watchlist.filter(item => item.id !== id);
    saveWatchlist();
    renderWatchlist();
}

function renderWatchlist() {
    const container = document.getElementById('watchlist-items');
    if (!container) return;
    if (!watchlist.length) {
        container.innerHTML = '<div class="empty-watch">Henüz takipte araç veya kriter yok. Arama sayfasından ilanları ya da kriterleri takibe alabilirsin.</div>';
        updateDashboard();
        return;
    }
    container.innerHTML = watchlist.map(item => `
        <article class="watch-card">
            <span>${escapeHtml(item.type === 'listing' ? 'İlan' : 'Kriter')}</span>
            <h3>${escapeHtml(item.title)}</h3>
            <p>${escapeHtml(item.meta)}</p>
            <small>Eklenme: ${formatCatalogDate(item.createdAt)}</small>
            <button onclick="removeWatchItem('${encodeURIComponent(item.id)}')">Kaldır</button>
        </article>
    `).join('');
    updateDashboard();
}

function updateDashboard() {
    setText('watchlist-count', watchlist.length);
    setText('dashboard-watch-count', watchlist.length);
    setText('dashboard-last-activity', watchlist[0] ? formatCatalogDate(watchlist[0].createdAt) : 'Yok');
}

// ============================================================
// HELPERS
// ============================================================

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function calculatePriceStats(results) {
    const prices = results
        .map(item => extractPriceNumber(item.price))
        .filter(price => price > 0);

    if (!prices.length) {
        return { avg: 0, min: 0, max: 0 };
    }

    const total = prices.reduce((sum, price) => sum + price, 0);
    return {
        avg: total / prices.length,
        min: Math.min(...prices),
        max: Math.max(...prices)
    };
}

function calculateSourceBreakdown(results) {
    const counts = results.reduce((acc, item) => {
        const source = item.source || 'bilinmiyor';
        acc[source] = (acc[source] || 0) + 1;
        return acc;
    }, {});

    return Object.entries(counts)
        .map(([source, count]) => source.replace('.com', '') + ': ' + count)
        .join(' · ') || '-';
}

function extractPriceNumber(priceStr) {
    if (!priceStr) return 0;
    try {
        const clean = priceStr.replace(/TL/gi, '').replace(/\./g, '').replace(/,/g, '.').trim();
        return parseFloat(clean) || 0;
    } catch {
        return 0;
    }
}

function formatPrice(num) {
    if (num <= 0) return '-';
    return Math.round(num).toLocaleString('tr-TR') + ' TL';
}

function formatCatalogDate(value) {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString('tr-TR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatNewsDate(value) {
    if (!value) return 'yeni';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'yeni';
    return date.toLocaleDateString('tr-TR', {
        day: '2-digit',
        month: 'short'
    });
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function getValue(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : '';
}

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================

// ============================================================
// KREDİ HESAPLAMA
// ============================================================

const KREDI_RATES = {
    sifir:    { label: 'Sıfır Araç',     aylik: 3.99, max_vade: 60 },
    ikinciEl: { label: 'İkinci El Araç', aylik: 4.49, max_vade: 48 }
};
let aktifKrediTip = 'sifir';

function switchKrediTab(tip, btn) {
    aktifKrediTip = tip;
    document.querySelectorAll('.kredi-tab').forEach(t => t.classList.remove('is-active'));
    btn.classList.add('is-active');
    renderKrediRateInfo();
    calcKredi();
}

function renderKrediRateInfo() {
    const el = document.getElementById('kredi-rate-info');
    if (!el) return;
    const r = KREDI_RATES[aktifKrediTip];
    el.innerHTML = `
        <div class="market-row"><span>Araç Tipi</span><strong>${r.label}</strong></div>
        <div class="market-row"><span>Aylık Faiz (Ort.)</span><strong>%${r.aylik.toFixed(2)}</strong></div>
        <div class="market-row"><span>Yıllık Faiz (Ort.)</span><strong>%${(r.aylik * 12).toFixed(2)}</strong></div>
        <div class="market-row"><span>Maks. Vade</span><strong>${r.max_vade} ay</strong></div>
    `;
}

function calcKredi() {
    const fiyat = parseFloat(document.getElementById('kredi-fiyat').value) || 0;
    const pesinat = parseFloat(document.getElementById('kredi-pesinat').value) || 0;
    const vade = parseInt(document.getElementById('kredi-vade').value) || 24;
    const sonuc = document.getElementById('kredi-sonuc');
    const emptyHint = document.getElementById('kredi-sonuc-empty');
    if (!sonuc) return;
    const tutar = fiyat - pesinat;
    if (tutar <= 0 || fiyat <= 0) {
        sonuc.classList.add('hidden');
        if (emptyHint) emptyHint.classList.remove('hidden');
        return;
    }
    const r = KREDI_RATES[aktifKrediTip];
    const aylikFaiz = r.aylik / 100;
    const pow = Math.pow(1 + aylikFaiz, vade);
    const taksit = tutar * (aylikFaiz * pow) / (pow - 1);
    const toplam = taksit * vade;
    const toplamFaiz = toplam - tutar;
    const fmt = n => n.toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + ' ₺';
    document.getElementById('kr-faiz-oran').textContent = `%${r.aylik.toFixed(2)} aylık (${r.label})`;
    document.getElementById('kr-tutar').textContent = fmt(tutar);
    document.getElementById('kr-taksit').textContent = fmt(taksit);
    document.getElementById('kr-toplam').textContent = fmt(toplam);
    document.getElementById('kr-faiz').textContent = fmt(toplamFaiz);
    document.getElementById('kr-genel-toplam').textContent = fmt(pesinat + toplam);
    sonuc.classList.remove('hidden');
    if (emptyHint) emptyHint.classList.add('hidden');
}

function showToast(message, type) {
    const container = document.getElementById('toast-container');

    // Eski toast'ları temizle
    container.innerHTML = '';

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️'
    };

    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.innerHTML = '<span>' + (icons[type] || '') + '</span><span>' + escapeHtml(message) + '</span>';
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
