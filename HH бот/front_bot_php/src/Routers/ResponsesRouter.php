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
 * Обработчик откликов на вакансии
 */
class ResponsesRouter
{
    private const DAILY_RESPONSE_LIMIT = 200;

    /**
     * Начальная точка входа для откликов
     */
    public static function startResponsesEntry(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        $keyboard = new InlineKeyboard(
            [new InlineKeyboardButton(['text' => 'Создать новый запрос', 'callback_data' => 'new_request'])],
            [new InlineKeyboardButton(['text' => 'Выбрать из прошлых запросов', 'callback_data' => 'past_requests'])]
        );

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::CHOOSE_ACTION,
            'reply_markup' => $keyboard
        ]);

        $userData['current_state'] = States::SELECTING_ACTION;
        return ['state' => States::SELECTING_ACTION];
    }

    /**
     * Выбор резюме
     */
    public static function askResume(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $userData['new_request'] = [];

        // Используем демо-резюме из конфига
        $resumes = Config::DEMO_RESUMES;

        $keyboard = [];
        foreach ($resumes as $resume) {
            $keyboard[] = [new InlineKeyboardButton([
                'text' => $resume['title'],
                'callback_data' => 'resume_' . $resume['id']
            ])];
        }

        $replyMarkup = new InlineKeyboard(...$keyboard);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::ASK_RESUME,
            'reply_markup' => $replyMarkup
        ]);

        $userData['current_state'] = States::ASK_RESUME;
        return ['state' => States::ASK_RESUME];
    }

    /**
     * Выбор способа поиска
     */
    public static function askSearchMethod(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        $userData['new_request']['resume'] = str_replace('resume_', '', $callbackQuery->getData());

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $keyboard = new InlineKeyboard(
            [new InlineKeyboardButton(['text' => 'Настроить фильтры', 'callback_data' => 'configure_filters'])],
            [new InlineKeyboardButton(['text' => 'Вставить ссылку hh.ru', 'callback_data' => 'paste_link'])]
        );

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => 'Выберите способ настройки поиска:',
            'reply_markup' => $keyboard
        ]);

        $userData['current_state'] = States::ASK_SEARCH_METHOD;
        return ['state' => States::ASK_SEARCH_METHOD];
    }

    /**
     * Выбор страны для фильтров
     */
    public static function askCountryForFilters(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Используем демо-страны из конфига
        $countries = Config::DEMO_COUNTRIES;

        $replyMarkup = Helpers::buildPaginatedKeyboard($countries, 0, 'country');

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::ASK_COUNTRY,
            'reply_markup' => $replyMarkup
        ]);

        $userData['current_state'] = States::ASK_REGION;
        return ['state' => States::ASK_REGION];
    }

    /**
     * Выбор региона
     */
    public static function askRegion(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        $countryId = str_replace('country_', '', $callbackQuery->getData());
        $userData['new_request']['country'] = $countryId;

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Используем демо-регионы из конфига
        $regions = Config::DEMO_REGIONS[$countryId] ?? [];
        if (!empty($regions)) {
            // Добавляем опцию "По всей стране" если её нет
            $hasAllCountry = false;
            foreach ($regions as $region) {
                if ($region['id'] === "all_{$countryId}") {
                    $hasAllCountry = true;
                    break;
                }
            }
            if (!$hasAllCountry) {
                array_unshift($regions, ['id' => "all_{$countryId}", 'name' => "По всей стране"]);
            }
        }

        $replyMarkup = Helpers::buildPaginatedKeyboard($regions, 0, "region_{$countryId}");

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::ASK_REGION,
            'reply_markup' => $replyMarkup
        ]);

        $userData['current_state'] = States::ASK_SCHEDULE;
        return ['state' => States::ASK_SCHEDULE];
    }

    /**
     * Выбор графика работы
     */
    public static function askSchedule(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        $userData['new_request']['region'] = str_replace('region_', '', $callbackQuery->getData());

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Используем демо-графики из конфига
        $schedules = Config::DEMO_SCHEDULES;
        $scheduleOptions = [];
        foreach ($schedules as $schedule) {
            $scheduleOptions[$schedule['id']] = $schedule['name'];
        }

        $userData['schedule_selection'] = [];
        $replyMarkup = Helpers::buildMultiChoiceKeyboard($scheduleOptions, 'schedule_selection', 'schedule', $userData);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::ASK_SCHEDULE,
            'reply_markup' => $replyMarkup
        ]);

        $userData['current_state'] = States::ASK_EMPLOYMENT;
        return ['state' => States::ASK_EMPLOYMENT];
    }

    /**
     * Обработка выбора графика
     */
    public static function handleScheduleChoice(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $schedules = Config::DEMO_SCHEDULES;
        $scheduleOptions = [];
        foreach ($schedules as $schedule) {
            $scheduleOptions[$schedule['id']] = $schedule['name'];
        }

        Helpers::handleMultiChoice($callbackQuery->getData(), $scheduleOptions, 'schedule_selection', 'schedule', $userData);

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $replyMarkup = Helpers::buildMultiChoiceKeyboard($scheduleOptions, 'schedule_selection', 'schedule', $userData);

        Request::editMessageReplyMarkup([
            'chat_id' => $callbackQuery->getMessage()->getChat()->getId(),
            'message_id' => $callbackQuery->getMessage()->getMessageId(),
            'reply_markup' => $replyMarkup
        ]);

        return ['state' => States::ASK_EMPLOYMENT];
    }

    /**
     * Выбор типа занятости
     */
    public static function askEmployment(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        // Сохраняем выбранные графики
        $userData['new_request']['schedule'] = $userData['schedule_selection'] ?? [];

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Используем демо-типы занятости из конфига
        $employments = Config::DEMO_EMPLOYMENT;
        $employmentOptions = [];
        foreach ($employments as $employment) {
            $employmentOptions[$employment['id']] = $employment['name'];
        }

        $userData['employment_selection'] = [];
        $replyMarkup = Helpers::buildMultiChoiceKeyboard($employmentOptions, 'employment_selection', 'employment', $userData);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::ASK_EMPLOYMENT,
            'reply_markup' => $replyMarkup
        ]);

        $userData['current_state'] = States::ASK_PROFESSION;
        return ['state' => States::ASK_PROFESSION];
    }

    /**
     * Обработка выбора типа занятости
     */
    public static function handleEmploymentChoice(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $employments = Config::DEMO_EMPLOYMENT;
        $employmentOptions = [];
        foreach ($employments as $employment) {
            $employmentOptions[$employment['id']] = $employment['name'];
        }

        Helpers::handleMultiChoice($callbackQuery->getData(), $employmentOptions, 'employment_selection', 'employment', $userData);

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $replyMarkup = Helpers::buildMultiChoiceKeyboard($employmentOptions, 'employment_selection', 'employment', $userData);

        Request::editMessageReplyMarkup([
            'chat_id' => $callbackQuery->getMessage()->getChat()->getId(),
            'message_id' => $callbackQuery->getMessage()->getMessageId(),
            'reply_markup' => $replyMarkup
        ]);

        return ['state' => States::ASK_PROFESSION];
    }

    /**
     * Выбор профессиональной области
     */
    public static function askProfession(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        // Сохраняем выбранные типы занятости
        $userData['new_request']['employment'] = $userData['employment_selection'] ?? [];

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        // Используем демо-профессии из конфига
        $professions = Config::DEMO_PROFESSIONS;

        $userData['profession_selection'] = [];
        $replyMarkup = Helpers::buildPaginatedKeyboard($professions, 0, 'profession', 'profession_selection', $userData, 9, true);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::ASK_PROFESSION,
            'reply_markup' => $replyMarkup
        ]);

        $userData['current_state'] = States::ASK_KEYWORD;
        return ['state' => States::ASK_KEYWORD];
    }

    /**
     * Обработка выбора профессии
     */
    public static function handleProfessionChoice(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $professions = Config::DEMO_PROFESSIONS;

        // Извлекаем ID профессии из callback_data
        $professionId = str_replace('profession_', '', $callbackQuery->getData());
        
        $selected = $userData['profession_selection'] ?? [];
        if (in_array($professionId, $selected)) {
            $selected = array_diff($selected, [$professionId]);
        } else {
            $selected[] = $professionId;
        }
        $userData['profession_selection'] = array_values($selected);

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $replyMarkup = Helpers::buildPaginatedKeyboard($professions, 0, 'profession', 'profession_selection', $userData, 9, true);

        Request::editMessageReplyMarkup([
            'chat_id' => $callbackQuery->getMessage()->getChat()->getId(),
            'message_id' => $callbackQuery->getMessage()->getMessageId(),
            'reply_markup' => $replyMarkup
        ]);

        return ['state' => States::ASK_KEYWORD];
    }

    /**
     * Обработка "Выбрать все" для профессий
     */
    public static function handleProfessionSelectAll(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $professions = Config::DEMO_PROFESSIONS;
        $allIds = array_column($professions, 'id');
        
        $selected = $userData['profession_selection'] ?? [];
        if (count($selected) === count($allIds) && empty(array_diff($allIds, $selected))) {
            $userData['profession_selection'] = [];
        } else {
            $userData['profession_selection'] = $allIds;
        }

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $replyMarkup = Helpers::buildPaginatedKeyboard($professions, 0, 'profession', 'profession_selection', $userData, 9, true);

        Request::editMessageReplyMarkup([
            'chat_id' => $callbackQuery->getMessage()->getChat()->getId(),
            'message_id' => $callbackQuery->getMessage()->getMessageId(),
            'reply_markup' => $replyMarkup
        ]);

        return ['state' => States::ASK_KEYWORD];
    }

    /**
     * Обработка навигации по профессиям
     */
    public static function handleProfessionNavigation(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $data = $callbackQuery->getData();
        $page = (int)str_replace('page_profession_nav_', '', $data);
        
        $professions = Config::DEMO_PROFESSIONS;

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $replyMarkup = Helpers::buildPaginatedKeyboard($professions, $page, 'profession', 'profession_selection', $userData, 9, true);

        Request::editMessageReplyMarkup([
            'chat_id' => $callbackQuery->getMessage()->getChat()->getId(),
            'message_id' => $callbackQuery->getMessage()->getMessageId(),
            'reply_markup' => $replyMarkup
        ]);

        return ['state' => States::ASK_KEYWORD];
    }

    /**
     * Запрос ключевого слова
     */
    public static function askKeyword(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        // Сохраняем выбранные профессии
        $userData['new_request']['profession'] = $userData['profession_selection'] ?? [];

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::ASK_KEYWORD
        ]);

        $userData['current_state'] = States::ASK_KEYWORD;
        return ['state' => States::ASK_KEYWORD];
    }

    /**
     * Показывает подтверждение настроек
     */
    public static function confirmation(Update $update, array &$userData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        $data = $userData['new_request'];

        // Получаем названия для отображения
        $countryName = 'Не указано';
        foreach (Config::DEMO_COUNTRIES as $country) {
            if ($country['id'] === $data['country']) {
                $countryName = $country['name'];
                break;
            }
        }

        $regionName = 'Не указано';
        if (isset($data['region'])) {
            if (strpos($data['region'], 'all_') === 0) {
                $regionName = 'Вся страна';
            } else {
                $regions = Config::DEMO_REGIONS[$data['country']] ?? [];
                foreach ($regions as $region) {
                    if ($region['id'] === $data['region']) {
                        $regionName = $region['name'];
                        break;
                    }
                }
            }
        }

        $scheduleNames = [];
        if (isset($userData['schedule_selection'])) {
            foreach (Config::DEMO_SCHEDULES as $schedule) {
                if (in_array($schedule['id'], $userData['schedule_selection'])) {
                    $scheduleNames[] = $schedule['name'];
                }
            }
        }

        // Демо-данные для вакансий
        $vacancyCount = count(Config::DEMO_VACANCIES);
        $hhRuLink = "https://hh.ru/search/vacancy?text=" . ($data['keyword'] ?? 'demo');

        // Получаем информацию о дневных лимитах
        $userId = $callbackQuery->getFrom()->getId();
        $dailyCount = 0; // В демо режиме
        $remainingCount = self::DAILY_RESPONSE_LIMIT;

        $summaryText = Texts::getConfirmationText(
            $vacancyCount,
            $hhRuLink,
            $countryName,
            $regionName,
            implode(', ', $scheduleNames) ?: 'Не указано',
            'Не указано', // employment
            'Не указано', // profession
            $data['keyword'] ?? 'Не указано',
            'Не указано', // search_field
            'Без сопроводительного письма', // cover_letter
            $dailyCount,
            $remainingCount
        );

        $keyboard = new InlineKeyboard(
            [new InlineKeyboardButton(['text' => 'Отправить отклики', 'callback_data' => 'send_responses'])],
            [new InlineKeyboardButton(['text' => 'Создать новый запрос', 'callback_data' => 'restart_flow'])]
        );

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => $summaryText,
            'reply_markup' => $keyboard,
            'parse_mode' => 'HTML',
            'disable_web_page_preview' => true
        ]);

        $userData['current_state'] = States::CONFIRMATION;
        return ['state' => States::CONFIRMATION];
    }

    /**
     * Отправка откликов
     */
    public static function sendResponses(Update $update, array &$userData, array &$botData): array
    {
        $callbackQuery = $update->getCallbackQuery();
        $chatId = $callbackQuery->getMessage()->getChat()->getId();
        $messageId = $callbackQuery->getMessage()->getMessageId();

        Request::answerCallbackQuery([
            'callback_query_id' => $callbackQuery->getId()
        ]);

        $userId = $callbackQuery->getFrom()->getId();

        // Проверяем дневной лимит
        $remaining = Helpers::getRemainingResponses($botData, $userId, self::DAILY_RESPONSE_LIMIT);
        if ($remaining <= 0) {
            Request::editMessageText([
                'chat_id' => $chatId,
                'message_id' => $messageId,
                'text' => '❌ Достигнут дневной лимит откликов (200/день). Попробуйте завтра.'
            ]);
            return ['state' => null];
        }

        // Показываем финальное сообщение
        $keyboard = new InlineKeyboard([
            new InlineKeyboardButton(['text' => 'Главное меню', 'callback_data' => 'main_menu'])
        ]);

        Request::editMessageText([
            'chat_id' => $chatId,
            'message_id' => $messageId,
            'text' => Texts::RESPONSES_STARTED,
            'reply_markup' => $keyboard
        ]);

        $userData = []; // Очищаем данные пользователя
        return ['state' => null];
    }

    /**
     * Обработка текстового сообщения (ключевое слово)
     */
    public static function handleKeywordInput(Update $update, array &$userData): array
    {
        $message = $update->getMessage();
        $chatId = $message->getChat()->getId();
        $keyword = $message->getText();

        $userData['new_request']['keyword'] = $keyword;

        // Переходим к подтверждению (упрощенная версия)
        $keyboard = new InlineKeyboard([
            new InlineKeyboardButton(['text' => 'Продолжить', 'callback_data' => 'continue_to_confirmation'])
        ]);

        Request::sendMessage([
            'chat_id' => $chatId,
            'text' => "Ключевое слово: {$keyword}\nНажмите 'Продолжить' для завершения настройки.",
            'reply_markup' => $keyboard
        ]);

        $userData['current_state'] = States::CONFIRMATION;
        return ['state' => States::CONFIRMATION];
    }
}