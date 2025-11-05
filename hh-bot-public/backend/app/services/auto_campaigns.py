from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from time import perf_counter

from fastapi import status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.auto_campaigns import (
    Campaign,
    CampaignAuditLog,
    CampaignCompanyBlacklist,
    CampaignCooldownPolicy,
    CampaignDeliveryLog,
    CampaignDeliveryWindow,
    CampaignFrequencyCaps,
    CampaignMode,
    CampaignRun,
    CampaignStatus,
    CampaignStep,
    CampaignUserOptOut,
    CooldownStrategy,
    DeliveryLogStatus,
    SkipPolicy,
)
from backend.app.models.user import User
from backend.app.schemas.auto_campaigns import (
    CampaignCreateRequest,
    CampaignCreatedResponse,
    CampaignFullResponse,
    CampaignResource,
    CampaignRunResource,
    CampaignStartResponse,
    CampaignStatusResponse,
    CampaignStepInput,
    CampaignStepResource,
    CompanyBlacklistCreate,
    CompanyBlacklistItem,
    CompanyBlacklistPage,
    CooldownPolicyInput,
    DeliveryWindowInput,
    DeliveryWindowResource,
    FrequencyCapsInput,
    FrequencyCapsResource,
    PauseRequest,
    SkipRequest,
    SkipResult,
    _hash_payload,
    CooldownPolicyResource,
)
from backend.app.telemetry.metrics import (
    observe_campaign_run_duration,
    observe_operation_latency,
    record_application_skipped,
    record_auto_pause,
    record_campaign_created,
    record_campaign_run,
    record_delivery_error,
    record_delivery_log,
    record_idempotency_conflict,
    record_state_transition,
    set_blacklist_size,
    set_campaign_delay_ms,
    set_scheduler_lag,
)

UTC = timezone.utc


class AutoCampaignError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class FeatureDisabledError(AutoCampaignError):
    status_code = status.HTTP_501_NOT_IMPLEMENTED


class NotFoundError(AutoCampaignError):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(AutoCampaignError):
    status_code = status.HTTP_409_CONFLICT


class LockedError(AutoCampaignError):
    status_code = status.HTTP_423_LOCKED


