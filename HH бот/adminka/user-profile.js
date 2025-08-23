// User Profile Page JavaScript
// Mock data for demonstration
const currentUser = {
    id: 1,
    telegramId: 123456789,
    name: 'Иван Петров',
    username: '@ivan_petrov',
    registrationDate: '2024-01-15',
    hhConnected: true,
    subscription: 'month',
    subscriptionEnd: '2024-02-15',
    lastActivity: '2024-01-29',
    status: 'active',
    balance: 1250,
    totalResponses: 156,
    autoResponses: true,
    aiResponses: false,
    aiResponsesCount: 0,
    referrals: ['@maria_sid', '@alex_kozlov'],
    referredBy: null,
    comment: 'Активный пользователь, много откликов',
    utmSource: 'telegram',
    utmMedium: 'social',
    utmCampaign: 'winter2024'
};

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    initializeUserProfile();
    setupEventListeners();
    loadUserData();
});

function initializeUserProfile() {
    // Get user ID from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('id');
    
    if (userId) {
        // In a real application, you would fetch user data from the server
        console.log('Loading user profile for ID:', userId);
    }
    
    // Set up tab switching
    setupTabSwitching();
}

function setupEventListeners() {
    // Sidebar navigation
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', function() {
            const page = this.dataset.page;
            if (page === 'users') {
                window.location.href = 'index.html';
            } else {
                navigateToPage(page);
            }
        });
    });
    
    // Toggle switches
    document.querySelectorAll('.toggle-switch input').forEach(toggle => {
        toggle.addEventListener('change', function() {
            handleToggleChange(this);
        });
    });
    
    // Filter inputs
    setupFilterListeners();
}

function setupTabSwitching() {
    const tabs = document.querySelectorAll('.profile-tab');
    const panels = document.querySelectorAll('.tab-panel');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            // Remove active class from all tabs and panels
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding panel
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            // Load tab-specific data
            loadTabData(targetTab);
        });
    });
}

function loadUserData() {
    // Load basic user information
    document.getElementById('userProfileName').textContent = currentUser.name;
    document.getElementById('userProfileUsername').textContent = currentUser.username;
    document.getElementById('userProfileId').textContent = `ID: ${currentUser.telegramId}`;
    document.getElementById('userTotalResponses').textContent = currentUser.totalResponses;
    document.getElementById('userBalance').textContent = `${currentUser.balance.toLocaleString()} ₽`;
    document.getElementById('userReferrals').textContent = currentUser.referrals.length;
    
    // Load detailed information
    document.getElementById('telegramId').textContent = currentUser.telegramId;
    document.getElementById('userName').textContent = currentUser.name;
    document.getElementById('userUsername').textContent = currentUser.username;
    document.getElementById('registrationDate').textContent = formatDate(currentUser.registrationDate);
    document.getElementById('lastActivity').textContent = formatDate(currentUser.lastActivity);
    document.getElementById('subscriptionEnd').textContent = formatDate(currentUser.subscriptionEnd);
    document.getElementById('userBalanceDetail').textContent = `${currentUser.balance.toLocaleString()} ₽`;
    document.getElementById('adminComment').value = currentUser.comment;
    
    // Load UTM data
    document.getElementById('utmSource').textContent = currentUser.utmSource || '—';
    document.getElementById('utmMedium').textContent = currentUser.utmMedium || '—';
    document.getElementById('utmCampaign').textContent = currentUser.utmCampaign || '—';
    
    // Update status badge
    updateStatusBadge(currentUser.status);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'operations':
            loadOperationsData();
            break;
        case 'referrals':
            loadReferralsData();
            break;
        case 'responses':
            loadResponsesData();
            break;
    }
}

function loadOperationsData() {
    // Mock operations data
    const operations = [
        {
            id: 1,
            date: '29.01.2024 14:30',
            type: 'payment',
            amount: 1900,
            description: 'Продление подписки на месяц',
            status: 'completed'
        },
        {
            id: 2,
            date: '25.01.2024 16:45',
            type: 'withdrawal',
            amount: -150,
            description: 'Использование AI-откликов',
            status: 'completed'
        },
        {
            id: 3,
            date: '20.01.2024 12:15',
            type: 'bonus',
            amount: 500,
            description: 'Реферальный бонус',
            status: 'completed'
        }
    ];
    
    const tbody = document.getElementById('operationsTableBody');
    if (tbody) {
        tbody.innerHTML = operations.map(op => `
            <tr>
                <td>${op.date}</td>
                <td><span class="operation-type ${op.type}">${getOperationTypeText(op.type)}</span></td>
                <td class="amount ${op.amount > 0 ? 'positive' : 'negative'}">${op.amount > 0 ? '+' : ''}${op.amount.toLocaleString()} ₽</td>
                <td>${op.description}</td>
                <td><span class="status-badge status-success">Выполнено</span></td>
                <td>
                    <button class="action-btn action-view" onclick="viewOperation(${op.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

function loadReferralsData() {
    // Referrals data is already loaded in HTML
    console.log('Referrals data loaded');
}

function loadResponsesData() {
    // Mock responses data
    const responses = [
        {
            id: 1,
            date: '29.01.2024',
            vacancy: 'Senior Python Developer',
            company: 'TechCorp',
            type: 'manual',
            status: 'sent'
        },
        {
            id: 2,
            date: '28.01.2024',
            vacancy: 'Backend Developer',
            company: 'StartupXYZ',
            type: 'auto',
            status: 'viewed'
        },
        {
            id: 3,
            date: '27.01.2024',
            vacancy: 'Python Developer',
            company: 'DevCompany',
            type: 'manual',
            status: 'invited'
        }
    ];
    
    const tbody = document.getElementById('responsesTableBody');
    if (tbody) {
        tbody.innerHTML = responses.map(resp => `
            <tr>
                <td>${resp.date}</td>
                <td>${resp.vacancy}</td>
                <td>${resp.company}</td>
                <td><span class="response-type ${resp.type}">${getResponseTypeText(resp.type)}</span></td>
                <td><span class="status-badge status-${getResponseStatusClass(resp.status)}">${getResponseStatusText(resp.status)}</span></td>
                <td>
                    <button class="action-btn action-view" onclick="viewResponse(${resp.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

function setupFilterListeners() {
    // Operations filters
    const operationFilters = ['operationType', 'operationDateFrom', 'operationDateTo'];
    operationFilters.forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', applyOperationFilters);
        }
    });
    
    // Response filters
    const responseFilters = ['responseStatus', 'responseType', 'responseDateFrom', 'responseDateTo'];
    responseFilters.forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', applyResponseFilters);
        }
    });
}

