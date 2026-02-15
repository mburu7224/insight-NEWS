/**
 * Israel News Module - Frontend JavaScript
 */

const DEFAULT_API_BASE_URL = 'http://localhost:3000/api';
const AUTO_REFRESH_INTERVAL = 60000; // 1 minute

function readMeta(name) {
    const element = document.querySelector(`meta[name="${name}"]`);
    return element ? element.getAttribute('content') : '';
}

function getApiBaseUrl() {
    const configured = (window.ISRAEL_NEWS_CONFIG && window.ISRAEL_NEWS_CONFIG.apiBaseUrl)
        || localStorage.getItem('israelNewsApiBaseUrl')
        || readMeta('api-base-url')
        || DEFAULT_API_BASE_URL;
    return configured.replace(/\/+$/, '');
}

function getApiKey() {
    return (window.ISRAEL_NEWS_CONFIG && window.ISRAEL_NEWS_CONFIG.apiKey)
        || localStorage.getItem('israelNewsApiKey')
        || readMeta('api-key')
        || '';
}

const API_BASE_URL = getApiBaseUrl();
const API_KEY = getApiKey();

// State
let currentCategory = 'all';
let currentPage = 1;
let articles = [];
let isLoading = false;
let eventSource = null;
let autoRefreshEnabled = true;
let lastRefresh = Date.now();

// DOM Elements
const newsGrid = document.getElementById('news-grid');
const loadingElement = document.getElementById('loading');
const errorElement = document.getElementById('error');
const errorMessageElement = document.getElementById('error-message');
const retryButton = document.getElementById('retry-btn');
const loadMoreButton = document.getElementById('load-more');
const tabButtons = document.querySelectorAll('.tab-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    if (retryButton) {
        retryButton.addEventListener('click', () => loadNews());
    }
    if (loadMoreButton) {
        loadMoreButton.addEventListener('click', () => {
            currentPage += 1;
            loadMoreArticles();
        });
    }
    loadNews();
    initRealTimeUpdates();
});

function initTabs() {
    tabButtons.forEach((button) => {
        button.addEventListener('click', () => {
            tabButtons.forEach((btn) => btn.classList.remove('active'));
            button.classList.add('active');

            currentCategory = button.dataset.category;
            currentPage = 1;
            articles = [];
            loadNews();
        });
    });
}

function getCategoryEndpoint() {
    return currentCategory === 'all'
        ? `${API_BASE_URL}/general`
        : `${API_BASE_URL}/${currentCategory}`;
}

async function fetchArticlesPage(page = 1, limit = 20) {
    const endpoint = getCategoryEndpoint();
    const url = new URL(endpoint, window.location.origin);
    url.searchParams.set('limit', String(limit));
    url.searchParams.set('page', String(page));

    const headers = {};
    if (API_KEY) {
        headers['x-api-key'] = API_KEY;
    }

    const response = await fetch(url.toString(), { headers });
    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            throw new Error('Unauthorized: missing or invalid API key.');
        }
        throw new Error('Failed to fetch news');
    }

    const data = await response.json();
    if (!data.success) {
        throw new Error(data.error || 'Unknown error');
    }
    return data.data || [];
}

async function loadNews() {
    if (isLoading) return;

    isLoading = true;
    showLoading();
    hideError();

    try {
        const fetchedArticles = await fetchArticlesPage(1, 20);
        currentPage = 1;
        articles = fetchedArticles;
        renderArticles();
        toggleLoadMore(fetchedArticles.length >= 20);
    } catch (error) {
        console.error('Error loading news:', error);
        showError(error.message);
    } finally {
        isLoading = false;
        hideLoading();
    }
}

async function loadMoreArticles() {
    if (isLoading) return;

    isLoading = true;
    loadMoreButton.textContent = 'Loading...';
    loadMoreButton.disabled = true;

    try {
        const nextPageArticles = await fetchArticlesPage(currentPage, 20);
        articles = [...articles, ...nextPageArticles];
        renderArticles();
        toggleLoadMore(nextPageArticles.length >= 20);
    } catch (error) {
        console.error('Error loading more news:', error);
    } finally {
        isLoading = false;
        loadMoreButton.textContent = 'Load More';
        loadMoreButton.disabled = false;
    }
}

function renderArticles() {
    newsGrid.innerHTML = '';

    if (articles.length === 0) {
        const noResults = document.createElement('p');
        noResults.className = 'no-results';
        noResults.textContent = 'No news articles found.';
        newsGrid.appendChild(noResults);
        return;
    }

    articles.forEach((article) => {
        const card = createNewsCard(article);
        newsGrid.appendChild(card);
    });
}

