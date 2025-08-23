<?php

require_once __DIR__ . '/vendor/autoload.php';

use FrontBot\Config\Config;
use FrontBot\Routers\StartRouter;
use FrontBot\Routers\MenuRouter;
use FrontBot\Routers\ResponsesRouter;
use FrontBot\Routers\AutoResponsesRouter;
use FrontBot\Routers\LettersRouter;
use FrontBot\Routers\StatsRouter;
use FrontBot\Utils\States;
use FrontBot\Utils\Texts;
use Longman\TelegramBot\Telegram;
use Longman\TelegramBot\Request;
use Longman\TelegramBot\Exception\TelegramException;
use Monolog\Logger;
use Monolog\Handler\StreamHandler;

// Настройка логирования
$logger = new Logger('telegram_bot');
$logger->pushHandler(new StreamHandler(__DIR__ . '/bot.log', Logger::INFO));

// Хранилище данных пользователей (в реальном проекте используйте базу данных)
$userData = [];
$botData = [];

try {
    // Создаем экземпляр бота
    $telegram = new Telegram(Config::TELEGRAM_BOT_TOKEN, Config::BOT_USERNAME);
    
    // Включаем логирование
    $telegram->enableLimiter();
    
    // Устанавливаем команды бота
    $commands = [
        ['command' => 'start', 'description' => 'Начать / Перезапустить'],
        ['command' => 'menu', 'description' => 'Главное меню 🧭'],
        ['command' => 'responses', 'description' => 'Запустить отклики 🚀'],
        ['command' => 'response_messages', 'description' => 'Сопроводительные письма ✉️'],
        ['command' => 'auto_responses', 'description' => 'Автоотклики по параметрам 🤖'],
        ['command' => 'subscription', 'description' => 'Подписка 💎'],
        ['command' => 'stats', 'description' => 'Статистика 📊'],
        ['command' => 'support', 'description' => 'Поддержка 🆘'],
        ['command' => 'referral', 'description' => 'Реферальная программа 🎁'],
    ];
    
    Request::setMyCommands(['commands' => $commands]);
    
    $logger->info('Demo bot started successfully!');
    
    // Основной цикл обработки обновлений
    while (true) {
        try {
            // Получаем обновления
            $serverResponse = Request::getUpdates([
                'offset' => $botData['last_update_id'] ?? 0,
                'limit' => 100,
                'timeout' => 10
            ]);
            
            if ($serverResponse->isOk()) {
                $updates = $serverResponse->getResult();
                
                foreach ($updates as $update) {
                    $updateId = $update->getUpdateId();
                    $botData['last_update_id'] = $updateId + 1;
                    
                    // Получаем ID пользователя
                    $userId = null;
                    if ($update->getMessage()) {
                        $userId = $update->getMessage()->getFrom()->getId();
                    } elseif ($update->getCallbackQuery()) {
                        $userId = $update->getCallbackQuery()->getFrom()->getId();
                    }
                    
                    if (!$userId) {
                        continue;
                    }
                    
                    // Инициализируем данные пользователя
                    if (!isset($userData[$userId])) {
                        $userData[$userId] = [];
                    }
                    
                    // Обрабатываем обновление
                    handleUpdate($update, $userData[$userId], $botData, $logger);
                }
            }
            
        } catch (TelegramException $e) {
            $logger->error('Telegram API error: ' . $e->getMessage());
            sleep(5); // Ждем перед повторной попыткой
        } catch (Exception $e) {
            $logger->error('General error: ' . $e->getMessage());
            sleep(1);
        }
        
        // Небольшая пауза между запросами
        usleep(100000); // 0.1 секунды
    }
    
} catch (TelegramException $e) {
    $logger->error('Failed to initialize bot: ' . $e->getMessage());
    echo 'Error: ' . $e->getMessage() . PHP_EOL;
} catch (Exception $e) {
    $logger->error('Unexpected error: ' . $e->getMessage());
    echo 'Unexpected error: ' . $e->getMessage() . PHP_EOL;
}

/**
 * Обрабатывает входящее обновление
 */
