<?php

namespace FrontBot\Routers;

use FrontBot\Config\Config;
use FrontBot\Utils\Texts;
use FrontBot\Utils\States;
use FrontBot\Utils\Helpers;
use FrontBot\Utils\Buttons;
use Longman\TelegramBot\Entities\InlineKeyboard;
use Longman\TelegramBot\Entities\InlineKeyboardButton;
use Longman\TelegramBot\Entities\Update;
use Longman\TelegramBot\Request;

/**
 * Обработчик автооткликов по параметрам
 */
class AutoResponsesRouter
{
    /**
     * Показывает главное меню автооткликов
     */
    public static function showAutoResponsesMenu(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Проверяем статус автооткликов
        $autoResponsesActive = $userData['auto_responses_active'] ?? false;
        
        if ($autoResponsesActive) {
            // Показываем активный статус
            $startDate = $userData['auto_responses_start_date'] ?? date('d.m.Y');
            $startTime = $userData['auto_responses_start_time'] ?? date('H:i');
            $todayCount = $userData['auto_responses_today_count'] ?? 0;
            $totalCount = $userData['auto_responses_total_count'] ?? 0;
            $filtersInfo = $userData['auto_responses_filters_info'] ?? 'Настройки не заданы';

            $text = Texts::getAutoResponseActiveStatus(
                $startDate,
                $startTime,
                $todayCount,
                $totalCount,
                $filtersInfo
            );

            $keyboard = new InlineKeyboard(
                [new InlineKeyboardButton(['text' => '⏹️ Остановить автоотклики', 'callback_data' => 'auto_stop'])],
                [new InlineKeyboardButton(['text' => '⚙️ Изменить настройки', 'callback_data' => 'auto_change_settings'])],
                [new InlineKeyboardButton(['text' => Texts::BACK_TO_MAIN_MENU, 'callback_data' => 'main_menu'])]
            );
        } else {
            // Показываем неактивный статус
            $text = Texts::AUTO_RESPONSE_INACTIVE_STATUS;

            $keyboard = new InlineKeyboard(
                [new InlineKeyboardButton(['text' => '🚀 Настроить автоотклики', 'callback_data' => 'auto_setup'])],
                [new InlineKeyboardButton(['text' => Texts::BACK_TO_MAIN_MENU, 'callback_data' => 'main_menu'])]
            );
        }

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => $text,
            'reply_markup' => $keyboard
        ]);

        return ['state' => null];
    }

    /**
     * Начинает настройку автооткликов
     */
    public static function startAutoSetup(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Показываем информацию об автооткликах
        $text = Texts::AUTO_RESPONSE_MAIN;

        $keyboard = new InlineKeyboard([
            new InlineKeyboardButton(['text' => '▶️ Начать настройку', 'callback_data' => 'auto_ask_resume'])
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => $text,
            'reply_markup' => $keyboard
        ]);

        return ['state' => null];
    }

    /**
     * Выбор резюме для автооткликов
     */
    public static function askAutoResume(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $userData['auto_request'] = [];

        // Используем демо-резюме из конфига
        $resumes = Config::DEMO_RESUMES;

        $keyboard = [];
        foreach ($resumes as $resume) {
            $keyboard[] = [new InlineKeyboardButton([
                'text' => $resume['title'],
                'callback_data' => 'auto_resume_' . $resume['id']
            ])];
        }

        $replyMarkup = new InlineKeyboard(...$keyboard);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::AUTO_RESPONSE_ASK_RESUME,
            'reply_markup' => $replyMarkup
        ]);

        $userData['current_state'] = States::AUTO_ASK_RESUME;
        return ['state' => States::AUTO_ASK_RESUME];
    }

    /**
     * Выбор способа поиска для автооткликов
     */
    public static function askAutoSearchMethod(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        $userData['auto_request']['resume'] = str_replace('auto_resume_', '', $callbackQuery->getData());

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $keyboard = new InlineKeyboard(
            [new InlineKeyboardButton(['text' => 'Настроить фильтры', 'callback_data' => 'auto_configure_filters'])],
            [new InlineKeyboardButton(['text' => 'Вставить ссылку hh.ru', 'callback_data' => 'auto_paste_link'])]
        );

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::AUTO_RESPONSE_ASK_SEARCH_METHOD,
            'reply_markup' => $keyboard
        ]);

        $userData['current_state'] = States::AUTO_ASK_SEARCH_METHOD;
        return ['state' => States::AUTO_ASK_SEARCH_METHOD];
    }

    /**
     * Настройка фильтров для автооткликов (используем тот же флоу что и для обычных откликов)
     */
    public static function configureAutoFilters(Update $update, array &$userData): array
    {
        // Перенаправляем на настройку фильтров из ResponsesRouter
        return ResponsesRouter::askCountryForFilters($update, $userData);
    }

    /**
     * Запрос ссылки HH.ru для автооткликов
     */
    public static function askAutoHhUrl(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::AUTO_RESPONSE_ASK_HH_URL
        ]);

        $userData['current_state'] = States::AUTO_ASK_HH_URL;
        return ['state' => States::AUTO_ASK_HH_URL];
    }

    /**
     * Подтверждение настроек автооткликов
     */
    public static function autoConfirmation(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Получаем данные для подтверждения
        $resumeTitle = 'Выбранное резюме';
        $searchMethod = 'Настроенные фильтры';
        $filtersSummary = 'Демо настройки фильтров';
        $coverLetterStatus = 'Без сопроводительного письма';

        $text = Texts::getAutoResponseConfirmation(
            $resumeTitle,
            $searchMethod,
            $filtersSummary,
            $coverLetterStatus
        );

        $keyboard = new InlineKeyboard(
            [new InlineKeyboardButton(['text' => '🚀 Запустить автоотклики', 'callback_data' => 'auto_start'])],
            [new InlineKeyboardButton(['text' => 'Изменить настройки', 'callback_data' => 'auto_ask_resume'])]
        );

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => $text,
            'reply_markup' => $keyboard
        ]);

        $userData['current_state'] = States::AUTO_CONFIRMATION;
        return ['state' => States::AUTO_CONFIRMATION];
    }

    /**
     * Запуск автооткликов
     */
    public static function startAutoResponses(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Сохраняем настройки автооткликов
        $userData['auto_responses_active'] = true;
        $userData['auto_responses_start_date'] = date('d.m.Y');
        $userData['auto_responses_start_time'] = date('H:i');
        $userData['auto_responses_today_count'] = 0;
        $userData['auto_responses_total_count'] = 0;
        $userData['auto_responses_filters_info'] = 'Демо настройки фильтров';

        $keyboard = new InlineKeyboard([
            new InlineKeyboardButton(['text' => 'Главное меню', 'callback_data' => 'main_menu'])
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::AUTO_RESPONSE_STARTED,
            'reply_markup' => $keyboard
        ]);

        return ['state' => null];
    }

    /**
     * Остановка автооткликов
     */
    public static function stopAutoResponses(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Останавливаем автоотклики
        $userData['auto_responses_active'] = false;

        $keyboard = new InlineKeyboard(
            [new InlineKeyboardButton(['text' => '🚀 Настроить автоотклики', 'callback_data' => 'auto_setup'])],
            [new InlineKeyboardButton(['text' => Texts::BACK_TO_MAIN_MENU, 'callback_data' => 'main_menu'])]
        );

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::AUTO_RESPONSE_STOPPED,
            'reply_markup' => $keyboard
        ]);

        return ['state' => null];
    }

    /**
     * Обработка текстового ввода ссылки HH.ru
     */
    public static function handleAutoHhUrlInput(Update $update, array &$userData): array
    {
        $message = $update->getMessage();
        $chatId = $message->getChat()->getId();
        $url = $message->getText();

        $userData['auto_request']['hh_url'] = $url;

        // Переходим к подтверждению
        $keyboard = new InlineKeyboard([
            new InlineKeyboardButton(['text' => 'Продолжить', 'callback_data' => 'auto_continue_to_confirmation'])
        ]);

        Request::sendMessage([
            'chat_id' => $chatId,
            'text' => "Ссылка HH.ru: {$url}\nНажмите 'Продолжить' для завершения настройки.",
            'reply_markup' => $keyboard
        ]);

        $userData['current_state'] = States::AUTO_CONFIRMATION;
        return ['state' => States::AUTO_CONFIRMATION];
    }
}