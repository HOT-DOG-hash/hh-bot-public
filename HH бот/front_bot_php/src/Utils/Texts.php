<?php

namespace FrontBot\Utils;

/**
 * Тексты для бота
 */
class Texts
{
    // --- General ---
    public const CANCEL_ACTION = "Действие отменено. Начинаем заново.";
    public const IN_DEVELOPMENT = "Раздел в разработке.";
    public const BACK_TO_MAIN_MENU = "🔙 Главное меню";

    // --- Start ---
    public const WELCOME = "👋 Добро пожаловать в Get Offer Bot!\n" .
        "Я помогу тебе массово откликаться на вакансии на hh.ru.\n" .
        "Для начала — привяжи свой аккаунт, а дальше сможешь настроить автоотклик, письма и аналитику.";

    public const ACCOUNT_LINKED = "✅ Аккаунт успешно привязан! Теперь ты можешь использовать возможности бота.";

    // --- Main Menu ---
    public const MAIN_MENU_TITLE = "Главное меню:";

    // --- Subscription ---
    public const SUBSCRIPTION_INFO = "💳 Чтобы пользоваться ботом, нужно оплатить тариф.\n\n" .
        "Тариф включает:\n" .
        "✓ Доступ к массовым откликам\n" .
        "✓ Лимит 200 откликов в сутки\n" .
        "✓ Личную статистику и сопровождение\n\n";

    public const SUBSCRIPTION_ACTIVE = "✅ Подписка активна до 17 июля 2025";
    public const SUBSCRIPTION_INACTIVE = "🚫 Не оплачено";
    public const SUBSCRIPTION_SUCCESS = "✅ Подписка активна до 17 июля 2025";

    // --- Support ---
    public const SUPPORT_INFO = "🛠 Нужна помощь?\n\n" .
        "Если у тебя возникли вопросы по работе бота, подписке или откликам — просто напиши нам 👇\n" .
        "@hh_support_bot\n\n" .
        "Мы на связи каждый день с 10:00 до 20:00 (МСК)";

    // --- Cover Letters ---
    public const CL_MENU_HEADER = "📄 Сопроводительные письма\n\n" .
        "Сопроводительное письмо — это дополнительный текст, который будет автоматически добавляться к каждому отклику.\n\n" .
        "📌 В этом разделе можно настроить сопроводительные письма, чтобы они всегда были под рукой в момент создания запроса.\n\n" .
        "Если ты не хочешь добавлять письмо — можно откликаться без него.";

    public const CL_LIMIT_REACHED = "❗ У тебя уже 5 писем. Удали одно, чтобы создать новое.";
    public const CL_ASK_TITLE = "Шаг 1/2: Отправьте название сопроводительного письма (до 50 символов):\n_Будет видно только вам в этом боте._";
    public const CL_ASK_BODY = "Шаг 2/2: Отправьте текст сопроводительного письма:\n_Будет видно работодателям._";
    public const CL_SAVED = "✅ Письмо сохранено!";
    public const CL_DELETED = "Письмо удалено.";

    // --- Responses Flow ---
    public const CHOOSE_ACTION = "Выберите действие:";
    public const ASK_RESUME = "📍 Шаг 1/10:\nВыберите резюме с которого будут отправлены отклики";
    public const ASK_COUNTRY = "📍 Шаг 2/10:\nВыберите страну поиска";
    public const ASK_REGION = "📍 Шаг 3/10:\nВыберите регион";

    public const ASK_SCHEDULE = "📍 Шаг 4/10:\n" .
        "Выберите график работы и нажмите \"Далее\".\n\n" .
        "Можете отметить несколько:\n" .
        "🔴 - не выбрано\n" .
        "🟢 - выбрано";

    public const ASK_EMPLOYMENT = "📍 Шаг 5/10:\n" .
        "Выберите тип занятости и нажмите \"Далее\".\n\n" .
        "Можете отметить несколько:\n" .
        "🔴 - не выбрано\n" .
        "🟢 - выбрано";

    public const ASK_PROFESSION = "📍 Шаг 6/10:\n" .
        "Выберите профессиональную область\n\n" .
        "Можете отметить несколько:\n" .
        "🔴 - не выбрано\n" .
        "🟢 - выбрано\n\n" .
        "Добавить пагинация: ⬅️ Назад | Вперед ➡️";

