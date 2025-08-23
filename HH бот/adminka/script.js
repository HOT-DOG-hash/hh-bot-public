// Mock data for demonstration
const mockData = {
    stats: {
        totalUsers: 15847,
        newUsersToday: 127,
        newUsersWeek: 892,
        newUsersMonth: 3456,
        activeUsers24h: 2341,
        activeUsers7d: 8923,
        activeUsers30d: 12456,
        paidSubscribers: 2891,
        paidSubscribersPercent: 18.2,
        autoResponseUsers: 1456,
        aiResponseUsers: 987,
        avgResponsesPerUser: 12.4,
        responses24h: 1247,
        responses7d: 8934,
        responses30d: 34567,
        conversion24h: 2.1,
        conversion7d: 4.3,
        conversion30d: 18.2,
        revenueToday: 45600,
        revenueWeek: 234500,
        revenueMonth: 987600,
        revenueTotal: 2456700,
        revenueSubscriptions: 1876500,
        revenueAI: 580200,
        avgCheck: 1650,
        arpu: 156,
        weeklyPayments: 234,
        monthlyPayments: 567,
        quarterlyPayments: 123,
        repeatPayments: 456,
        botStatus: 'online',
        openaiBalance: 847.32,
        totalResponses: 156789,
        errorResponses: 234,
        successResponses: 156555,
        connectedResumes: 3456,
        autoResponses30d: 23456,
        aiResponses30d: 12345
    },
    broadcasts: [
        {
            id: 1,
            title: 'Обновление функций бота',
            message: 'Добавлены новые возможности для автооткликов и AI-генерации сопроводительных писем. Попробуйте уже сегодня!',
            audience: 'all',
            audienceCount: 15847,
            sentAt: '2024-01-29 15:30',
            status: 'sent',
            delivered: 15234,
            failed: 613,
            read: 12456,
            hasAttachment: true,
            attachment: {
                type: 'image',
                name: 'update_preview.jpg',
                url: '/uploads/update_preview.jpg'
            }
        },
        {
            id: 2,
            title: 'Акция на премиум подписку',
            message: 'Скидка 30% на все тарифы до конца месяца! Не упустите возможность получить больше откликов по выгодной цене.',
            audience: 'no_subscription',
            audienceCount: 8934,
            sentAt: '2024-01-28 12:00',
            status: 'sent',
            delivered: 8756,
            failed: 178,
            read: 6234,
            hasAttachment: false,
            attachment: null
        },
        {
            id: 3,
            title: 'Техническое обслуживание',
            message: 'Завтра с 02:00 до 04:00 МСК будет проводиться техническое обслуживание. Бот может быть временно недоступен.',
            audience: 'premium',
            audienceCount: 2891,
            sentAt: '2024-01-27 18:45',
            status: 'sent',
            delivered: 2891,
            failed: 0,
            read: 2456,
            hasAttachment: false,
            attachment: null
        },
        {
            id: 4,
            title: 'Новые возможности AI',
            message: 'Черновик сообщения о новых AI функциях...',
            audience: 'ai_responses',
            audienceCount: 987,
            sentAt: null,
            status: 'draft',
            delivered: 0,
            failed: 0,
            read: 0,
            hasAttachment: false,
            attachment: null
        }
    ],
    users: [
        {
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
        },
        {
            id: 2,
            telegramId: 987654321,
            name: 'Мария Сидорова',
            username: '@maria_sid',
            registrationDate: '2024-01-20',
            hhConnected: true,
            subscription: 'week',
            subscriptionEnd: '2024-02-05',
            lastActivity: '2024-01-28',
            status: 'active',
            balance: 450,
            totalResponses: 89,
            autoResponses: false,
            aiResponses: true,
            aiResponsesCount: 23,
            referrals: ['@elena_v'],
            referredBy: '@ivan_petrov',
            comment: 'Использует AI-отклики',
            utmSource: 'google',
            utmMedium: 'cpc',
            utmCampaign: 'search_ads'
        },
        {
            id: 3,
            telegramId: 456789123,
            name: 'Алексей Козлов',
            username: '@alex_kozlov',
            registrationDate: '2024-01-25',
            hhConnected: false,
            subscription: 'none',
            subscriptionEnd: null,
            lastActivity: '2024-01-26',
            status: 'banned',
            balance: 0,
            totalResponses: 12,
            autoResponses: false,
            aiResponses: false,
            aiResponsesCount: 0,
            referrals: [],
            referredBy: '@ivan_petrov',
            comment: 'Заблокирован за спам',
            utmSource: 'direct',
            utmMedium: 'none',
            utmCampaign: 'organic'
        },
        {
            id: 4,
            telegramId: 789123456,
            name: 'Елена Волкова',
            username: '@elena_v',
            registrationDate: '2024-01-28',
            hhConnected: true,
            subscription: 'quarter',
            subscriptionEnd: '2024-04-28',
            lastActivity: '2024-01-29',
            status: 'active',
            balance: 2340,
            totalResponses: 234,
            autoResponses: true,
            aiResponses: true,
            aiResponsesCount: 45,
            referrals: ['@dmitry_nov', '@anna_k'],
            referredBy: '@maria_sid',
            comment: 'VIP пользователь',
            utmSource: 'facebook',
            utmMedium: 'social',
            utmCampaign: 'fb_promo'
        },
        {
            id: 5,
            telegramId: 321654987,
            name: 'Дмитрий Новиков',
            username: '@dmitry_nov',
            registrationDate: '2024-01-29',
            hhConnected: true,
            subscription: 'none',
            subscriptionEnd: null,
            lastActivity: '2024-01-29',
            status: 'active',
            balance: 0,
            totalResponses: 34,
            autoResponses: false,
            aiResponses: false,
            aiResponsesCount: 0,
            referrals: [],
            referredBy: '@elena_v',
            comment: 'Новый пользователь',
            utmSource: 'youtube',
            utmMedium: 'video',
            utmCampaign: 'tutorial_2024'
        },
        {
            id: 6,
            telegramId: 654987321,
            name: 'Анна Кузнецова',
            username: '@anna_k',
            registrationDate: '2024-01-30',
            hhConnected: false,
            subscription: 'week',
            subscriptionEnd: '2024-02-06',
            lastActivity: '2024-01-30',
            status: 'inactive',
            balance: 150,
            totalResponses: 5,
            autoResponses: false,
            aiResponses: false,
            aiResponsesCount: 0,
            referrals: [],
            referredBy: '@elena_v',
            comment: 'Не подключила HH',
            utmSource: 'email',
            utmMedium: 'newsletter',
            utmCampaign: 'weekly_digest'
        }
    ],
    subscriptions: [
        { userId: 1, userName: 'Иван Петров', type: '1 месяц', endDate: '2024-02-15', status: 'Активна', amount: 1900 },
        { userId: 2, userName: 'Мария Сидорова', type: '1 неделя', endDate: '2024-02-05', status: 'Активна', amount: 690 },
        { userId: 4, userName: 'Елена Волкова', type: '1 месяц', endDate: '2024-02-28', status: 'Активна', amount: 1900 },
        { userId: 6, userName: 'Сергей Иванов', type: '1 неделя', endDate: '2024-01-30', status: 'Истекла', amount: 690 }
    ],
    responses: [
        { id: 1, userId: 1, userName: 'Иван Петров', date: '2024-01-29', resume: 'Python разработчик', vacancy: 'Senior Python Developer', company: 'TechCorp', status: 'Отправлен' },
        { id: 2, userId: 2, userName: 'Мария Сидорова', date: '2024-01-29', resume: 'Frontend разработчик', vacancy: 'React Developer', company: 'WebStudio', status: 'Просмотрен' },
        { id: 3, userId: 4, userName: 'Елена Волкова', date: '2024-01-28', resume: 'Менеджер по продажам', vacancy: 'Sales Manager', company: 'SalesInc', status: 'Отклонен' },
        { id: 4, userId: 1, userName: 'Иван Петров', date: '2024-01-28', resume: 'Python разработчик', vacancy: 'Backend Developer', company: 'StartupXYZ', status: 'Отправлен' }
    ],
    autoResponses: [
        { userId: 1, userName: 'Иван Петров', status: 'Активно', lastRun: '2024-01-29 14:30', filters: 'Python, Senior, Москва', responsesCount: 15 },
        { userId: 4, userName: 'Елена Волкова', status: 'Активно', lastRun: '2024-01-29 12:15', filters: 'Продажи, Менеджер', responsesCount: 8 },
        { userId: 7, userName: 'Андрей Смирнов', status: 'Неактивно', lastRun: '2024-01-27 16:45', filters: 'JavaScript, Frontend', responsesCount: 3 }
    ],
    aiResponses: [
        { id: 1, date: '2024-01-29', userId: 2, userName: 'Мария Сидорова', vacancy: 'React Developer', keyword: 'React', responseText: 'Здравствуйте! Меня заинтересовала ваша вакансия React разработчика...', status: 'Отправлен' },
        { id: 2, date: '2024-01-29', userId: 4, userName: 'Елена Волкова', vacancy: 'Sales Manager', keyword: 'продажи', responseText: 'Добрый день! Хочу откликнуться на вашу вакансию менеджера по продажам...', status: 'Черновик' },
        { id: 3, date: '2024-01-28', userId: 2, userName: 'Мария Сидорова', vacancy: 'Frontend Developer', keyword: 'frontend', responseText: 'Привет! Увидела вашу вакансию frontend разработчика и хочу предложить...', status: 'Отправлен' }
    ],
    notifications: [
        { id: 1, userId: 1, userName: 'Иван Петров', text: 'Ваша подписка истекает через 3 дня', time: '2024-01-29 10:00', status: 'Отправлено' },
        { id: 2, userId: 'all', userName: 'Все пользователи', text: 'Обновление бота: добавлены новые функции', time: '2024-01-28 15:30', status: 'Отправлено' },
        { id: 3, userId: 4, userName: 'Елена Волкова', text: 'Поздравляем с успешным откликом!', time: '2024-01-28 12:15', status: 'Доставлено' }
    ],
    logs: [
        { id: 1, date: '2024-01-29 14:35', userId: 1, userName: 'Иван Петров', action: 'Отправка отклика', type: 'info', text: 'Успешно отправлен отклик на вакансию Senior Python Developer' },
        { id: 2, date: '2024-01-29 14:30', userId: null, userName: 'Система', action: 'Автоотклики', type: 'info', text: 'Запущен процесс автооткликов для 5 пользователей' },
        { id: 3, date: '2024-01-29 14:25', userId: 3, userName: 'Алексей Козлов', action: 'Ошибка авторизации', type: 'error', text: 'Неудачная попытка авторизации в HH API' },
        { id: 4, date: '2024-01-29 14:20', userId: 2, userName: 'Мария Сидорова', action: 'Создание письма', type: 'info', text: 'Создано новое сопроводительное письмо' }
    ],
    texts: [
        {
            id: 1,
            category: 'welcome',
            name: 'Приветственное сообщение',
            key: 'WELCOME',
            text: '👋 Добро пожаловать в Get Offer Bot!\nЯ помогу тебе массово откликаться на вакансии на hh.ru.\nДля начала — привяжи свой аккаунт, а дальше сможешь настроить автоотклик, письма и аналитику.',
            hasAttachment: false,
            attachment: null,
            lastModified: '2024-01-29 10:00'
        },
        {
            id: 2,
            category: 'subscription',
            name: 'Информация о подписке',
            key: 'SUBSCRIPTION_INFO',
            text: '💳 Чтобы пользоваться ботом, нужно оплатить тариф.\n\nТариф включает:\n✓ Доступ к массовым откликам\n✓ Лимит 200 откликов в сутки\n✓ Личную статистику и сопровождение',
            hasAttachment: true,
            attachment: {
                type: 'image',
                name: 'subscription_info.jpg',
                url: '/uploads/subscription_info.jpg'
            },
            lastModified: '2024-01-28 15:30'
        },
        {
            id: 3,
            category: 'support',
            name: 'Информация о поддержке',
            key: 'SUPPORT_INFO',
            text: '🛠 Нужна помощь?\n\nЕсли у тебя возникли вопросы по работе бота, подписке или откликам — просто напиши нам 👇\n@hh_support_bot\n\nМы на связи каждый день с 10:00 до 20:00 (МСК)',
            hasAttachment: false,
            attachment: null,
            lastModified: '2024-01-27 12:15'
        },
        {
            id: 4,
            category: 'responses',
            name: 'Начало процесса откликов',
            key: 'RESPONSES_STARTED',
            text: '🚀 Процесс запущен\n\nПосмотреть отклики вы сможете в личном кабинете на hh.ru\nБот пришлёт уведомление после завершения задачи.',
            hasAttachment: false,
            attachment: null,
            lastModified: '2024-01-26 14:20'
        },
        {
            id: 5,
            category: 'buttons',
            name: 'Кнопка "Главное меню"',
            key: 'BACK_TO_MAIN_MENU',
            text: '🔙 Главное меню',
            hasAttachment: false,
            attachment: null,
            lastModified: '2024-01-25 16:45'
        },
        {
            id: 6,
            category: 'cover_letters',
            name: 'Заголовок сопроводительных писем',
            key: 'CL_MENU_HEADER',
            text: '📄 Сопроводительные письма\n\nСопроводительное письмо — это дополнительный текст, который будет автоматически добавляться к каждому отклику.\n\n📌 В этом разделе можно настроить сопроводительные письма, чтобы они всегда были под рукой в момент создания запроса.\n\nЕсли ты не хочешь добавлять письмо — можно откликаться без него.',
            hasAttachment: true,
            attachment: {
                type: 'video',
                name: 'cover_letters_guide.mp4',
                url: '/uploads/cover_letters_guide.mp4'
            },
            lastModified: '2024-01-24 11:30'
        }
    ],
    pricing: {
        freeResponses: 10,
        subscriptionPrices: {
            week: 690,
            month: 1900,
            quarter: 4500,
            halfYear: 8500,
            year: 15900
        },
        aiResponsesPrices: {
            responses30: 299,
            responses100: 899,
            responses500: 3999,
            responses1000: 7499,
            responses3000: 19999
        }
    }
};

// Application state
let currentPage = 'dashboard';
let currentData = {};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupEventListeners();
    loadPage('dashboard');
}

function setupEventListeners() {
    // Sidebar menu items
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', function() {
            const page = this.dataset.page;
            setActivePage(page);
            loadPage(page);
        });
    });
}

function setActivePage(page) {
    // Remove active class from all menu items
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to current page
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    
    // Update page title
    const pageTitle = document.querySelector(`[data-page="${page}"] span`).textContent;
    document.getElementById('page-title').textContent = pageTitle;
    
    currentPage = page;
}

