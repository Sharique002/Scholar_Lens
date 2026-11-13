/**
 * Scholar Lens — application shell behaviour.
 * Progressive enhancement only: every page works without this file.
 */
document.addEventListener('DOMContentLoaded', () => {
    const root = document.documentElement;
    const sidebar = document.getElementById('navLinks');
    const backdrop = document.getElementById('sidebarBackdrop');
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const collapseBtn = document.getElementById('sidebarCollapse');

    // 1. Mobile navigation drawer
    const setDrawer = (open) => {
        if (!sidebar) return;
        sidebar.classList.toggle('active', open);
        if (mobileBtn) {
            mobileBtn.setAttribute('aria-expanded', String(open));
            mobileBtn.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
        }
        if (backdrop) {
            backdrop.hidden = !open;
            requestAnimationFrame(() => backdrop.classList.toggle('is-visible', open));
        }
        if (open) {
            const first = sidebar.querySelector('a');
            if (first) first.focus();
        }
    };
    if (mobileBtn && sidebar) {
        mobileBtn.addEventListener('click', () => setDrawer(!sidebar.classList.contains('active')));
        if (backdrop) backdrop.addEventListener('click', () => setDrawer(false));
        sidebar.addEventListener('click', (e) => { if (e.target.closest('a')) setDrawer(false); });
    }

    // 2. Desktop sidebar collapse (state restored in <head> to avoid a flash)
    if (collapseBtn && sidebar) {
        const apply = (collapsed) => {
            root.classList.toggle('sb-collapsed', collapsed);
            sidebar.classList.toggle('is-collapsed', collapsed);
            collapseBtn.setAttribute('aria-expanded', String(!collapsed));
            collapseBtn.setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
            collapseBtn.title = collapsed ? 'Expand sidebar' : 'Collapse sidebar';
        };
        apply(root.classList.contains('sb-collapsed'));
        collapseBtn.addEventListener('click', () => {
            const collapsed = !root.classList.contains('sb-collapsed');
            apply(collapsed);
            try { localStorage.setItem('ums-sidebar', collapsed ? '1' : '0'); } catch (e) {}
        });
    }

    // 3. Dropdown menus (click, Esc, outside click)
    const dropdowns = document.querySelectorAll('.nav-dropdown');
    const closeDropdown = (d) => {
        d.classList.remove('active');
        const t = d.querySelector('.dropdown-toggle');
        if (t) t.setAttribute('aria-expanded', 'false');
    };
    dropdowns.forEach((dropdown) => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        if (!toggle) return;
        toggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropdowns.forEach((d) => { if (d !== dropdown) closeDropdown(d); });
            const open = dropdown.classList.toggle('active');
            toggle.setAttribute('aria-expanded', String(open));
            if (open) {
                const first = dropdown.querySelector('.dropdown-menu a, .dropdown-menu button');
                if (first && e.detail === 0) first.focus(); // keyboard activation moves focus into the menu
            }
        });
    });
    document.addEventListener('click', (e) => {
        dropdowns.forEach((d) => { if (!d.contains(e.target)) closeDropdown(d); });
    });

    // 4. Global keys: Esc closes overlays, "/" focuses search
    const search = document.getElementById('globalSearch');
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            dropdowns.forEach((d) => {
                if (d.classList.contains('active')) {
                    closeDropdown(d);
                    const t = d.querySelector('.dropdown-toggle');
                    if (t) t.focus();
                }
            });
            if (sidebar && sidebar.classList.contains('active')) {
                setDrawer(false);
                if (mobileBtn) mobileBtn.focus();
            }
        }
        const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable;
        if (e.key === '/' && !typing && search && search.offsetParent !== null) {
            e.preventDefault();
            search.focus();
        }
    });

    // 5. Toasts (Django messages). Errors persist until dismissed.
    document.querySelectorAll('.toast-region .alert, .alert-dismissible').forEach((alert) => {
        const dismiss = () => {
            alert.classList.add('is-leaving');
            setTimeout(() => alert.remove(), 200);
        };
        const closeBtn = alert.querySelector('.close-alert');
        if (closeBtn) closeBtn.addEventListener('click', dismiss);
        if (alert.closest('.toast-region') && !alert.hasAttribute('data-persist')) {
            let timer = setTimeout(dismiss, 6000);
            alert.addEventListener('mouseenter', () => clearTimeout(timer));
            alert.addEventListener('mouseleave', () => { timer = setTimeout(dismiss, 3000); });
        }
    });

    // 6. Tabs (.tab-btn[data-target]) with ARIA state
    document.querySelectorAll('.tab-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const container = btn.closest('.tabs-container') || document;
            container.querySelectorAll('.tab-btn').forEach((b) => { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); });
            container.querySelectorAll('.tab-content').forEach((c) => c.classList.remove('active'));
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
            const target = document.getElementById(btn.getAttribute('data-target'));
            if (target) target.classList.add('active');
        });
    });

    // 6b. Bootstrap-markup tabs (data-bs-toggle="tab") — templates use this markup without Bootstrap's JS
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach((tab) => {
        const list = tab.closest('[role="tablist"], .nav-tabs, .nav');
        const tabs = () => Array.from(list ? list.querySelectorAll('[data-bs-toggle="tab"]') : [tab]);
        const panelOf = (t) => document.querySelector(t.getAttribute('data-bs-target') || t.getAttribute('href'));
        const activate = (t, focus) => {
            tabs().forEach((other) => {
                const on = other === t;
                other.classList.toggle('active', on);
                other.setAttribute('aria-selected', String(on));
                other.tabIndex = on ? 0 : -1;
                const p = panelOf(other);
                if (p) { p.classList.toggle('active', on); p.classList.toggle('show', on); }
            });
            if (focus) t.focus();
        };
        const p = panelOf(tab);
        if (p) {
            p.setAttribute('role', 'tabpanel');
            if (tab.id) p.setAttribute('aria-labelledby', tab.id);
            tab.setAttribute('aria-controls', p.id);
        }
        tab.setAttribute('role', 'tab');
        tab.setAttribute('aria-selected', String(tab.classList.contains('active')));
        tab.tabIndex = tab.classList.contains('active') ? 0 : -1;
        tab.addEventListener('click', (e) => { e.preventDefault(); activate(tab, false); });
        tab.addEventListener('keydown', (e) => {
            const all = tabs(), i = all.indexOf(tab);
            const next = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: all.length - 1 }[e.key];
            if (next === undefined) return;
            e.preventDefault();
            activate(all[(next + all.length) % all.length], true);
        });
    });
    document.querySelectorAll('[data-bs-dismiss="alert"]').forEach((btn) => {
        btn.addEventListener('click', () => { const a = btn.closest('.alert'); if (a) a.remove(); });
    });

    // 7. Confirmation dialog for destructive actions: <form data-confirm="..."> or <button data-confirm="...">
    const dialog = document.getElementById('confirmDialog');
    if (dialog) {
        dialog.querySelectorAll('[data-dialog-value]').forEach((b) => {
            b.addEventListener('click', () => dialog.close(b.getAttribute('data-dialog-value')));
        });
    }
    const askConfirm = (message, label) => new Promise((resolve) => {
        if (!dialog || typeof dialog.showModal !== 'function') { resolve(window.confirm(message)); return; }
        dialog.querySelector('#confirmMessage').textContent = message;
        dialog.querySelector('#confirmAccept').textContent = label || 'Confirm';
        dialog.returnValue = 'cancel';
        dialog.showModal();
        dialog.addEventListener('close', () => resolve(dialog.returnValue === 'confirm'), { once: true });
    });
    document.addEventListener('submit', (e) => {
        const form = e.target;
        const submitter = e.submitter;
        const source = (submitter && submitter.hasAttribute('data-confirm')) ? submitter : (form.hasAttribute('data-confirm') ? form : null);
        if (!source || form.dataset.confirmed === '1') return;
        e.preventDefault();
        e.stopImmediatePropagation();
        askConfirm(source.getAttribute('data-confirm') || 'Are you sure?', source.getAttribute('data-confirm-label')).then((ok) => {
            if (!ok) return;
            form.dataset.confirmed = '1';
            if (submitter && submitter.name) {
                const hidden = document.createElement('input');
                hidden.type = 'hidden';
                hidden.name = submitter.name;
                hidden.value = submitter.value;
                form.appendChild(hidden);
            }
            form.requestSubmit ? form.requestSubmit() : form.submit();
        });
    }, true);
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a[data-confirm]');
        if (!link) return;
        e.preventDefault();
        askConfirm(link.getAttribute('data-confirm'), link.getAttribute('data-confirm-label')).then((ok) => { if (ok) window.location.href = link.href; });
    });

    // 8. Prevent double submission: mark the clicked button busy (POST forms only)
    document.addEventListener('submit', (e) => {
        const form = e.target;
        if (e.defaultPrevented || (form.method || '').toLowerCase() !== 'post' || form.hasAttribute('data-no-busy') || form.target) return;
        const btn = e.submitter || form.querySelector('button[type="submit"], button:not([type])');
        if (!btn || btn.classList.contains('dropdown-item')) return;
        // Defer so the submitter's name/value is still sent with the request.
        setTimeout(() => {
            btn.classList.add('is-loading');
            btn.setAttribute('aria-busy', 'true');
            btn.disabled = true;
        }, 0);
    });
    // Restore buttons if the page is shown again from the back/forward cache.
    window.addEventListener('pageshow', (e) => {
        if (!e.persisted) return;
        document.querySelectorAll('.is-loading').forEach((b) => { b.classList.remove('is-loading'); b.disabled = false; b.removeAttribute('aria-busy'); });
    });

    // 9. Client-side sorting for tables that opt in with <table data-sortable>
    document.querySelectorAll('table[data-sortable]').forEach((table) => {
        const tbody = table.tBodies[0];
        if (!tbody) return;
        table.querySelectorAll('thead th').forEach((th, idx) => {
            if (th.hasAttribute('data-nosort')) return;
            th.setAttribute('data-sort', '');
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.innerHTML = th.innerHTML;
            th.innerHTML = '';
            th.appendChild(btn);
            btn.addEventListener('click', () => {
                const asc = th.getAttribute('aria-sort') !== 'ascending';
                table.querySelectorAll('thead th').forEach((h) => h.removeAttribute('aria-sort'));
                th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
                const key = (row) => {
                    const cell = row.cells[idx];
                    const raw = cell ? (cell.getAttribute('data-value') || cell.textContent.trim()) : '';
                    const n = parseFloat(raw.replace(/[^0-9.\-]/g, ''));
                    return raw !== '' && /^[\s\d.,%\-₹$€£]+$/.test(raw) && !isNaN(n) ? n : raw.toLowerCase();
                };
                const rows = Array.from(tbody.rows).filter((r) => r.cells.length > 1);
                rows.sort((a, b) => {
                    const x = key(a), y = key(b);
                    return (x > y ? 1 : x < y ? -1 : 0) * (asc ? 1 : -1);
                });
                rows.forEach((r) => tbody.appendChild(r));
            });
        });
    });

    // 9b. Stacked mobile tables: label each cell from its column header
    document.querySelectorAll('table.table-stack').forEach((table) => {
        const heads = Array.from(table.querySelectorAll('thead th')).map((th) => th.textContent.trim());
        table.querySelectorAll('tbody tr').forEach((tr) => {
            Array.from(tr.cells).forEach((td, i) => {
                if (!td.hasAttribute('data-label') && heads[i] && td.colSpan === 1) td.setAttribute('data-label', heads[i]);
            });
        });
    });

    // 10. Score rings (evaluation)
    document.querySelectorAll('.score-ring').forEach((ring) => {
        const score = parseFloat(ring.getAttribute('data-score') || 0);
        const pct = score <= 1 ? score * 100 : score;
        ring.style.setProperty('--score', `${pct}%`);
        if (pct >= 80) ring.style.setProperty('--primary', 'var(--sl-success)');
        else if (pct >= 50) ring.style.setProperty('--primary', 'var(--sl-warning)');
        else ring.style.setProperty('--primary', 'var(--sl-error)');
    });

    // 11. File input label preview
    document.querySelectorAll('input[type="file"]').forEach((input) => {
        input.addEventListener('change', (e) => {
            const label = input.nextElementSibling;
            if (label && label.classList.contains('custom-file-label')) {
                label.textContent = e.target.files[0] ? e.target.files[0].name : 'Choose file...';
            }
        });
    });
});

// CSRF token helper for fetch() calls
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
