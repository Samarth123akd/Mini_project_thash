// E-Commerce Dashboard JavaScript
const API_BASE_URL = 'http://localhost:5000/api';

// Global chart instances
let charts = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    initializeDashboard();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            console.log('Refresh button clicked');
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

    const mixToggle = document.getElementById('mixToggle');
    if (mixToggle) {
        mixToggle.addEventListener('change', () => {
            console.log('Mix toggle changed:', mixToggle.checked);
            applyFilters();
        });
    }

    const darkToggle = document.getElementById('darkToggle');
    if (darkToggle) {
        darkToggle.addEventListener('click', () => {
            const isDark = document.body.getAttribute('data-theme') === 'dark';
            document.body.setAttribute('data-theme', isDark ? 'light' : 'dark');
        });
    }
}

// Initialize dashboard
async function initializeDashboard() {
    try {
        showLoading();
        await loadDashboardBundle();
        hideLoading();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showError('Failed to load dashboard data. Please check if the backend server is running.');
        hideLoading();
    }
}

// Refresh dashboard
async function refreshDashboard() {
    destroyCharts();
    await initializeDashboard();
}

// Fetch bundle and render all components
async function loadDashboardBundle() {
    const days = document.getElementById('dateFilter')?.value || '30';
    const mix = document.getElementById('mixToggle')?.checked ? 'true' : 'false';
    const url = `${API_BASE_URL}/dashboard?days=${encodeURIComponent(days)}&mix=${mix}`;
    const res = await fetch(url);
    const bundle = await res.json();
    renderKPIs(bundle.kpis);
    renderSalesTrends(bundle.sales_trends);
    renderTopProducts(bundle.top_products);
    renderCustomerSegments(bundle.customer_segments);
    renderOrdersByStatus(bundle.orders_status);
    renderRevenueByState(bundle.revenue_by_state);
    renderRecentOrders(bundle.recent_orders);
    const lastUpdate = document.getElementById('lastUpdate');
    if (lastUpdate) lastUpdate.textContent = new Date().toLocaleString('pt-BR');
}

// Load sales trends
function renderSalesTrends(data) {
    try {
        const ctx = document.getElementById('salesTrendsChart').getContext('2d');
        charts.salesTrends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [
                    {
                        label: 'Revenue (R$)',
                        data: data.revenue,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        tension: 0.4,
                        fill: true,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Orders',
                        data: data.orders,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true,
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
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    if (context.datasetIndex === 0) {
                                        label += formatCurrency(context.parsed.y);
                                    } else {
                                        label += formatNumber(context.parsed.y);
                                    }
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Revenue (R$)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Orders'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering sales trends:', error);
    }
}

function renderTopProducts(data) {
    try {
        const ctx = document.getElementById('topProductsChart').getContext('2d');
        charts.topProducts = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.product_names,
                datasets: [{
                    label: 'Revenue (R$)',
                    data: data.revenue,
                    backgroundColor: '#7c3aed',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
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
                        title: {
                            display: true,
                            text: 'Revenue (R$)'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering top products:', error);
    }
}

function renderCustomerSegments(data) {
    try {
        const ctx = document.getElementById('customerSegmentsChart').getContext('2d');
        charts.customerSegments = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.segments,
                datasets: [{
                    data: data.counts,
                    backgroundColor: [
                        '#2563eb',
                        '#10b981',
                        '#f59e0b',
                        '#ef4444'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${formatNumber(value)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering customer segments:', error);
    }
}

function renderOrdersByStatus(data) {
    try {
        const ctx = document.getElementById('orderStatusChart').getContext('2d');
        charts.orderStatus = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.statuses,
                datasets: [{
                    data: data.counts,
                    backgroundColor: [
                        '#10b981',
                        '#f59e0b',
                        '#ef4444',
                        '#6366f1',
                        '#8b5cf6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering order status:', error);
    }
}

function renderRevenueByState(data) {
    try {
        const ctx = document.getElementById('revenueByStateChart').getContext('2d');
        charts.revenueByState = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.states,
                datasets: [{
                    label: 'Revenue (R$)',
                    data: data.revenue,
                    backgroundColor: '#2563eb',
                    borderRadius: 8
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
                                return formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: 'Revenue (R$)'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error rendering revenue by state:', error);
    }
}

function renderRecentOrders(data) {
    try {
        const tbody = document.getElementById('recentOrdersTable');
        tbody.innerHTML = '';
        data.forEach(order => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${order.order_id}</td>
                <td>${order.customer_id}</td>
                <td>${formatCurrency(order.total_amount)}</td>
                <td><span class="badge ${getStatusClass(order.status)}">${order.status}</span></td>
                <td>${formatDateTime(order.date)}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error rendering recent orders:', error);
    }
}

// Render KPIs
function renderKPIs(data) {
    try {
        document.getElementById('totalRevenue').textContent = formatCurrency(data.total_revenue);
        document.getElementById('totalOrders').textContent = formatNumber(data.total_orders);
        document.getElementById('totalCustomers').textContent = formatNumber(data.unique_customers);
        document.getElementById('avgOrderValue').textContent = formatCurrency(data.avg_order_value);
        if (data.revenue_change !== undefined) updateChangeIndicator('revenueChange', data.revenue_change);
        if (data.orders_change !== undefined) updateChangeIndicator('ordersChange', data.orders_change);
    } catch (e) {
        console.error('Error rendering KPIs:', e);
    }
}

// Helper Functions
function formatCurrency(value) {
    if (value === null || value === undefined) return 'R$ 0.00';
    return `R$ ${parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatNumber(value) {
    if (value === null || value === undefined) return '0';
    return parseFloat(value).toLocaleString('pt-BR');
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('pt-BR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function getStatusClass(status) {
    const statusMap = {
        'delivered': 'success',
        'shipped': 'info',
        'processing': 'warning',
        'canceled': 'danger',
        'pending': 'warning'
    };
    return statusMap[status?.toLowerCase()] || 'info';
}

function updateChangeIndicator(elementId, change) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const isPositive = change >= 0;
    element.className = `change ${isPositive ? 'positive' : 'negative'}`;
    element.innerHTML = `
        <span>${isPositive ? '↑' : '↓'}</span>
        ${Math.abs(change).toFixed(1)}%
    `;
}

function showLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.style.display = 'flex';
}

function hideLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.style.display = 'none';
}

function showError(message) {
    const errorEl = document.createElement('div');
    errorEl.className = 'error-message';
    errorEl.textContent = message;
    
    const container = document.querySelector('.main-content .container');
    if (container) {
        container.insertBefore(errorEl, container.firstChild);
    }
}

function destroyCharts() {
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
    charts = {};
}

function applyFilters() {
    refreshDashboard();
}