function createNewsCard(article) {
    const card = document.createElement('div');
    card.className = 'news-card';

    if (article.image_url) {
        const safeImageUrl = toSafeUrl(article.image_url);
        if (safeImageUrl) {
            const image = document.createElement('img');
            image.src = safeImageUrl;
            image.alt = article.title || 'News image';
            image.className = 'news-card-image';
            image.loading = 'lazy';
            image.addEventListener('error', () => {
                image.style.display = 'none';
            });
            card.appendChild(image);
        }
    }

    const content = document.createElement('div');
    content.className = 'news-card-content';

    const category = document.createElement('span');
    category.className = 'news-card-category';
    category.textContent = article.category_name || article.category || 'General';
    content.appendChild(category);

    const title = document.createElement('h3');
    title.className = 'news-card-title';
    const link = document.createElement('a');
    link.href = toSafeUrl(article.url) || '#';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = article.title || 'Untitled';
    title.appendChild(link);
    content.appendChild(title);

    const description = document.createElement('p');
    description.className = 'news-card-description';
    description.textContent = article.description || '';
    content.appendChild(description);

    if (Array.isArray(article.summary) && article.summary.length) {
        const summaryList = document.createElement('ul');
        summaryList.className = 'news-card-summary';
        article.summary.slice(0, 3).forEach((bullet) => {
            const item = document.createElement('li');
            item.textContent = String(bullet);
            summaryList.appendChild(item);
        });
        content.appendChild(summaryList);
    }

    const meta = document.createElement('div');
    meta.className = 'news-card-meta';
    const source = document.createElement('span');
    source.className = 'news-card-source';
    source.textContent = article.source || 'Unknown';
    const date = document.createElement('span');
    date.className = 'news-card-date';
    date.textContent = formatDate(article.published_at);
    meta.appendChild(source);
    meta.appendChild(date);
    content.appendChild(meta);

    card.appendChild(content);
    return card;
}

function formatDate(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function toSafeUrl(value) {
    if (!value) return '';
    try {
        const parsed = new URL(value, window.location.origin);
        if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
            return parsed.toString();
        }
        return '';
    } catch (_error) {
        return '';
    }
}

function showLoading() {
    loadingElement.style.display = 'block';
    newsGrid.style.display = 'none';
}

function hideLoading() {
    loadingElement.style.display = 'none';
    newsGrid.style.display = 'grid';
}

function showError(message) {
    if (errorMessageElement) {
        errorMessageElement.textContent = message || 'Failed to load news. Please try again later.';
    }
    errorElement.style.display = 'block';
    newsGrid.style.display = 'none';
}

function hideError() {
    errorElement.style.display = 'none';
}

function toggleLoadMore(visible) {
    loadMoreButton.style.display = visible ? 'inline-block' : 'none';
}

function initRealTimeUpdates() {
    if (!autoRefreshEnabled) return;
    const streamUrl = `${API_BASE_URL.replace(/\/api$/, '')}/api/stream`;

    try {
        eventSource = new EventSource(streamUrl);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'heartbeat') {
                    refreshNewsIfNeeded();
                } else if (data.type === 'new_article' && data.article) {
                    showNewArticleNotification(data.article);
                }
            } catch (e) {
                console.error('Error parsing SSE message:', e);
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            setTimeout(() => {
                if (autoRefreshEnabled) {
                    initRealTimeUpdates();
                }
            }, 5000);
        };
    } catch (e) {
        console.error('Error initializing SSE:', e);
    }
}

function refreshNewsIfNeeded() {
    const now = Date.now();
    if (now - lastRefresh >= AUTO_REFRESH_INTERVAL) {
        lastRefresh = now;
        fetchNewsSilently();
    }
}

async function fetchNewsSilently() {
    try {
        const latest = await fetchArticlesPage(1, 20);
        const hasNew = latest.length > 0 && (!articles.length || latest[0].id !== articles[0].id);
        if (hasNew) {
            articles = latest;
            currentPage = 1;
            renderArticles();
            toggleLoadMore(latest.length >= 20);
        }
    } catch (e) {
        // Silent fail for background refresh.
    }
}

function showNewArticleNotification(article) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';

    const label = document.createElement('span');
    const title = String(article.title || 'New article');
    label.textContent = `New article: ${title.substring(0, 50)}${title.length > 50 ? '...' : ''}`;

    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'View';
    button.addEventListener('click', () => {
        toast.remove();
        loadNews();
    });

    toast.appendChild(label);
    toast.appendChild(button);
    document.body.appendChild(toast);

    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

window.addEventListener('beforeunload', () => {
    if (eventSource) {
        eventSource.close();
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        loadNews,
        renderArticles,
        createNewsCard
    };
}
