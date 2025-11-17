// E-Commerce ETL Analytics Dashboard JavaScript

const API_BASE = 'http://localhost:5001/api';
let chartInstances = {};
let currentDays = 'all';

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeDateFilter();
    loadAllData();
});

function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            // Update active state
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            
            // Switch view
            const viewName = this.getAttribute('data-view');
            switchView(viewName);
        });
    });
}

function switchView(viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    
    // Show selected view
    const viewElement = document.getElementById(`${viewName}View`);
    if (viewElement) {
        viewElement.classList.add('active');
    }
    
    // Update header
    const titles = {
        overview: {
            title: 'Dashboard Overview',
            subtitle: 'Complete analytics for your e-commerce ETL pipeline'
        },
        orders: {
            title: 'Order Analytics',
            subtitle: 'Track orders, delivery performance, and status trends'
        },
        customers: {
            title: 'Customer Insights',
            subtitle: 'Analyze customer behavior, geography, and lifetime value'
        },
        products: {
            title: 'Product Performance',
            subtitle: 'Best-selling products and category analytics'
        },
        sellers: {
            title: 'Seller Analytics',
            subtitle: 'Monitor seller performance and distribution'
        },
        payments: {
            title: 'Payment Insights',
            subtitle: 'Payment methods and installment analysis'
        },
        geography: {
            title: 'Geographic Analysis',
            subtitle: 'Customer and revenue distribution by location'
        }
    };
    
    const titleInfo = titles[viewName] || titles.overview;
    document.getElementById('viewTitle').textContent = titleInfo.title;
    document.getElementById('viewSubtitle').textContent = titleInfo.subtitle;
    
    // Load view-specific data
    loadViewData(viewName);
}

function initializeDateFilter() {
    const filter = document.getElementById('dateFilter');
    filter.addEventListener('change', function() {
        currentDays = this.value;
        refreshData();
    });
}

// ============================================
// DATA LOADING
// ============================================

function loadAllData() {
    showLoading();
    loadViewData('overview');
}

function loadViewData(viewName) {
    showLoading();
    
    switch(viewName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'orders':
            loadOrdersData();
            break;
        case 'customers':
            loadCustomersData();
            break;
        case 'products':
            loadProductsData();
            break;
        case 'sellers':
            loadSellersData();
            break;
        case 'payments':
            loadPaymentsData();
            break;
        case 'geography':
            loadGeographyData();
            break;
    }
}

async function loadOverviewData() {
    try {
        const [overview, timeline, categories, payments, clv] = await Promise.all([
            fetch(`${API_BASE}/overview?days=${currentDays}`).then(r => r.json()),
            fetch(`${API_BASE}/orders/timeline?days=${currentDays}`).then(r => r.json()),
            fetch(`${API_BASE}/products/categories?days=${currentDays}`).then(r => r.json()),
            fetch(`${API_BASE}/payments/methods?days=${currentDays}`).then(r => r.json()),
            fetch(`${API_BASE}/customers/lifetime-value`).then(r => r.json())
        ]);
        
        if (overview.success) {
            updateKPIs(overview.data);
            renderOrderStatusChart(overview.data.order_status_distribution);
        }
        
        if (timeline.success) {
            renderOrderTimelineChart(timeline.data);
        }
        
        if (categories.success) {
            renderTopCategoriesChart(categories.data.slice(0, 10));
        }
        
        if (payments.success) {
            renderPaymentMethodsOverviewChart(payments.data);
        }
        
        if (clv.success) {
            renderCustomerSegmentsChart(clv.data);
        }
        
        hideLoading();
    } catch (error) {
        console.error('Error loading overview:', error);
        hideLoading();
    }
}

async function loadOrdersData() {
    try {
        const [statusTimeline, delivery] = await Promise.all([
            fetch(`${API_BASE}/orders/by-status?days=${currentDays}`).then(r => r.json()),
            fetch(`${API_BASE}/orders/delivery-performance?days=${currentDays}`).then(r => r.json())
        ]);
        
        if (statusTimeline.success) {
            renderOrderStatusTimelineChart(statusTimeline.data);
        }
        
        if (delivery.success) {
            renderDeliveryPerformanceChart(delivery.data);
            if (delivery.stats) {
                document.getElementById('statsAvgDelivery').textContent = 
                    `${delivery.stats.avg_delivery_days?.toFixed(1) || 0} days`;
            }
        }
        
        hideLoading();
    } catch (error) {
        console.error('Error loading orders:', error);
        hideLoading();
    }
}

