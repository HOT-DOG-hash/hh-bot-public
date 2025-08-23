<?php

namespace FrontBot\Routers;

use FrontBot\Utils\Texts;
use Longman\TelegramBot\Entities\InlineKeyboard;
use Longman\TelegramBot\Entities\InlineKeyboardButton;
use Longman\TelegramBot\Entities\Update;
use Longman\TelegramBot\Request;

/**
 * Обработчик команды /start и привязки аккаунта
 */
class StartRouter
{
    /**
     * Обрабатывает команду /start
     */
    public static function start(Update $update, array &$userData): array
    {
        $userData = []; // Очищаем данные пользователя
        $chatId = $update->getMessage()->getChat()->getId();
        $messageText = $update->getMessage()->getText();

        // Проверяем реферальный код
        $args = explode(' ', $messageText);
        if (count($args) > 1) {
            $referrerId = (int)$args[1];
            if ($referrerId > 0) {
                error_log("User {$chatId} was referred by {$referrerId}");
                $userData['referrer_id'] = $referrerId;
            }
        }

        // Проверяем, привязан ли аккаунт
        if (isset($userData['account_linked']) && $userData['account_linked']) {
            // Если аккаунт уже привязан, показываем главное меню
            return MenuRouter::mainMenu($update, $userData);
        } else {
            // Показываем приветствие с кнопкой привязки аккаунта
            $keyboard = new InlineKeyboard([
                new InlineKeyboardButton([
                    'text' => '🔗 Привязать аккаунт на HH',
                    'callback_data' => 'link_account'
                ])
            ]);

            Request::sendMessage([
                'chat_id' => $chatId,
                'text' => Texts::WELCOME,
                'reply_markup' => $keyboard
            ]);

            return ['state' => null];
        }
    }

    /**
     * Имитирует привязку аккаунта
     */
    public static function linkAccount(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        // Отвечаем на callback query
        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Имитируем успешную привязку аккаунта
        $userData['account_linked'] = true;

        // Редактируем сообщение
        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::ACCOUNT_LINKED
        ]);

        // Показываем главное меню через 1 секунду
        sleep(1);
        return MenuRouter::mainMenu($update, $userData);
    }

    /**
     * Отменяет текущее действие и возвращает в стартовое меню
     */
    public static function startOver(Update $update, array &$userData): array
    {
        $chatId = $update->getMessage()->getChat()->getId();

        Request::sendMessage([
            'chat_id' => $chatId,
            'text' => Texts::CANCEL_ACTION
        ]);

        return self::start($update, $userData);
    }

    /**
     * Показывает сообщение "В разработке"
     */
    public static function inDevelopment(Update $update): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        Request::sendMessage([
            'chat_id' => $chatId,
            'text' => Texts::IN_DEVELOPMENT
        ]);

        // Удаляем предыдущее сообщение
        Request::deleteMessage([
            'chat_id' => $chatId,
            'message_id' => $callbackQuery->getMessage()->getMessageId()
        ]);

        return ['state' => null];
    }
}