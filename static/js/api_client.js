/**
 * Scholar Lens — Unified P08 Institutional API Client & UI Integrations
 *
 * Provides a canonical client for all 9 P08 JSON endpoints defined in scholar_lens/api.py:
 *   1. /api/researchers/        (M1 Profiles directory)
 *   2. /api/publications/       (M2 Publications register)
 *   3. /api/search/expertise/   (M3 Full-text expertise search)
 *   4. /api/openings/           (M4 Research openings & opportunities)
 *   5. /api/projects/           (M8 Projects & milestones)
 *   6. /api/facilities/         (M6 Facilities catalogue)
 *   7. /api/bookings/           (M6 Facility reservations)
 *   8. /api/funding-calls/      (M7 Funding opportunities)
 *   9. /api/analytics/research/ (M9 Research office & Dean confidential metrics)
 *
 * Features:
 *   - Automatic CSRF token attachment
 *   - Exponential backoff retry for network resilience
 *   - Session expiry (HTTP 401) detection and graceful feedback
 *   - Debounced live search binding with loading, empty, and error states
 *   - Global header instant search integration
 */
(function(window, document) {
    'use strict';

    // Canonical API Endpoints Registry
    const ENDPOINTS = {
        RESEARCHERS: '/api/researchers/',
        PUBLICATIONS: '/api/publications/',
        EXPERTISE_SEARCH: '/api/search/expertise/',
        OPENINGS: '/api/openings/',
        PROJECTS: '/api/projects/',
        FACILITIES: '/api/facilities/',
        BOOKINGS: '/api/bookings/',
        FUNDING_CALLS: '/api/funding-calls/',
        RESEARCH_ANALYTICS: '/api/analytics/research/'
    };

    function getCsrfToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
    }

    async function request(endpoint, options = {}) {
        const config = {
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...(options.headers || {})
            },
            ...options
        };

        const method = (config.method || 'GET').toUpperCase();
        if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
            const csrfToken = getCsrfToken();
            if (csrfToken) {
                config.headers['X-CSRFToken'] = csrfToken;
            }
            if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
                config.headers['Content-Type'] = 'application/json';
                config.body = JSON.stringify(config.body);
            }
        }

        let retries = options.retries || 0;
        let lastError = null;

        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                const response = await fetch(endpoint, config);

                if (response.status === 401) {
                    const err = new Error('Session expired or authentication required. Please sign in again.');
                    err.status = 401;
                    throw err;
                }

                if (!response.ok) {
                    let errorData;
                    try {
                        errorData = await response.json();
                    } catch (e) {
                        errorData = { detail: response.statusText };
                    }
                    const err = new Error(errorData.error || errorData.detail || `Request failed (HTTP ${response.status})`);
                    err.status = response.status;
                    err.data = errorData;
                    throw err;
                }
                return await response.json();
            } catch (err) {
                lastError = err;
                if (attempt < retries && (!err.status || err.status >= 500)) {
                    await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 400));
                    continue;
                }
                throw err;
            }
        }
        throw lastError;
    }

    function buildQuery(params = {}) {
        const q = new URLSearchParams();
        Object.entries(params).forEach(([key, val]) => {
            if (val !== undefined && val !== null && val !== '') {
                q.append(key, val);
            }
        });
        const str = q.toString();
        return str ? `?${str}` : '';
    }

    const ScholarLensAPI = {
        ENDPOINTS,

        // 1. M1: Researcher Profiles Directory
        getResearchers(params = {}) {
            return request(`${ENDPOINTS.RESEARCHERS}${buildQuery(params)}`);
        },

        // 2. M2: Publications Register
        getPublications(params = {}) {
            return request(`${ENDPOINTS.PUBLICATIONS}${buildQuery(params)}`);
        },

        // 3. M3: Weighted Expertise Search
        searchExpertise(params = {}) {
            return request(`${ENDPOINTS.EXPERTISE_SEARCH}${buildQuery(params)}`);
        },

        // 4. M4: Research Openings & Opportunities
        getOpenings(params = {}) {
            return request(`${ENDPOINTS.OPENINGS}${buildQuery(params)}`);
        },
        // Alias for backwards compatibility
        getOpportunities(params = {}) {
            return this.getOpenings(params);
        },

        // 5. M8: Research Projects & Milestone Status
        getProjects(params = {}) {
            return request(`${ENDPOINTS.PROJECTS}${buildQuery(params)}`);
        },

        // 6. M6: Facilities Catalogue & Operating Hours
        getFacilities(params = {}) {
            return request(`${ENDPOINTS.FACILITIES}${buildQuery(params)}`);
        },

        // 7. M6: Facility Reservations & Bookings
        getBookings(params = {}) {
            return request(`${ENDPOINTS.BOOKINGS}${buildQuery(params)}`);
        },

        // 8. M7: Funding Opportunities Register
        getFundingCalls(params = {}) {
            return request(`${ENDPOINTS.FUNDING_CALLS}${buildQuery(params)}`);
        },

        // 9. M9: Research Analytics (Dean confidential)
        getResearchAnalytics(params = {}) {
            return request(`${ENDPOINTS.RESEARCH_ANALYTICS}${buildQuery(params)}`);
        },
        // Alias for backwards compatibility
        getAnalyticsOverview(params = {}) {
            return this.getResearchAnalytics(params);
        },

        // Utility: Debounce for fast input triggers
        debounce(func, wait = 250) {
            let timeout;
            return function(...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        },

        // --- Frontend Consumer: Global Header Live Instant Search ---
        initHeaderLiveSearch() {
            const searchForm = document.querySelector('.ums-header-search');
            if (!searchForm) return;

            const input = searchForm.querySelector('input[name="q"]');
            if (!input) return;

            // Create dropdown container
            let dropdown = document.getElementById('umsLiveSearchDropdown');
            if (!dropdown) {
                dropdown = document.createElement('div');
                dropdown.id = 'umsLiveSearchDropdown';
                dropdown.className = 'ums-live-search-dropdown shadow-lg';
                dropdown.style.cssText = `
                    position: absolute;
                    top: calc(100% + 6px);
                    left: 0;
                    right: 0;
                    background: #FFFFFF;
                    border: 1px solid var(--border, #E2E4E8);
                    border-radius: var(--radius-md, 8px);
                    max-height: 420px;
                    overflow-y: auto;
                    z-index: 1000;
                    display: none;
                `;
                searchForm.style.position = 'relative';
                searchForm.appendChild(dropdown);
            }

            const onInput = this.debounce(async () => {
                const query = input.value.trim();
                if (query.length < 2) {
                    dropdown.style.display = 'none';
                    dropdown.innerHTML = '';
                    return;
                }

                // Show loading state
                dropdown.style.display = 'block';
                dropdown.innerHTML = `
                    <div class="p-3 text-center text-muted small">
                        <span class="spinner-border spinner-border-sm me-2" role="status" style="width: 14px; height: 14px; border-width: 2px;"></span>
                        Searching researchers and publications...
                    </div>
                `;

                try {
                    // Fetch in parallel: expertise search + publications
                    const [expertiseRes, pubRes] = await Promise.allSettled([
                        ScholarLensAPI.searchExpertise({ q: query, limit: 5 }),
                        ScholarLensAPI.getPublications({ limit: 5 })
                    ]);

                    let html = '';
                    let totalMatches = 0;

                    // 1. Researcher Matches
                    if (expertiseRes.status === 'fulfilled' && expertiseRes.value && expertiseRes.value.results) {
                        const researchers = expertiseRes.value.results;
                        if (researchers.length > 0) {
                            totalMatches += researchers.length;
                            html += `<div class="p-2 bg-light border-bottom text-uppercase fw-bold text-muted small" style="font-size: 11px; letter-spacing: 0.05em;">Researchers (${researchers.length})</div>`;
                            researchers.forEach(r => {
                                html += `
                                    <a href="/researchers/${r.id}/" class="d-flex justify-content-between align-items-center p-2 text-decoration-none border-bottom text-dark hover-bg-light">
                                        <div>
                                            <div class="fw-bold small text-dark">${r.name || r.username}</div>
                                            <div class="text-secondary" style="font-size: 11.5px;">${r.department || 'Department unassigned'} &bull; ${r.headline || 'Scholar'}</div>
                                        </div>
                                        <span class="badge bg-light text-dark border small" style="font-size: 10px;">Profile ➔</span>
                                    </a>
                                `;
                            });
                        }
                    }

                    // 2. Publication Matches (Client filtered query match)
                    if (pubRes.status === 'fulfilled' && pubRes.value && pubRes.value.results) {
                        const qLower = query.toLowerCase();
                        const matchingPubs = pubRes.value.results.filter(p =>
                            (p.title && p.title.toLowerCase().includes(qLower)) ||
                            (p.venue && p.venue.toLowerCase().includes(qLower))
                        );
                        if (matchingPubs.length > 0) {
                            totalMatches += matchingPubs.length;
                            html += `<div class="p-2 bg-light border-bottom text-uppercase fw-bold text-muted small" style="font-size: 11px; letter-spacing: 0.05em;">Publications (${matchingPubs.length})</div>`;
                            matchingPubs.forEach(p => {
                                html += `
                                    <a href="/papers/${p.id}/" class="d-block p-2 text-decoration-none border-bottom text-dark hover-bg-light">
                                        <div class="fw-bold small text-dark text-truncate">${p.title}</div>
                                        <div class="text-secondary" style="font-size: 11px;">${p.year || ''} &bull; ${p.venue || 'Scholarly Paper'}</div>
                                    </a>
                                `;
                            });
                        }
                    }

                    // Empty state
                    if (totalMatches === 0) {
                        dropdown.innerHTML = `
                            <div class="p-3 text-center text-muted small">
                                <div>🔍 No immediate matches found for "<strong>${query}</strong>"</div>
                                <div class="mt-1" style="font-size: 11px;">Press Enter to run a comprehensive system search.</div>
                            </div>
                        `;
                    } else {
                        html += `
                            <div class="p-2 text-center bg-light border-top">
                                <button type="submit" class="btn btn-sm btn-link text-decoration-none text-muted small py-0">View all results in search hub ➔</button>
                            </div>
                        `;
                        dropdown.innerHTML = html;
                    }
                } catch (err) {
                    dropdown.innerHTML = `
                        <div class="p-3 text-center text-danger small">
                            ${err.message || 'Error executing live search.'}
                            <div class="mt-1"><a href="javascript:void(0)" onclick="this.closest('.ums-live-search-dropdown').style.display='none'" class="text-secondary">Dismiss</a></div>
                        </div>
                    `;
                }
            }, 250);

            input.addEventListener('input', onInput);

            // Close on click outside or Escape
            document.addEventListener('click', (e) => {
                if (!searchForm.contains(e.target)) {
                    dropdown.style.display = 'none';
                }
            });

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    dropdown.style.display = 'none';
                }
            });

            input.addEventListener('focus', () => {
                if (input.value.trim().length >= 2 && dropdown.innerHTML.trim() !== '') {
                    dropdown.style.display = 'block';
                }
            });
        }
    };

    // Auto-initialize header live search on DOM load
    document.addEventListener('DOMContentLoaded', () => {
        try {
            ScholarLensAPI.initHeaderLiveSearch();
        } catch (e) {
            console.warn('ScholarLensAPI auto-init error:', e);
        }
    });

    window.ScholarLensAPI = ScholarLensAPI;
})(window, document);