async function loadCustomersData() {
    try {
        const [geography, cities, clv] = await Promise.all([
            fetch(`${API_BASE}/customers/geography`).then(r => r.json()),
            fetch(`${API_BASE}/customers/top-cities?limit=20`).then(r => r.json()),
            fetch(`${API_BASE}/customers/lifetime-value`).then(r => r.json())
        ]);
        
        if (geography.success) {
            renderCustomerGeographyChart(geography.data.slice(0, 15));
        }
        
        if (cities.success) {
            renderTopCitiesChart(cities.data);
        }
        
        if (clv.success) {
            renderCLVSegmentsChart(clv.data);
        }
        
        hideLoading();
    } catch (error) {
        console.error('Error loading customers:', error);
        hideLoading();
    }
}

async function loadProductsData() {
    try {
        const [topProducts, categories, pricesDist] = await Promise.all([
            fetch(`${API_BASE}/products/top-selling?days=${currentDays}&limit=20`).then(r => r.json()),
            fetch(`${API_BASE}/products/categories?days=${currentDays}`).then(r => r.json()),
            fetch(`${API_BASE}/products/price-distribution`).then(r => r.json())
        ]);
        
        if (topProducts.success) {
            renderTopProductsChart(topProducts.data);
        }
        
        if (categories.success) {
            renderCategoryPerformanceChart(categories.data.slice(0, 15));
        }
        
        if (pricesDist.success) {
            renderPriceDistributionChart(pricesDist.data);
        }
        
        hideLoading();
    } catch (error) {
        console.error('Error loading products:', error);
        hideLoading();
    }
}

async function loadSellersData() {
    try {
        const [performance, geography] = await Promise.all([
            fetch(`${API_BASE}/sellers/performance?days=${currentDays}&limit=20`).then(r => r.json()),
            fetch(`${API_BASE}/sellers/geography?days=${currentDays}`).then(r => r.json())
        ]);
        
        if (performance.success) {
            renderTopSellersChart(performance.data);
        }
        
        if (geography.success) {
            renderSellerGeographyChart(geography.data);
        }
        
        hideLoading();
    } catch (error) {
        console.error('Error loading sellers:', error);
        hideLoading();
    }
}

async function loadPaymentsData() {
    try {
        const [methods, installments] = await Promise.all([
            fetch(`${API_BASE}/payments/methods?days=${currentDays}`).then(r => r.json()),
            fetch(`${API_BASE}/payments/installments?days=${currentDays}`).then(r => r.json())
        ]);
        
        if (methods.success) {
            renderPaymentMethodDistChart(methods.data);
        }
        
        if (installments.success) {
            renderInstallmentChart(installments.data);
        }
        
        hideLoading();
    } catch (error) {
        console.error('Error loading payments:', error);
        hideLoading();
    }
}

async function loadGeographyData() {
    try {
        const geography = await fetch(`${API_BASE}/customers/geography`).then(r => r.json());
        
        if (geography.success) {
            renderGeoCustomerChart(geography.data);
            renderGeoRevenueChart(geography.data);
        }
        
        hideLoading();
    } catch (error) {
        console.error('Error loading geography:', error);
        hideLoading();
    }
}

// ============================================
// KPI UPDATES
// ============================================

function updateKPIs(data) {
    document.getElementById('kpiTotalOrders').textContent = formatNumber(data.total_orders);
    document.getElementById('kpiTotalRevenue').textContent = formatCurrency(data.total_revenue);
    document.getElementById('kpiTotalCustomers').textContent = formatNumber(data.total_customers);
    document.getElementById('kpiAvgOrderValue').textContent = formatCurrency(data.avg_order_value);
}

// ============================================
// CHART RENDERING
// ============================================

