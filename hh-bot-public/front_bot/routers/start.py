from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, List, MutableMapping, Tuple, cast
from uuid import uuid4

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from front_bot import texts
from front_bot.api import BackendApi, BackendApiError
from front_bot.models import CampaignDraft, TelegramIdentity

LANDING, CAMPAIGN = range(2)

CAMPAIGN_STEPS: List[Tuple[str, str]] = [
    ("resume", "1/10. Пришли ссылку на резюме на HH или идентификатор вакансии."),
    ("country", "2/10. В какой стране ищем работу?"),
    ("region", "3/10. Город или регион (можно несколько через запятую)."),
    ("schedule", "4/10. График (офис, удалёнка, гибрид — перечисли через запятую)."),
    ("employment", "5/10. Тип занятости (полная, частичная, проектная и т.д.)."),
    ("professions", "6/10. Названия должностей или профобластей (через запятую)."),
    ("keywords", "7/10. Ключевые слова/фразы для поиска (через запятую)."),
    ("target_salary", "8/10. Желаемый уровень дохода (число + валюта или 'любая')."),
    ("search_scope", "9/10. Где искать? Напиши title, description или both."),
    ("cover_letter", "10/10. Скопируй сопроводительное письмо или напиши 'по умолчанию'."),
]

MenuCallback = Callable[[CallbackQuery, ContextTypes.DEFAULT_TYPE], Awaitable[int]]


def _user_data(context: ContextTypes.DEFAULT_TYPE) -> MutableMapping[str, Any]:
    data = context.user_data
    if data is None:
        raise RuntimeError("user_data storage is disabled")
    return cast(MutableMapping[str, Any], data)


def register(application: Application, api: BackendApi) -> None:
    """
    Attach the MVP FSM to the provided Telegram application instance.
    """

    application.bot_data["backend_api"] = api

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", _start_entry)],
        states={
            LANDING: [
                CallbackQueryHandler(_handle_menu_action, pattern=r"^menu:"),
            ],
            CAMPAIGN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_campaign_input),
                CallbackQueryHandler(_handle_campaign_callback, pattern=r"^campaign:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", _cancel_flow)],
        name="mvp3-start",
        persistent=False,
    )

    application.add_handler(conversation)


async def _start_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = _user_data(context)
    data.clear()
    try:
        identity = TelegramIdentity.from_update(update)
    except ValueError:
        await _safe_reply(update, "Не удалось определить профиль Telegram. Попробуй снова.")
        return ConversationHandler.END

    data["identity"] = identity
    data["draft"] = CampaignDraft()
    data["step_index"] = 0

    await _send_landing(update, context, identity)
    return LANDING


async def _handle_menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None or query.data is None:
        return LANDING
    await query.answer()
    action, *rest = query.data.split(":")[1:]

    if action == "payplan":
        plan_code = rest[0] if rest else ""
        return await _initiate_payment(query, context, plan_code)

    handlers: dict[str, MenuCallback] = {
        "trial": _activate_trial,
        "campaign": _enter_campaign,
        "quota": _show_quota,
        "plans": _show_plans,
        "pay": _prompt_payment_plan,
    }

    handler = handlers.get(action)
    if handler is None:
        await query.edit_message_text("Неизвестное действие, попробуй ещё раз.")
        return LANDING

    return await handler(query, context)


async def _handle_campaign_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = _user_data(context)
    draft = data.get("draft")
    if not isinstance(draft, CampaignDraft):
        draft = CampaignDraft()
        data["draft"] = draft
    step_index = int(data.get("step_index", 0))

    if step_index >= len(CAMPAIGN_STEPS):
        await _send_campaign_preview(update, context, draft)
        return CAMPAIGN

    field, _ = CAMPAIGN_STEPS[step_index]
    text = update.message.text if update.message else ""
    try:
        _apply_answer(draft, field, text or "")
    except ValueError as exc:
        await _safe_reply(update, f"⚠️ {exc}")
        return CAMPAIGN

    data["step_index"] = step_index + 1
    if data["step_index"] >= len(CAMPAIGN_STEPS):
        await _send_campaign_preview(update, context, draft)
        return CAMPAIGN

    await _prompt_next_step(update.effective_chat.id if update.effective_chat else None, context)
    return CAMPAIGN


async def _handle_campaign_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None or query.data is None:
        return CAMPAIGN
    await query.answer()
    action = query.data.split(":", 1)[1]
    data = _user_data(context)
    draft = data.get("draft")
    if not isinstance(draft, CampaignDraft):
        draft = CampaignDraft()
        data["draft"] = draft

    if action == "confirm":
        await _launch_campaign(query, context, draft)
        return LANDING
    if action == "restart":
        draft.reset()
        data["step_index"] = 0
        await query.edit_message_text("Начнём заново. Пришли ответы ещё раз.")
        chat_id = None
        if isinstance(query.message, Message):
            chat_id = query.message.chat_id
        await _prompt_next_step(chat_id, context)
        return CAMPAIGN
    if action == "cancel":
        await query.edit_message_text("Мастер кампании отменён. Возвращаемся к меню.")
        return LANDING
    return CAMPAIGN


