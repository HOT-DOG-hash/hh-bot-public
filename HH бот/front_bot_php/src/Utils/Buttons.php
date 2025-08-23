<?php

namespace FrontBot\Utils;

/**
 * Кнопки и опции для бота
 */
class Buttons
{
    public const SEARCH_FIELD_OPTIONS = [
        "name" => "В названии описания вакансии",
        "description" => "В описании вакансии",
        "company_name" => "В названии компании",
    ];

    // Кнопки для автооткликов
    public const AUTO_RESPONSE_SEARCH_METHOD_OPTIONS = [
        "configure_filters" => "🔎 Настроить фильтры в боте",
        "paste_hh_link" => "🌐 Вставить ссылку поиска hh.ru"
    ];
}