class TooManyRequestsError(AutoCampaignError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


async def _close_active_run(
    session: AsyncSession,
    campaign_id: int,
    *,
    finished_at: datetime,
    delay_ms: Optional[int] = None,
) -> None:
    stmt = (
        select(CampaignRun)
        .where(CampaignRun.campaign_id == campaign_id)
        .order_by(CampaignRun.run_started_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    run = result.scalar_one_or_none()
    if run and run.run_finished_at is None:
        run.run_finished_at = finished_at
        run.delay_applied_ms = delay_ms
        duration = (finished_at - run.run_started_at).total_seconds()
        if duration >= 0:
            observe_campaign_run_duration(campaign_id, duration)
        set_campaign_delay_ms(campaign_id, delay_ms)


async def _update_blacklist_metric(session: AsyncSession, owner_id: int) -> None:
    size_stmt = (
        select(func.count(CampaignCompanyBlacklist.id))
        .where(CampaignCompanyBlacklist.owner_id == owner_id, CampaignCompanyBlacklist.removed_at.is_(None))
    )
    size = (await session.execute(size_stmt)).scalar_one()
    set_blacklist_size(owner_id, size)


async def _get_user(session: AsyncSession, owner_id: int) -> User:
    user = await session.get(User, owner_id)
    if not user:
        raise NotFoundError(f"user {owner_id} not found")
    return user


async def _has_active_opt_out(session: AsyncSession, owner_id: int, at: datetime) -> bool:
    stmt = select(CampaignUserOptOut).where(
        CampaignUserOptOut.owner_id == owner_id,
        or_(CampaignUserOptOut.expires_at.is_(None), CampaignUserOptOut.expires_at > at),
        CampaignUserOptOut.effective_from <= at,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _get_campaign(session: AsyncSession, campaign_id: int) -> Campaign:
    campaign = await session.get(Campaign, campaign_id)
    if not campaign:
        raise NotFoundError(f"campaign {campaign_id} not found")
    return campaign


async def _get_delivery_window_map(
    session: AsyncSession,
    campaign_id: int,
) -> dict[str, int]:
    stmt = select(CampaignDeliveryWindow)
    windows = (await session.execute(stmt.where(CampaignDeliveryWindow.campaign_id == campaign_id))).scalars()
    return {str(window.id): window.id for window in windows}


async def _query_audit(
    session: AsyncSession,
    *,
    action: str,
    idempotency_key: Optional[str],
) -> Optional[CampaignAuditLog]:
    if not idempotency_key:
        return None
    stmt = (
        select(CampaignAuditLog)
        .where(
            CampaignAuditLog.action == action,
            CampaignAuditLog.idempotency_key == idempotency_key,
        )
        .order_by(CampaignAuditLog.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _store_audit_record(
    session: AsyncSession,
    *,
    campaign_id: int,
    actor_id: Optional[int],
    action: str,
    idempotency_key: Optional[str],
    request_payload: dict[str, Any],
    response_payload: dict[str, Any],
) -> None:
    record = CampaignAuditLog(
        campaign_id=campaign_id,
        actor_id=actor_id,
        action=action,
        idempotency_key=idempotency_key,
        request_hash=_hash_payload(request_payload),
        payload={
            "request": request_payload,
            "response": response_payload,
        },
    )
    session.add(record)


def _resolve_window_id(
    token: str,
    token_map: dict[str, int],
) -> int:
    if token in token_map:
        return token_map[token]
    try:
        return int(token)
    except (TypeError, ValueError) as exc:
        raise ConflictError(f"unknown delivery window reference: {token}") from exc


async def create_campaign(
    session: AsyncSession,
    request: CampaignCreateRequest,
    *,
    idempotency_key: Optional[str],
    actor_id: Optional[int],
) -> CampaignCreatedResponse:
    request_payload = request.model_dump(mode="json", by_alias=True)
    existing = await _query_audit(session, action="campaign.create", idempotency_key=idempotency_key)
    if existing:
        if existing.request_hash and existing.request_hash != _hash_payload(request_payload):
            record_idempotency_conflict("/campaigns")
            raise ConflictError("Idempotency key already used with different payload")
        response_payload = existing.payload.get("response", {})
        return CampaignCreatedResponse(**response_payload)

    await _get_user(session, request.owner_id)
    now = datetime.now(tz=UTC)
    if await _has_active_opt_out(session, request.owner_id, now):
        raise LockedError("Owner has opted out from auto campaigns")

    campaign = Campaign(
        owner_id=request.owner_id,
        status=CampaignStatus.DRAFT,
        mode=request.mode,
        daily_quota_target=request.daily_quota_target,
    )
    session.add(campaign)
    await session.flush()

    window_token_map: dict[str, int] = {}
    default_window_id: Optional[int] = None
    for window in request.windows:
        created_window = CampaignDeliveryWindow(
            campaign_id=campaign.id,
            start_utc=window.start_utc,
            end_utc=window.end_utc,
            days_mask=window.days_mask,
            is_default=window.is_default,
        )
        session.add(created_window)
        await session.flush()
        window_token_map[window.client_token] = created_window.id
        if window.is_default:
            default_window_id = created_window.id

    if default_window_id is None:
        default_token = request.default_window_token or request.windows[0].client_token
        default_window_id = window_token_map.get(default_token)
        if default_window_id is None:
            raise ConflictError("Default window reference is invalid")
    campaign.default_window_id = default_window_id

    for step_input in request.steps:
        delivery_window_id = _resolve_window_id(step_input.delivery_window_token, window_token_map)
        session.add(
            CampaignStep(
                campaign_id=campaign.id,
                step_order=step_input.step_order,
                vacancy_filter=step_input.vacancy_filter,
                message_template_id=step_input.message_template_id,
                delivery_window_id=delivery_window_id,
                skip_policy=step_input.skip_policy,
            )
        )

    caps_input: FrequencyCapsInput = request.frequency_caps or FrequencyCapsInput()
    caps = CampaignFrequencyCaps(
        campaign_id=campaign.id,
        per_day=caps_input.per_day,
        per_week=caps_input.per_week,
        per_company=caps_input.per_company,
    )
    session.add(caps)

    cooldown_input: CooldownPolicyInput = request.cooldown_policy or CooldownPolicyInput()
    policy = CampaignCooldownPolicy(
        campaign_id=campaign.id,
        base_delay_ms=cooldown_input.base_delay_ms,
        max_delay_ms=cooldown_input.max_delay_ms,
        strategy=cooldown_input.strategy,
        error_streak_limit=cooldown_input.error_streak_limit,
    )
    session.add(policy)
    await session.flush()
    campaign.cooldown_policy_id = policy.id

    response = CampaignCreatedResponse(
        id=campaign.id,
        status=campaign.status,
        revision=1,
        default_window_id=campaign.default_window_id or 0,
    )

    await _store_audit_record(
        session,
        campaign_id=campaign.id,
        actor_id=actor_id or campaign.owner_id,
        action="campaign.create",
        idempotency_key=idempotency_key,
        request_payload=request_payload,
        response_payload=response.model_dump(mode="json"),
    )
    record_campaign_created(request.mode)
    await session.commit()
    return response


async def _load_campaign_full(session: AsyncSession, campaign: Campaign) -> CampaignFullResponse:
    await session.refresh(campaign)
    windows = (
        await session.execute(
            select(CampaignDeliveryWindow)
            .where(CampaignDeliveryWindow.campaign_id == campaign.id)
            .order_by(CampaignDeliveryWindow.id.asc())
        )
    ).scalars().all()
    steps = (
        await session.execute(
            select(CampaignStep)
            .where(CampaignStep.campaign_id == campaign.id)
            .order_by(CampaignStep.step_order.asc())
        )
    ).scalars().all()
    caps = (
        await session.execute(
            select(CampaignFrequencyCaps).where(CampaignFrequencyCaps.campaign_id == campaign.id)
        )
    ).scalar_one_or_none()
    policy = (
        await session.execute(
            select(CampaignCooldownPolicy).where(CampaignCooldownPolicy.campaign_id == campaign.id)
        )
    ).scalar_one_or_none()
    runs = (
        await session.execute(
            select(CampaignRun)
            .where(CampaignRun.campaign_id == campaign.id)
            .order_by(CampaignRun.run_started_at.desc())
            .limit(10)
        )
    ).scalars().all()
    blacklist_sample = (
        await session.execute(
            select(CampaignCompanyBlacklist)
            .where(
                CampaignCompanyBlacklist.owner_id == campaign.owner_id,
                CampaignCompanyBlacklist.removed_at.is_(None),
            )
            .order_by(CampaignCompanyBlacklist.added_at.desc())
            .limit(5)
        )
    ).scalars().all()

    return CampaignFullResponse(
        campaign=CampaignResource.model_validate(campaign),
        windows=[DeliveryWindowResource.model_validate(window) for window in windows],
        steps=[CampaignStepResource.model_validate(step) for step in steps],
        frequency_caps=caps and FrequencyCapsResource.model_validate(caps),
        cooldown_policy=policy and CooldownPolicyResource.model_validate(policy),
        runs=[CampaignRunResource.model_validate(run) for run in runs],
        blacklist_sample=[CompanyBlacklistItem.model_validate(item) for item in blacklist_sample],
    )
async def get_campaign_details(session: AsyncSession, campaign_id: int) -> CampaignFullResponse:
    campaign = await _get_campaign(session, campaign_id)
    return await _load_campaign_full(session, campaign)


async def _get_frequency_caps(session: AsyncSession, campaign_id: int) -> CampaignFrequencyCaps | None:
    stmt = select(CampaignFrequencyCaps).where(CampaignFrequencyCaps.campaign_id == campaign_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _enforce_frequency_caps(
    session: AsyncSession,
    campaign: Campaign,
    *,
    now: datetime,
    force: bool,
) -> None:
    if force:
        return

    caps = await _get_frequency_caps(session, campaign.id)
    per_day = caps.per_day if caps else 10
    per_week = caps.per_week if caps else 50

    if per_day:
        day_count_stmt = select(func.count(CampaignDeliveryLog.id)).where(
            CampaignDeliveryLog.campaign_id == campaign.id,
            CampaignDeliveryLog.status == DeliveryLogStatus.SENT,
            CampaignDeliveryLog.attempted_at >= now - timedelta(days=1),
        )
        day_count = (await session.execute(day_count_stmt)).scalar_one()
        if day_count >= per_day:
            raise TooManyRequestsError("Daily frequency cap reached")

    if per_week:
        week_count_stmt = select(func.count(CampaignDeliveryLog.id)).where(
            CampaignDeliveryLog.campaign_id == campaign.id,
            CampaignDeliveryLog.status == DeliveryLogStatus.SENT,
            CampaignDeliveryLog.attempted_at >= now - timedelta(days=7),
        )
        week_count = (await session.execute(week_count_stmt)).scalar_one()
        if week_count >= per_week:
            raise TooManyRequestsError("Weekly frequency cap reached")


async def start_campaign(
    session: AsyncSession,
    campaign_id: int,
    *,
    idempotency_key: Optional[str],
    actor_id: Optional[int],
    force: bool = False,
) -> CampaignStartResponse:
    op_started = perf_counter()
    try:
        request_payload = {"force": force}
        existing = await _query_audit(session, action="campaign.start", idempotency_key=idempotency_key)
        if existing:
            if existing.request_hash and existing.request_hash != _hash_payload(request_payload):
                record_idempotency_conflict("/campaigns/start")
                raise ConflictError("Idempotency key already used with different payload")
            return CampaignStartResponse(**existing.payload.get("response", {}))

        campaign = await _get_campaign(session, campaign_id)
        previous_status = campaign.status
        if previous_status is CampaignStatus.ARCHIVED:
            raise ConflictError("Archived campaign cannot be restarted")
        if previous_status is CampaignStatus.ACTIVE and not force:
            # treat as idempotent success
            return CampaignStartResponse(
                campaign_id=campaign.id,
                scheduled_at=datetime.now(tz=UTC),
                delay_ms=None,
                status_after=campaign.status,
            )

        now = datetime.now(tz=UTC)
        if await _has_active_opt_out(session, campaign.owner_id, now):
            raise LockedError("Owner opted out")

        await _enforce_frequency_caps(session, campaign, now=now, force=force)

        campaign.status = CampaignStatus.ACTIVE
        run = CampaignRun(
            campaign_id=campaign.id,
            run_started_at=now,
            run_finished_at=None,
            scheduled_by="user" if actor_id and actor_id != campaign.owner_id else "system",
            status="success",
            sent_count=0,
            error_count=0,
            skipped_count=0,
            delay_applied_ms=None,
        )
        session.add(run)

        response = CampaignStartResponse(
            campaign_id=campaign.id,
            scheduled_at=now,
            delay_ms=None,
            status_after=campaign.status,
        )

        await _store_audit_record(
            session,
            campaign_id=campaign.id,
            actor_id=actor_id or campaign.owner_id,
            action="campaign.start",
            idempotency_key=idempotency_key,
            request_payload=request_payload,
            response_payload=response.model_dump(mode="json"),
        )
        record_state_transition(previous_status, campaign.status, mode=campaign.mode)
        record_campaign_run(campaign.id, campaign.mode)
        set_campaign_delay_ms(campaign.id, run.delay_applied_ms)
        set_scheduler_lag(0.0)
        await session.commit()
        return response
    finally:
        observe_operation_latency("start", perf_counter() - op_started)


async def pause_campaign(
    session: AsyncSession,
    campaign_id: int,
    *,
    idempotency_key: Optional[str],
    actor_id: Optional[int],
    payload: PauseRequest,
) -> CampaignStatusResponse:
    op_started = perf_counter()
    try:
        request_payload = payload.model_dump(mode="json")
        existing = await _query_audit(session, action="campaign.pause", idempotency_key=idempotency_key)
        if existing:
            if existing.request_hash and existing.request_hash != _hash_payload(request_payload):
                record_idempotency_conflict("/campaigns/pause")
                raise ConflictError("Idempotency key already used with different payload")
            return CampaignStatusResponse(**existing.payload.get("response", {}))

        campaign = await _get_campaign(session, campaign_id)
        if campaign.status is not CampaignStatus.ACTIVE:
            raise ConflictError("Only active campaigns can be paused")

        campaign.status = CampaignStatus.PAUSED
        updated_at = datetime.now(tz=UTC)
        await _close_active_run(session, campaign.id, finished_at=updated_at)
        response = CampaignStatusResponse(
            campaign_id=campaign.id,
            status=campaign.status,
            updated_at=updated_at,
        )

        await _store_audit_record(
            session,
            campaign_id=campaign.id,
            actor_id=actor_id or campaign.owner_id,
            action="campaign.pause",
            idempotency_key=idempotency_key,
            request_payload=request_payload,
            response_payload=response.model_dump(mode="json"),
        )
        record_state_transition(CampaignStatus.ACTIVE, CampaignStatus.PAUSED, mode=campaign.mode)
        record_auto_pause(payload.reason)
        await session.commit()
        return response
    finally:
        observe_operation_latency("pause", perf_counter() - op_started)


async def stop_campaign(
    session: AsyncSession,
    campaign_id: int,
    *,
    idempotency_key: Optional[str],
    actor_id: Optional[int],
) -> CampaignStatusResponse:
    op_started = perf_counter()
    try:
        existing = await _query_audit(session, action="campaign.stop", idempotency_key=idempotency_key)
        if existing:
            return CampaignStatusResponse(**existing.payload.get("response", {}))

        campaign = await _get_campaign(session, campaign_id)
        previous_status = campaign.status
        if previous_status is CampaignStatus.ARCHIVED:
            return CampaignStatusResponse(
                campaign_id=campaign.id,
                status=campaign.status,
                updated_at=datetime.now(tz=UTC),
            )

        campaign.status = CampaignStatus.ARCHIVED
        updated_at = datetime.now(tz=UTC)
        await _close_active_run(session, campaign.id, finished_at=updated_at)
        response = CampaignStatusResponse(
            campaign_id=campaign.id,
            status=campaign.status,
            updated_at=updated_at,
        )

        await _store_audit_record(
            session,
            campaign_id=campaign.id,
            actor_id=actor_id or campaign.owner_id,
            action="campaign.stop",
            idempotency_key=idempotency_key,
            request_payload={},
            response_payload=response.model_dump(mode="json"),
        )
        record_state_transition(previous_status, CampaignStatus.ARCHIVED, mode=campaign.mode)
        await session.commit()
        return response
    finally:
        observe_operation_latency("stop", perf_counter() - op_started)

async def skip_target(
    session: AsyncSession,
    campaign_id: int,
    *,
    idempotency_key: Optional[str],
    actor_id: Optional[int],
    payload: SkipRequest,
) -> SkipResult:
    op_started = perf_counter()
    request_payload = payload.model_dump(mode="json")
    try:
        existing = await _query_audit(session, action="campaign.skip", idempotency_key=idempotency_key)
        if existing:
            if existing.request_hash and existing.request_hash != _hash_payload(request_payload):
                record_idempotency_conflict("/campaigns/skip")
                raise ConflictError("Idempotency key already used with different payload")
            return SkipResult(**existing.payload.get("response", {}))

        campaign = await _get_campaign(session, campaign_id)
        now = datetime.now(tz=UTC)
        log = CampaignDeliveryLog(
            campaign_id=campaign.id,
            campaign_run_id=None,
            step_id=payload.step_id,
            vacancy_id=payload.vacancy_id,
            status=DeliveryLogStatus.SKIPPED,
            response_payload={"reason": payload.reason, "note": payload.note},
            attempted_at=now,
            error_code=None,
        )
        session.add(log)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            stmt = select(CampaignDeliveryLog).where(
                CampaignDeliveryLog.campaign_id == campaign.id,
                CampaignDeliveryLog.vacancy_id == payload.vacancy_id,
                CampaignDeliveryLog.step_id == payload.step_id,
            )
            existing_log = (await session.execute(stmt)).scalar_one_or_none()
            if existing_log is None:
                raise ConflictError("Duplicate skip request")
            return SkipResult(
                delivery_log_id=existing_log.id,
                status=existing_log.status,
                attempted_at=existing_log.attempted_at,
            )

        result = SkipResult(
            delivery_log_id=log.id,
            status=log.status,
            attempted_at=log.attempted_at,
        )

        await _store_audit_record(
            session,
            campaign_id=campaign.id,
            actor_id=actor_id or campaign.owner_id,
            action="campaign.skip",
            idempotency_key=idempotency_key,
            request_payload=request_payload,
        response_payload=result.model_dump(mode="json"),
        )
        record_delivery_log(DeliveryLogStatus.SKIPPED)
        record_application_skipped(campaign.id, payload.reason, "bot")
        await session.commit()
        return result
    finally:
        observe_operation_latency("skip", perf_counter() - op_started)


async def list_blacklist(
    session: AsyncSession,
    campaign_id: int,
) -> CompanyBlacklistPage:
    campaign = await _get_campaign(session, campaign_id)
    stmt = (
        select(CampaignCompanyBlacklist)
        .where(
            CampaignCompanyBlacklist.owner_id == campaign.owner_id,
            CampaignCompanyBlacklist.removed_at.is_(None),
        )
        .order_by(CampaignCompanyBlacklist.added_at.desc())
    )
    items = (await session.execute(stmt)).scalars().all()
    return CompanyBlacklistPage(items=[CompanyBlacklistItem.model_validate(item) for item in items], next_cursor=None)


async def add_to_blacklist(
    session: AsyncSession,
    campaign_id: int,
    *,
    idempotency_key: Optional[str],
    actor_id: Optional[int],
    payload: CompanyBlacklistCreate,
) -> CompanyBlacklistItem:
    op_started = perf_counter()
    request_payload = payload.model_dump(mode="json")
    try:
        existing = await _query_audit(session, action="blacklist.create", idempotency_key=idempotency_key)
        if existing:
            if existing.request_hash and existing.request_hash != _hash_payload(request_payload):
                record_idempotency_conflict("/campaigns/blacklist")
                raise ConflictError("Idempotency key already used with different payload")
            return CompanyBlacklistItem(**existing.payload.get("response", {}))

        campaign = await _get_campaign(session, campaign_id)
        entry = CampaignCompanyBlacklist(
            owner_id=campaign.owner_id,
            company_name=payload.company_name,
            company_id_external=payload.company_id_external,
            reason=payload.reason,
        )
        session.add(entry)
        try:
            await session.flush()
        except IntegrityError as exc:
            await session.rollback()
            raise ConflictError("Company already blacklisted") from exc

        item = CompanyBlacklistItem.model_validate(entry)
        await _store_audit_record(
            session,
            campaign_id=campaign.id,
            actor_id=actor_id or campaign.owner_id,
            action="blacklist.create",
            idempotency_key=idempotency_key,
            request_payload=request_payload,
            response_payload=item.model_dump(mode="json"),
        )
        await _update_blacklist_metric(session, campaign.owner_id)
        await session.commit()
        return item
    finally:
        observe_operation_latency("blacklist", perf_counter() - op_started)


async def remove_from_blacklist(
    session: AsyncSession,
    campaign_id: int,
    *,
    blacklist_id: int,
    idempotency_key: Optional[str],
    actor_id: Optional[int],
) -> CompanyBlacklistItem:
    op_started = perf_counter()
    try:
        campaign = await _get_campaign(session, campaign_id)
        entry = await session.get(CampaignCompanyBlacklist, blacklist_id)
        if entry is None or entry.owner_id != campaign.owner_id:
            raise NotFoundError("Blacklist entry not found")

        existing = await _query_audit(session, action="blacklist.delete", idempotency_key=idempotency_key)
        if existing:
            return CompanyBlacklistItem(**existing.payload.get("response", {}))

        entry.removed_at = datetime.now(tz=UTC)
        item = CompanyBlacklistItem.model_validate(entry)

        await _store_audit_record(
            session,
            campaign_id=campaign.id,
            actor_id=actor_id or campaign.owner_id,
            action="blacklist.delete",
            idempotency_key=idempotency_key,
            request_payload={"blacklist_id": blacklist_id},
            response_payload=item.model_dump(mode="json"),
        )
        await _update_blacklist_metric(session, campaign.owner_id)
        await session.commit()
        return item
    finally:
        observe_operation_latency("blacklist", perf_counter() - op_started)