function loadPage(page) {
    const contentArea = document.getElementById('content-area');
    
    switch(page) {
        case 'dashboard':
            contentArea.innerHTML = getDashboardHTML();
            break;
        case 'users':
            contentArea.innerHTML = getUsersHTML();
            break;
        case 'subscriptions':
            contentArea.innerHTML = getSubscriptionsHTML();
            break;
        case 'responses':
            contentArea.innerHTML = getResponsesHTML();
            break;
        case 'auto-responses':
            contentArea.innerHTML = getAutoResponsesHTML();
            break;
        case 'ai-responses':
            contentArea.innerHTML = getAIResponsesHTML();
            break;
        case 'analytics':
            contentArea.innerHTML = getAnalyticsHTML();
            break;
        case 'notifications':
            contentArea.innerHTML = getNotificationsHTML();
            break;
        case 'bot-settings':
            contentArea.innerHTML = getBotSettingsHTML();
            break;
        case 'messages':
            contentArea.innerHTML = getMessagesHTML();
            break;
        case 'integrations':
            contentArea.innerHTML = getIntegrationsHTML();
            break;
        case 'modules':
            contentArea.innerHTML = getModulesHTML();
            break;
        case 'texts':
            contentArea.innerHTML = getTextsHTML();
            break;
        case 'pricing':
            contentArea.innerHTML = getPricingHTML();
            break;
        case 'logs':
            contentArea.innerHTML = getLogsHTML();
            break;
        default:
            contentArea.innerHTML = '<div>Страница не найдена</div>';
    }
    
    // Setup page-specific event listeners
    setupPageEventListeners(page);
}

function getDashboardHTML() {
    const stats = mockData.stats;
    return `
        <div class="dashboard-header">
            <h1 class="dashboard-title">Обзор</h1>
            <p class="dashboard-subtitle">Ключевые метрики и аналитика вашего Telegram бота</p>
        </div>

        <!-- Key Metrics -->
        <div class="key-metrics">
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Всего пользователей</span>
                    <div class="metric-icon users">
                        <i class="fas fa-users"></i>
                    </div>
                </div>
                <div class="metric-value">${stats.totalUsers.toLocaleString()}</div>
                <div class="metric-change positive">
                    <i class="fas fa-arrow-up"></i>
                    +12% за месяц
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Новых за сегодня</span>
                    <div class="metric-icon new">
                        <i class="fas fa-user-plus"></i>
                    </div>
                </div>
                <div class="metric-value">${stats.newUsersToday}</div>
                <div class="metric-change positive">
                    <i class="fas fa-arrow-up"></i>
                    +15% от вчера
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Активных за 24 часа</span>
                    <div class="metric-icon active">
                        <i class="fas fa-user-check"></i>
                    </div>
                </div>
                <div class="metric-value">${stats.activeUsers24h.toLocaleString()}</div>
                <div class="metric-change positive">
                    <i class="fas fa-arrow-up"></i>
                    +8% за день
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Платные подписчики</span>
                    <div class="metric-icon subscriptions">
                        <i class="fas fa-crown"></i>
                    </div>
                </div>
                <div class="metric-value">${stats.paidSubscribers.toLocaleString()}</div>
                <div class="metric-change neutral">
                    ${stats.paidSubscribersPercent}% от общего числа
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">С автооткликами</span>
                    <div class="metric-icon auto">
                        <i class="fas fa-magic"></i>
                    </div>
                </div>
                <div class="metric-value">${stats.autoResponseUsers.toLocaleString()}</div>
                <div class="metric-change positive">
                    <i class="fas fa-arrow-up"></i>
                    +5% за неделю
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">С AI-откликами</span>
                    <div class="metric-icon ai">
                        <i class="fas fa-brain"></i>
                    </div>
                </div>
                <div class="metric-value">${stats.aiResponseUsers.toLocaleString()}</div>
                <div class="metric-change positive">
                    <i class="fas fa-arrow-up"></i>
                    +12% за неделю
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Среднее откликов на пользователя</span>
                    <div class="metric-icon responses">
                        <i class="fas fa-chart-line"></i>
                    </div>
                </div>
                <div class="metric-value">${stats.avgResponsesPerUser}</div>
                <div class="metric-change positive">
                    <i class="fas fa-arrow-up"></i>
                    +3% за месяц
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Откликов за 24 часа</span>
                    <div class="metric-icon responses">
                        <i class="fas fa-paper-plane"></i>
                    </div>
                </div>
                <div class="metric-value">${stats.responses24h.toLocaleString()}</div>
                <div class="metric-change positive">
                    <i class="fas fa-arrow-up"></i>
                    +18% за день
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Конверсия в премиум (30 дней)</span>
                    <div class="metric-icon conversion">
                        <i class="fas fa-percentage"></i>
                    </div>
                </div>
                <div class="metric-value">${stats.conversion30d}%</div>
                <div class="metric-change positive">
                    <i class="fas fa-arrow-up"></i>
                    +2.1% за месяц
                </div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="charts-section">
            <div class="chart-card">
                <div class="chart-header">
                    <h3 class="chart-title">Динамика регистраций</h3>
                    <p class="chart-subtitle">Новые пользователи по дням за последний месяц</p>
                </div>
                <div class="chart-placeholder">
                    📈 График регистраций (Chart.js)
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-header">
                    <h3 class="chart-title">Платящие пользователи</h3>
                    <p class="chart-subtitle">Рост подписчиков</p>
                </div>
                <div class="chart-placeholder">
                    💳 График подписок
                </div>
            </div>
        </div>

        <!-- Revenue Section -->
        <div class="revenue-section">
            <div class="chart-card">
                <div class="chart-header">
                    <h3 class="chart-title">Денежные метрики</h3>
                    <p class="chart-subtitle">Доходы и финансовые показатели</p>
                </div>
                <div class="revenue-grid">
                    <div class="revenue-card">
                        <div class="revenue-label">Доход сегодня</div>
                        <div class="revenue-value">${(stats.revenueToday / 1000).toFixed(0)}к ₽</div>
                        <div class="revenue-change">+12% от вчера</div>
                    </div>
                    <div class="revenue-card">
                        <div class="revenue-label">Доход за неделю</div>
                        <div class="revenue-value">${(stats.revenueWeek / 1000).toFixed(0)}к ₽</div>
                        <div class="revenue-change">+8% от пред. недели</div>
                    </div>
                    <div class="revenue-card">
                        <div class="revenue-label">Доход за месяц</div>
                        <div class="revenue-value">${(stats.revenueMonth / 1000).toFixed(0)}к ₽</div>
                        <div class="revenue-change">+15% от пред. месяца</div>
                    </div>
                    <div class="revenue-card">
                        <div class="revenue-label">Общий доход</div>
                        <div class="revenue-value">${(stats.revenueTotal / 1000000).toFixed(1)}М ₽</div>
                        <div class="revenue-change">Всё время</div>
                    </div>
                    <div class="revenue-card">
                        <div class="revenue-label">Доход с AI-откликов</div>
                        <div class="revenue-value">${(stats.revenueAI / 1000).toFixed(0)}к ₽</div>
                        <div class="revenue-change">AI-отклики</div>
                    </div>
                    <div class="revenue-card">
                        <div class="revenue-label">Доход с тарифов</div>
                        <div class="revenue-value">${(stats.revenueSubscriptions / 1000).toFixed(0)}к ₽</div>
                        <div class="revenue-change">Подписки</div>
                    </div>
                    <div class="revenue-card">
                        <div class="revenue-label">Средний чек</div>
                        <div class="revenue-value">${stats.avgCheck} ₽</div>
                        <div class="revenue-change">За последний месяц</div>
                    </div>
                    <div class="revenue-card">
                        <div class="revenue-label">ARPU</div>
                        <div class="revenue-value">${stats.arpu} ₽</div>
                        <div class="revenue-change">Доход на пользователя</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Bot Status Section -->
        <div class="bot-status-section">
            <div class="status-card">
                <div class="status-header">
                    <div class="status-icon online">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div>
                        <div class="status-title">Статус бота</div>
                        <div class="status-value">Онлайн</div>
                        <div class="status-description">Работает стабильно</div>
                    </div>
                </div>
            </div>

            <div class="status-card">
                <div class="status-header">
                    <div class="status-icon balance">
                        <i class="fas fa-wallet"></i>
                    </div>
                    <div>
                        <div class="status-title">Баланс OpenAI</div>
                        <div class="status-value">$${stats.openaiBalance}</div>
                        <div class="status-description">Достаточно на 2 недели</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Funnel Section -->
        <div class="funnel-section">
            <div class="funnel-card">
                <div class="chart-header">
                    <h3 class="chart-title">Воронка конверсии</h3>
                    <p class="chart-subtitle">Путь пользователя от регистрации до подписки</p>
                </div>
                <div class="funnel-steps">
                    <div class="funnel-step">
                        <div class="funnel-number">15,847</div>
                        <div class="funnel-label">Зашли в бота</div>
                    </div>
                    <div class="funnel-step">
                        <div class="funnel-number">12,456</div>
                        <div class="funnel-label">Подключили HH</div>
                        <div class="funnel-rate">78.6%</div>
                    </div>
                    <div class="funnel-step">
                        <div class="funnel-number">8,923</div>
                        <div class="funnel-label">Сделали 20 откликов</div>
                        <div class="funnel-rate">71.6%</div>
                    </div>
                    <div class="funnel-step">
                        <div class="funnel-number">2,891</div>
                        <div class="funnel-label">Оформили подписку</div>
                        <div class="funnel-rate">32.4%</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getUsersHTML() {
    const users = mockData.users;
    
    const getStatusBadge = (status) => {
        const statusMap = {
            'active': { class: 'status-active', text: 'Активен' },
            'inactive': { class: 'status-inactive', text: 'Неактивен' },
            'banned': { class: 'status-banned', text: 'Заблокирован' }
        };
        const statusInfo = statusMap[status] || { class: 'status-inactive', text: status };
        return `<span class="status-badge ${statusInfo.class}">${statusInfo.text}</span>`;
    };
    
    const getSubscriptionBadge = (subscription) => {
        const subMap = {
            'month': { class: 'subscription-premium', text: 'Месяц' },
            'week': { class: 'subscription-basic', text: 'Неделя' },
            'quarter': { class: 'subscription-premium', text: 'Квартал' },
            'none': { class: 'subscription-none', text: 'Нет' }
        };
        const subInfo = subMap[subscription] || { class: 'subscription-none', text: subscription };
        return `<span class="subscription-badge ${subInfo.class}">${subInfo.text}</span>`;
    };
    
    const getHHBadge = (connected) => {
        return connected
            ? '<span class="feature-badge feature-enabled">Подключен</span>'
            : '<span class="feature-badge feature-disabled">Не подключен</span>';
    };
    
    const getFeatureBadge = (enabled, enabledText = 'Включено', disabledText = 'Выключено') => {
        return enabled
            ? `<span class="feature-badge feature-enabled">${enabledText}</span>`
            : `<span class="feature-badge feature-disabled">${disabledText}</span>`;
    };
    
    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    };
    
    const tableRows = users.map(user => `
        <tr class="user-row" data-user-id="${user.id}">
            <td class="user-telegram-id">${user.telegramId}</td>
            <td class="user-name">${user.name}</td>
            <td class="user-username">${user.username}</td>
            <td class="user-registration">${formatDate(user.registrationDate)}</td>
            <td class="user-hh">${getHHBadge(user.hhConnected)}</td>
            <td class="user-subscription">${getSubscriptionBadge(user.subscription)}</td>
            <td class="user-subscription-end">${user.subscriptionEnd ? formatDate(user.subscriptionEnd) : '—'}</td>
            <td class="user-activity">${formatDate(user.lastActivity)}</td>
            <td class="user-balance">${user.balance.toLocaleString()} ₽</td>
            <td class="user-responses">${user.totalResponses}</td>
            <td class="user-auto">${getFeatureBadge(user.autoResponses)}</td>
            <td class="user-ai">${user.aiResponsesCount}</td>
            <td class="user-status">${getStatusBadge(user.status)}</td>
            <td class="user-actions">
                <div class="action-buttons">
                    <button class="action-btn action-edit" onclick="openUserProfile(${user.id})" title="Редактировать">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    return `
        <div class="users-section">
            <!-- Header -->
            <div class="users-header">
                <div class="users-title-section">
                    <h1 class="users-title">Пользователи</h1>
                    <p class="users-subtitle">Управление пользователями и их данными</p>
                </div>
                <div class="users-actions">
                    <button class="btn btn-secondary" onclick="exportUsers()">
                        <i class="fas fa-download"></i>
                        Экспорт
                    </button>
                </div>
            </div>

            <!-- Filters and Search -->
            <div class="users-filters">
                <div class="filter-group">
                    <div class="search-container">
                        <i class="fas fa-search search-icon"></i>
                        <input type="text" class="search-input" placeholder="Поиск по имени, username, Telegram ID..." id="users-search">
                    </div>
                </div>
                
                <div class="filter-group">
                    <select class="filter-select" id="status-filter">
                        <option value="">Все статусы</option>
                        <option value="active">Активные</option>
                        <option value="inactive">Неактивные</option>
                        <option value="banned">Заблокированные</option>
                    </select>
                    
                    <select class="filter-select" id="subscription-filter">
                        <option value="">Все подписки</option>
                        <option value="month">Месяц</option>
                        <option value="week">Неделя</option>
                        <option value="quarter">Квартал</option>
                        <option value="none">Без подписки</option>
                    </select>
                    
                    <select class="filter-select" id="hh-filter">
                        <option value="">HH подключение</option>
                        <option value="connected">Подключен</option>
                        <option value="not-connected">Не подключен</option>
                    </select>
                    
                    <button class="btn btn-ghost" onclick="clearFilters()">
                        <i class="fas fa-times"></i>
                        Очистить
                    </button>
                </div>
            </div>

            <!-- Users Table -->
            <div class="users-table-container">
                <table class="users-table">
                    <thead class="users-table-header">
                        <tr>
                            <th class="sortable" data-sort="telegramId">
                                Telegram ID
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="name">
                                Имя
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="username">
                                Ник
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="registrationDate">
                                Регистрация
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="hhConnected">
                                HH подключение
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="subscription">
                                Подписка
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="subscriptionEnd">
                                Окончание подписки
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="lastActivity">
                                Последняя активность
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="balance">
                                Баланс
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="totalResponses">
                                Откликов
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="autoResponses">
                                Автоотклики
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="aiResponsesCount">
                                AI-отклики
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="status">
                                Статус
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody class="users-table-body">
                        ${tableRows}
                    </tbody>
                </table>
            </div>

            <!-- Pagination -->
            <div class="users-pagination">
                <div class="pagination-info">
                    Показано <span class="pagination-current">1-${users.length}</span> из <span class="pagination-total">${users.length}</span> пользователей
                </div>
                <div class="pagination-controls">
                    <button class="pagination-btn" disabled>
                        <i class="fas fa-chevron-left"></i>
                        Предыдущая
                    </button>
                    <div class="pagination-pages">
                        <button class="pagination-page active">1</button>
                    </div>
                    <button class="pagination-btn" disabled>
                        Следующая
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- User Modal -->
        <div class="user-modal-overlay" id="userModal" onclick="closeUserModal()">
            <div class="user-modal" onclick="event.stopPropagation()">
                <div class="user-modal-header">
                    <h2 class="user-modal-title">Информация о пользователе</h2>
                    <button class="user-modal-close" onclick="closeUserModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="user-modal-content" id="userModalContent">
                    <!-- Content will be populated by JavaScript -->
                </div>
            </div>
        </div>
    `;
}

