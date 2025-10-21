<?php

namespace FrontBot\Routers;

use FrontBot\Utils\Texts;
use FrontBot\Utils\States;
use Longman\TelegramBot\Entities\InlineKeyboard;
use Longman\TelegramBot\Entities\InlineKeyboardButton;
use Longman\TelegramBot\Entities\Update;
use Longman\TelegramBot\Request;

/**
 * Обработчик сопроводительных писем
 */
class LettersRouter
{
    /**
     * Показывает главное меню сопроводительных писем (демо режим)
     */
    public static function showCoverLetters(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        if (!isset($userData['cover_letters'])) {
            $userData['cover_letters'] = [];
        }

        $coverLetters = $userData['cover_letters'];
        $text = Texts::CL_MENU_HEADER;

        $keyboard = [[new InlineKeyboardButton([
            'text' => '✏️ Новое сопроводительное письмо',
            'callback_data' => 'cl_new'
        ])]];

        foreach ($coverLetters as $i => $letter) {
            $keyboard[] = [new InlineKeyboardButton([
                'text' => "📄 {$letter['title']}",
                'callback_data' => "cl_view_{$i}"
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
            'text' => $text,
            'reply_markup' => $replyMarkup
        ]);

        $userData['current_state'] = States::COVER_LETTER_MENU;
        return ['state' => States::COVER_LETTER_MENU];
    }

    /**
     * Запрашивает заголовок нового сопроводительного письма
     */
    public static function askNewCoverLetterTitle(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        if (count($userData['cover_letters'] ?? []) >= 5) {
            $keyboard = new InlineKeyboard([
                new InlineKeyboardButton([
                    'text' => '🔙 Вернуться в список писем',
                    'callback_data' => 'cl_back_to_list'
                ])
            ]);

            Request::answerCallbackQuery([
                'callback_query_id' => $callbackQuery->getId()
            ]);

            Request::editMessageText([
                'chat_id' => $chatId,
                'message_id' => $messageId,
                'text' => Texts::CL_LIMIT_REACHED,
                'reply_markup' => $keyboard
            ]);

            return ['state' => States::COVER_LETTER_MENU];
        }

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::CL_ASK_TITLE
        ]);

        $userData['current_state'] = States::CL_ASK_TITLE;
        return ['state' => States::CL_ASK_TITLE];
    }

    /**
     * Сохраняет заголовок и запрашивает тело письма
     */
    public static function askNewCoverLetterBody(Update $update, array &$userData): array
    {
        $message = $update->getMessage();
        $chatId = $message->getChat()->getId();

        $userData['new_cl_title'] = substr($message->getText(), 0, 50);

        Request::sendMessage([
            'chat_id' => $chatId,
            'text' => Texts::CL_ASK_BODY
        ]);

        $userData['current_state'] = States::CL_SAVE_BODY;
        return ['state' => States::CL_SAVE_BODY];
    }

    /**
     * Сохраняет новое сопроводительное письмо
     */
    public static function saveCoverLetterBody(Update $update, array &$userData): array
    {
        $message = $update->getMessage();
        $chatId = $message->getChat()->getId();

        $title = $userData['new_cl_title'];
        $body = $message->getText();

        unset($userData['new_cl_title']);

        if (!isset($userData['cover_letters'])) {
            $userData['cover_letters'] = [];
        }

        $userData['cover_letters'][] = ['title' => $title, 'body' => $body];

        $keyboard = new InlineKeyboard([
            new InlineKeyboardButton([
                'text' => '🔙 Вернуться в список писем',
                'callback_data' => 'cl_back_to_list'
            ])
        ]);

        Request::sendMessage([
            'chat_id' => $chatId,
            'text' => Texts::CL_SAVED,
            'reply_markup' => $keyboard
        ]);

        $userData['current_state'] = States::COVER_LETTER_MENU;
        return ['state' => States::COVER_LETTER_MENU];
    }

    /**
     * Отображает конкретное сопроводительное письмо и кнопку удаления
     */
    public static function viewCoverLetter(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        $letterIndex = (int)explode('_', $callbackQuery->getData())[2];
        $userData['current_cl_index'] = $letterIndex;
        $letter = $userData['cover_letters'][$letterIndex];

        $text = Texts::getClViewText($letter['body']);

        $keyboard = new InlineKeyboard(
            [new InlineKeyboardButton([
                'text' => '🗑 Удалить сопроводительное письмо',
                'callback_data' => 'cl_delete'
            ])],
            [new InlineKeyboardButton([
                'text' => '🔙 Назад',
                'callback_data' => 'cl_back_to_list'
            ])]
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

        $userData['current_state'] = States::CL_VIEW;
        return ['state' => States::CL_VIEW];
    }

    /**
     * Удаляет выбранное сопроводительное письмо
     */
    public static function deleteCoverLetter(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $letterIndex = $userData['current_cl_index'];

        unset($userData['cover_letters'][$letterIndex]);
        $userData['cover_letters'] = array_values($userData['cover_letters']); // Переиндексация массива
        unset($userData['current_cl_index']);

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId(),
            'text' => Texts::CL_DELETED
        ]);

        return self::showCoverLetters($update, $userData);
    }
}