function handleUpdate($update, array &$userData, array &$botData, Logger $logger): void
{
    try {
        // Обработка команд
        if ($update->getMessage() && $update->getMessage()->getText()) {
            $text = $update->getMessage()->getText();
            $command = explode(' ', $text)[0];
            
            switch ($command) {
                case '/start':
                    StartRouter::start($update, $userData);
                    break;
                    
                case '/menu':
                    MenuRouter::mainMenu($update, $userData);
                    break;
                    
                case '/responses':
                    ResponsesRouter::startResponsesEntry($update, $userData);
                    break;
                    
                case '/response_messages':
                    LettersRouter::showCoverLetters($update, $userData);
                    break;
                    
                case '/auto_responses':
                    AutoResponsesRouter::showAutoResponsesMenu($update, $userData);
                    break;
                    
                case '/subscription':
                    MenuRouter::showSubscription($update, $userData);
                    break;
                    
                case '/stats':
                    StatsRouter::showStatsMenu($update, $userData);
                    break;
                    
                case '/support':
                    MenuRouter::showSupport($update, $userData);
                    break;
                    
                case '/referral':
                    MenuRouter::showReferralProgram($update, $userData);
                    break;
                    
                default:
                    // Обработка текстовых сообщений в зависимости от состояния
                    handleTextMessage($update, $userData, $botData);
                    break;
            }
        }
        
        // Обработка callback queries
        if ($update->getCallbackQuery()) {
            handleCallbackQuery($update, $userData, $botData);
        }
        
    } catch (Exception $e) {
        $logger->error('Error handling update: ' . $e->getMessage());
    }
}

/**
 * Обрабатывает callback queries
 */
function handleCallbackQuery($update, array &$userData, array &$botData): void
{
    $callbackQuery = $update->getCallbackQuery();
    $data = $callbackQuery->getData();
    
    // Основные команды меню
    if ($data === 'link_account') {
        StartRouter::linkAccount($update, $userData);
        return;
    }
    
    if ($data === 'main_menu') {
        MenuRouter::backToMainMenu($update, $userData);
        return;
    }
    
    if ($data === 'subscription') {
        MenuRouter::showSubscription($update, $userData);
        return;
    }
    
    if ($data === 'pay_week' || $data === 'pay_month') {
        MenuRouter::handlePaymentStub($update, $userData);
        return;
    }
    
    if ($data === 'support') {
        MenuRouter::showSupport($update, $userData);
        return;
    }
    
    if ($data === 'referral') {
        MenuRouter::showReferralProgram($update, $userData);
        return;
    }
    
    // Главные разделы
    if ($data === 'start_responses') {
        ResponsesRouter::startResponsesEntry($update, $userData);
        return;
    }
    
    if ($data === 'auto_responses') {
        AutoResponsesRouter::showAutoResponsesMenu($update, $userData);
        return;
    }
    
    if ($data === 'cover_letters') {
        LettersRouter::showCoverLetters($update, $userData);
        return;
    }
    
    if ($data === 'stats') {
        StatsRouter::showStatsMenu($update, $userData);
        return;
    }
    
    // Обработка откликов
    if ($data === 'new_request') {
        ResponsesRouter::askResume($update, $userData);
        return;
    }
    
    if ($data === 'past_requests') {
        sendInDevelopmentMessage($update);
        return;
    }
    
    // Обработка резюме
    if (preg_match('/^resume_/', $data)) {
        ResponsesRouter::askSearchMethod($update, $userData);
        return;
    }
    
    // Обработка способа поиска
    if ($data === 'configure_filters') {
        ResponsesRouter::askCountryForFilters($update, $userData);
        return;
    }
    
    if ($data === 'paste_link') {
        sendInDevelopmentMessage($update);
        return;
    }
    
    // Обработка стран
    if (preg_match('/^country_/', $data)) {
        ResponsesRouter::askRegion($update, $userData);
        return;
    }
    
    // Обработка регионов
    if (preg_match('/^region_/', $data)) {
        ResponsesRouter::askSchedule($update, $userData);
        return;
    }
    
    // Обработка графика работы
    if (preg_match('/^schedule_(?!next)/', $data)) {
        ResponsesRouter::handleScheduleChoice($update, $userData);
        return;
    }
    
    if ($data === 'schedule_next') {
        ResponsesRouter::askEmployment($update, $userData);
        return;
    }
    
    // Обработка типа занятости
    if (preg_match('/^employment_(?!next)/', $data)) {
        ResponsesRouter::handleEmploymentChoice($update, $userData);
        return;
    }
    
    if ($data === 'employment_next') {
        ResponsesRouter::askProfession($update, $userData);
        return;
    }
    
    // Обработка профессий
    if (preg_match('/^profession_(?!next)/', $data)) {
        ResponsesRouter::handleProfessionChoice($update, $userData);
        return;
    }
    
    if ($data === 'profession_next') {
        ResponsesRouter::askKeyword($update, $userData);
        return;
    }
    
    // Обработка пагинации профессий
    if (preg_match('/^page_profession_select_all/', $data)) {
        ResponsesRouter::handleProfessionSelectAll($update, $userData);
        return;
    }
    
    if (preg_match('/^page_profession_nav_/', $data)) {
        ResponsesRouter::handleProfessionNavigation($update, $userData);
        return;
    }
    
    // Обработка подтверждения
    if ($data === 'continue_to_confirmation') {
        ResponsesRouter::confirmation($update, $userData);
        return;
    }
    
    if ($data === 'send_responses') {
        ResponsesRouter::sendResponses($update, $userData, $botData);
        return;
    }
    
    if ($data === 'restart_flow') {
        ResponsesRouter::askResume($update, $userData);
        return;
    }
    
    // Обработка сопроводительных писем
    if ($data === 'cl_new') {
        LettersRouter::askNewCoverLetterTitle($update, $userData);
        return;
    }
    
    if (preg_match('/^cl_view_/', $data)) {
        LettersRouter::viewCoverLetter($update, $userData);
        return;
    }
    
    if ($data === 'cl_back_to_list') {
        LettersRouter::showCoverLetters($update, $userData);
        return;
    }
    
    if ($data === 'cl_delete') {
        LettersRouter::deleteCoverLetter($update, $userData);
        return;
    }
    
    // Обработка статистики
    if (preg_match('/^stats_resume_/', $data)) {
        StatsRouter::showResumeStats($update, $userData);
        return;
    }
    
    // Обработка автооткликов
    if ($data === 'auto_setup') {
        AutoResponsesRouter::startAutoSetup($update, $userData);
        return;
    }
    
    if ($data === 'auto_ask_resume') {
        AutoResponsesRouter::askAutoResume($update, $userData);
        return;
    }
    
    if (preg_match('/^auto_resume_/', $data)) {
        AutoResponsesRouter::askAutoSearchMethod($update, $userData);
        return;
    }
    
    if ($data === 'auto_configure_filters') {
        AutoResponsesRouter::configureAutoFilters($update, $userData);
        return;
    }
    
    if ($data === 'auto_paste_link') {
        AutoResponsesRouter::askAutoHhUrl($update, $userData);
        return;
    }
    
    if ($data === 'auto_continue_to_confirmation') {
        AutoResponsesRouter::autoConfirmation($update, $userData);
        return;
    }
    
    if ($data === 'auto_start') {
        AutoResponsesRouter::startAutoResponses($update, $userData);
        return;
    }
    
    if ($data === 'auto_stop') {
        AutoResponsesRouter::stopAutoResponses($update, $userData);
        return;
    }
    
    if ($data === 'auto_change_settings') {
        AutoResponsesRouter::askAutoResume($update, $userData);
        return;
    }
    
    // Если ничего не подошло, отправляем сообщение о разработке
    sendInDevelopmentMessage($update);
}