function getSubscriptionsHTML() {
    const subscriptions = mockData.subscriptions;
    const tableRows = subscriptions.map(sub => `
        <tr>
            <td>${sub.userId}</td>
            <td>${sub.userName}</td>
            <td>${sub.type}</td>
            <td>${sub.endDate}</td>
            <td><span class="badge ${sub.status === 'Активна' ? 'badge-success' : 'badge-danger'}">${sub.status}</span></td>
            <td>${sub.amount}₽</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn edit" onclick="extendSubscription(${sub.userId})">Продлить</button>
                    <button class="action-btn delete" onclick="cancelSubscription(${sub.userId})">Отключить</button>
                </div>
            </td>
        </tr>
    `).join('');
    
    return `
        <div class="table-container">
            <div class="table-header">
                <h2 class="table-title">Подписки</h2>
                <div class="table-actions">
                    <input type="text" class="search-box" placeholder="Поиск подписок..." id="subscriptions-search">
                    <button class="btn btn-primary" onclick="addSubscription()">
                        <i class="fas fa-plus"></i>
                        Добавить подписку
                    </button>
                </div>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID пользователя</th>
                        <th>Имя пользователя</th>
                        <th>Тип подписки</th>
                        <th>Окончание</th>
                        <th>Статус</th>
                        <th>Сумма</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
}

function getResponsesHTML() {
    const responses = mockData.responses;
    const tableRows = responses.map(response => `
        <tr>
            <td>${response.id}</td>
            <td>${response.userId}</td>
            <td>${response.userName}</td>
            <td>${response.date}</td>
            <td>${response.resume}</td>
            <td>${response.vacancy}</td>
            <td>${response.company}</td>
            <td><span class="badge ${response.status === 'Отправлен' ? 'badge-info' : response.status === 'Просмотрен' ? 'badge-warning' : 'badge-danger'}">${response.status}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn view" onclick="viewResponse(${response.id})">Просмотр</button>
                    <button class="action-btn edit" onclick="goToUser(${response.userId})">К пользователю</button>
                </div>
            </td>
        </tr>
    `).join('');
    
    return `
        <div class="table-container">
            <div class="table-header">
                <h2 class="table-title">Отклики</h2>
                <div class="table-actions">
                    <input type="text" class="search-box" placeholder="Поиск откликов..." id="responses-search">
                    <select class="form-input" style="width: auto; margin-left: 1rem;">
                        <option value="">Все статусы</option>
                        <option value="sent">Отправлен</option>
                        <option value="viewed">Просмотрен</option>
                        <option value="rejected">Отклонен</option>
                    </select>
                </div>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>ID пользователя</th>
                        <th>Имя пользователя</th>
                        <th>Дата</th>
                        <th>Резюме</th>
                        <th>Вакансия</th>
                        <th>Компания</th>
                        <th>Статус</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
}

function getAutoResponsesHTML() {
    const autoResponses = mockData.autoResponses;
    const tableRows = autoResponses.map(ar => `
        <tr>
            <td>${ar.userId}</td>
            <td>${ar.userName}</td>
            <td><span class="badge ${ar.status === 'Активно' ? 'badge-success' : 'badge-danger'}">${ar.status}</span></td>
            <td>${ar.lastRun}</td>
            <td>${ar.filters}</td>
            <td>${ar.responsesCount}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn ${ar.status === 'Активно' ? 'delete' : 'edit'}" onclick="toggleAutoResponse(${ar.userId})">
                        ${ar.status === 'Активно' ? 'Отключить' : 'Включить'}
                    </button>
                    <button class="action-btn view" onclick="viewAutoResponseSettings(${ar.userId})">Настройки</button>
                </div>
            </td>
        </tr>
    `).join('');
    
    return `
        <div class="table-container">
            <div class="table-header">
                <h2 class="table-title">Автоотклики</h2>
                <div class="table-actions">
                    <input type="text" class="search-box" placeholder="Поиск пользователей..." id="auto-responses-search">
                    <select class="form-input" style="width: auto; margin-left: 1rem;">
                        <option value="">Все статусы</option>
                        <option value="active">Активно</option>
                        <option value="inactive">Неактивно</option>
                    </select>
                </div>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID пользователя</th>
                        <th>Имя пользователя</th>
                        <th>Статус</th>
                        <th>Последний запуск</th>
                        <th>Фильтры</th>
                        <th>Откликов отправлено</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
}

function getAIResponsesHTML() {
    const aiResponses = mockData.aiResponses;
    const tableRows = aiResponses.map(ai => `
        <tr>
            <td>${ai.id}</td>
            <td>${ai.date}</td>
            <td>${ai.userId}</td>
            <td>${ai.userName}</td>
            <td>${ai.vacancy}</td>
            <td>${ai.keyword}</td>
            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${ai.responseText}">${ai.responseText}</td>
            <td><span class="badge ${ai.status === 'Отправлен' ? 'badge-success' : 'badge-warning'}">${ai.status}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn view" onclick="viewAIResponse(${ai.id})">Просмотр</button>
                    <button class="action-btn edit" onclick="copyAIResponse(${ai.id})">Копировать</button>
                    ${ai.status === 'Черновик' ? '<button class="action-btn message" onclick="sendAIResponse(' + ai.id + ')">Отправить</button>' : ''}
                </div>
            </td>
        </tr>
    `).join('');
    
    return `
        <div class="table-container">
            <div class="table-header">
                <h2 class="table-title">AI-отклики</h2>
                <div class="table-actions">
                    <input type="text" class="search-box" placeholder="Поиск AI-откликов..." id="ai-responses-search">
                    <select class="form-input" style="width: auto; margin-left: 1rem;">
                        <option value="">Все статусы</option>
                        <option value="sent">Отправлен</option>
                        <option value="draft">Черновик</option>
                    </select>
                </div>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Дата</th>
                        <th>ID пользователя</th>
                        <th>Имя пользователя</th>
                        <th>Вакансия</th>
                        <th>Ключевое слово</th>
                        <th>Текст отклика</th>
                        <th>Статус</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
}

function getAnalyticsHTML() {
    return `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-card-header">
                    <span class="stat-card-title">Рост пользователей</span>
                    <div class="stat-card-icon users">
                        <i class="fas fa-chart-line"></i>
                    </div>
                </div>
                <div class="stat-card-value">+12.5%</div>
                <div class="stat-card-change positive">
                    <i class="fas fa-arrow-up"></i>
                    За последний месяц
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-card-header">
                    <span class="stat-card-title">Удержание пользователей</span>
                    <div class="stat-card-icon conversion">
                        <i class="fas fa-users"></i>
                    </div>
                </div>
                <div class="stat-card-value">68.3%</div>
                <div class="stat-card-change positive">
                    <i class="fas fa-arrow-up"></i>
                    30-дневное удержание
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-card-header">
                    <span class="stat-card-title">Среднее откликов в день</span>
                    <div class="stat-card-icon responses">
                        <i class="fas fa-paper-plane"></i>
                    </div>
                </div>
                <div class="stat-card-value">1,247</div>
                <div class="stat-card-change positive">
                    <i class="fas fa-arrow-up"></i>
                    +8% за неделю
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h3 class="chart-title">Активность по времени</h3>
                <p class="chart-subtitle">Когда пользователи наиболее активны</p>
            </div>
            <div style="height: 300px; display: flex; align-items: center; justify-content: center; background: #f8f9fa; border-radius: 8px;">
                <p style="color: #6c757d;">График активности по времени</p>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h3 class="chart-title">ТОП пользователей по активности</h3>
                <p class="chart-subtitle">Самые активные пользователи за месяц</p>
            </div>
            <div style="height: 250px; display: flex; align-items: center; justify-content: center; background: #f8f9fa; border-radius: 8px;">
                <p style="color: #6c757d;">Рейтинг активных пользователей</p>
            </div>
        </div>
    `;
}

function getNotificationsHTML() {
    const notifications = mockData.notifications;
    const tableRows = notifications.map(notif => `
        <tr>
            <td>${notif.id}</td>
            <td>${notif.userId === 'all' ? 'Все пользователи' : notif.userId}</td>
            <td>${notif.userName}</td>
            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${notif.text}">${notif.text}</td>
            <td>${notif.time}</td>
            <td><span class="badge ${notif.status === 'Отправлено' ? 'badge-success' : notif.status === 'Доставлено' ? 'badge-info' : 'badge-warning'}">${notif.status}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn view" onclick="viewNotification(${notif.id})">Просмотр</button>
                    <button class="action-btn delete" onclick="deleteNotification(${notif.id})">Удалить</button>
                </div>
            </td>
        </tr>
    `).join('');
    
    return `
        <div class="table-container">
            <div class="table-header">
                <h2 class="table-title">Уведомления</h2>
                <div class="table-actions">
                    <input type="text" class="search-box" placeholder="Поиск уведомлений..." id="notifications-search">
                    <button class="btn btn-primary" onclick="createNotification()">
                        <i class="fas fa-plus"></i>
                        Создать уведомление
                    </button>
                    <button class="btn btn-secondary" onclick="sendBulkNotification()">
                        <i class="fas fa-bullhorn"></i>
                        Массовая рассылка
                    </button>
                </div>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>ID пользователя</th>
                        <th>Имя пользователя</th>
                        <th>Текст</th>
                        <th>Время</th>
                        <th>Статус</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
}

function getBotSettingsHTML() {
    return `
        <div class="table-container">
            <div class="table-header">
                <h2 class="table-title">Настройки бота</h2>
                <div class="table-actions">
                    <button class="btn btn-success" onclick="saveSettings()">
                        <i class="fas fa-save"></i>
                        Сохранить
                    </button>
                    <button class="btn btn-secondary" onclick="testSettings()">
                        <i class="fas fa-vial"></i>
                        Тестировать
                    </button>
                </div>
            </div>
            <div style="padding: 2rem;">
                <div class="form-group">
                    <label class="form-label">Telegram Bot Token</label>
                    <input type="text" class="form-input" value="тут токен тг ботика" placeholder="Введите токен Telegram бота">
                </div>
                
                <div class="form-group">
                    <label class="form-label">HH API Client ID</label>
                    <input type="text" class="form-input" value="и сюда" placeholder="Введите Client ID для HH API">
                </div>
                
                <div class="form-group">
                    <label class="form-label">HH API Client Secret</label>
                    <input type="password" class="form-input" value="и сюда" placeholder="Введите Client Secret для HH API">
                </div>
                
                <div class="form-group">
                    <label class="form-label">OpenAI API Key</label>
                    <input type="password" class="form-input" value=""OPENAI_API_KEY_HERE" placeholder="Введите API ключ OpenAI">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Redirect Domain</label>
                    <input type="text" class="form-input" value="https://a5e7c129bdc791.lhr.life" placeholder="Введите домен для редиректа">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Webhook URL</label>
                    <input type="text" class="form-input" value="https://a5e7c129bdc791.lhr.life/webhook" placeholder="Введите URL для webhook">
                </div>
            </div>
        </div>
    `
}

function getMessagesHTML() {
    const broadcasts = mockData.broadcasts;
    
    const getStatusBadge = (status) => {
        const statusMap = {
            'sent': { class: 'status-sent', text: 'Отправлено', icon: 'fas fa-check-circle' },
            'draft': { class: 'status-draft', text: 'Черновик', icon: 'fas fa-edit' },
            'sending': { class: 'status-sending', text: 'Отправляется', icon: 'fas fa-spinner fa-spin' },
            'failed': { class: 'status-failed', text: 'Ошибка', icon: 'fas fa-exclamation-circle' }
        };
        const statusInfo = statusMap[status] || { class: 'status-draft', text: status, icon: 'fas fa-question' };
        return `<span class="broadcast-status ${statusInfo.class}"><i class="${statusInfo.icon}"></i> ${statusInfo.text}</span>`;
    };
    
    const getAudienceBadge = (audience, count) => {
        const audienceMap = {
            'all': { class: 'audience-all', text: 'Все пользователи' },
            'premium': { class: 'audience-premium', text: 'Премиум' },
            'no_subscription': { class: 'audience-free', text: 'Без подписки' },
            'active': { class: 'audience-active', text: 'Активные' },
            'auto_responses': { class: 'audience-auto', text: 'С автооткликами' },
            'ai_responses': { class: 'audience-ai', text: 'С AI-откликами' }
        };
        const audienceInfo = audienceMap[audience] || { class: 'audience-other', text: audience };
        return `<span class="audience-badge ${audienceInfo.class}">${audienceInfo.text} (${count.toLocaleString()})</span>`;
    };
    
    const formatDate = (dateStr) => {
        if (!dateStr) return '—';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };
    
    const getDeliveryStats = (broadcast) => {
        if (broadcast.status !== 'sent') return '—';
        const deliveryRate = ((broadcast.delivered / broadcast.audienceCount) * 100).toFixed(1);
        const readRate = ((broadcast.read / broadcast.delivered) * 100).toFixed(1);
        return `
            <div class="delivery-stats">
                <div class="stat-item">
                    <span class="stat-label">Доставлено:</span>
                    <span class="stat-value">${broadcast.delivered.toLocaleString()} (${deliveryRate}%)</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Прочитано:</span>
                    <span class="stat-value">${broadcast.read.toLocaleString()} (${readRate}%)</span>
                </div>
                ${broadcast.failed > 0 ? `
                    <div class="stat-item error">
                        <span class="stat-label">Ошибки:</span>
                        <span class="stat-value">${broadcast.failed.toLocaleString()}</span>
                    </div>
                ` : ''}
            </div>
        `;
    };
    
    const historyRows = broadcasts.map(broadcast => `
        <tr class="broadcast-row" data-broadcast-id="${broadcast.id}">
            <td class="broadcast-title">
                <div class="title-content">
                    <div class="broadcast-name">${broadcast.title}</div>
                    <div class="broadcast-preview">${broadcast.message.substring(0, 80)}${broadcast.message.length > 80 ? '...' : ''}</div>
                </div>
            </td>
            <td class="broadcast-audience">${getAudienceBadge(broadcast.audience, broadcast.audienceCount)}</td>
            <td class="broadcast-date">${formatDate(broadcast.sentAt)}</td>
            <td class="broadcast-status">${getStatusBadge(broadcast.status)}</td>
            <td class="broadcast-stats">${getDeliveryStats(broadcast)}</td>
            <td class="broadcast-actions">
                <div class="action-buttons">
                    <button class="action-btn action-view" onclick="viewBroadcast(${broadcast.id})" title="Просмотр">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${broadcast.status === 'draft' ? `
                        <button class="action-btn action-edit" onclick="editBroadcast(${broadcast.id})" title="Редактировать">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn action-send" onclick="sendBroadcast(${broadcast.id})" title="Отправить">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    ` : ''}
                    <button class="action-btn action-copy" onclick="duplicateBroadcast(${broadcast.id})" title="Дублировать">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="action-btn action-delete" onclick="deleteBroadcast(${broadcast.id})" title="Удалить">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    return `
        <div class="broadcasts-section">
            <!-- Header -->
            <div class="broadcasts-header">
                <div class="broadcasts-title-section">
                    <h1 class="broadcasts-title">Рассылки</h1>
                    <p class="broadcasts-subtitle">Создание и управление рассылками для пользователей бота</p>
                </div>
                <div class="broadcasts-actions">
                    <button class="btn btn-secondary" onclick="exportBroadcasts()">
                        <i class="fas fa-download"></i>
                        Экспорт
                    </button>
                    <button class="btn btn-primary" onclick="createNewBroadcast()">
                        <i class="fas fa-plus"></i>
                        Новая рассылка
                    </button>
                </div>
            </div>

            <!-- Quick Stats -->
            <div class="broadcast-stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-paper-plane"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${broadcasts.filter(b => b.status === 'sent').length}</div>
                        <div class="stat-label">Отправлено рассылок</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-users"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${broadcasts.filter(b => b.status === 'sent').reduce((sum, b) => sum + b.delivered, 0).toLocaleString()}</div>
                        <div class="stat-label">Сообщений доставлено</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-eye"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${broadcasts.filter(b => b.status === 'sent').reduce((sum, b) => sum + b.read, 0).toLocaleString()}</div>
                        <div class="stat-label">Прочитано</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-edit"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value">${broadcasts.filter(b => b.status === 'draft').length}</div>
                        <div class="stat-label">Черновиков</div>
                    </div>
                </div>
            </div>

            <!-- Filters -->
            <div class="broadcasts-filters">
                <div class="filter-group">
                    <div class="search-container">
                        <i class="fas fa-search search-icon"></i>
                        <input type="text" class="search-input" placeholder="Поиск по названию или тексту..." id="broadcasts-search">
                    </div>
                </div>
                
                <div class="filter-group">
                    <select class="filter-select" id="status-filter">
                        <option value="">Все статусы</option>
                        <option value="sent">Отправленные</option>
                        <option value="draft">Черновики</option>
                        <option value="sending">Отправляются</option>
                        <option value="failed">С ошибками</option>
                    </select>
                    
                    <select class="filter-select" id="audience-filter">
                        <option value="">Все аудитории</option>
                        <option value="all">Все пользователи</option>
                        <option value="premium">Премиум</option>
                        <option value="no_subscription">Без подписки</option>
                        <option value="active">Активные</option>
                        <option value="auto_responses">С автооткликами</option>
                        <option value="ai_responses">С AI-откликами</option>
                    </select>
                    
                    <button class="btn btn-ghost" onclick="clearBroadcastFilters()">
                        <i class="fas fa-times"></i>
                        Очистить
                    </button>
                </div>
            </div>

            <!-- Broadcasts History Table -->
            <div class="broadcasts-table-container">
                <table class="broadcasts-table">
                    <thead class="broadcasts-table-header">
                        <tr>
                            <th class="sortable" data-sort="title">
                                Рассылка
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="audience">
                                Аудитория
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="sentAt">
                                Дата отправки
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="status">
                                Статус
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th>Статистика</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody class="broadcasts-table-body">
                        ${historyRows}
                    </tbody>
                </table>
            </div>

            <!-- Pagination -->
            <div class="broadcasts-pagination">
                <div class="pagination-info">
                    Показано <span class="pagination-current">1-${broadcasts.length}</span> из <span class="pagination-total">${broadcasts.length}</span> рассылок
                </div>
                <div class="pagination-controls">
                    <button class="pagination-btn" disabled>
                        <i class="fas fa-chevron-left"></i>
                        Предыдущая
                    </button>
                    <div class="pagination-pages">
                        <button class="pagination-page active">1</button>
                    </div>
                    <button class="pagination-btn" disabled>
                        Следующая
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- Broadcast Creation/Edit Modal -->
        <div class="broadcast-modal-overlay" id="broadcastModal" onclick="closeBroadcastModal()">
            <div class="broadcast-modal" onclick="event.stopPropagation()">
                <div class="broadcast-modal-header">
                    <h2 class="broadcast-modal-title" id="broadcastModalTitle">Новая рассылка</h2>
                    <button class="broadcast-modal-close" onclick="closeBroadcastModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="broadcast-modal-content" id="broadcastModalContent">
                    <!-- Content will be populated by JavaScript -->
                </div>
            </div>
        </div>

        <!-- Broadcast View Modal -->
        <div class="broadcast-view-modal-overlay" id="broadcastViewModal" onclick="closeBroadcastViewModal()">
            <div class="broadcast-view-modal" onclick="event.stopPropagation()">
                <div class="broadcast-view-modal-header">
                    <h2 class="broadcast-view-modal-title" id="broadcastViewModalTitle">Просмотр рассылки</h2>
                    <button class="broadcast-view-modal-close" onclick="closeBroadcastViewModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="broadcast-view-modal-content" id="broadcastViewModalContent">
                    <!-- Content will be populated by JavaScript -->
                </div>
            </div>
        </div>
    `;
}