    public const ASK_KEYWORD = "📍 Шаг 7/10:\n" .
        "Введите ключевое слово для поиска так, как вы бы искали вакансию на HH\n\n" .
        "Пример: Таргетолог, Менеджер маркетплейсов, SMM специалист, Веб дизайнер и тд\n\n" .
        "На следующем шаге можно будет выбрать настройки поиска:\n" .
        "— В названии компании\n" .
        "— В названии описания вакансии\n" .
        "— В описании вакансии\n" .
        "— Везде";

    public const ASK_COVER_LETTER = "📍 Шаг 9/10:\n" .
        "Напишите сопроводительное письмо, которое будет отправляться вместе с откликами.\n\n" .
        "Или выберите из ранее созданных шаблонов:";

    public const RESPONSES_STARTED = "🚀 Процесс запущен\n\n" .
        "Посмотреть отклики вы сможете в личном кабинете на hh.ru\n" .
        "Бот пришлёт уведомление после завершения задачи.";

    public const RESPONSES_SENT = "Отклики успешно отправлены!";

    // ================== HH.RU ===================
    public const HH_AUTHORIZATION_PROMPT = "Чтобы использовать функции, связанные с hh.ru, вам необходимо авторизоваться. Нажмите на кнопку ниже, чтобы перейти на сайт hh.ru и предоставить доступ.";

    // ================== AUTO RESPONSES ===================
    public const AUTO_RESPONSE_MAIN = "Теперь вы можете откликаться на свежие вакансии сразу после их появления.\n" .
        "• Бот сам отслеживает новые вакансии по вашим фильтрам и автоматически отправляет отклик, как только работодатель опубликовал вакансию.\n" .
        "• Всё работает 24/7 — вам нужно только один раз настроить фильтры для поиска.\n" .
        "• Автоотклики срабатывают только на новые вакансии.\n\n" .
        "Просто настройте фильтры — и ваш поиск работы будет идти даже когда вы спите!";

    public const AUTO_RESPONSE_ASK_RESUME = "📍 Шаг 1/10:\nВыберите резюме, с которого будут отправляться автоотклики:";

    public const AUTO_RESPONSE_ASK_SEARCH_METHOD = "📍 Шаг 2/10:\n" .
        "Выберите способ поиска вакансий:";

    public const AUTO_RESPONSE_ASK_HH_URL = "Вставьте ссылку с сформированным списком вакансий по вашим фильтрам из hh.ru";

    public const AUTO_RESPONSE_INACTIVE_STATUS = "Статус:\n" .
        "🔴 Автоотклики выключены\n\n" .
        "Нажмите кнопку ниже, чтобы настроить и запустить автоотклики.";

    public const AUTO_RESPONSE_STARTED = "✅ Автоотклики запущены!\n\n" .
        "Бот будет автоматически отслеживать новые вакансии и отправлять отклики 24/7.\n" .
        "Вы получите уведомления о каждом отправленном отклике.";

    public const AUTO_RESPONSE_STOPPED = "⏹️ Автоотклики остановлены.\n\n" .
        "Вы можете в любой момент запустить их снова с теми же настройками или изменить параметры.";

    public const AUTO_RESPONSE_SETTINGS_CHANGED = "✅ Настройки автооткликов обновлены!";

    // ================== STATS ===================
    public const STATS_SELECT_RESUME = "Выберите резюме для отображения статистики:";
    public const STATS_NO_RESUMES = "У вас пока нет добавленных резюме для сбора статистики.";

    /**
     * Генерирует текст реферальной программы
     */
    public static function getReferralText(string $link, int $l1, int $l2, int $l3, int $income, int $balance, int $minWithdrawal): string
    {
        return "👥 Твоя реферальная ссылка:\n\n" .
            "{$link}\n\n" .
            "Каждый, кто оплачивает подписку после перехода по ней, становится твоим рефералом. С каждой оплаты ты получаешь % на внутренний баланс, а так же с оплат тех, кого пригласили твои рефералы.\n\n" .
            "1-й уровень — 20% от всех платежей\n" .
            "2-й уровень — 10% от всех платежей\n" .
            "3-й уровень — 5% от всех платежей\n\n" .
            "📊 Твоя структура:\n" .
            "👤 1 уровень: {$l1}\n" .
            "👥 2 уровень: {$l2}\n" .
            "👥 3 уровень: {$l3}\n\n" .
            "Общий доход: {$income}₽\n" .
            "Баланс: {$balance}₽\n\n" .
            "Чтобы вывести баланс, свяжитесь с поддержкой.\n" .
            "Минимальная сумма для вывода - {$minWithdrawal}р";
    }

