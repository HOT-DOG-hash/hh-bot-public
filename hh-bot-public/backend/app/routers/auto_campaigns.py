from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.schemas.auto_campaigns import (
    CampaignCreateRequest,
    CampaignCreatedResponse,
    CampaignFullResponse,
    CampaignStartRequest,
    CampaignStartResponse,
    CampaignStatusResponse,
    CompanyBlacklistCreate,
    CompanyBlacklistItem,
    CompanyBlacklistPage,
    PauseRequest,
    SkipRequest,
    SkipResult,
)
from backend.app.services.auto_campaigns import (
    AutoCampaignError,
    add_to_blacklist,
    create_campaign,
    get_campaign_details,
    list_blacklist,
    pause_campaign,
    remove_from_blacklist,
    skip_target,
    start_campaign,
    stop_campaign,
)

router = APIRouter(prefix="/api/v1/auto/campaigns", tags=["auto_campaigns"])


def _campaigns_enabled(request: Request) -> bool:
    return bool(getattr(request.app.state, "campaigns_enabled", False))


def require_feature_enabled(request: Request, write: bool) -> None:
    if _campaigns_enabled(request):
        return
    if write:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Auto campaigns feature is disabled",
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auto campaigns not found")


def ensure_feature_enabled_write(request: Request) -> None:
    require_feature_enabled(request, write=True)


def ensure_feature_enabled_read(request: Request) -> None:
    require_feature_enabled(request, write=False)


async def get_idempotency_key(idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")) -> str:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required for this operation",
        )
    return idempotency_key


def _handle_service_error(exc: AutoCampaignError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("", response_model=CampaignCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign_endpoint(
    payload: CampaignCreateRequest,
    session: AsyncSession = Depends(get_db),
    idempotency_key: str = Depends(get_idempotency_key),
    _: None = Depends(ensure_feature_enabled_write),
) -> CampaignCreatedResponse:
    try:
        return await create_campaign(
            session,
            payload,
            idempotency_key=idempotency_key,
            actor_id=payload.owner_id,
        )
    except AutoCampaignError as exc:
        raise _handle_service_error(exc)


@router.get("/{campaign_id}", response_model=CampaignFullResponse)
async def get_campaign_endpoint(
    campaign_id: int,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(ensure_feature_enabled_read),
) -> CampaignFullResponse:
    try:
        return await get_campaign_details(session, campaign_id)
    except AutoCampaignError as exc:
        raise _handle_service_error(exc)


@router.post(
    "/{campaign_id}/start",
    response_model=CampaignStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_campaign_endpoint(
    campaign_id: int,
    payload: Optional[CampaignStartRequest] = None,
    session: AsyncSession = Depends(get_db),
    idempotency_key: str = Depends(get_idempotency_key),
    _: None = Depends(ensure_feature_enabled_write),
) -> CampaignStartResponse:
    force = payload.force if payload else False
    try:
        return await start_campaign(
            session,
            campaign_id,
            idempotency_key=idempotency_key,
            actor_id=None,
            force=force,
        )
    except AutoCampaignError as exc:
        raise _handle_service_error(exc)


@router.post("/{campaign_id}/pause", response_model=CampaignStatusResponse)
async def pause_campaign_endpoint(
    campaign_id: int,
    payload: PauseRequest,
    session: AsyncSession = Depends(get_db),
    idempotency_key: str = Depends(get_idempotency_key),
    _: None = Depends(ensure_feature_enabled_write),
) -> CampaignStatusResponse:
    try:
        return await pause_campaign(
            session,
            campaign_id,
            idempotency_key=idempotency_key,
            actor_id=None,
            payload=payload,
        )
    except AutoCampaignError as exc:
        raise _handle_service_error(exc)


@router.post("/{campaign_id}/stop", response_model=CampaignStatusResponse)
async def stop_campaign_endpoint(
    campaign_id: int,
    session: AsyncSession = Depends(get_db),
    idempotency_key: str = Depends(get_idempotency_key),
    _: None = Depends(ensure_feature_enabled_write),
) -> CampaignStatusResponse:
    try:
        return await stop_campaign(
            session,
            campaign_id,
            idempotency_key=idempotency_key,
            actor_id=None,
        )
    except AutoCampaignError as exc:
        raise _handle_service_error(exc)


@router.post("/{campaign_id}/skip", response_model=SkipResult)
async def skip_target_endpoint(
    campaign_id: int,
    payload: SkipRequest,
    session: AsyncSession = Depends(get_db),
    idempotency_key: str = Depends(get_idempotency_key),
    _: None = Depends(ensure_feature_enabled_write),
) -> SkipResult:
    try:
        return await skip_target(
            session,
            campaign_id,
            idempotency_key=idempotency_key,
            actor_id=None,
            payload=payload,
        )
    except AutoCampaignError as exc:
        raise _handle_service_error(exc)


@router.get("/{campaign_id}/blacklist", response_model=CompanyBlacklistPage)
async def list_blacklist_endpoint(
    campaign_id: int,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(ensure_feature_enabled_read),
) -> CompanyBlacklistPage:
    try:
        return await list_blacklist(session, campaign_id)
    except AutoCampaignError as exc:
        raise _handle_service_error(exc)


@router.post(
    "/{campaign_id}/blacklist",
    response_model=CompanyBlacklistItem,
    status_code=status.HTTP_201_CREATED,
)
async def add_blacklist_entry_endpoint(
    campaign_id: int,
    payload: CompanyBlacklistCreate,
    session: AsyncSession = Depends(get_db),
    idempotency_key: str = Depends(get_idempotency_key),
    _: None = Depends(ensure_feature_enabled_write),
) -> CompanyBlacklistItem:
    try:
        return await add_to_blacklist(
            session,
            campaign_id,
            idempotency_key=idempotency_key,
            actor_id=None,
            payload=payload,
        )
    except AutoCampaignError as exc:
        raise _handle_service_error(exc)


@router.delete("/{campaign_id}/blacklist/{blacklist_id}", response_model=CompanyBlacklistItem)
async def delete_blacklist_entry_endpoint(
    campaign_id: int,
    blacklist_id: int,
    session: AsyncSession = Depends(get_db),
    idempotency_key: str = Depends(get_idempotency_key),
    _: None = Depends(ensure_feature_enabled_write),
) -> CompanyBlacklistItem:
    try:
        return await remove_from_blacklist(
            session,
            campaign_id,
            blacklist_id=blacklist_id,
            idempotency_key=idempotency_key,
            actor_id=None,
        )
    except AutoCampaignError as exc:
        raise _handle_service_error(exc)