function getIntegrationsHTML() {
    return `
        <div class="table-container">
            <div class="table-header">
                <h2 class="table-title">Интеграции</h2>
                <div class="table-actions">
                    <button class="btn btn-primary" onclick="addIntegration()">
                        <i class="fas fa-plus"></i>
                        Добавить интеграцию
                    </button>
                </div>
            </div>
            <div style="padding: 2rem;">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <span class="stat-card-title">HH.ru API</span>
                            <div class="stat-card-icon status">
                                <i class="fab fa-hh"></i>
                            </div>
                        </div>
                        <div class="stat-card-value">Подключено</div>
                        <div class="stat-card-change positive">
                            <i class="fas fa-check-circle"></i>
                            Работает стабильно
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <span class="stat-card-title">OpenAI API</span>
                            <div class="stat-card-icon status">
                                <i class="fas fa-brain"></i>
                            </div>
                        </div>
                        <div class="stat-card-value">Подключено</div>
                        <div class="stat-card-change positive">
                            <i class="fas fa-check-circle"></i>
                            Активно используется
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <span class="stat-card-title">Telegram Bot API</span>
                            <div class="stat-card-icon status">
                                <i class="fab fa-telegram"></i>
                            </div>
                        </div>
                        <div class="stat-card-value">Подключено</div>
                        <div class="stat-card-change positive">
                            <i class="fas fa-check-circle"></i>
                            Онлайн
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getModulesHTML() {
    return `
        <div class="table-container">
            <div class="table-header">
                <h2 class="table-title">Модули и разделы</h2>
                <div class="table-actions">
                    <button class="btn btn-primary" onclick="addModule()">
                        <i class="fas fa-plus"></i>
                        Добавить модуль
                    </button>
                </div>
            </div>
            <div style="padding: 2rem;">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <span class="stat-card-title">Реферальная программа</span>
                            <div class="stat-card-icon status">
                                <i class="fas fa-users"></i>
                            </div>
                        </div>
                        <div class="stat-card-value">Активен</div>
                        <div class="stat-card-change positive">
                            <i class="fas fa-toggle-on"></i>
                            Включен
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <span class="stat-card-title">Промо-акции</span>
                            <div class="stat-card-icon status">
                                <i class="fas fa-gift"></i>
                            </div>
                        </div>
                        <div class="stat-card-value">Неактивен</div>
                        <div class="stat-card-change negative">
                            <i class="fas fa-toggle-off"></i>
                            Отключен
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-card-header">
                            <span class="stat-card-title">Тестовые функции</span>
                            <div class="stat-card-icon status">
                                <i class="fas fa-flask"></i>
                            </div>
                        </div>
                        <div class="stat-card-value">Активен</div>
                        <div class="stat-card-change positive">
                            <i class="fas fa-toggle-on"></i>
                            Бета-тестирование
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getTextsHTML() {
    const texts = mockData.texts;
    
    const getCategoryBadge = (category) => {
        const categoryMap = {
            'welcome': { class: 'category-welcome', text: 'Приветствие' },
            'subscription': { class: 'category-subscription', text: 'Подписка' },
            'support': { class: 'category-support', text: 'Поддержка' },
            'responses': { class: 'category-responses', text: 'Отклики' },
            'buttons': { class: 'category-buttons', text: 'Кнопки' },
            'cover_letters': { class: 'category-letters', text: 'Письма' }
        };
        const catInfo = categoryMap[category] || { class: 'category-other', text: category };
        return `<span class="category-badge ${catInfo.class}">${catInfo.text}</span>`;
    };
    
    const getAttachmentBadge = (hasAttachment, attachment) => {
        if (!hasAttachment) return '<span class="attachment-badge no-attachment">Без вложения</span>';
        
        const typeMap = {
            'image': { icon: 'fas fa-image', text: 'Изображение' },
            'video': { icon: 'fas fa-video', text: 'Видео' },
            'document': { icon: 'fas fa-file', text: 'Документ' }
        };
        const typeInfo = typeMap[attachment.type] || { icon: 'fas fa-paperclip', text: 'Файл' };
        return `<span class="attachment-badge has-attachment"><i class="${typeInfo.icon}"></i> ${typeInfo.text}</span>`;
    };
    
    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };
    
    const tableRows = texts.map(text => `
        <tr class="text-row" data-text-id="${text.id}">
            <td class="text-category">${getCategoryBadge(text.category)}</td>
            <td class="text-name">
                <div class="text-title">${text.name}</div>
                <div class="text-key">${text.key}</div>
            </td>
            <td class="text-preview">
                <div class="text-content-preview">${text.text.substring(0, 100)}${text.text.length > 100 ? '...' : ''}</div>
            </td>
            <td class="text-attachment">${getAttachmentBadge(text.hasAttachment, text.attachment)}</td>
            <td class="text-modified">${formatDate(text.lastModified)}</td>
            <td class="text-actions">
                <div class="action-buttons">
                    <button class="action-btn action-view" onclick="viewText(${text.id})" title="Просмотр">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="action-btn action-edit" onclick="editText(${text.id})" title="Редактировать">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="action-btn action-copy" onclick="copyText(${text.id})" title="Копировать">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="action-btn action-delete" onclick="deleteText(${text.id})" title="Удалить">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    return `
        <div class="texts-section">
            <!-- Header -->
            <div class="texts-header">
                <div class="texts-title-section">
                    <h1 class="texts-title">Тексты сообщений</h1>
                    <p class="texts-subtitle">Управление текстами сообщений и кнопок бота</p>
                </div>
                <div class="texts-actions">
                    <button class="btn btn-secondary" onclick="exportTexts()">
                        <i class="fas fa-download"></i>
                        Экспорт
                    </button>
                    <button class="btn btn-primary" onclick="addText()">
                        <i class="fas fa-plus"></i>
                        Добавить текст
                    </button>
                </div>
            </div>

            <!-- Filters and Search -->
            <div class="texts-filters">
                <div class="filter-group">
                    <div class="search-container">
                        <i class="fas fa-search search-icon"></i>
                        <input type="text" class="search-input" placeholder="Поиск по названию, ключу или тексту..." id="texts-search">
                    </div>
                </div>
                
                <div class="filter-group">
                    <select class="filter-select" id="category-filter">
                        <option value="">Все категории</option>
                        <option value="welcome">Приветствие</option>
                        <option value="subscription">Подписка</option>
                        <option value="support">Поддержка</option>
                        <option value="responses">Отклики</option>
                        <option value="buttons">Кнопки</option>
                        <option value="cover_letters">Письма</option>
                    </select>
                    
                    <select class="filter-select" id="attachment-filter">
                        <option value="">Все типы</option>
                        <option value="with-attachment">С вложением</option>
                        <option value="without-attachment">Без вложения</option>
                    </select>
                    
                    <button class="btn btn-ghost" onclick="clearTextsFilters()">
                        <i class="fas fa-times"></i>
                        Очистить
                    </button>
                </div>
            </div>

            <!-- Texts Table -->
            <div class="texts-table-container">
                <table class="texts-table">
                    <thead class="texts-table-header">
                        <tr>
                            <th class="sortable" data-sort="category">
                                Категория
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="name">
                                Название
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th>Предварительный просмотр</th>
                            <th class="sortable" data-sort="hasAttachment">
                                Вложение
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th class="sortable" data-sort="lastModified">
                                Изменено
                                <i class="fas fa-sort sort-icon"></i>
                            </th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody class="texts-table-body">
                        ${tableRows}
                    </tbody>
                </table>
            </div>

            <!-- Pagination -->
            <div class="texts-pagination">
                <div class="pagination-info">
                    Показано <span class="pagination-current">1-${texts.length}</span> из <span class="pagination-total">${texts.length}</span> текстов
                </div>
                <div class="pagination-controls">
                    <button class="pagination-btn" disabled>
                        <i class="fas fa-chevron-left"></i>
                        Предыдущая
                    </button>
                    <div class="pagination-pages">
                        <button class="pagination-page active">1</button>
                    </div>
                    <button class="pagination-btn" disabled>
                        Следующая
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- Text Edit Modal -->
        <div class="text-modal-overlay" id="textModal" onclick="closeTextModal()">
            <div class="text-modal" onclick="event.stopPropagation()">
                <div class="text-modal-header">
                    <h2 class="text-modal-title">Редактирование текста</h2>
                    <button class="text-modal-close" onclick="closeTextModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="text-modal-content" id="textModalContent">
                    <!-- Content will be populated by JavaScript -->
                </div>
            </div>
        </div>
    `;
}

function getLogsHTML() {
    const logs = mockData.logs;
    const tableRows = logs.map(log => `
        <tr>
            <td>${log.id}</td>
            <td>${log.date}</td>
            <td>${log.userId || '-'}</td>
            <td>${log.userName}</td>
            <td>${log.action}</td>
            <td><span class="badge ${log.type === 'info' ? 'badge-info' : log.type === 'error' ? 'badge-danger' : 'badge-warning'}">${log.type.toUpperCase()}</span></td>
            <td style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${log.text}">${log.text}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn view" onclick="viewLog(${log.id})">Просмотр</button>
                </div>
            </td>
        </tr>
    `).join('');
    
    return `
        <div class="table-container">
            <div class="table-header">
                <h2 class="table-title">Логи системы</h2>
                <div class="table-actions">
                    <input type="text" class="search-box" placeholder="Поиск в логах..." id="logs-search">
                    <select class="form-input" style="width: auto; margin-left: 1rem;">
                        <option value="">Все типы</option>
                        <option value="info">INFO</option>
                        <option value="error">ERROR</option>
                        <option value="warning">WARNING</option>
                    </select>
                    <button class="btn btn-secondary" onclick="clearLogs()">
                        <i class="fas fa-trash"></i>
                        Очистить логи
                    </button>
                </div>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Дата/Время</th>
                        <th>ID пользователя</th>
                        <th>Пользователь</th>
                        <th>Действие</th>
                        <th>Тип</th>
                        <th>Текст</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
    `;
}

function getPricingHTML() {
    const pricing = mockData.pricing;
    
    return `
        <div class="modern-pricing-section">
            <!-- Header -->
            <div class="modern-pricing-header">
                <div class="pricing-header-content">
                    <div class="pricing-title-group">
                        <h1 class="modern-pricing-title">Управление тарифами</h1>
                        <p class="modern-pricing-subtitle">Настройка цен на подписки и AI-отклики для пользователей бота</p>
                    </div>
                    <div class="pricing-header-actions">
                        <button class="modern-btn modern-btn-secondary" onclick="resetPricingToDefaults()">
                            <i class="fas fa-undo-alt"></i>
                            <span>Сбросить</span>
                        </button>
                        <button class="modern-btn modern-btn-primary" onclick="savePricingSettings()">
                            <i class="fas fa-save"></i>
                            <span>Сохранить</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Pricing Cards Grid -->
            <div class="modern-pricing-grid">
                <!-- Free Responses Card -->
                <div class="modern-pricing-card modern-pricing-card-highlight">
                    <div class="pricing-card-icon">
                        <div class="icon-wrapper icon-gift">
                            <i class="fas fa-gift"></i>
                        </div>
                    </div>
                    <div class="pricing-card-header">
                        <h3 class="pricing-card-title">Бесплатные отклики</h3>
                        <p class="pricing-card-description">Количество бесплатных откликов для новых пользователей</p>
                    </div>
                    <div class="pricing-card-content">
                        <div class="modern-input-group">
                            <label class="modern-input-label">Количество откликов</label>
                            <div class="modern-input-wrapper">
                                <input type="number" class="modern-input" id="freeResponses" value="${pricing.freeResponses}" min="0" max="100" placeholder="10">
                                <span class="input-addon">откликов</span>
                            </div>
                            <div class="input-help">
                                <i class="fas fa-info-circle"></i>
                                <span>Сколько бесплатных откликов получает каждый новый пользователь</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Subscription Pricing Card -->
                <div class="modern-pricing-card modern-pricing-card-full">
                    <div class="pricing-card-icon">
                        <div class="icon-wrapper icon-crown">
                            <i class="fas fa-crown"></i>
                        </div>
                    </div>
                    <div class="pricing-card-header">
                        <h3 class="pricing-card-title">Подписки на бота</h3>
                        <p class="pricing-card-description">Стоимость подписок на различные периоды</p>
                    </div>
                    <div class="pricing-card-content">
                        <div class="modern-pricing-items">
                            <div class="modern-pricing-item">
                                <div class="pricing-item-header">
                                    <span class="pricing-item-period">1 неделя</span>
                                    <span class="pricing-item-badge">Базовый</span>
                                </div>
                                <div class="modern-input-wrapper">
                                    <input type="number" class="modern-input" id="priceWeek" value="${pricing.subscriptionPrices.week}" min="0" placeholder="690">
                                    <span class="input-addon">₽</span>
                                </div>
                            </div>
                            <div class="modern-pricing-item">
                                <div class="pricing-item-header">
                                    <span class="pricing-item-period">1 месяц</span>
                                    <span class="pricing-item-badge pricing-popular">Популярный</span>
                                </div>
                                <div class="modern-input-wrapper">
                                    <input type="number" class="modern-input" id="priceMonth" value="${pricing.subscriptionPrices.month}" min="0" placeholder="1900">
                                    <span class="input-addon">₽</span>
                                </div>
                            </div>
                            <div class="modern-pricing-item">
                                <div class="pricing-item-header">
                                    <span class="pricing-item-period">3 месяца</span>
                                    <span class="pricing-item-badge">Выгодный</span>
                                </div>
                                <div class="modern-input-wrapper">
                                    <input type="number" class="modern-input" id="priceQuarter" value="${pricing.subscriptionPrices.quarter}" min="0" placeholder="4500">
                                    <span class="input-addon">₽</span>
                                </div>
                            </div>
                            <div class="modern-pricing-item">
                                <div class="pricing-item-header">
                                    <span class="pricing-item-period">6 месяцев</span>
                                    <span class="pricing-item-badge">Экономия</span>
                                </div>
                                <div class="modern-input-wrapper">
                                    <input type="number" class="modern-input" id="priceHalfYear" value="${pricing.subscriptionPrices.halfYear}" min="0" placeholder="8500">
                                    <span class="input-addon">₽</span>
                                </div>
                            </div>
                            <div class="modern-pricing-item">
                                <div class="pricing-item-header">
                                    <span class="pricing-item-period">12 месяцев</span>
                                    <span class="pricing-item-badge pricing-best">Лучшая цена</span>
                                </div>
                                <div class="modern-input-wrapper">
                                    <input type="number" class="modern-input" id="priceYear" value="${pricing.subscriptionPrices.year}" min="0" placeholder="15900">
                                    <span class="input-addon">₽</span>
                                </div>
                            </div>
                        </div>
                        <div class="pricing-info-box">
                            <i class="fas fa-lightbulb"></i>
                            <span>Цены должны увеличиваться пропорционально периоду для логичности тарифов</span>
                        </div>
                    </div>
                </div>

                <!-- AI Responses Pricing Card -->
                <div class="modern-pricing-card modern-pricing-card-full">
                    <div class="pricing-card-icon">
                        <div class="icon-wrapper icon-brain">
                            <i class="fas fa-brain"></i>
                        </div>
                    </div>
                    <div class="pricing-card-header">
                        <h3 class="pricing-card-title">AI-отклики</h3>
                        <p class="pricing-card-description">Стоимость пакетов AI-откликов для пользователей</p>
                    </div>
                    <div class="pricing-card-content">
                        <div class="modern-pricing-items">
                            <div class="modern-pricing-item">
                                <div class="pricing-item-header">
                                    <span class="pricing-item-period">30 откликов</span>
                                    <span class="pricing-item-badge">Пробный</span>
                                </div>
                                <div class="modern-input-wrapper">
                                    <input type="number" class="modern-input" id="aiPrice30" value="${pricing.aiResponsesPrices.responses30}" min="0" placeholder="299">
                                    <span class="input-addon">₽</span>
                                </div>
                                <div class="pricing-item-meta">
                                    <span class="cost-per-unit">${(pricing.aiResponsesPrices.responses30 / 30).toFixed(1)} ₽/отклик</span>
                                </div>
                            </div>
                            <div class="modern-pricing-item">
                                <div class="pricing-item-header">
                                    <span class="pricing-item-period">100 откликов</span>
                                    <span class="pricing-item-badge pricing-popular">Популярный</span>
                                </div>
                                <div class="modern-input-wrapper">
                                    <input type="number" class="modern-input" id="aiPrice100" value="${pricing.aiResponsesPrices.responses100}" min="0" placeholder="899">
                                    <span class="input-addon">₽</span>
                                </div>
                                <div class="pricing-item-meta">
                                    <span class="cost-per-unit">${(pricing.aiResponsesPrices.responses100 / 100).toFixed(1)} ₽/отклик</span>
                                </div>
                            </div>
                            <div class="modern-pricing-item">
                                <div class="pricing-item-header">
                                    <span class="pricing-item-period">500 откликов</span>
                                    <span class="pricing-item-badge">Выгодный</span>
                                </div>
                                <div class="modern-input-wrapper">
                                    <input type="number" class="modern-input" id="aiPrice500" value="${pricing.aiResponsesPrices.responses500}" min="0" placeholder="3999">
                                    <span class="input-addon">₽</span>
                                </div>
                                <div class="pricing-item-meta">
                                    <span class="cost-per-unit">${(pricing.aiResponsesPrices.responses500 / 500).toFixed(1)} ₽/отклик</span>
                                </div>
                            </div>
                            <div class="modern-pricing-item">
                                <div class="pricing-item-header">
                                    <span class="pricing-item-period">1000 откликов</span>
                                    <span class="pricing-item-badge">Бизнес</span>
                                </div>
                                <div class="modern-input-wrapper">
                                    <input type="number" class="modern-input" id="aiPrice1000" value="${pricing.aiResponsesPrices.responses1000}" min="0" placeholder="7499">
                                    <span class="input-addon">₽</span>
                                </div>
                                <div class="pricing-item-meta">
                                    <span class="cost-per-unit">${(pricing.aiResponsesPrices.responses1000 / 1000).toFixed(1)} ₽/отклик</span>
                                </div>
                            </div>
                            <div class="modern-pricing-item">
                                <div class="pricing-item-header">
                                    <span class="pricing-item-period">3000 откликов</span>
                                    <span class="pricing-item-badge pricing-best">Максимум</span>
                                </div>
                                <div class="modern-input-wrapper">
                                    <input type="number" class="modern-input" id="aiPrice3000" value="${pricing.aiResponsesPrices.responses3000}" min="0" placeholder="19999">
                                    <span class="input-addon">₽</span>
                                </div>
                                <div class="pricing-item-meta">
                                    <span class="cost-per-unit">${(pricing.aiResponsesPrices.responses3000 / 3000).toFixed(1)} ₽/отклик</span>
                                </div>
                            </div>
                        </div>
                        <div class="pricing-info-box">
                            <i class="fas fa-chart-line"></i>
                            <span>Стоимость за отклик должна уменьшаться при увеличении объема пакета</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Action Bar -->
            <div class="modern-pricing-actions">
                <div class="pricing-actions-content">
                    <div class="pricing-status-info">
                        <div class="status-indicator">
                            <i class="fas fa-check-circle"></i>
                            <span>Все изменения сохраняются автоматически</span>
                        </div>
                        <div class="keyboard-shortcut">
                            <span>Быстрое сохранение:</span>
                            <kbd>Ctrl</kbd> + <kbd>S</kbd>
                        </div>
                    </div>
                    <div class="pricing-actions-buttons">
                        <button class="modern-btn modern-btn-outline" onclick="resetPricingToDefaults()">
                            <i class="fas fa-undo-alt"></i>
                            <span>Сбросить к умолчанию</span>
                        </button>
                        <button class="modern-btn modern-btn-primary modern-btn-large" onclick="savePricingSettings()">
                            <i class="fas fa-save"></i>
                            <span>Сохранить настройки</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Page-specific event listeners
function setupPageEventListeners(page) {
    // Add search functionality
    const searchBox = document.querySelector(`#${page}-search`);
    if (searchBox) {
        searchBox.addEventListener('input', function() {
            filterTable(this.value, page);
        });
    }
}

// Utility functions
function filterTable(searchTerm, page) {
    // Simple table filtering implementation
    const table = document.querySelector('.data-table tbody');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm.toLowerCase())) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Action functions (placeholders)
function viewUser(userId) { showToast(`Просмотр пользователя ${userId}`, 'info'); }
function editUser(userId) { showToast(`Редактирование пользователя ${userId}`, 'info'); }
function messageUser(userId) { showToast(`Отправка сообщения пользователю ${userId}`, 'info'); }
function banUser(userId) { showToast(`Блокировка пользователя ${userId}`, 'error'); }
function exportUsers() { showToast('Экспорт пользователей', 'info'); }

function extendSubscription(userId) { showToast(`Продление подписки для пользователя ${userId}`, 'success'); }
function cancelSubscription(userId) { showToast(`Отмена подписки для пользователя ${userId}`, 'error'); }
function addSubscription() { showToast('Добавление новой подписки', 'info'); }

function viewResponse(responseId) { showToast(`Просмотр отклика ${responseId}`, 'info'); }
function goToUser(userId) {
    setActivePage('users');
    loadPage('users');
    showToast(`Переход к пользователю ${userId}`, 'info');
}

function toggleAutoResponse(userId) { showToast(`Переключение автооткликов для пользователя ${userId}`, 'info'); }
function viewAutoResponseSettings(userId) { showToast(`Настройки автооткликов для пользователя ${userId}`, 'info'); }

function viewAIResponse(aiId) { showToast(`Просмотр AI-отклика ${aiId}`, 'info'); }
function copyAIResponse(aiId) {
    navigator.clipboard.writeText('Текст AI-отклика скопирован');
    showToast(`AI-отклик ${aiId} скопирован в буфер обмена`, 'success');
}
function sendAIResponse(aiId) { showToast(`Отправка AI-отклика ${aiId}`, 'success'); }

function viewNotification(notifId) { showToast(`Просмотр уведомления ${notifId}`, 'info'); }
function deleteNotification(notifId) { showToast(`Удаление уведомления ${notifId}`, 'error'); }
function createNotification() { showToast('Создание нового уведомления', 'info'); }
function sendBulkNotification() { showToast('Массовая рассылка уведомлений', 'info'); }

function saveSettings() { showToast('Настройки сохранены', 'success'); }
function testSettings() { showToast('Тестирование настроек...', 'info'); }

function createBroadcast() { showToast('Создание новой рассылки', 'info'); }
function viewMessageHistory() { showToast('Просмотр истории сообщений', 'info'); }

function addIntegration() { showToast('Добавление новой интеграции', 'info'); }
function addModule() { showToast('Добавление нового модуля', 'info'); }

function viewLog(logId) { showToast(`Просмотр лога ${logId}`, 'info'); }
function clearLogs() {
    if (confirm('Вы уверены, что хотите очистить все логи?')) {
        showToast('Логи очищены', 'success');
    }
}
// Enhanced page-specific event listeners
function setupPageEventListeners(page) {
    // Add search functionality
    const searchBox = document.querySelector(`#${page}-search`);
    if (searchBox) {
        searchBox.addEventListener('input', function() {
            filterTable(this.value, page);
        });
    }
    
    // Dashboard-specific listeners
    if (page === 'dashboard') {
        setupDashboardListeners();
    }
    
    // Users-specific listeners
    if (page === 'users') {
        setupUsersPageListeners();
    }
    
    // Texts-specific listeners
    if (page === 'texts') {
        setupTextsPageListeners();
    }
    
    // Pricing-specific listeners
    if (page === 'pricing') {
        setupPricingPageListeners();
    }
}

function setupDashboardListeners() {
    // Period selector functionality
    const periodButtons = document.querySelectorAll('.period-btn');
    periodButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            periodButtons.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            const period = this.dataset.period;
            updateDashboardData(period);
        });
    });
}

