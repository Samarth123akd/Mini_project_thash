// Professional Dashboard JavaScript
const API_BASE = 'http://localhost:5000/api';

// Chart instances
let charts = {};

// Chart.js global config
Chart.defaults.color = '#a8a8b3';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 52, 96, 0.95)';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(102, 126, 234, 0.5)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.cornerRadius = 12;
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.titleFont = { size: 13, weight: 700 };
Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };

// Initialize
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 Professional Dashboard initializing...');
    await loadDashboard();
    updateTimestamp();
});

// Load all data
async function loadDashboard() {
    try {
        showLoading();
        
        // Load data in parallel
        const [overview, sales, products, customers, payments, status, reviews, mlMetrics] = await Promise.all([
            fetchAPI('/overview'),
            fetchAPI('/sales-timeline'),
            fetchAPI('/top-products'),
            fetchAPI('/customer-distribution'),
            fetchAPI('/payment-methods'),
            fetchAPI('/order-status'),
            fetchAPI('/reviews-stats'),
            fetchAPI('/ml/metrics')
        ]);

        // Render KPIs
        if (overview.success) {
            renderKPIs(overview.data);
        }

        // Render ML metrics
        if (mlMetrics.success) {
            renderMLMetrics(mlMetrics.data);
        }

        // Render charts
        if (sales.success) {
            renderSalesChart(sales.data);
        }
        
        if (products.success) {
            renderProductsChart(products.data);
        }
        
        if (customers.success) {
            renderCustomersChart(customers.data);
        }
        
        if (payments.success) {
            renderPaymentsChart(payments.data);
        }
        
        if (status.success) {
            renderStatusChart(status.data);
        }
        
        if (reviews.success) {
            renderReviewsChart(reviews.data);
        }

        hideLoading();
    } catch (error) {
        console.error('Error loading dashboard:', error);
        hideLoading();
        alert('Error loading dashboard data. Please check console.');
    }
}

// Fetch from API
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(API_BASE + endpoint);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return { success: false, error: error.message };
    }
}

// Render KPIs
function renderKPIs(data) {
    document.getElementById('totalRevenue').textContent = formatCurrency(data.total_revenue || 0);
    document.getElementById('totalOrders').textContent = formatNumber(data.total_orders || 0);
    document.getElementById('totalCustomers').textContent = formatNumber(data.unique_customers || data.total_customers || 0);
    document.getElementById('totalProducts').textContent = formatNumber(data.total_products || 0);
}

// Render ML Metrics
function renderMLMetrics(data) {
    document.getElementById('mlR2').textContent = (data.r2_score || 0).toFixed(3);
    document.getElementById('mlMAE').textContent = (data.mae || 0).toFixed(2);
    document.getElementById('mlROC').textContent = (data.roc_auc || 0).toFixed(4);
    document.getElementById('mlSamples').textContent = formatNumber(data.samples || 0);
}

// Render Sales Chart
function renderSalesChart(data) {
    const ctx = document.getElementById('salesChart');
    if (!ctx) return;

    destroyChart('salesChart');

    charts.salesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates || [],
            datasets: [
                {
                    label: 'Revenue (R$)',
                    data: data.revenue || [],
                    borderColor: '#43e97b',
                    backgroundColor: 'rgba(67, 233, 123, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: 'Orders',
                    data: data.orders || [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    yAxisID: 'y1'
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
                        padding: 15,
                        font: { size: 12, weight: 600 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.datasetIndex === 0) {
                                label += formatCurrency(context.parsed.y);
                            } else {
                                label += formatNumber(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + formatNumber(value);
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    grid: { display: false },
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// Render Products Chart
function renderProductsChart(data) {
    const ctx = document.getElementById('productsChart');
    if (!ctx) return;

    destroyChart('productsChart');

    charts.productsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.categories || [],
            datasets: [{
                label: 'Revenue (R$)',
                data: data.revenue || [],
                backgroundColor: createGradient(ctx, ['#667eea', '#764ba2']),
                borderRadius: 8,
                borderWidth: 0
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.parsed.x);
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + formatNumber(value);
                        }
                    }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
}

// Render Customers Chart
function renderCustomersChart(data) {
    const ctx = document.getElementById('customersChart');
    if (!ctx) return;

    destroyChart('customersChart');

    charts.customersChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.states || [],
            datasets: [{
                label: 'Customers',
                data: data.counts || [],
                backgroundColor: createGradient(ctx, ['#4facfe', '#00f2fe']),
                borderRadius: 8,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatNumber(context.parsed.y) + ' customers';
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

// Render Payments Chart
function renderPaymentsChart(data) {
    const ctx = document.getElementById('paymentsChart');
    if (!ctx) return;

    destroyChart('paymentsChart');

    const colors = [
        '#667eea',
        '#43e97b',
        '#4facfe',
        '#fa709a',
        '#fee140'
    ];

    charts.paymentsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.types || [],
            datasets: [{
                data: data.values || [],
                backgroundColor: colors,
                borderWidth: 0,
                spacing: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + formatCurrency(context.parsed);
                        }
                    }
                }
            }
        }
    });
}

// Render Status Chart
function renderStatusChart(data) {
    const ctx = document.getElementById('statusChart');
    if (!ctx) return;

    destroyChart('statusChart');

    const colors = [
        '#43e97b',
        '#667eea',
        '#4facfe',
        '#fa709a',
        '#fee140',
        '#f093fb'
    ];

    charts.statusChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.statuses || [],
            datasets: [{
                data: data.counts || [],
                backgroundColor: colors,
                borderWidth: 0,
                spacing: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + formatNumber(context.parsed);
                        }
                    }
                }
            }
        }
    });
}

// Render Reviews Chart
function renderReviewsChart(data) {
    const ctx = document.getElementById('reviewsChart');
    if (!ctx) return;

    destroyChart('reviewsChart');

    charts.reviewsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: (data.scores || []).map(s => s + ' ⭐'),
            datasets: [{
                label: 'Reviews',
                data: data.counts || [],
                backgroundColor: createGradient(ctx, ['#f093fb', '#f5576c']),
                borderRadius: 8,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatNumber(context.parsed.y) + ' reviews';
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

// Helper: Create gradient
function createGradient(ctx, colors) {
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, colors[0]);
    gradient.addColorStop(1, colors[1]);
    return gradient;
}

// Helper: Destroy chart
function destroyChart(chartId) {
    if (charts[chartId]) {
        charts[chartId].destroy();
        delete charts[chartId];
    }
}

// Helper: Format currency
function formatCurrency(value) {
    if (value === null || value === undefined) return 'R$ 0.00';
    return 'R$ ' + parseFloat(value).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Helper: Format number
function formatNumber(value) {
    if (value === null || value === undefined) return '0';
    return parseFloat(value).toLocaleString('pt-BR');
}

// Helper: Show loading
function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
}

// Helper: Hide loading
function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

// Update timestamp
function updateTimestamp() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleString('pt-BR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Refresh dashboard
async function refreshDashboard() {
    console.log('🔄 Refreshing dashboard...');
    Object.values(charts).forEach(chart => chart.destroy());
    charts = {};
    await loadDashboard();
}

// Export data
function exportData() {
    alert('Export functionality coming soon! 📊\n\nThis will allow you to download dashboard data as CSV or PDF.');
}

console.log('✅ Professional Dashboard JS loaded');