/**
 * Обрабатывает текстовые сообщения
 */
function handleTextMessage($update, array &$userData, array &$botData): void
{
    $currentState = $userData['current_state'] ?? null;
    
    // В зависимости от текущего состояния обрабатываем сообщение
    switch ($currentState) {
        case States::ASK_KEYWORD:
            ResponsesRouter::handleKeywordInput($update, $userData);
            break;
            
        case States::CL_ASK_TITLE:
            LettersRouter::askNewCoverLetterBody($update, $userData);
            break;
            
        case States::CL_SAVE_BODY:
            LettersRouter::saveCoverLetterBody($update, $userData);
            break;
            
        case States::AUTO_ASK_HH_URL:
            AutoResponsesRouter::handleAutoHhUrlInput($update, $userData);
            break;
            
        default:
            // Если состояние не определено, показываем главное меню
            MenuRouter::mainMenu($update, $userData);
            break;
    }
}

/**
 * Отправляет сообщение "В разработке"
 */
function sendInDevelopmentMessage($update): void
{
    if ($update->getCallbackQuery()) {
        $chatId = $update->getCallbackQuery()->getMessage()->getChat()->getId();
        
        Request::answerCallbackQuery([
            'callback_query_id' => $update->getCallbackQuery()->getId()
        ]);
        
        Request::sendMessage([
            'chat_id' => $chatId,
            'text' => Texts::IN_DEVELOPMENT
        ]);
    } elseif ($update->getMessage()) {
        $chatId = $update->getMessage()->getChat()->getId();
        
        Request::sendMessage([
            'chat_id' => $chatId,
            'text' => Texts::IN_DEVELOPMENT
        ]);
    }
}