function renderOrderTimelineChart(data) {
    destroyChart('orderTimelineChart');
    
    const ctx = document.getElementById('orderTimelineChart').getContext('2d');
    chartInstances.orderTimelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: 'Orders',
                data: data.map(d => d.order_count),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true,
                yAxisID: 'y'
            }, {
                label: 'Revenue (R$)',
                data: data.map(d => d.revenue),
                borderColor: '#38ef7d',
                backgroundColor: 'rgba(56, 239, 125, 0.1)',
                tension: 0.4,
                fill: true,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    grid: { display: false },
                    ticks: { 
                        color: '#a0aec0',
                        callback: value => formatCurrency(value)
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { labels: { color: '#a0aec0' } },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    titleColor: '#ffffff',
                    bodyColor: '#a0aec0',
                    callbacks: {
                        label: context => {
                            const label = context.dataset.label;
                            const value = context.parsed.y;
                            return label.includes('Revenue') 
                                ? `${label}: ${formatCurrency(value)}`
                                : `${label}: ${formatNumber(value)}`;
                        }
                    }
                }
            }
        }
    });
}

function renderOrderStatusChart(data) {
    destroyChart('orderStatusChart');
    
    const ctx = document.getElementById('orderStatusChart').getContext('2d');
    chartInstances.orderStatusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.order_status),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: [
                    '#667eea',
                    '#38ef7d',
                    '#4facfe',
                    '#fa709a',
                    '#ff6b6b',
                    '#f2994a'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#a0aec0', padding: 15 }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => `${context.label}: ${formatNumber(context.parsed)}`
                    }
                }
            }
        }
    });
}

function renderTopCategoriesChart(data) {
    destroyChart('topCategoriesChart');
    
    const ctx = document.getElementById('topCategoriesChart').getContext('2d');
    chartInstances.topCategoriesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.category.substring(0, 20)),
            datasets: [{
                label: 'Revenue (R$)',
                data: data.map(d => d.total_revenue),
                backgroundColor: '#667eea',
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { 
                        color: '#a0aec0',
                        callback: value => formatCurrency(value)
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => formatCurrency(context.parsed.x)
                    }
                }
            }
        }
    });
}

function renderPaymentMethodsOverviewChart(data) {
    destroyChart('paymentMethodsChart');
    
    const ctx = document.getElementById('paymentMethodsChart').getContext('2d');
    chartInstances.paymentMethodsChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.map(d => d.payment_type),
            datasets: [{
                data: data.map(d => d.transaction_count),
                backgroundColor: [
                    '#667eea',
                    '#38ef7d',
                    '#4facfe',
                    '#fa709a',
                    '#ff6b6b'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#a0aec0', padding: 15 }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => `${context.label}: ${formatNumber(context.parsed)}`
                    }
                }
            }
        }
    });
}

function renderCustomerSegmentsChart(data) {
    destroyChart('customerSegmentsChart');
    
    const ctx = document.getElementById('customerSegmentsChart').getContext('2d');
    chartInstances.customerSegmentsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.segment),
            datasets: [{
                label: 'Customers',
                data: data.map(d => d.customer_count),
                backgroundColor: ['#38ef7d', '#4facfe', '#fa709a', '#667eea'],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => formatNumber(context.parsed.y)
                    }
                }
            }
        }
    });
}

function renderOrderStatusTimelineChart(data) {
    destroyChart('orderStatusTimelineChart');
    
    // Group by date and status
    const statusMap = {};
    data.forEach(row => {
        if (!statusMap[row.order_status]) {
            statusMap[row.order_status] = {};
        }
        statusMap[row.order_status][row.date] = row.count;
    });
    
    const dates = [...new Set(data.map(d => d.date))].sort();
    const statuses = Object.keys(statusMap);
    
    const colors = ['#667eea', '#38ef7d', '#4facfe', '#fa709a', '#ff6b6b', '#f2994a'];
    
    const datasets = statuses.map((status, idx) => ({
        label: status,
        data: dates.map(date => statusMap[status][date] || 0),
        backgroundColor: colors[idx % colors.length],
        borderColor: colors[idx % colors.length],
        tension: 0.4,
        fill: false
    }));
    
    const ctx = document.getElementById('orderStatusTimelineChart').getContext('2d');
    chartInstances.orderStatusTimelineChart = new Chart(ctx, {
        type: 'line',
        data: { labels: dates, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    stacked: false,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { labels: { color: '#a0aec0' } },
                tooltip: { backgroundColor: 'rgba(30, 37, 55, 0.95)' }
            }
        }
    });
}

