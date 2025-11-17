// Premium Analytics Dashboard - ML-Powered JavaScript
const API_BASE_URL = 'http://localhost:5000/api';

// Global chart instances
let charts = {};

// Chart.js default configuration
Chart.defaults.color = '#a8a8b3';
Chart.defaults.font.family = 'Inter, sans-serif';
Chart.defaults.plugins.legend.display = false;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(26, 26, 46, 0.95)';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.padding = 12;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Premium Analytics Dashboard initializing...');
    initializeDashboard();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            console.log('Refreshing dashboard...');
            refreshDashboard();
        });
    }
    
    const dateFilter = document.getElementById('dateFilter');
    if (dateFilter) {
        dateFilter.addEventListener('change', () => {
            console.log('Date filter changed:', dateFilter.value);
            applyFilters();
        });
    }

    const darkToggle = document.getElementById('darkToggle');
    if (darkToggle) {
        darkToggle.addEventListener('click', () => {
            // Placeholder for dark mode toggle
            console.log('Theme toggle clicked');
        });
    }
}

// Initialize dashboard
async function initializeDashboard() {
    try {
        showLoading();
        await loadDashboardData();
        hideLoading();
        updateTimestamp();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        hideLoading();
    }
}

// Refresh dashboard
async function refreshDashboard() {
    destroyCharts();
    await initializeDashboard();
}

// Apply filters
function applyFilters() {
    refreshDashboard();
}

// Load all dashboard data
async function loadDashboardData() {
    try {
        const days = document.getElementById('dateFilter')?.value || '30';
        
        // Load data in parallel
        const [kpis, mlPerf, forecast, clv, delivery, recommendations] = await Promise.all([
            fetchData(`${API_BASE_URL}/kpis?days=${days}`),
            fetchData(`${API_BASE_URL}/ml/model-performance`),
            fetchData(`${API_BASE_URL}/advanced/revenue-forecast`),
            fetchData(`${API_BASE_URL}/advanced/customer-lifetime-value`),
            fetchData(`${API_BASE_URL}/advanced/delivery-performance`),
            fetchData(`${API_BASE_URL}/advanced/product-recommendations`)
        ]);
        
        // Render all sections
        renderKPIs(kpis);
        renderMLPerformance(mlPerf);
        renderForecast(forecast);
        renderCLV(clv);
        renderDelivery(delivery);
        renderRecommendations(recommendations);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Fetch helper
async function fetchData(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
}

// Render KPIs
function renderKPIs(data) {
    document.getElementById('totalRevenue').textContent = formatCurrency(data.total_revenue);
    document.getElementById('totalOrders').textContent = formatNumber(data.total_orders);
    document.getElementById('totalCustomers').textContent = formatNumber(data.unique_customers);
    document.getElementById('avgOrderValue').textContent = formatCurrency(data.avg_order_value);
}

// Render ML Performance
function renderMLPerformance(data) {
    if (data.error) {
        console.warn('ML metrics not available:', data.error);
        return;
    }
    
    const r2 = data.regression?.r2 || 0;
    const mae = data.regression?.mae || 0;
    const roc = data.classification?.roc_auc || 0;
    const samples = data.samples || 0;
    
    document.getElementById('mlR2').textContent = r2.toFixed(3);
    document.getElementById('mlMAE').textContent = mae.toFixed(2);
    document.getElementById('mlROC').textContent = roc.toFixed(4);
    document.getElementById('mlSamples').textContent = formatNumber(samples);
    
    // Animate progress bars
    setTimeout(() => {
        document.getElementById('mlR2Bar').style.width = `${r2 * 100}%`;
        document.getElementById('mlROCBar').style.width = `${roc * 100}%`;
    }, 100);
}

// Render Revenue Forecast
function renderForecast(data) {
    if (data.error || !data.forecast_dates) {
        console.warn('Forecast data not available');
        return;
    }
    
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return;
    
    // Combine historical and forecast
    const allDates = [...data.historical_dates, ...data.forecast_dates];
    const historicalData = [...data.historical_revenue, ...Array(data.forecast_dates.length).fill(null)];
    const forecastData = [...Array(data.historical_dates.length).fill(null), ...data.forecast_revenue];
    
    charts.forecast = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allDates,
            datasets: [
                {
                    label: 'Historical Revenue',
                    data: historicalData,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: '30-Day Forecast',
                    data: forecastData,
                    borderColor: '#38ef7d',
                    backgroundColor: 'rgba(56, 239, 125, 0.1)',
                    borderWidth: 3,
                    borderDash: [5, 5],
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            size: 13,
                            weight: 600
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// Render Customer Lifetime Value
function renderCLV(data) {
    if (data.error || !data.segments) {
        console.warn('CLV data not available');
        return;
    }
    
    const ctx = document.getElementById('clvChart');
    if (!ctx) return;
    
    charts.clv = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.segments,
            datasets: [{
                label: 'Average CLV',
                data: data.avg_clv,
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(79, 172, 254, 0.8)',
                    'rgba(56, 239, 125, 0.8)',
                    'rgba(242, 153, 74, 0.8)'
                ],
                borderRadius: 8,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Avg CLV: ${formatCurrency(context.parsed.y)}`;
                        },
                        footer: function(items) {
                            const index = items[0].dataIndex;
                            return `Customers: ${formatNumber(data.count[index])}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Render Delivery Performance
function renderDelivery(data) {
    if (data.error || !data.states) {
        console.warn('Delivery data not available');
        return;
    }
    
    const ctx = document.getElementById('deliveryChart');
    if (!ctx) return;
    
    charts.delivery = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.states,
            datasets: [{
                label: 'Avg Delivery Days',
                data: data.avg_delivery_days,
                backgroundColor: 'rgba(242, 153, 74, 0.8)',
                borderRadius: 8,
                borderWidth: 0
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.x.toFixed(1)} days avg`;
                        },
                        footer: function(items) {
                            const index = items[0].dataIndex;
                            return `Orders: ${formatNumber(data.order_count[index])}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Render Product Recommendations
function renderRecommendations(data) {
    if (data.error || !data.pairs) {
        console.warn('Recommendations data not available');
        return;
    }
    
    const container = document.getElementById('recommendationsGrid');
    if (!container) return;
    
    container.innerHTML = '';
    
    data.pairs.slice(0, 6).forEach(pair => {
        const card = document.createElement('div');
        card.className = 'recommendation-card';
        card.innerHTML = `
            <div class="rec-products">
                <div class="rec-product">${truncate(pair.product_a, 20)}</div>
                <div class="rec-arrow">→</div>
                <div class="rec-product">${truncate(pair.product_b, 20)}</div>
            </div>
            <div class="rec-stats">
                <div class="rec-frequency">Bought together ${pair.frequency}× times</div>
                <div class="rec-confidence">${pair.confidence}% confidence</div>
            </div>
        `;
        container.appendChild(card);
    });
}

// Helper Functions
function formatCurrency(value) {
    if (value === null || value === undefined) return 'R$ 0.00';
    return `R$ ${parseFloat(value).toLocaleString('pt-BR', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
    })}`;
}

function formatNumber(value) {
    if (value === null || value === undefined) return '0';
    return parseFloat(value).toLocaleString('pt-BR');
}

function truncate(str, maxLen) {
    if (!str) return '';
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

function showLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.style.display = 'flex';
}

function hideLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.style.display = 'none';
}

function destroyCharts() {
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    charts = {};
}

function updateTimestamp() {
    const el = document.getElementById('lastUpdate');
    if (el) {
        el.textContent = new Date().toLocaleString('pt-BR', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

console.log('✅ Premium Dashboard JS loaded');
