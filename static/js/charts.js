/**
 * Charts Initialization for Scholar Lens
 */

function initResearchAreasChart() {
    const canvas = document.getElementById('researchAreasChart');
    const dataScript = document.getElementById('researchAreasData');
    
    if (!canvas || !dataScript) return;
    
    try {
        const rawData = JSON.parse(dataScript.textContent);
        const labels = Object.keys(rawData);
        const values = Object.values(rawData);
        
        if (labels.length === 0) return;
        
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#2563eb', // primary
                        '#7c3aed', // secondary
                        '#059669', // success
                        '#d97706', // warning
                        '#dc2626', // danger
                        '#0284c7', // info
                        '#9333ea', // purple
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            font: {
                                family: "'Inter', sans-serif",
                                size: 12
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    } catch (e) {
        console.error("Error initializing research areas chart:", e);
    }
}

// Function placeholders for other potential charts
function initActivityChart(canvasId, dataUrl) {
    // To be implemented
}

function initScoreChart(canvasId, data) {
    // To be implemented
}