function renderDeliveryPerformanceChart(data) {
    destroyChart('deliveryPerformanceChart');
    
    // Group into buckets
    const buckets = {
        '0-5 days': 0,
        '6-10 days': 0,
        '11-15 days': 0,
        '16-20 days': 0,
        '21-30 days': 0,
        '30+ days': 0
    };
    
    data.forEach(row => {
        const days = row.delivery_days;
        const count = row.count;
        if (days <= 5) buckets['0-5 days'] += count;
        else if (days <= 10) buckets['6-10 days'] += count;
        else if (days <= 15) buckets['11-15 days'] += count;
        else if (days <= 20) buckets['16-20 days'] += count;
        else if (days <= 30) buckets['21-30 days'] += count;
        else buckets['30+ days'] += count;
    });
    
    const ctx = document.getElementById('deliveryPerformanceChart').getContext('2d');
    chartInstances.deliveryPerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(buckets),
            datasets: [{
                label: 'Orders',
                data: Object.values(buckets),
                backgroundColor: '#38ef7d',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => formatNumber(context.parsed.y)
                    }
                }
            }
        }
    });
}

function renderCustomerGeographyChart(data) {
    destroyChart('customerGeographyChart');
    
    const ctx = document.getElementById('customerGeographyChart').getContext('2d');
    chartInstances.customerGeographyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.customer_state),
            datasets: [{
                label: 'Customers',
                data: data.map(d => d.customer_count),
                backgroundColor: '#667eea',
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => formatNumber(context.parsed.x)
                    }
                }
            }
        }
    });
}

function renderCLVSegmentsChart(data) {
    destroyChart('clvSegmentsChart');
    
    const ctx = document.getElementById('clvSegmentsChart').getContext('2d');
    chartInstances.clvSegmentsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.segment),
            datasets: [{
                data: data.map(d => d.customer_count),
                backgroundColor: ['#667eea', '#38ef7d', '#4facfe', '#fa709a'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#a0aec0', padding: 15 }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => `${context.label}: ${formatNumber(context.parsed)}`
                    }
                }
            }
        }
    });
}

function renderTopCitiesChart(data) {
    destroyChart('topCitiesChart');
    
    const ctx = document.getElementById('topCitiesChart').getContext('2d');
    chartInstances.topCitiesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => `${d.customer_city}, ${d.customer_state}`),
            datasets: [{
                label: 'Customers',
                data: data.map(d => d.customer_count),
                backgroundColor: '#4facfe',
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0', font: { size: 10 } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: 'rgba(30, 37, 55, 0.95)' }
            }
        }
    });
}

function renderTopProductsChart(data) {
    destroyChart('topProductsChart');
    
    const ctx = document.getElementById('topProductsChart').getContext('2d');
    chartInstances.topProductsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map((d, i) => `Product ${i + 1}`),
            datasets: [{
                label: 'Quantity Sold',
                data: data.map(d => d.total_quantity_sold),
                backgroundColor: '#667eea',
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        title: context => {
                            const idx = context[0].dataIndex;
                            return data[idx].product_category_name || 'Unknown';
                        },
                        label: context => formatNumber(context.parsed.x)
                    }
                }
            }
        }
    });
}

function renderCategoryPerformanceChart(data) {
    destroyChart('categoryPerformanceChart');
    
    const ctx = document.getElementById('categoryPerformanceChart').getContext('2d');
    chartInstances.categoryPerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.category.substring(0, 15)),
            datasets: [{
                label: 'Revenue (R$)',
                data: data.map(d => d.total_revenue),
                backgroundColor: '#38ef7d',
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { 
                        color: '#a0aec0',
                        callback: value => formatCurrency(value)
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0', font: { size: 10 } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => formatCurrency(context.parsed.x)
                    }
                }
            }
        }
    });
}

function renderPriceDistributionChart(data) {
    destroyChart('priceDistributionChart');
    
    const ctx = document.getElementById('priceDistributionChart').getContext('2d');
    chartInstances.priceDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.price_range),
            datasets: [{
                label: 'Items Sold',
                data: data.map(d => d.item_count),
                backgroundColor: '#4facfe',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => formatNumber(context.parsed.y)
                    }
                }
            }
        }
    });
}