    /**
     * Генерирует текст просмотра сопроводительного письма
     */
    public static function getClViewText(string $body): string
    {
        return "📝 Текст сопроводительного письма:\n\n{$body}";
    }

    /**
     * Генерирует текст для поля поиска
     */
    public static function getSearchFieldText(string $keyword): string
    {
        return "📍 Шаг 8/10:\n" .
            "Ваш поиск выполнен по запросу \"{$keyword}\".\n\n" .
            "Выберите где искать совпадения и нажмите \"Далее\":\n\n" .
            "Можете отметить несколько:\n" .
            "🔴 - не выбрано\n" .
            "🟢 - выбрано";
    }

    /**
     * Генерирует текст подтверждения
     */
    public static function getConfirmationText(
        int $vacancyCount,
        string $hhRuLink,
        string $countryName,
        string $regionName,
        string $schedule,
        string $employment,
        string $profession,
        string $keyword,
        string $searchField,
        string $coverLetter,
        int $dailyCount = 0,
        int $remainingCount = 200
    ): string {
        $coverLetterStatus = $coverLetter !== "Без сопроводительного письма" ? "Да" : "Нет";

        return "📍 Шаг 10/10: Настройка завершена!\n" .
            "Количество найденных вакансий — {$vacancyCount}\n\n" .
            "Посмотреть вакансии на HH.ru из сформированного запроса — <a href=\"{$hhRuLink}\">посмотреть</a>\n\n" .
            "Запрос:\n" .
            "1) Страна: {$countryName}\n" .
            "2) Регион: {$regionName}\n" .
            "3) График работы: {$schedule}\n" .
            "4) Тип занятости: {$employment}\n" .
            "5) Проф. область: {$profession}\n" .
            "6) Запрос: {$keyword}\n" .
            "7) Где ищем: {$searchField}\n" .
            "8) Сопроводительное письмо: {$coverLetterStatus}\n\n" .
            "Нажмите кнопку ниже, чтобы отправить отклики.\n" .
            "Количество доступных откликов для отправки сегодня — {$remainingCount}";
    }

    /**
     * Генерирует статус активных автооткликов
     */
    public static function getAutoResponseActiveStatus(
        string $startDate,
        string $startTime,
        int $todayCount,
        int $totalCount,
        string $filtersInfo
    ): string {
        return "Статус:\n" .
            "🟢 Автоотклики включены\n\n" .
            "Статистика:\n" .
            "• Старт продвижения: {$startDate}, {$startTime}\n" .
            "• Отправлено сегодня: {$todayCount} откликов\n" .
            "• Отправлено всего: {$totalCount} откликов\n\n" .
            "Настройки фильтров:\n{$filtersInfo}";
    }

    /**
     * Генерирует подтверждение настроек автооткликов
     */
    public static function getAutoResponseConfirmation(
        string $resumeTitle,
        string $searchMethod,
        string $filtersSummary,
        string $coverLetterStatus
    ): string {
        return "📍 Шаг 10/10: Настройка завершена!\n\n" .
            "Резюме: {$resumeTitle}\n" .
            "Способ поиска: {$searchMethod}\n" .
            "Фильтры: {$filtersSummary}\n" .
            "Сопроводительное письмо: {$coverLetterStatus}\n\n" .
            "Нажмите кнопку ниже, чтобы запустить автоотклики.";
    }

    /**
     * Генерирует текст статистики
     */
    public static function getStatsText(
        string $resumeName,
        int $totalResponses,
        int $responsesToday,
        int $invites,
        int $declines
    ): string {
        $conversion = $totalResponses > 0 ? round(($invites / $totalResponses) * 100, 1) : 0;

        return "📊 Статистика для резюме \"{$resumeName}\":\n" .
            "• Всего откликов через бота: {$totalResponses}\n" .
            "• Сегодня: {$responsesToday}\n" .
            "• Приглашений: {$invites}\n" .
            "• Отказов: {$declines}\n\n" .
            "Конверсия из отклика в приглашение — {$conversion}%";
    }
}
