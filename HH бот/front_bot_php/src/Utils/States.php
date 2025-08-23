<?php

namespace FrontBot\Utils;

/**
 * State definitions for demo bot
 */
class States
{
    // Основные состояния
    public const SELECTING_ACTION = 0;
    public const ASK_RESUME = 1;
    public const ASK_SEARCH_METHOD = 2;
    public const ASK_COUNTRY = 3;
    public const ASK_REGION = 4;
    public const ASK_SCHEDULE = 5;
    public const ASK_EMPLOYMENT = 6;
    public const ASK_PROFESSION = 7;
    public const ASK_KEYWORD = 8;
    public const ASK_SEARCH_FIELD = 9;
    public const ASK_COVER_LETTER = 10;
    public const CONFIRMATION = 11;
    public const ASK_PROFESSION_PAGE = 12;

    // Cover Letter states
    public const COVER_LETTER_MENU = 13;
    public const CL_ASK_TITLE = 14;
    public const CL_ASK_BODY = 15;
    public const CL_VIEW = 16;
    public const CL_SAVE_BODY = 17;

    // New state for asking HH URL
    public const ASK_HH_URL = 18;

    // Auto-response states
    public const AUTO_RESPONSE_MAIN = 19;
    public const AUTO_RESPONSE_SETUP = 20;
    public const AUTO_RESPONSE_RESUME = 21;
    public const AUTO_RESPONSE_SEARCH_METHOD = 22;
    public const AUTO_RESPONSE_FILTERS = 23;
    public const AUTO_RESPONSE_HH_URL = 24;
    public const AUTO_RESPONSE_COVER_LETTER = 25;
    public const AUTO_RESPONSE_CONFIRMATION = 26;
    public const AUTO_RESPONSE_ACTIVE = 27;
    public const AUTO_RESPONSE_STATS = 28;

    // Additional auto-response states
    public const AUTO_ASK_RESUME = 31;
    public const AUTO_ASK_SEARCH_METHOD = 32;
    public const AUTO_ASK_HH_URL = 33;
    public const AUTO_CONFIRMATION = 34;

    // Stats states
    public const STATS_SELECT_RESUME = 29;
    public const STATS_SHOW_RESUME_STATS = 30;
}