function updateDashboardData(period) {
    // This function would update the dashboard data based on selected period
    // For now, just show a toast notification
    showToast(`Данные обновлены для периода: ${getPeriodName(period)}`, 'info');
    
    // Here you would typically:
    // 1. Fetch new data from API based on period
    // 2. Update the metric cards with new values
    // 3. Update charts with new data
    // 4. Animate the changes
}

function getPeriodName(period) {
    const names = {
        'today': 'Сегодня',
        'week': 'Неделя', 
        'month': 'Месяц',
        'all': 'Всё время'
    };
    return names[period] || period;
}

// Animation helpers for dashboard updates
function animateValue(element, start, end, duration = 1000) {
    const startTime = performance.now();
    const difference = end - start;
    
    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = start + (difference * progress);
        element.textContent = Math.floor(current).toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }
    
    requestAnimationFrame(updateValue);
}

// User management functions
function openUserModal(userId) {
    const user = mockData.users.find(u => u.id === userId);
    if (!user) return;
    
    const modal = document.getElementById('userModal');
    const content = document.getElementById('userModalContent');
    
    const formatDate = (dateStr) => {
        if (!dateStr) return '—';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };
    
    const getStatusClass = (status) => {
        const statusMap = {
            'active': 'status-active',
            'inactive': 'status-inactive', 
            'banned': 'status-banned'
        };
        return statusMap[status] || 'status-inactive';
    };
    
    const getStatusText = (status) => {
        const statusMap = {
            'active': 'Активен',
            'inactive': 'Неактивен',
            'banned': 'Заблокирован'
        };
        return statusMap[status] || status;
    };
    
    content.innerHTML = `
        <div class="user-modal-tabs">
            <button class="user-tab active" onclick="switchUserTab('info')">Основная информация</button>
            <button class="user-tab" onclick="switchUserTab('activity')">Активность</button>
            <button class="user-tab" onclick="switchUserTab('referrals')">Рефералы</button>
            <button class="user-tab" onclick="switchUserTab('history')">История</button>
        </div>
        
        <div class="user-tab-content" id="user-tab-info">
            <div class="user-info-grid">
                <div class="user-info-section">
                    <h3 class="user-info-title">Личные данные</h3>
                    <div class="user-info-item">
                        <label>Telegram ID:</label>
                        <span>${user.telegramId}</span>
                    </div>
                    <div class="user-info-item">
                        <label>Имя:</label>
                        <span>${user.name}</span>
                    </div>
                    <div class="user-info-item">
                        <label>Username:</label>
                        <span>${user.username}</span>
                    </div>
                    <div class="user-info-item">
                        <label>Дата регистрации:</label>
                        <span>${formatDate(user.registrationDate)}</span>
                    </div>
                    <div class="user-info-item">
                        <label>Последняя активность:</label>
                        <span>${formatDate(user.lastActivity)}</span>
                    </div>
                    <div class="user-info-item">
                        <label>Статус:</label>
                        <span class="status-badge ${getStatusClass(user.status)}">${getStatusText(user.status)}</span>
                    </div>
                    <div class="user-info-item">
                        <label>UTM Source:</label>
                        <span>${user.utmSource || '—'}</span>
                    </div>
                    <div class="user-info-item">
                        <label>UTM Medium:</label>
                        <span>${user.utmMedium || '—'}</span>
                    </div>
                    <div class="user-info-item">
                        <label>UTM Campaign:</label>
                        <span>${user.utmCampaign || '—'}</span>
                    </div>
                </div>
                
                <div class="user-info-section">
                    <h3 class="user-info-title">Подписка и баланс</h3>
                    <div class="user-info-item">
                        <label>Тип подписки:</label>
                        <span>${user.subscription === 'none' ? 'Нет подписки' : user.subscription}</span>
                    </div>
                    <div class="user-info-item">
                        <label>Окончание подписки:</label>
                        <span>${user.subscriptionEnd ? formatDate(user.subscriptionEnd) : '—'}</span>
                    </div>
                    <div class="user-info-item">
                        <label>Баланс:</label>
                        <span class="balance-amount">${user.balance.toLocaleString()} ₽</span>
                    </div>
                    <div class="user-info-item">
                        <label>HH подключение:</label>
                        <span class="feature-badge ${user.hhConnected ? 'feature-enabled' : 'feature-disabled'}">
                            ${user.hhConnected ? 'Подключен' : 'Не подключен'}
                        </span>
                    </div>
                </div>
                
                <div class="user-info-section">
                    <h3 class="user-info-title">Активность и отклики</h3>
                    <div class="user-info-item">
                        <label>Всего откликов:</label>
                        <span>${user.totalResponses}</span>
                    </div>
                    <div class="user-info-item">
                        <label>Автоотклики:</label>
                        <span class="feature-badge ${user.autoResponses ? 'feature-enabled' : 'feature-disabled'}">
                            ${user.autoResponses ? 'Включены' : 'Выключены'}
                        </span>
                    </div>
                    <div class="user-info-item">
                        <label>AI-отклики:</label>
                        <span class="feature-badge ${user.aiResponses ? 'feature-enabled' : 'feature-disabled'}">
                            ${user.aiResponses ? 'Включены' : 'Выключены'}
                        </span>
                    </div>
                    <div class="user-info-item">
                        <label>Количество AI-откликов:</label>
                        <span>${user.aiResponsesCount}</span>
                    </div>
                </div>
                
                <div class="user-info-section">
                    <h3 class="user-info-title">Реферальная программа</h3>
                    <div class="user-info-item">
                        <label>Привлечен пользователем:</label>
                        <span>${user.referredBy || '—'}</span>
                    </div>
                    <div class="user-info-item">
                        <label>Привлек пользователей:</label>
                        <span>${user.referrals.length}</span>
                    </div>
                    <div class="user-info-item">
                        <label>Комментарий:</label>
                        <span>${user.comment || '—'}</span>
                    </div>
                </div>
            </div>
            
            <div class="user-modal-actions">
                <button class="btn btn-primary" onclick="editUserInModal(${user.id})">
                    <i class="fas fa-edit"></i>
                    Редактировать
                </button>
                <button class="btn btn-warning" onclick="toggleUserStatus(${user.id})">
                    <i class="fas fa-user-slash"></i>
                    ${user.status === 'banned' ? 'Разблокировать' : 'Заблокировать'}
                </button>
                <button class="btn btn-success" onclick="addBalance(${user.id})">
                    <i class="fas fa-plus"></i>
                    Пополнить баланс
                </button>
            </div>
        </div>
        
        <div class="user-tab-content" id="user-tab-activity" style="display: none;">
            <div class="activity-section">
                <h3>Последние действия</h3>
                <div class="activity-list">
                    <div class="activity-item">
                        <div class="activity-icon">
                            <i class="fas fa-paper-plane"></i>
                        </div>
                        <div class="activity-content">
                            <div class="activity-title">Отправлен отклик</div>
                            <div class="activity-description">На вакансию "Senior Python Developer"</div>
                            <div class="activity-time">2 часа назад</div>
                        </div>
                    </div>
                    <div class="activity-item">
                        <div class="activity-icon">
                            <i class="fas fa-sign-in-alt"></i>
                        </div>
                        <div class="activity-content">
                            <div class="activity-title">Вход в систему</div>
                            <div class="activity-description">Авторизация через Telegram</div>
                            <div class="activity-time">5 часов назад</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="user-tab-content" id="user-tab-referrals" style="display: none;">
            <div class="referrals-section">
                <h3>Реферальное дерево</h3>
                <div class="referral-tree">
                    ${user.referrals.length > 0 ? 
                        user.referrals.map(ref => `
                            <div class="referral-item">
                                <i class="fas fa-user"></i>
                                <span>${ref}</span>
                            </div>
                        `).join('') : 
                        '<p class="no-referrals">Нет привлеченных пользователей</p>'
                    }
                </div>
            </div>
        </div>
        
        <div class="user-tab-content" id="user-tab-history" style="display: none;">
            <div class="history-section">
                <h3>История операций</h3>
                <div class="history-list">
                    <div class="history-item">
                        <div class="history-date">29.01.2024 14:30</div>
                        <div class="history-action">Продление подписки</div>
                        <div class="history-details">Месячная подписка - 1900₽</div>
                    </div>
                    <div class="history-item">
                        <div class="history-date">15.01.2024 10:15</div>
                        <div class="history-action">Регистрация</div>
                        <div class="history-details">Первый вход в систему</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeUserModal() {
    const modal = document.getElementById('userModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

function switchUserTab(tabName) {
    // Remove active class from all tabs
    document.querySelectorAll('.user-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Hide all tab contents
    document.querySelectorAll('.user-tab-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // Show selected tab content
    document.getElementById(`user-tab-${tabName}`).style.display = 'block';
    
    // Add active class to selected tab
    event.target.classList.add('active');
}

function addUser() {
    showToast('Добавление нового пользователя', 'info');
}

function editUserInModal(userId) {
    showToast(`Редактирование пользователя ${userId}`, 'info');
}

function toggleUserStatus(userId) {
    const user = mockData.users.find(u => u.id === userId);
    if (user) {
        const newStatus = user.status === 'banned' ? 'active' : 'banned';
        user.status = newStatus;
        showToast(`Статус пользователя изменен на: ${newStatus === 'active' ? 'Активен' : 'Заблокирован'}`, 'success');
        closeUserModal();
        loadPage('users'); // Refresh the page
    }
}

function addBalance(userId) {
    const amount = prompt('Введите сумму для пополнения баланса:');
    if (amount && !isNaN(amount)) {
        showToast(`Баланс пополнен на ${amount}₽`, 'success');
    }
}

function showUserActions(userId) {
    showToast(`Дополнительные действия для пользователя ${userId}`, 'info');
}

function clearFilters() {
    document.getElementById('users-search').value = '';
    document.getElementById('status-filter').value = '';
    document.getElementById('subscription-filter').value = '';
    document.getElementById('hh-filter').value = '';
    showToast('Фильтры очищены', 'info');
    // Here you would typically refresh the table data
}

// Enhanced users page event listeners
function setupUsersPageListeners() {
    // Search functionality
    const searchInput = document.getElementById('users-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterUsersTable(this.value);
        });
    }
    
    // Filter functionality
    const filters = ['status-filter', 'subscription-filter', 'hh-filter'];
    filters.forEach(filterId => {
        const filter = document.getElementById(filterId);
        if (filter) {
            filter.addEventListener('change', function() {
                applyUsersFilters();
            });
        }
    });
    
    // Table sorting
    const sortableHeaders = document.querySelectorAll('.users-table .sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const sortField = this.dataset.sort;
            sortUsersTable(sortField);
        });
    });
}

function filterUsersTable(searchTerm) {
    const rows = document.querySelectorAll('.user-row');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm.toLowerCase())) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function applyUsersFilters() {
    const statusFilter = document.getElementById('status-filter').value;
    const subscriptionFilter = document.getElementById('subscription-filter').value;
    const hhFilter = document.getElementById('hh-filter').value;
    
    const rows = document.querySelectorAll('.user-row');
    rows.forEach(row => {
        let show = true;
        const userId = row.dataset.userId;
        const user = mockData.users.find(u => u.id == userId);
        
        if (statusFilter && user.status !== statusFilter) show = false;
        if (subscriptionFilter && user.subscription !== subscriptionFilter) show = false;
        if (hhFilter) {
            if (hhFilter === 'connected' && !user.hhConnected) show = false;
            if (hhFilter === 'not-connected' && user.hhConnected) show = false;
        }
        
        row.style.display = show ? '' : 'none';
    });
}

function sortUsersTable(field) {
    // Simple sorting implementation
    showToast(`Сортировка по полю: ${field}`, 'info');
}

// Text management functions
function viewText(textId) {
    const text = mockData.texts.find(t => t.id === textId);
    if (!text) return;
    
    const modal = document.getElementById('textModal');
    const content = document.getElementById('textModalContent');
    
    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };
    
    const attachmentSection = text.hasAttachment ? `
        <div class="text-info-section">
            <h3 class="text-info-title">Вложение</h3>
            <div class="attachment-info">
                <div class="attachment-preview">
                    ${text.attachment.type === 'image' ? 
                        `<img src="${text.attachment.url}" alt="${text.attachment.name}" class="attachment-image">` :
                        `<div class="attachment-file">
                            <i class="fas fa-${text.attachment.type === 'video' ? 'video' : 'file'}"></i>
                            <span>${text.attachment.name}</span>
                        </div>`
                    }
                </div>
                <div class="attachment-actions">
                    <button class="btn btn-secondary" onclick="downloadAttachment('${text.attachment.url}')">
                        <i class="fas fa-download"></i>
                        Скачать
                    </button>
                    <button class="btn btn-danger" onclick="removeAttachment(${text.id})">
                        <i class="fas fa-trash"></i>
                        Удалить
                    </button>
                </div>
            </div>
        </div>
    ` : '';
    
    content.innerHTML = `
        <div class="text-edit-form">
            <div class="text-info-grid">
                <div class="text-info-section">
                    <h3 class="text-info-title">Основная информация</h3>
                    <div class="form-group">
                        <label class="form-label">Название:</label>
                        <input type="text" class="form-input" value="${text.name}" id="textName">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Ключ:</label>
                        <input type="text" class="form-input" value="${text.key}" id="textKey" readonly>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Категория:</label>
                        <select class="form-input" id="textCategory">
                            <option value="welcome" ${text.category === 'welcome' ? 'selected' : ''}>Приветствие</option>
                            <option value="subscription" ${text.category === 'subscription' ? 'selected' : ''}>Подписка</option>
                            <option value="support" ${text.category === 'support' ? 'selected' : ''}>Поддержка</option>
                            <option value="responses" ${text.category === 'responses' ? 'selected' : ''}>Отклики</option>
                            <option value="buttons" ${text.category === 'buttons' ? 'selected' : ''}>Кнопки</option>
                            <option value="cover_letters" ${text.category === 'cover_letters' ? 'selected' : ''}>Письма</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Последнее изменение:</label>
                        <span class="form-text">${formatDate(text.lastModified)}</span>
                    </div>
                </div>
                
                <div class="text-info-section">
                    <h3 class="text-info-title">Текст сообщения</h3>
                    <div class="form-group">
                        <label class="form-label">Содержимое:</label>
                        <textarea class="form-textarea" rows="10" id="textContent">${text.text}</textarea>
                    </div>
                    <div class="text-preview">
                        <h4>Предварительный просмотр:</h4>
                        <div class="preview-content">${text.text.replace(/\n/g, '<br>')}</div>
                    </div>
                </div>
                
                ${attachmentSection}
                
                <div class="text-info-section">
                    <h3 class="text-info-title">Добавить вложение</h3>
                    <div class="attachment-upload">
                        <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                            <i class="fas fa-cloud-upload-alt"></i>
                            <p>Нажмите для выбора файла или перетащите сюда</p>
                            <small>Поддерживаются: изображения, видео, документы (до 10 МБ)</small>
                        </div>
                        <input type="file" id="fileInput" style="display: none" accept="image/*,video/*,.pdf,.doc,.docx" onchange="handleFileUpload(event, ${text.id})">
                    </div>
                </div>
            </div>
            
            <div class="text-modal-actions">
                <button class="btn btn-primary" onclick="saveText(${text.id})">
                    <i class="fas fa-save"></i>
                    Сохранить изменения
                </button>
                <button class="btn btn-secondary" onclick="previewText(${text.id})">
                    <i class="fas fa-eye"></i>
                    Предварительный просмотр
                </button>
                <button class="btn btn-warning" onclick="resetText(${text.id})">
                    <i class="fas fa-undo"></i>
                    Сбросить изменения
                </button>
                <button class="btn btn-danger" onclick="deleteText(${text.id})">
                    <i class="fas fa-trash"></i>
                    Удалить текст
                </button>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function editText(textId) {
    viewText(textId); // Используем ту же модалку для редактирования
}

function closeTextModal() {
    const modal = document.getElementById('textModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

function saveText(textId) {
    const text = mockData.texts.find(t => t.id === textId);
    if (!text) return;
    
    const name = document.getElementById('textName').value;
    const category = document.getElementById('textCategory').value;
    const content = document.getElementById('textContent').value;
    
    if (!name.trim() || !content.trim()) {
        showToast('Заполните все обязательные поля', 'error');
        return;
    }
    
    text.name = name;
    text.category = category;
    text.text = content;
    text.lastModified = new Date().toISOString().slice(0, 16).replace('T', ' ');
    
    showToast('Текст успешно сохранен', 'success');
    closeTextModal();
    loadPage('texts'); // Обновляем страницу
}

function copyText(textId) {
    const text = mockData.texts.find(t => t.id === textId);
    if (text) {
        navigator.clipboard.writeText(text.text);
        showToast('Текст скопирован в буфер обмена', 'success');
    }
}

function deleteText(textId) {
    if (confirm('Вы уверены, что хотите удалить этот текст?')) {
        const index = mockData.texts.findIndex(t => t.id === textId);
        if (index !== -1) {
            mockData.texts.splice(index, 1);
            showToast('Текст удален', 'success');
            closeTextModal();
            loadPage('texts');
        }
    }
}

function addText() {
    const newId = Math.max(...mockData.texts.map(t => t.id)) + 1;
    const newText = {
        id: newId,
        category: 'welcome',
        name: 'Новый текст',
        key: 'NEW_TEXT_' + newId,
        text: 'Введите текст сообщения...',
        hasAttachment: false,
        attachment: null,
        lastModified: new Date().toISOString().slice(0, 16).replace('T', ' ')
    };
    
    mockData.texts.push(newText);
    loadPage('texts');
    editText(newId);
}

function exportTexts() {
    const texts = mockData.texts;
    const dataStr = JSON.stringify(texts, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'bot_texts_export.json';
    link.click();
    showToast('Тексты экспортированы', 'success');
}

function handleFileUpload(event, textId) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
        showToast('Файл слишком большой. Максимальный размер: 10 МБ', 'error');
        return;
    }
    
    const text = mockData.texts.find(t => t.id === textId);
    if (!text) return;
    
    // Simulate file upload
    const fileType = file.type.startsWith('image/') ? 'image' : 
                    file.type.startsWith('video/') ? 'video' : 'document';
    
    text.hasAttachment = true;
    text.attachment = {
        type: fileType,
        name: file.name,
        url: `/uploads/${file.name}`
    };
    
    showToast('Файл успешно загружен', 'success');
    viewText(textId); // Обновляем модалку
}

function removeAttachment(textId) {
    const text = mockData.texts.find(t => t.id === textId);
    if (text) {
        text.hasAttachment = false;
        text.attachment = null;
        showToast('Вложение удалено', 'success');
        viewText(textId); // Обновляем модалку
    }
}

function downloadAttachment(url) {
    const link = document.createElement('a');
    link.href = url;
    link.download = url.split('/').pop();
    link.click();
    showToast('Загрузка началась', 'info');
}

function previewText(textId) {
    const text = mockData.texts.find(t => t.id === textId);
    if (text) {
        const content = document.getElementById('textContent').value;
        const previewWindow = window.open('', '_blank', 'width=600,height=400');
        previewWindow.document.write(`
            <html>
                <head><title>Предварительный просмотр: ${text.name}</title></head>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>${text.name}</h2>
                    <div style="border: 1px solid #ccc; padding: 15px; border-radius: 5px; background: #f9f9f9;">
                        ${content.replace(/\n/g, '<br>')}
                    </div>
                </body>
            </html>
        `);
    }
}

function resetText(textId) {
    if (confirm('Сбросить все изменения?')) {
        viewText(textId); // Перезагружаем модалку с оригинальными данными
    }
}

function clearTextsFilters() {
    document.getElementById('texts-search').value = '';
    document.getElementById('category-filter').value = '';
    document.getElementById('attachment-filter').value = '';
    showToast('Фильтры очищены', 'info');
}

// Enhanced texts page event listeners
function setupTextsPageListeners() {
    // Search functionality
    const searchInput = document.getElementById('texts-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterTextsTable(this.value);
        });
    }
    
    // Filter functionality
    const filters = ['category-filter', 'attachment-filter'];
    filters.forEach(filterId => {
        const filter = document.getElementById(filterId);
        if (filter) {
            filter.addEventListener('change', function() {
                applyTextsFilters();
            });
        }
    });
    
    // Table sorting
    const sortableHeaders = document.querySelectorAll('.texts-table .sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const sortField = this.dataset.sort;
            sortTextsTable(sortField);
        });
    });
}

