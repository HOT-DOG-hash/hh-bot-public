<?php

namespace FrontBot\Routers;

use FrontBot\Utils\Texts;
use Longman\TelegramBot\Entities\InlineKeyboard;
use Longman\TelegramBot\Entities\InlineKeyboardButton;
use Longman\TelegramBot\Entities\Update;
use Longman\TelegramBot\Request;

/**
 * Обработчик главного меню
 */
class MenuRouter
{
    /**
     * Создает и возвращает клавиатуру главного меню
     */
    public static function getMainMenuKeyboard(): InlineKeyboard
    {
        return new InlineKeyboard(
            [new InlineKeyboardButton(['text' => '🚀 Запустить отклики', 'callback_data' => 'start_responses'])],
            [new InlineKeyboardButton(['text' => '📎 Автоотклики по параметрам', 'callback_data' => 'auto_responses'])],
            [new InlineKeyboardButton(['text' => '📄 Сопроводительные письма', 'callback_data' => 'cover_letters'])],
            [new InlineKeyboardButton(['text' => '💳 Подписка', 'callback_data' => 'subscription'])],
            [new InlineKeyboardButton(['text' => '📊 Статистика откликов', 'callback_data' => 'stats'])],
            [new InlineKeyboardButton(['text' => '🛠 Поддержка', 'callback_data' => 'support'])],
            [new InlineKeyboardButton(['text' => '👥 Реферальная программа', 'callback_data' => 'referral'])]
        );
    }

    /**
     * Отображает главное меню
     */
    public static function mainMenu(Update $update, array &$userData, ?int $chatId = null): array
    {
        $replyMarkup = self::getMainMenuKeyboard();
        $text = Texts::MAIN_MENU_TITLE;

        if ($update && $update->getCallbackQuery()) {
            $callbackQuery = $update->getCallbackQuery();
            $chatId = $callbackQuery->getMessage()->getChat()->getId();
            $messageId = $callbackQuery->getMessage()->getMessageId();

            Request::answerCallbackQuery([
                'callback_query_id' => $callbackQuery->getId()
            ]);

            Request::editMessageText([
                'chat_id' => $chatId,
                'message_id' => $messageId,
                'text' => $text,
                'reply_markup' => $replyMarkup
            ]);
        } elseif ($update && $update->getMessage()) {
            $chatId = $update->getMessage()->getChat()->getId();
            Request::sendMessage([
                'chat_id' => $chatId,
                'text' => $text,
                'reply_markup' => $replyMarkup
            ]);
        } elseif ($chatId) {
            // Для вызова из внешних источников
            Request::sendMessage([
                'chat_id' => $chatId,
                'text' => $text,
                'reply_markup' => $replyMarkup
            ]);
        }

        return ['state' => null];
    }

    /**
     * Возвращает в главное меню
     */
    public static function backToMainMenu(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        return self::mainMenu($update, $userData);
    }

    /**
     * Показывает информацию о реферальной программе
     */
    public static function showReferralProgram(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $userId = $callbackQuery->getFrom()->getId();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        // Получаем информацию о боте для создания реферальной ссылки
        $botInfo = Request::getMe();
        $botUsername = $botInfo->getResult()->getUsername();
        $referralLink = "https://t.me/{$botUsername}?start={$userId}";

        // Демо данные
        $level1Referrals = 5;
        $level2Referrals = 12;
        $level3Referrals = 3;
        $totalIncome = 2500;
        $balance = 1200;
        $minWithdrawal = 500;

        $text = Texts::getReferralText(
            $referralLink,
            $level1Referrals,
            $level2Referrals,
            $level3Referrals,
            $totalIncome,
            $balance,
            $minWithdrawal
        );

        $keyboard = new InlineKeyboard([
            new InlineKeyboardButton([
                'text' => Texts::BACK_TO_MAIN_MENU,
                'callback_data' => 'main_menu'
            ])
        ]);

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
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
     * Показывает статус подписки и варианты оплаты (демо режим)
     */
    public static function showSubscription(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        $subscriptionStatus = $userData['subscription_status'] ?? 'active'; // По умолчанию активна в демо

        $text = Texts::SUBSCRIPTION_INFO;

        if ($subscriptionStatus === 'active') {
            $text .= "**Ваш статус:**\n" . Texts::SUBSCRIPTION_ACTIVE;
        } else {
            $text .= "**Ваш статус:**\n" . Texts::SUBSCRIPTION_INACTIVE;
        }

        $keyboard = new InlineKeyboard(
            [new InlineKeyboardButton(['text' => 'Неделя — 690₽', 'callback_data' => 'pay_week'])],
            [new InlineKeyboardButton(['text' => 'Месяц — 1900₽', 'callback_data' => 'pay_month'])],
            [new InlineKeyboardButton(['text' => Texts::BACK_TO_MAIN_MENU, 'callback_data' => 'main_menu'])]
        );

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
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
     * Обрабатывает заглушку для обработки платежей (демо режим)
     */
    public static function handlePaymentStub(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $userData['subscription_status'] = 'active';

        $text = Texts::SUBSCRIPTION_SUCCESS;
        $keyboard = new InlineKeyboard([
            new InlineKeyboardButton([
                'text' => Texts::BACK_TO_MAIN_MENU,
                'callback_data' => 'main_menu'
            ])
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
     * Показывает информацию о поддержке (демо режим)
     */
    public static function showSupport(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        $supportText = Texts::SUPPORT_INFO;

        $keyboard = new InlineKeyboard([
            new InlineKeyboardButton([
                'text' => Texts::BACK_TO_MAIN_MENU,
                'callback_data' => 'main_menu'
            ])
        ]);

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => $supportText,
            'reply_markup' => $keyboard
        ]);

        return ['state' => null];
    }
}