async def _cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _safe_reply(update, "Диалог сброшен. Напиши /start, чтобы начать заново.")
    data = _user_data(context)
    data.clear()
    return ConversationHandler.END


async def _send_landing(update: Update, context: ContextTypes.DEFAULT_TYPE, identity: TelegramIdentity) -> None:
    api = _get_api(context)
    quota_task = asyncio.create_task(api.get_quota(identity.to_payload()))
    subscription_task = asyncio.create_task(api.get_subscription(identity.to_payload()))
    try:
        quota, subscription = await asyncio.gather(quota_task, subscription_task)
    except BackendApiError as exc:
        await _safe_reply(update, f"{texts.WELCOME_LANDING}\n\n⚠️ API временно недоступно: {exc}")
        return

    quota_line = (
        f"Квота сегодня: {quota.get('daily_used', 0)}/{quota.get('daily_limit', 0)} "
        f"(осталось {quota.get('remaining_daily', 0)})."
    )
    trial_status = "нет" if not quota.get("has_trial") else "активен"
    subscription_status = subscription.get("subscription", {}).get("status") or "нет"
    summary = (
        f"{texts.WELCOME_LANDING}\n"
        f"{quota_line}\n"
        f"Триал: {trial_status}. Подписка: {subscription_status}."
    )

    buttons = _build_main_menu(trial_available=not quota.get("has_trial"))
    await _safe_reply(update, summary, reply_markup=InlineKeyboardMarkup(buttons))


async def _activate_trial(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> int:
    identity = _get_identity(context)
    api = _get_api(context)
    try:
        result = await api.activate_trial(identity.to_payload())
    except BackendApiError as exc:
        await query.edit_message_text(f"Не удалось активировать триал: {exc}")
        return LANDING

    quota = result.get("quota", {})
    message = (
        f"{texts.TRIAL_ACTIVATED}\n"
        f"Остаток: {quota.get('remaining_trial', 0)} / {quota.get('trial_limit', 0)}."
    )
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(_build_main_menu(trial_available=False)))
    return LANDING


