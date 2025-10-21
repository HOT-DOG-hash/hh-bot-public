<?php

namespace FrontBot\Utils;

use Longman\TelegramBot\Entities\InlineKeyboard;
use Longman\TelegramBot\Entities\InlineKeyboardButton;

/**
 * Вспомогательные функции для работы с клавиатурами и выбором
 */
class Helpers
{
    /**
     * Создает клавиатуру множественного выбора
     */
    public static function buildMultiChoiceKeyboard(
        array $options,
        string $selectionKey,
        string $prefix,
        array $userData
    ): InlineKeyboard {
        $selected = $userData[$selectionKey] ?? [];
        $allSelected = count($selected) === count($options) && empty(array_diff(array_keys($options), $selected));

        $keyboard = [];

        // Кнопка "Выбрать все"
        $selectAllStatus = $allSelected ? '🟢' : '🔴';
        $keyboard[] = [new InlineKeyboardButton([
            'text' => "{$selectAllStatus} Выбрать все",
            'callback_data' => "{$prefix}_all"
        ])];

        // Кнопки для каждого элемента
        foreach ($options as $key => $text) {
            $status = in_array($key, $selected) ? '🟢' : '🔴';
            $keyboard[] = [new InlineKeyboardButton([
                'text' => "{$status} {$text}",
                'callback_data' => "{$prefix}_{$key}"
            ])];
        }

        // Кнопка "Далее"
        $keyboard[] = [new InlineKeyboardButton([
            'text' => 'Далее',
            'callback_data' => "{$prefix}_next"
        ])];

        return new InlineKeyboard(...$keyboard);
    }

    /**
     * Обрабатывает множественный выбор
     */
    public static function handleMultiChoice(
        string $callbackData,
        array $options,
        string $selectionKey,
        string $prefix,
        array &$userData
    ): array {
        $choice = str_replace("{$prefix}_", "", $callbackData);
        $selected = $userData[$selectionKey] ?? [];
        $allOptions = array_keys($options);

        if ($choice === 'all') {
            if (count($selected) === count($allOptions) && empty(array_diff($allOptions, $selected))) {
                $selected = [];
            } else {
                $selected = $allOptions;
            }
        } elseif (in_array($choice, $selected)) {
            $selected = array_diff($selected, [$choice]);
        } else {
            $selected[] = $choice;
        }

        $userData[$selectionKey] = array_values($selected);

        return $userData;
    }

    /**
     * Создает клавиатуру с пагинацией
     */
    public static function buildPaginatedKeyboard(
        array $items,
        int $page,
        string $prefix,
        ?string $selectionKey = null,
        ?array $userData = null,
        int $pageSize = 9,
        bool $addSelectAll = false
    ): InlineKeyboard {
        $keyboard = [];

        // Кнопка "Выбрать все"
        if ($addSelectAll && $userData !== null && $selectionKey !== null) {
            $selected = $userData[$selectionKey] ?? [];
            $allIds = array_column($items, 'id');
            $allSelected = count($selected) === count($allIds) && empty(array_diff($allIds, $selected));
            $status = $allSelected ? '🟢' : '🔴';
            $keyboard[] = [new InlineKeyboardButton([
                'text' => "{$status} Выбрать все",
                'callback_data' => "page_{$prefix}_select_all"
            ])];
        }

        $totalPages = (int)ceil(count($items) / $pageSize);
        $startOffset = $page * $pageSize;
        $endOffset = $startOffset + $pageSize;

        // Кнопки элементов
        $selectedOnPage = ($userData && $selectionKey) ? ($userData[$selectionKey] ?? []) : [];
        $pageItems = array_slice($items, $startOffset, $pageSize);

        foreach ($pageItems as $item) {
            $itemId = (string)$item['id'];
            $status = in_array($itemId, $selectedOnPage) ? '🟢' : '🔴';
            $text = $addSelectAll ? "{$status} {$item['name']}" : $item['name'];
            $keyboard[] = [new InlineKeyboardButton([
                'text' => $text,
                'callback_data' => "{$prefix}_{$itemId}"
            ])];
        }

        // Кнопки навигации
        $navButtons = [];
        if ($page > 0) {
            $navButtons[] = new InlineKeyboardButton([
                'text' => '⬅️ Назад',
                'callback_data' => "page_{$prefix}_nav_" . ($page - 1)
            ]);
        }
        if ($page < $totalPages - 1) {
            $navButtons[] = new InlineKeyboardButton([
                'text' => 'Вперед ➡️',
                'callback_data' => "page_{$prefix}_nav_" . ($page + 1)
            ]);
        }

        if (!empty($navButtons)) {
            $keyboard[] = $navButtons;
        }

        // Кнопка "Далее" для режимов с выбором
        if ($addSelectAll) {
            $keyboard[] = [new InlineKeyboardButton([
                'text' => 'Далее',
                'callback_data' => "{$prefix}_next"
            ])];
        }

        return new InlineKeyboard(...$keyboard);
    }

    /**
     * Получает ключ для хранения дневных откликов пользователя
     */
    public static function getDailyResponsesKey(int $userId): string
    {
        $today = date('Y-m-d');
        return "daily_responses_{$userId}_{$today}";
    }

    /**
     * Получает количество откликов пользователя за сегодня
     */
    public static function getDailyResponseCount(array $botData, int $userId): int
    {
        $key = self::getDailyResponsesKey($userId);
        return $botData[$key] ?? 0;
    }

    /**
     * Увеличивает счетчик откликов пользователя за сегодня
     */
    public static function incrementDailyResponseCount(array &$botData, int $userId): int
    {
        $key = self::getDailyResponsesKey($userId);
        $currentCount = $botData[$key] ?? 0;
        $newCount = $currentCount + 1;
        $botData[$key] = $newCount;
        return $newCount;
    }

    /**
     * Получает количество оставшихся откликов на сегодня
     */
    public static function getRemainingResponses(array $botData, int $userId, int $dailyLimit = 200): int
    {
        $used = self::getDailyResponseCount($botData, $userId);
        return max(0, $dailyLimit - $used);
    }

    /**
     * Парсит URL с hh.ru и извлекает параметры поиска
     */
    public static function parseHhUrl(string $url): array
    {
        $parsedUrl = parse_url($url);
        if (!isset($parsedUrl['query'])) {
            throw new \InvalidArgumentException('URL не содержит параметров запроса');
        }

        parse_str($parsedUrl['query'], $queryParams);

        return [
            'keyword' => $queryParams['text'] ?? '',
            'area' => $queryParams['area'] ?? [],
            'schedule' => $queryParams['schedule'] ?? [],
            'employment' => $queryParams['employment'] ?? [],
            'profession' => $queryParams['professional_role'] ?? [],
            'search_fields' => $queryParams['search_field'] ?? []
        ];
    }

    /**
     * Генерирует демо-статистику для резюме
     */
    public static function getDemoStats(int $resumeId): array
    {
        // Генерируем случайные, но реалистичные данные
        $totalResponses = rand(50, 200);
        $responsesToday = rand(0, 15);
        $invites = rand(5, (int)($totalResponses / 4));
        $declines = rand($invites, $totalResponses - $invites);

        return [
            'total_responses' => $totalResponses,
            'responses_today' => $responsesToday,
            'invites' => $invites,
            'declines' => $declines
        ];
    }

    /**
     * Получает демо-резюме
     */
    public static function getDemoResumes(): array
    {
        return [
            ['id' => 1, 'name' => 'Python разработчик'],
            ['id' => 2, 'name' => 'Frontend разработчик'],
            ['id' => 3, 'name' => 'Data Analyst'],
        ];
    }
}
