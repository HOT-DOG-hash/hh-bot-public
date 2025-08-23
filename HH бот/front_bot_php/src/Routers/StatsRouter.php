<?php

namespace FrontBot\Routers;

use FrontBot\Utils\Texts;
use FrontBot\Utils\States;
use FrontBot\Utils\Helpers;
use Longman\TelegramBot\Entities\InlineKeyboard;
use Longman\TelegramBot\Entities\InlineKeyboardButton;
use Longman\TelegramBot\Entities\Update;
use Longman\TelegramBot\Request;

/**
 * Обработчик статистики откликов
 */
class StatsRouter
{
    /**
     * Показывает меню выбора резюме для статистики
     */
    public static function showStatsMenu(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        $resumes = Helpers::getDemoResumes();

        if (empty($resumes)) {
            // Если нет резюме
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
                'text' => Texts::STATS_NO_RESUMES,
                'reply_markup' => $keyboard
            ]);

            return ['state' => null];
        }

        // Создаем кнопки для каждого резюме
        $keyboard = [];
        foreach ($resumes as $resume) {
            $keyboard[] = [new InlineKeyboardButton([
                'text' => $resume['name'],
                'callback_data' => "stats_resume_{$resume['id']}"
            ])];
        }

        $keyboard[] = [new InlineKeyboardButton([
            'text' => Texts::BACK_TO_MAIN_MENU,
            'callback_data' => 'main_menu'
        ])];

        $replyMarkup = new InlineKeyboard(...$keyboard);

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::STATS_SELECT_RESUME,
            'reply_markup' => $replyMarkup
        ]);

        $userData['current_state'] = States::STATS_SELECT_RESUME;
        return ['state' => States::STATS_SELECT_RESUME];
    }

    /**
     * Показывает статистику для выбранного резюме
     */
    public static function showResumeStats(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Извлекаем ID резюме из callback_data
        $resumeId = (int)explode('_', $callbackQuery->getData())[2];

        // Получаем данные резюме и статистику
        $resumes = Helpers::getDemoResumes();
        $resume = null;
        foreach ($resumes as $r) {
            if ($r['id'] === $resumeId) {
                $resume = $r;
                break;
            }
        }

        if (!$resume) {
            Request::sendMessage([
                'chat_id' => $chatId,
                'text' => 'Резюме не найдено.'
            ]);
            return ['state' => null];
        }

        $stats = Helpers::getDemoStats($resumeId);

        // Формируем текст статистики
        $statsText = Texts::getStatsText(
            $resume['name'],
            $stats['total_responses'],
            $stats['responses_today'],
            $stats['invites'],
            $stats['declines']
        );

        $keyboard = new InlineKeyboard([
            new InlineKeyboardButton([
                'text' => Texts::BACK_TO_MAIN_MENU,
                'callback_data' => 'main_menu'
            ])
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => $statsText,
            'reply_markup' => $keyboard
        ]);

        return ['state' => null];
    }
}