function filterTextsTable(searchTerm) {
    const rows = document.querySelectorAll('.text-row');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm.toLowerCase())) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function applyTextsFilters() {
    const categoryFilter = document.getElementById('category-filter').value;
    const attachmentFilter = document.getElementById('attachment-filter').value;
    
    const rows = document.querySelectorAll('.text-row');
    rows.forEach(row => {
        let show = true;
        const textId = row.dataset.textId;
        const text = mockData.texts.find(t => t.id == textId);
        
        if (categoryFilter && text.category !== categoryFilter) show = false;
        if (attachmentFilter) {
            if (attachmentFilter === 'with-attachment' && !text.hasAttachment) show = false;
            if (attachmentFilter === 'without-attachment' && text.hasAttachment) show = false;
        }
        
        row.style.display = show ? '' : 'none';
    });
}

function sortTextsTable(field) {
    showToast(`Сортировка по полю: ${field}`, 'info');
}

// User Profile Navigation
function openUserProfile(userId) {
    // Navigate to user profile page with user ID parameter
    window.location.href = `user-profile.html?id=${userId}`;
}

// Pricing management functions
function savePricingSettings() {
    // Get all pricing values
    const freeResponses = parseInt(document.getElementById('freeResponses').value);
    const subscriptionPrices = {
        week: parseInt(document.getElementById('priceWeek').value),
        month: parseInt(document.getElementById('priceMonth').value),
        quarter: parseInt(document.getElementById('priceQuarter').value),
        halfYear: parseInt(document.getElementById('priceHalfYear').value),
        year: parseInt(document.getElementById('priceYear').value)
    };
    const aiResponsesPrices = {
        responses30: parseInt(document.getElementById('aiPrice30').value),
        responses100: parseInt(document.getElementById('aiPrice100').value),
        responses500: parseInt(document.getElementById('aiPrice500').value),
        responses1000: parseInt(document.getElementById('aiPrice1000').value),
        responses3000: parseInt(document.getElementById('aiPrice3000').value)
    };
    
    // Validation
    if (isNaN(freeResponses) || freeResponses < 0 || freeResponses > 100) {
        showToast('Количество бесплатных откликов должно быть от 0 до 100', 'error');
        return;
    }
    
    // Validate subscription prices
    for (const [key, value] of Object.entries(subscriptionPrices)) {
        if (isNaN(value) || value < 0) {
            showToast('Все цены на подписки должны быть положительными числами', 'error');
            return;
        }
    }
    
    // Validate AI responses prices
    for (const [key, value] of Object.entries(aiResponsesPrices)) {
        if (isNaN(value) || value < 0) {
            showToast('Все цены на AI-отклики должны быть положительными числами', 'error');
            return;
        }
    }
    
    // Check logical pricing order for subscriptions
    if (subscriptionPrices.week >= subscriptionPrices.month) {
        showToast('Цена за месяц должна быть больше цены за неделю', 'error');
        return;
    }
    
    if (subscriptionPrices.month >= subscriptionPrices.quarter) {
        showToast('Цена за квартал должна быть больше цены за месяц', 'error');
        return;
    }
    
    // Check logical pricing order for AI responses
    if (aiResponsesPrices.responses30 >= aiResponsesPrices.responses100) {
        showToast('Цена за 100 откликов должна быть больше цены за 30 откликов', 'error');
        return;
    }
    
    if (aiResponsesPrices.responses100 >= aiResponsesPrices.responses500) {
        showToast('Цена за 500 откликов должна быть больше цены за 100 откликов', 'error');
        return;
    }
    
    // Save to mock data
    mockData.pricing.freeResponses = freeResponses;
    mockData.pricing.subscriptionPrices = subscriptionPrices;
    mockData.pricing.aiResponsesPrices = aiResponsesPrices;
    
    // Show success message
    showToast('Настройки тарифов успешно сохранены!', 'success');
    
    // Here you would typically send the data to the server
    console.log('Pricing settings saved:', {
        freeResponses,
        subscriptionPrices,
        aiResponsesPrices
    });
}

