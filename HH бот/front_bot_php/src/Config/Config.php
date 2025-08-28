<?php
namespace FrontBot\Config;

final class Config
{
    /** Берём токен только из ENV (как у Python-бота). */
    public static function botToken(): ?string {
        $v = getenv('TELEGRAM_BOT_TOKEN') ?: getenv('BOT_TOKEN') ?: null;
        if ($v !== null) {
            $v = trim($v, " \t\n\r\0\x0B\"'><");
        }
        return $v ?: null;
    }

    public static function botUsername(): ?string {
        $v = getenv('BOT_USERNAME') ?: null;
        return $v ? trim($v) : null;
    }

    public const PROJECT_NAME = "Front App";

    /** Включать демо-справочники только если DEMO_MODE=1 */
    public static function demoMode(): bool {
        return getenv('DEMO_MODE') === '1';
    }

    public const DEMO_COUNTRIES = [
        ["id" => "113", "name" => "Россия"],
        ["id" => "40", "name" => "Казахстан"],
        ["id" => "5", "name" => "Украина"],
        ["id" => "16", "name" => "Беларусь"],
    ];

    public const DEMO_REGIONS = [
        "113" => [
            ["id" => "1", "name" => "Москва"],
            ["id" => "2", "name" => "Санкт-Петербург"],
            ["id" => "3", "name" => "Екатеринбург"],
            ["id" => "4", "name" => "Новосибирск"],
            ["id" => "all_113", "name" => "По всей стране"],
        ],
    ];

    public const DEMO_SCHEDULES = [
        ["id" => "fullDay", "name" => "Полный день"],
        ["id" => "shift", "name" => "Сменный график"],
        ["id" => "flexible", "name" => "Гибкий график"],
        ["id" => "remote", "name" => "Удаленная работа"],
        ["id" => "flyInFlyOut", "name" => "Вахтовый метод"],
    ];

    public const DEMO_EMPLOYMENT = [
        ["id" => "full", "name" => "Полная занятость"],
        ["id" => "part", "name" => "Частичная занятость"],
        ["id" => "project", "name" => "Проектная работа"],
        ["id" => "volunteer", "name" => "Волонтерство"],
        ["id" => "probation", "name" => "Стажировка"],
    ];

    public const DEMO_PROFESSIONS = [
        ["id" => "1", "name" => "Информационные технологии"],
        ["id" => "2", "name" => "Продажи"],
        ["id" => "3", "name" => "Маркетинг, реклама, PR"],
        ["id" => "4", "name" => "Административная работа"],
        ["id" => "5", "name" => "Бухгалтерия, финансы"],
        ["id" => "6", "name" => "Управление персоналом, HR"],
        ["id" => "7", "name" => "Производство, сырье, с/х"],
        ["id" => "8", "name" => "Строительство, недвижимость"],
    ];

    public const DEMO_RESUMES = [
        ["id" => "resume_1", "title" => "Python разработчик"],
        ["id" => "resume_2", "title" => "Frontend разработчик"],
        ["id" => "resume_3", "title" => "Менеджер по продажам"],
    ];

    public const DEMO_VACANCIES = [
        [
            "id" => "vacancy_1",
            "name" => "Python разработчик",
            "employer" => ["name" => "ТехКомпания"],
            "salary" => ["from" => 100000, "to" => 150000, "currency" => "RUR"],
            "area" => ["name" => "Москва"],
        ],
        [
            "id" => "vacancy_2",
            "name" => "Frontend разработчик React",
            "employer" => ["name" => "Веб-студия"],
            "salary" => ["from" => 80000, "to" => 120000, "currency" => "RUR"],
            "area" => ["name" => "Санкт-Петербург"],
        ],
        [
            "id" => "vacancy_3",
            "name" => "Менеджер по продажам",
            "employer" => ["name" => "Торговая компания"],
            "salary" => ["from" => 60000, "to" => 100000, "currency" => "RUR"],
            "area" => ["name" => "Москва"],
        ],
    ];
}
