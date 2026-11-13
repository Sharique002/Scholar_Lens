/**
 * Chart defaults for Scholar Lens: one calm palette, Inter, light gridlines.
 */
const SL_CHART_COLORS = ['#4338CA', '#0F766E', '#D97706', '#64748B', '#7C3AED', '#0369A1', '#BE123C', '#15803D'];

if (window.Chart) {
    Chart.defaults.font.family = "'Inter', ui-sans-serif, system-ui, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = '#64748B';
    Chart.defaults.borderColor = '#E2E8F0';
    Chart.defaults.plugins.legend.labels.boxWidth = 10;
    Chart.defaults.plugins.legend.labels.boxHeight = 10;
    Chart.defaults.plugins.tooltip.backgroundColor = '#0F172A';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        Chart.defaults.animation = false;
    }
}

function slReadJson(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { console.error('Bad chart data in #' + id, e); return null; }
}

function initResearchAreasChart() {
    const canvas = document.getElementById('researchAreasChart');
    const rawData = slReadJson('researchAreasData');
    if (!canvas || !rawData || !window.Chart) return;
    const labels = Object.keys(rawData);
    if (labels.length === 0) return;
    new Chart(canvas, {
        type: 'doughnut',
        data: { labels, datasets: [{ data: Object.values(rawData), backgroundColor: SL_CHART_COLORS, borderColor: '#fff', borderWidth: 2 }] },
        options: { maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, cutout: '68%' },
    });
}

/** Bar/line chart from a json_script payload shaped {labels: [...], values: [...]}. */
function initSeriesChart(canvasId, dataId, type, label) {
    const canvas = document.getElementById(canvasId);
    const data = slReadJson(dataId);
    if (!canvas || !data || !window.Chart || !data.labels || data.labels.length === 0) return;
    new Chart(canvas, {
        type: type || 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: label || '',
                data: data.values,
                backgroundColor: type === 'line' ? 'rgba(67, 56, 202, 0.08)' : '#4338CA',
                borderColor: '#4338CA',
                borderWidth: type === 'line' ? 2 : 0,
                borderRadius: 4,
                maxBarThickness: 28,
                fill: type === 'line',
                tension: 0.3,
                pointRadius: type === 'line' ? 3 : 0,
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#F1F5F9' } },
            },
        },
    });
}