// Utility functions
function formatDate(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function updateStatusBadge(status) {
    const statusElement = document.getElementById('userProfileStatus');
    const statusMap = {
        'active': { class: 'status-active', text: 'Активен' },
        'inactive': { class: 'status-inactive', text: 'Неактивен' },
        'banned': { class: 'status-banned', text: 'Заблокирован' }
    };
    
    const statusInfo = statusMap[status] || statusMap['inactive'];
    statusElement.innerHTML = `<span class="status-badge ${statusInfo.class}">${statusInfo.text}</span>`;
    
    // Update toggle button text
    const toggleText = document.getElementById('statusToggleText');
    if (toggleText) {
        toggleText.textContent = status === 'banned' ? 'Разблокировать' : 'Заблокировать';
    }
}

function getOperationTypeText(type) {
    const typeMap = {
        'payment': 'Платеж',
        'withdrawal': 'Списание',
        'bonus': 'Бонус',
        'refund': 'Возврат'
    };
    return typeMap[type] || type;
}

function getResponseTypeText(type) {
    const typeMap = {
        'manual': 'Ручной',
        'auto': 'Автоотклик',
        'ai': 'AI-отклик'
    };
    return typeMap[type] || type;
}

function getResponseStatusText(status) {
    const statusMap = {
        'sent': 'Отправлен',
        'viewed': 'Просмотрен',
        'rejected': 'Отклонен',
        'invited': 'Приглашен'
    };
    return statusMap[status] || status;
}

function getResponseStatusClass(status) {
    const classMap = {
        'sent': 'info',
        'viewed': 'warning',
        'rejected': 'danger',
        'invited': 'success'
    };
    return classMap[status] || 'info';
}

// Action functions

function toggleUserStatus() {
    const newStatus = currentUser.status === 'banned' ? 'active' : 'banned';
    currentUser.status = newStatus;
    updateStatusBadge(newStatus);
    showToast(`Статус пользователя изменен на: ${newStatus === 'active' ? 'Активен' : 'Заблокирован'}`, 'success');
}

function editSubscriptionAndBalance() {
    showToast('Редактирование подписки и баланса', 'info');
}

function addBalance() {
    const amount = prompt('Введите сумму для пополнения баланса:');
    if (amount && !isNaN(amount)) {
        currentUser.balance += parseInt(amount);
        document.getElementById('userBalance').textContent = `${currentUser.balance.toLocaleString()} ₽`;
        document.getElementById('userBalanceDetail').textContent = `${currentUser.balance.toLocaleString()} ₽`;
        showToast(`Баланс пополнен на ${amount}₽`, 'success');
    }
}

function saveComment() {
    const comment = document.getElementById('adminComment').value;
    currentUser.comment = comment;
    showToast('Комментарий сохранен', 'success');
}

function clearComment() {
    document.getElementById('adminComment').value = '';
    showToast('Комментарий очищен', 'info');
}


function applyOperationFilters() {
    const type = document.getElementById('operationType').value;
    const dateFrom = document.getElementById('operationDateFrom').value;
    const dateTo = document.getElementById('operationDateTo').value;
    
    showToast('Фильтры операций применены', 'info');
    // In a real application, you would filter the operations table
}

function applyResponseFilters() {
    const status = document.getElementById('responseStatus').value;
    const type = document.getElementById('responseType').value;
    const dateFrom = document.getElementById('responseDateFrom').value;
    const dateTo = document.getElementById('responseDateTo').value;
    
    showToast('Фильтры откликов применены', 'info');
    // In a real application, you would filter the responses table
}

function clearOperationFilters() {
    document.getElementById('operationType').value = '';
    document.getElementById('operationDateFrom').value = '';
    document.getElementById('operationDateTo').value = '';
    showToast('Фильтры операций очищены', 'info');
}

function clearResponseFilters() {
    document.getElementById('responseStatus').value = '';
    document.getElementById('responseType').value = '';
    document.getElementById('responseDateFrom').value = '';
    document.getElementById('responseDateTo').value = '';
    showToast('Фильтры откликов очищены', 'info');
}

function viewOperation(operationId) {
    showToast(`Просмотр операции ${operationId}`, 'info');
}

function viewResponse(responseId) {
    showToast(`Просмотр отклика ${responseId}`, 'info');
}

function viewReferralProfile(userId) {
    window.location.href = `user-profile.html?id=${userId}`;
}

function addManualOperation() {
    showToast('Добавление ручной операции', 'info');
}

function exportOperations() {
    showToast('Экспорт операций', 'info');
}

function navigateToPage(page) {
    // In a real application, you would navigate to different pages
    showToast(`Переход на страницу: ${page}`, 'info');
}

// Toast notification function
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// URL parameter handling
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}