function renderTopSellersChart(data) {
    destroyChart('topSellersChart');
    
    const ctx = document.getElementById('topSellersChart').getContext('2d');
    chartInstances.topSellersChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map((d, i) => `Seller ${i + 1}`),
            datasets: [{
                label: 'Revenue (R$)',
                data: data.map(d => d.total_revenue),
                backgroundColor: '#667eea',
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { 
                        color: '#a0aec0',
                        callback: value => formatCurrency(value)
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        title: context => {
                            const idx = context[0].dataIndex;
                            return `${data[idx].seller_city}, ${data[idx].seller_state}`;
                        },
                        label: context => formatCurrency(context.parsed.x)
                    }
                }
            }
        }
    });
}

function renderSellerGeographyChart(data) {
    destroyChart('sellerGeographyChart');
    
    const ctx = document.getElementById('sellerGeographyChart').getContext('2d');
    chartInstances.sellerGeographyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.seller_state),
            datasets: [{
                label: 'Revenue (R$)',
                data: data.map(d => d.total_revenue),
                backgroundColor: '#38ef7d',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { 
                        color: '#a0aec0',
                        callback: value => formatCurrency(value)
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => formatCurrency(context.parsed.y)
                    }
                }
            }
        }
    });
}

function renderPaymentMethodDistChart(data) {
    destroyChart('paymentMethodDistChart');
    
    const ctx = document.getElementById('paymentMethodDistChart').getContext('2d');
    chartInstances.paymentMethodDistChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.payment_type),
            datasets: [{
                data: data.map(d => d.total_value),
                backgroundColor: ['#667eea', '#38ef7d', '#4facfe', '#fa709a', '#ff6b6b'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#a0aec0', padding: 15 }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => `${context.label}: ${formatCurrency(context.parsed)}`
                    }
                }
            }
        }
    });
}

function renderInstallmentChart(data) {
    destroyChart('installmentChart');
    
    const ctx = document.getElementById('installmentChart').getContext('2d');
    chartInstances.installmentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => `${d.payment_installments}x`),
            datasets: [{
                label: 'Total Value (R$)',
                data: data.map(d => d.total_value),
                backgroundColor: '#4facfe',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { 
                        color: '#a0aec0',
                        callback: value => formatCurrency(value)
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => formatCurrency(context.parsed.y)
                    }
                }
            }
        }
    });
}

function renderGeoCustomerChart(data) {
    destroyChart('geoCustomerChart');
    
    const ctx = document.getElementById('geoCustomerChart').getContext('2d');
    chartInstances.geoCustomerChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.customer_state),
            datasets: [{
                label: 'Customers',
                data: data.map(d => d.customer_count),
                backgroundColor: '#667eea',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: { backgroundColor: 'rgba(30, 37, 55, 0.95)' }
            }
        }
    });
}

function renderGeoRevenueChart(data) {
    destroyChart('geoRevenueChart');
    
    const ctx = document.getElementById('geoRevenueChart').getContext('2d');
    chartInstances.geoRevenueChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.customer_state),
            datasets: [{
                label: 'Revenue (R$)',
                data: data.map(d => d.total_revenue),
                backgroundColor: '#38ef7d',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { 
                        color: '#a0aec0',
                        callback: value => formatCurrency(value)
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#a0aec0' }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(30, 37, 55, 0.95)',
                    callbacks: {
                        label: context => formatCurrency(context.parsed.y)
                    }
                }
            }
        }
    });
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function destroyChart(chartId) {
    if (chartInstances[chartId]) {
        chartInstances[chartId].destroy();
        delete chartInstances[chartId];
    }
}

function formatCurrency(value) {
    if (value === null || value === undefined) return 'R$ 0.00';
    return `R$ ${Number(value).toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
}

function formatNumber(value) {
    if (value === null || value === undefined) return '0';
    return Number(value).toLocaleString('pt-BR');
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

function refreshData() {
    const activeView = document.querySelector('.nav-item.active');
    if (activeView) {
        const viewName = activeView.getAttribute('data-view');
        loadViewData(viewName);
    }
}

function exportData() {
    alert('Export functionality - Coming soon!');
}