function resetPricingToDefaults() {
    if (confirm('Вы уверены, что хотите сбросить все цены к значениям по умолчанию?')) {
        // Reset to default values
        const defaultPricing = {
            freeResponses: 10,
            subscriptionPrices: {
                week: 690,
                month: 1900,
                quarter: 4500,
                halfYear: 8500,
                year: 15900
            },
            aiResponsesPrices: {
                responses30: 299,
                responses100: 899,
                responses500: 3999,
                responses1000: 7499,
                responses3000: 19999
            }
        };
        
        mockData.pricing = defaultPricing;
        
        // Reload the page to show default values
        loadPage('pricing');
        showToast('Настройки сброшены к значениям по умолчанию', 'info');
    }
}

function setupPricingPageListeners() {
    // Add real-time validation for pricing inputs
    const allInputs = document.querySelectorAll('.pricing-section input[type="number"]');
    allInputs.forEach(input => {
        input.addEventListener('input', function() {
            validatePricingInput(this);
        });
        
        input.addEventListener('blur', function() {
            formatPricingInput(this);
        });
    });
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            savePricingSettings();
        }
    });
}

function validatePricingInput(input) {
    const value = parseInt(input.value);
    
    // Remove any existing validation classes
    input.classList.remove('input-error', 'input-success');
    
    if (isNaN(value) || value < 0) {
        input.classList.add('input-error');
    } else {
        input.classList.add('input-success');
    }
}

function formatPricingInput(input) {
    const value = parseInt(input.value);
    if (!isNaN(value) && value >= 0) {
        input.value = value; // Remove any decimal places
    }
}

function calculatePricingMetrics() {
    // Calculate and display pricing metrics like cost per response, etc.
    const pricing = mockData.pricing;
    
    // Calculate cost per response for AI packages
    const costPerResponse = {
        package30: pricing.aiResponsesPrices.responses30 / 30,
        package100: pricing.aiResponsesPrices.responses100 / 100,
        package500: pricing.aiResponsesPrices.responses500 / 500,
        package1000: pricing.aiResponsesPrices.responses1000 / 1000,
        package3000: pricing.aiResponsesPrices.responses3000 / 3000
    };
    
    console.log('Cost per AI response:', costPerResponse);
    
    // You could display these metrics in the UI
    return costPerResponse;
}

