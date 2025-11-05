from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from backend.app.core.db import get_session_factory
from backend.app.main import app
from backend.app.models.auto_campaigns import Campaign, CampaignDeliveryLog, CampaignStatus
from backend.tests.payments.helpers import create_user


async def _fetch_campaign(session_factory, campaign_id: int) -> Campaign:
    async with session_factory() as session:
        campaign = await session.get(Campaign, campaign_id)
        assert campaign is not None
        await session.refresh(campaign)
        return campaign


@pytest.mark.asyncio
async def test_auto_campaign_lifecycle(client: AsyncClient):
    app.state.campaigns_enabled = True
    owner_id = await create_user()
    payload = {
        "owner_id": owner_id,
        "mode": "strict",
        "daily_quota_target": 5,
        "windows": [
            {
                "client_token": "morning",
                "start_utc": "03:00",
                "end_utc": "21:00",
                "days_mask": "1111100",
                "is_default": True,
            }
        ],
        "steps": [
            {
                "client_token": "step1",
                "step_order": 1,
                "delivery_window_id": "morning",
                "message_template_id": 1,
                "skip_policy": "manual",
                "vacancy_filter": {"salary_min": 100000},
            }
        ],
        "frequency_caps": {"per_day": 10, "per_week": 50, "per_company": 2},
        "cooldown_policy": {
            "base_delay_ms": 60000,
            "max_delay_ms": 120000,
            "strategy": "exp",
            "error_streak_limit": 5,
        },
    }
    headers = {"Idempotency-Key": "create-1"}
    response = await client.post("/api/v1/auto/campaigns", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    created = response.json()
    campaign_id = created["id"]
    assert created["status"] == "draft"
    session_factory = get_session_factory()
    campaign = await _fetch_campaign(session_factory, campaign_id)
    assert campaign.owner_id == owner_id
    assert campaign.status is CampaignStatus.DRAFT

    # Idempotent create
    response_dup = await client.post("/api/v1/auto/campaigns", json=payload, headers=headers)
    assert response_dup.status_code == 201
    assert response_dup.json()["id"] == campaign_id

    # GET details
    detail = await client.get(f"/api/v1/auto/campaigns/{campaign_id}")
    assert detail.status_code == 200
    detail_json = detail.json()
    assert detail_json["campaign"]["status"] == "draft"
    assert len(detail_json["windows"]) == 1
    step_id = detail_json["steps"][0]["id"]

    # Start campaign
    start_headers = {"Idempotency-Key": "start-1"}
    start_resp = await client.post(
        f"/api/v1/auto/campaigns/{campaign_id}/start",
        json={"force": False},
        headers=start_headers,
    )
    assert start_resp.status_code == 202
    assert start_resp.json()["status_after"] == "active"

    # Repeat start with same payload - should be idempotent
    repeat_start = await client.post(
        f"/api/v1/auto/campaigns/{campaign_id}/start",
        json={"force": False},
        headers=start_headers,
    )
    assert repeat_start.status_code == 202

    # Reusing key with different payload -> conflict
    conflict_resp = await client.post(
        f"/api/v1/auto/campaigns/{campaign_id}/start",
        json={"force": True},
        headers={"Idempotency-Key": "start-1"},
    )
    assert conflict_resp.status_code == 409

    # Pause campaign
    pause_resp = await client.post(
        f"/api/v1/auto/campaigns/{campaign_id}/pause",
        json={"reason": "manual investigation"},
        headers={"Idempotency-Key": "pause-1"},
    )
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "paused"

    # Resume campaign
    resume_resp = await client.post(
        f"/api/v1/auto/campaigns/{campaign_id}/start",
        json={"force": False},
        headers={"Idempotency-Key": "start-2"},
    )
    assert resume_resp.status_code == 202
    assert resume_resp.json()["status_after"] == "active"

    # Skip vacancy
    skip_payload = {
        "vacancy_id": "VAC-001",
        "step_id": step_id,
        "reason": "duplicate",
        "note": "already contacted",
    }
    skip_resp = await client.post(
        f"/api/v1/auto/campaigns/{campaign_id}/skip",
        json=skip_payload,
        headers={"Idempotency-Key": "skip-1"},
    )
    assert skip_resp.status_code == 200
    skip_data = skip_resp.json()
    assert skip_data["status"] == "skipped"

    # Skip idempotency
    skip_repeat = await client.post(
        f"/api/v1/auto/campaigns/{campaign_id}/skip",
        json=skip_payload,
        headers={"Idempotency-Key": "skip-1"},
    )
    assert skip_repeat.status_code == 200

    # Blacklist operations
    list_resp = await client.get(f"/api/v1/auto/campaigns/{campaign_id}/blacklist")
    assert list_resp.status_code == 200
    assert list_resp.json()["items"] == []

    blacklist_resp = await client.post(
        f"/api/v1/auto/campaigns/{campaign_id}/blacklist",
        json={"company_name": "ACME Corp", "reason": "abusive"},
        headers={"Idempotency-Key": "blacklist-1"},
    )
    assert blacklist_resp.status_code == 201
    blacklist_item = blacklist_resp.json()

    delete_resp = await client.delete(
        f"/api/v1/auto/campaigns/{campaign_id}/blacklist/{blacklist_item['id']}",
        headers={"Idempotency-Key": "blacklist-del-1"},
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["removed_at"] is not None

    # Stop campaign
    stop_resp = await client.post(
        f"/api/v1/auto/campaigns/{campaign_id}/stop",
        headers={"Idempotency-Key": "stop-1"},
    )
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "archived"

    # Metrics snapshot
    metrics_resp = await client.get("/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.text.splitlines()
    assert any("campaign_created_total" in line for line in metrics)
    assert any("campaign_state_transitions_total" in line for line in metrics)
    assert any("campaign_delivery_logs_total{result=\"skipped\"}" in line for line in metrics)

    # Verify delivery log persisted
    session_factory = get_session_factory()
    async with session_factory() as session:
        count_stmt = select(func.count(CampaignDeliveryLog.id)).where(
            CampaignDeliveryLog.campaign_id == campaign_id,
            CampaignDeliveryLog.vacancy_id == "VAC-001",
        )
        count = (await session.execute(count_stmt)).scalar_one()
        assert count == 1


@pytest.mark.asyncio
async def test_feature_flag_disables_endpoints(client: AsyncClient):
    app.state.campaigns_enabled = False
    response = await client.get("/api/v1/auto/campaigns/999")
    assert response.status_code == 404
    create_resp = await client.post(
        "/api/v1/auto/campaigns",
        json={},
        headers={"Idempotency-Key": "flag-test"},
    )
    assert create_resp.status_code == 501
    app.state.campaigns_enabled = True