async def _enter_campaign(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = _user_data(context)
    data["draft"] = CampaignDraft()
    data["step_index"] = 0
    await query.edit_message_text(texts.CAMPAIGN_INTRO)
    chat_id = None
    if isinstance(query.message, Message):
        chat_id = query.message.chat_id
    await _prompt_next_step(chat_id, context)
    return CAMPAIGN


async def _show_quota(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> int:
    identity = _get_identity(context)
    api = _get_api(context)
    try:
        quota = await api.get_quota(identity.to_payload())
    except BackendApiError as exc:
        await query.edit_message_text(f"Ошибка получения квоты: {exc}")
        return LANDING

    message = (
        f"📊 Квота\n"
        f"Суточный лимит: {quota.get('daily_limit', 0)}\n"
        f"Использовано: {quota.get('daily_used', 0)}\n"
        f"Осталось: {quota.get('remaining_daily', 0)}\n"
        f"Триал активен: {'да' if quota.get('has_trial') else 'нет'}"
    )
    await query.edit_message_text(message)
    return LANDING


async def _show_plans(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> int:
    api = _get_api(context)
    try:
        plans = await api.get_plans()
    except BackendApiError as exc:
        await query.edit_message_text(f"Не удалось загрузить тарифы: {exc}")
        return LANDING

    lines = ["💼 Тарифы:"]
    for plan in plans:
        amount = plan.get("amount") or plan.get("amount_minor", 0) / 100
        currency = plan.get("currency", "RUB")
        lines.append(f"• {plan.get('name')} — {amount} {currency} ({plan.get('granted_quota')} откликов)")
    await query.edit_message_text("\n".join(lines))
    return LANDING


async def _prompt_payment_plan(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> int:
    api = _get_api(context)
    try:
        plans = await api.get_plans()
    except BackendApiError as exc:
        await query.edit_message_text(f"Не удалось получить планы: {exc}")
        return LANDING

    if not plans:
        await query.edit_message_text("Планы пока не настроены. Попробуй позже.")
        return LANDING

    data = _user_data(context)
    data["plans"] = plans
    buttons = [
        [InlineKeyboardButton(plan["name"], callback_data=f"menu:payplan:{plan['code']}")]
        for plan in plans
    ]
    await query.edit_message_text("Выбери тариф для оплаты:", reply_markup=InlineKeyboardMarkup(buttons))
    return LANDING


async def _initiate_payment(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, plan_code: str) -> int:
    if not plan_code:
        await query.edit_message_text("Код тарифа не распознан, попробуй ещё раз.")
        return LANDING
    identity = _get_identity(context)
    api = _get_api(context)
    payload = identity.to_payload()
    idempotency_key = str(uuid4())
    try:
        result = await api.initiate_payment(payload, plan_code, idempotency_key)
    except BackendApiError as exc:
        await query.edit_message_text(f"Не удалось создать счёт: {exc}")
        return LANDING

    invoice_url = result.get("invoice_url", "https://pay.yoomoney.test")
    message = (
        f"Счёт готов ✅\n"
        f"План: {plan_code}\n"
        f"Оплата: {result.get('amount_minor', 0) / 100:.2f} {result.get('currency', 'RUB')}\n"
        f"Ссылка: {invoice_url}"
    )
    await query.edit_message_text(message)
    return LANDING


async def _launch_campaign(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, draft: CampaignDraft) -> None:
    identity = _get_identity(context)
    api = _get_api(context)
    try:
        await api.consume_quota(identity.to_payload(), count=1)
    except BackendApiError as exc:
        await query.edit_message_text(f"Не удалось запустить кампанию: {exc}")
        return

    await query.edit_message_text(
        f"{texts.CAMPAIGN_COMPLETE}\n\n" + "\n".join(draft.as_lines()),
        reply_markup=InlineKeyboardMarkup(_build_main_menu(trial_available=False)),
    )


def _build_main_menu(*, trial_available: bool) -> List[List[InlineKeyboardButton]]:
    buttons: List[List[InlineKeyboardButton]] = [
        [InlineKeyboardButton(texts.CTA_CAMPAIGN, callback_data="menu:campaign")],
        [InlineKeyboardButton(texts.CTA_QUOTA, callback_data="menu:quota")],
        [InlineKeyboardButton(texts.CTA_PLANS, callback_data="menu:plans")],
        [InlineKeyboardButton(texts.CTA_PAY, callback_data="menu:pay")],
    ]
    if trial_available:
        buttons.insert(1, [InlineKeyboardButton(texts.CTA_TRIAL, callback_data="menu:trial")])
    return buttons


async def _prompt_next_step(chat_id: int | None, context: ContextTypes.DEFAULT_TYPE) -> None:
    if chat_id is None:
        return
    data = _user_data(context)
    step_index = int(data.get("step_index", 0))
    if step_index >= len(CAMPAIGN_STEPS):
        return
    _, question = CAMPAIGN_STEPS[step_index]
    await context.bot.send_message(chat_id=chat_id, text=question)


def _apply_answer(draft: CampaignDraft, field: str, raw: str) -> None:
    value = raw.strip()
    if field in {"resume", "country", "region"} and not value:
        raise ValueError("Поле не может быть пустым.")
    if field in {"schedule", "employment", "professions", "keywords"}:
        items = [item.strip() for item in value.split(",") if item.strip()]
        setattr(draft, field, items)
        return
    if field == "target_salary":
        draft.target_salary = value or None
        return
    if field == "search_scope":
        normalized = value.lower()
        if normalized not in {"title", "description", "both"}:
            raise ValueError("Напиши title, description или both.")
        draft.search_scope = normalized
        return
    if field == "cover_letter":
        draft.cover_letter = value or None
        return
    setattr(draft, field, value)


async def _send_campaign_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, draft: CampaignDraft) -> None:
    lines = "\n".join(draft.as_lines())
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Запустить кампанию", callback_data="campaign:confirm"),
            ],
            [
                InlineKeyboardButton("✏️ Заполнить заново", callback_data="campaign:restart"),
                InlineKeyboardButton("✖️ Отмена", callback_data="campaign:cancel"),
            ],
        ]
    )
    await _safe_reply(
        update,
        f"Предпросмотр кампании:\n\n{lines}",
        reply_markup=buttons,
    )


async def _safe_reply(
    update: Update,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message | None:
    if update.message:
        return await update.message.reply_text(text, reply_markup=reply_markup)
    query = update.callback_query
    if query and query.message:
        result = await query.edit_message_text(text, reply_markup=reply_markup)
        return cast(Message, result)
    chat = update.effective_chat
    if chat is None:
        return None
    return await chat.send_message(text, reply_markup=reply_markup)


def _get_api(context: ContextTypes.DEFAULT_TYPE) -> BackendApi:
    api = context.application.bot_data.get("backend_api")
    if not isinstance(api, BackendApi):
        raise RuntimeError("BackendApi не инициализирован")
    return api


def _get_identity(context: ContextTypes.DEFAULT_TYPE) -> TelegramIdentity:
    identity = _user_data(context).get("identity")
    if not isinstance(identity, TelegramIdentity):
        raise RuntimeError("Отсутствует Telegram identity, перезапусти /start")
    return identity