// Broadcast management functions
function createNewBroadcast() {
    const modal = document.getElementById('broadcastModal');
    const title = document.getElementById('broadcastModalTitle');
    const content = document.getElementById('broadcastModalContent');
    
    title.textContent = 'Новая рассылка';
    
    content.innerHTML = `
        <div class="broadcast-form">
            <div class="form-section">
                <h3 class="form-section-title">Основная информация</h3>
                <div class="form-group">
                    <label class="form-label">Название рассылки</label>
                    <input type="text" class="form-input" id="broadcastTitle" placeholder="Введите название рассылки">
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="form-section-title">Аудитория</h3>
                <div class="audience-selector">
                    <div class="audience-options">
                        <label class="audience-option">
                            <input type="radio" name="audience" value="all" checked>
                            <div class="option-content">
                                <div class="option-title">Все пользователи</div>
                                <div class="option-count">${mockData.stats.totalUsers.toLocaleString()} пользователей</div>
                            </div>
                        </label>
                        <label class="audience-option">
                            <input type="radio" name="audience" value="premium">
                            <div class="option-content">
                                <div class="option-title">Премиум подписчики</div>
                                <div class="option-count">${mockData.stats.paidSubscribers.toLocaleString()} пользователей</div>
                            </div>
                        </label>
                        <label class="audience-option">
                            <input type="radio" name="audience" value="no_subscription">
                            <div class="option-content">
                                <div class="option-title">Без подписки</div>
                                <div class="option-count">${(mockData.stats.totalUsers - mockData.stats.paidSubscribers).toLocaleString()} пользователей</div>
                            </div>
                        </label>
                        <label class="audience-option">
                            <input type="radio" name="audience" value="active">
                            <div class="option-content">
                                <div class="option-title">Активные пользователи</div>
                                <div class="option-count">${mockData.stats.activeUsers30d.toLocaleString()} пользователей</div>
                            </div>
                        </label>
                        <label class="audience-option">
                            <input type="radio" name="audience" value="auto_responses">
                            <div class="option-content">
                                <div class="option-title">С автооткликами</div>
                                <div class="option-count">${mockData.stats.autoResponseUsers.toLocaleString()} пользователей</div>
                            </div>
                        </label>
                        <label class="audience-option">
                            <input type="radio" name="audience" value="ai_responses">
                            <div class="option-content">
                                <div class="option-title">С AI-откликами</div>
                                <div class="option-count">${mockData.stats.aiResponseUsers.toLocaleString()} пользователей</div>
                            </div>
                        </label>
                    </div>
                    
                    <div class="custom-audience">
                        <label class="audience-option">
                            <input type="radio" name="audience" value="custom">
                            <div class="option-content">
                                <div class="option-title">Пользовательский фильтр</div>
                                <div class="option-count">Настроить вручную</div>
                            </div>
                        </label>
                        <div class="custom-filters" id="customFilters" style="display: none;">
                            <div class="filter-row">
                                <input type="text" class="form-input" placeholder="Telegram ID или username (через запятую)">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="form-section-title">Сообщение</h3>
                <div class="message-editor">
                    <div class="editor-toolbar">
                        <button type="button" class="toolbar-btn" onclick="formatText('bold')" title="Жирный">
                            <i class="fas fa-bold"></i>
                        </button>
                        <button type="button" class="toolbar-btn" onclick="formatText('italic')" title="Курсив">
                            <i class="fas fa-italic"></i>
                        </button>
                        <button type="button" class="toolbar-btn" onclick="formatText('underline')" title="Подчеркнутый">
                            <i class="fas fa-underline"></i>
                        </button>
                        <button type="button" class="toolbar-btn" onclick="formatText('strikethrough')" title="Зачеркнутый">
                            <i class="fas fa-strikethrough"></i>
                        </button>
                        <div class="toolbar-separator"></div>
                        <button type="button" class="toolbar-btn" onclick="insertLink()" title="Ссылка">
                            <i class="fas fa-link"></i>
                        </button>
                        <button type="button" class="toolbar-btn" onclick="insertList('ul')" title="Маркированный список">
                            <i class="fas fa-list-ul"></i>
                        </button>
                        <button type="button" class="toolbar-btn" onclick="insertList('ol')" title="Нумерованный список">
                            <i class="fas fa-list-ol"></i>
                        </button>
                    </div>
                    <div class="editor-content" contenteditable="true" id="messageEditor" placeholder="Введите текст сообщения...">
                    </div>
                    <div class="editor-help">
                        <i class="fas fa-info-circle"></i>
                        <span>Поддерживается Telegram-разметка: **жирный**, *курсив*, __подчеркнутый__, ~~зачеркнутый~~</span>
                    </div>
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="form-section-title">Вложения</h3>
                <div class="attachment-upload">
                    <div class="upload-area" onclick="document.getElementById('broadcastFileInput').click()">
                        <i class="fas fa-cloud-upload-alt"></i>
                        <p>Нажмите для выбора файла или перетащите сюда</p>
                        <small>Поддерживаются: изображения, видео, документы (до 50 МБ)</small>
                    </div>
                    <input type="file" id="broadcastFileInput" style="display: none" accept="image/*,video/*,.pdf,.doc,.docx" onchange="handleBroadcastFileUpload(event)">
                    <div id="attachmentPreview" class="attachment-preview" style="display: none;"></div>
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="form-section-title">Предварительный просмотр</h3>
                <div class="message-preview" id="messagePreview">
                    <div class="preview-placeholder">Введите текст сообщения для предварительного просмотра</div>
                </div>
            </div>
            
            <div class="broadcast-modal-actions">
                <button class="btn btn-secondary" onclick="saveBroadcastDraft()">
                    <i class="fas fa-save"></i>
                    Сохранить как черновик
                </button>
                <button class="btn btn-warning" onclick="sendTestBroadcast()">
                    <i class="fas fa-vial"></i>
                    Тестовая отправка
                </button>
                <button class="btn btn-primary" onclick="sendBroadcastNow()">
                    <i class="fas fa-paper-plane"></i>
                    Отправить сейчас
                </button>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Setup event listeners
    setupBroadcastFormListeners();
}

function setupBroadcastFormListeners() {
    // Real-time preview update
    const editor = document.getElementById('messageEditor');
    const preview = document.getElementById('messagePreview');
    
    if (editor && preview) {
        editor.addEventListener('input', function() {
            updateMessagePreview();
        });
    }
    
    // Custom audience toggle
    const audienceRadios = document.querySelectorAll('input[name="audience"]');
    const customFilters = document.getElementById('customFilters');
    
    audienceRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'custom') {
                customFilters.style.display = 'block';
            } else {
                customFilters.style.display = 'none';
            }
        });
    });
}

function updateMessagePreview() {
    const editor = document.getElementById('messageEditor');
    const preview = document.getElementById('messagePreview');
    
    if (!editor || !preview) return;
    
    const text = editor.textContent || editor.innerText;
    
    if (text.trim()) {
        // Convert Telegram markup to HTML
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/__(.*?)__/g, '<u>$1</u>')
            .replace(/~~(.*?)~~/g, '<del>$1</del>')
            .replace(/\n/g, '<br>');
        
        preview.innerHTML = `<div class="preview-content">${formattedText}</div>`;
    } else {
        preview.innerHTML = '<div class="preview-placeholder">Введите текст сообщения для предварительного просмотра</div>';
    }
}

function formatText(command) {
    document.execCommand(command, false, null);
    updateMessagePreview();
}

function insertLink() {
    const url = prompt('Введите URL:');
    if (url) {
        const text = prompt('Введите текст ссылки:') || url;
        document.execCommand('insertHTML', false, `<a href="${url}">${text}</a>`);
        updateMessagePreview();
    }
}

function insertList(type) {
    document.execCommand(type === 'ul' ? 'insertUnorderedList' : 'insertOrderedList', false, null);
    updateMessagePreview();
}

function handleBroadcastFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (file.size > 50 * 1024 * 1024) { // 50MB limit
        showToast('Файл слишком большой. Максимальный размер: 50 МБ', 'error');
        return;
    }
    
    const preview = document.getElementById('attachmentPreview');
    const fileType = file.type.startsWith('image/') ? 'image' : 
                    file.type.startsWith('video/') ? 'video' : 'document';
    
    let previewContent = '';
    
    if (fileType === 'image') {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewContent = `
                <div class="attachment-item">
                    <img src="${e.target.result}" alt="${file.name}" class="attachment-image">
                    <div class="attachment-info">
                        <div class="attachment-name">${file.name}</div>
                        <div class="attachment-size">${(file.size / 1024 / 1024).toFixed(2)} МБ</div>
                    </div>
                    <button class="attachment-remove" onclick="removeBroadcastAttachment()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            preview.innerHTML = previewContent;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        previewContent = `
            <div class="attachment-item">
                <div class="attachment-icon">
                    <i class="fas fa-${fileType === 'video' ? 'video' : 'file'}"></i>
                </div>
                <div class="attachment-info">
                    <div class="attachment-name">${file.name}</div>
                    <div class="attachment-size">${(file.size / 1024 / 1024).toFixed(2)} МБ</div>
                </div>
                <button class="attachment-remove" onclick="removeBroadcastAttachment()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        preview.innerHTML = previewContent;
        preview.style.display = 'block';
    }
    
    showToast('Файл успешно загружен', 'success');
}

function removeBroadcastAttachment() {
    const preview = document.getElementById('attachmentPreview');
    const fileInput = document.getElementById('broadcastFileInput');
    
    preview.style.display = 'none';
    preview.innerHTML = '';
    fileInput.value = '';
    
    showToast('Вложение удалено', 'info');
}

function saveBroadcastDraft() {
    const title = document.getElementById('broadcastTitle').value;
    const audience = document.querySelector('input[name="audience"]:checked').value;
    const message = document.getElementById('messageEditor').textContent;
    
    if (!title.trim()) {
        showToast('Введите название рассылки', 'error');
        return;
    }
    
    if (!message.trim()) {
        showToast('Введите текст сообщения', 'error');
        return;
    }
    
    // Create new broadcast draft
    const newBroadcast = {
        id: Math.max(...mockData.broadcasts.map(b => b.id)) + 1,
        title: title,
        message: message,
        audience: audience,
        audienceCount: getAudienceCount(audience),
        sentAt: null,
        status: 'draft',
        delivered: 0,
        failed: 0,
        read: 0,
        hasAttachment: document.getElementById('attachmentPreview').style.display !== 'none',
        attachment: null // Would be populated with actual file data
    };
    
    mockData.broadcasts.push(newBroadcast);
    
    showToast('Рассылка сохранена как черновик', 'success');
    closeBroadcastModal();
    loadPage('messages'); // Refresh the page
}

function sendTestBroadcast() {
    const adminId = prompt('Введите ваш Telegram ID для тестовой отправки:');
    if (adminId) {
        showToast(`Тестовое сообщение отправлено на ID: ${adminId}`, 'success');
    }
}

function sendBroadcastNow() {
    const title = document.getElementById('broadcastTitle').value;
    const audience = document.querySelector('input[name="audience"]:checked').value;
    const message = document.getElementById('messageEditor').textContent;
    
    if (!title.trim() || !message.trim()) {
        showToast('Заполните все обязательные поля', 'error');
        return;
    }
    
    if (confirm('Вы уверены, что хотите отправить рассылку сейчас? Это действие нельзя отменить.')) {
        const audienceCount = getAudienceCount(audience);
        
        // Simulate sending
        const newBroadcast = {
            id: Math.max(...mockData.broadcasts.map(b => b.id)) + 1,
            title: title,
            message: message,
            audience: audience,
            audienceCount: audienceCount,
            sentAt: new Date().toISOString().slice(0, 16).replace('T', ' '),
            status: 'sent',
            delivered: Math.floor(audienceCount * 0.95), // 95% delivery rate
            failed: Math.floor(audienceCount * 0.05),
            read: Math.floor(audienceCount * 0.65), // 65% read rate
            hasAttachment: document.getElementById('attachmentPreview').style.display !== 'none',
            attachment: null
        };
        
        mockData.broadcasts.push(newBroadcast);
        
        showToast(`Рассылка отправлена ${audienceCount.toLocaleString()} пользователям`, 'success');
        closeBroadcastModal();
        loadPage('messages');
    }
}

function getAudienceCount(audience) {
    const audienceMap = {
        'all': mockData.stats.totalUsers,
        'premium': mockData.stats.paidSubscribers,
        'no_subscription': mockData.stats.totalUsers - mockData.stats.paidSubscribers,
        'active': mockData.stats.activeUsers30d,
        'auto_responses': mockData.stats.autoResponseUsers,
        'ai_responses': mockData.stats.aiResponseUsers,
        'custom': 0 // Would be calculated based on custom filters
    };
    return audienceMap[audience] || 0;
}

function closeBroadcastModal() {
    const modal = document.getElementById('broadcastModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

function viewBroadcast(broadcastId) {
    const broadcast = mockData.broadcasts.find(b => b.id === broadcastId);
    if (!broadcast) return;
    
    const modal = document.getElementById('broadcastViewModal');
    const title = document.getElementById('broadcastViewModalTitle');
    const content = document.getElementById('broadcastViewModalContent');
    
    title.textContent = `Просмотр рассылки: ${broadcast.title}`;
    
    const formatDate = (dateStr) => {
        if (!dateStr) return '—';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };
    
    content.innerHTML = `
        <div class="broadcast-view">
            <div class="broadcast-info-grid">
                <div class="info-section">
                    <h3>Основная информация</h3>
                    <div class="info-item">
                        <label>Название:</label>
                        <span>${broadcast.title}</span>
                    </div>
                    <div class="info-item">
                        <label>Статус:</label>
                        <span class="broadcast-status status-${broadcast.status}">${broadcast.status === 'sent' ? 'Отправлено' : 'Черновик'}</span>
                    </div>
                    <div class="info-item">
                        <label>Дата отправки:</label>
                        <span>${formatDate(broadcast.sentAt)}</span>
                    </div>
                    <div class="info-item">
                        <label>Аудитория:</label>
                        <span>${broadcast.audienceCount.toLocaleString()} пользователей</span>
                    </div>
                </div>
                
                ${broadcast.status === 'sent' ? `
                    <div class="info-section">
                        <h3>Статистика доставки</h3>
                        <div class="delivery-stats-detailed">
                            <div class="stat-item">
                                <div class="stat-icon delivered">
                                    <i class="fas fa-check-circle"></i>
                                </div>
                                <div class="stat-content">
                                    <div class="stat-value">${broadcast.delivered.toLocaleString()}</div>
                                    <div class="stat-label">Доставлено</div>
                                    <div class="stat-percent">${((broadcast.delivered / broadcast.audienceCount) * 100).toFixed(1)}%</div>
                                </div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-icon read">
                                    <i class="fas fa-eye"></i>
                                </div>
                                <div class="stat-content">
                                    <div class="stat-value">${broadcast.read.toLocaleString()}</div>
                                    <div class="stat-label">Прочитано</div>
                                    <div class="stat-percent">${((broadcast.read / broadcast.delivered) * 100).toFixed(1)}%</div>
                                </div>
                            </div>
                            ${broadcast.failed > 0 ? `
                                <div class="stat-item">
                                    <div class="stat-icon failed">
                                        <i class="fas fa-exclamation-circle"></i>
                                    </div>
                                    <div class="stat-content">
                                        <div class="stat-value">${broadcast.failed.toLocaleString()}</div>
                                        <div class="stat-label">Ошибки</div>
                                        <div class="stat-percent">${((broadcast.failed / broadcast.audienceCount) * 100).toFixed(1)}%</div>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                ` : ''}
            </div>
            
            <div class="message-content-section">
                <h3>Содержимое сообщения</h3>
                <div class="message-display">
                    ${broadcast.message.replace(/\n/g, '<br>')}
                </div>
                
                ${broadcast.hasAttachment ? `
                    <div class="attachment-section">
                        <h4>Вложение</h4>
                        <div class="attachment-display">
                            <i class="fas fa-paperclip"></i>
                            <span>Файл прикреплен к рассылке</span>
                        </div>
                    </div>
                ` : ''}
            </div>
            
            <div class="broadcast-view-actions">
                ${broadcast.status === 'draft' ? `
                    <button class="btn btn-primary" onclick="editBroadcast(${broadcast.id})">
                        <i class="fas fa-edit"></i>
                        Редактировать
                    </button>
                    <button class="btn btn-success" onclick="sendBroadcast(${broadcast.id})">
                        <i class="fas fa-paper-plane"></i>
                        Отправить
                    </button>
                ` : ''}
                <button class="btn btn-secondary" onclick="duplicateBroadcast(${broadcast.id})">
                    <i class="fas fa-copy"></i>
                    Дублировать
                </button>
                <button class="btn btn-danger" onclick="deleteBroadcast(${broadcast.id})">
                    <i class="fas fa-trash"></i>
                    Удалить
                </button>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeBroadcastViewModal() {
    const modal = document.getElementById('broadcastViewModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

function editBroadcast(broadcastId) {
    closeBroadcastViewModal();
    // Implementation would populate the create form with existing data
    createNewBroadcast();
    showToast(`Редактирование рассылки ${broadcastId}`, 'info');
}

function sendBroadcast(broadcastId) {
    const broadcast = mockData.broadcasts.find(b => b.id === broadcastId);
    if (!broadcast || broadcast.status !== 'draft') return;
    
    if (confirm('Отправить эту рассылку сейчас?')) {
        broadcast.status = 'sent';
        broadcast.sentAt = new Date().toISOString().slice(0, 16).replace('T', ' ');
        broadcast.delivered = Math.floor(broadcast.audienceCount * 0.95);
        broadcast.failed = Math.floor(broadcast.audienceCount * 0.05);
        broadcast.read = Math.floor(broadcast.audienceCount * 0.65);
        
        showToast('Рассылка отправлена', 'success');
        closeBroadcastViewModal();
        loadPage('messages');
    }
}

function duplicateBroadcast(broadcastId) {
    const broadcast = mockData.broadcasts.find(b => b.id === broadcastId);
    if (!broadcast) return;
    
    const newBroadcast = {
        ...broadcast,
        id: Math.max(...mockData.broadcasts.map(b => b.id)) + 1,
        title: `${broadcast.title} (копия)`,
        status: 'draft',
        sentAt: null,
        delivered: 0,
        failed: 0,
        read: 0
    };
    
    mockData.broadcasts.push(newBroadcast);
    showToast('Рассылка дублирована', 'success');
    loadPage('messages');
}

function deleteBroadcast(broadcastId) {
    if (confirm('Вы уверены, что хотите удалить эту рассылку?')) {
        const index = mockData.broadcasts.findIndex(b => b.id === broadcastId);
        if (index !== -1) {
            mockData.broadcasts.splice(index, 1);
            showToast('Рассылка удалена', 'success');
            closeBroadcastViewModal();
            loadPage('messages');
        }
    }
}

function exportBroadcasts() {
    const broadcasts = mockData.broadcasts;
    const dataStr = JSON.stringify(broadcasts, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'broadcasts_export.json';
    link.click();
    showToast('Рассылки экспортированы', 'success');
}

function clearBroadcastFilters() {
    document.getElementById('broadcasts-search').value = '';
    document.getElementById('status-filter').value = '';
    document.getElementById('audience-filter').value = '';
    showToast('Фильтры очищены', 'info');
}

// Update old function references
function createBroadcast() {
    createNewBroadcast();
}

function viewMessageHistory() {
    showToast('История сообщений отображается в таблице', 'info');
}