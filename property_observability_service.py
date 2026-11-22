from __future__ import annotations

from typing import Any

import infrai
from property_models import ActionDecision, PortfolioEvent

CUTOVER_FLAG_KEY = "property-observability-cutover"


def decide_action(event: PortfolioEvent) -> ActionDecision:
    if event.maintenance_request is not None:
        item = event.maintenance_request
        if item.category == "water_leak" and item.has_active_leak:
            return ActionDecision(
                event_type="maintenance_request",
                action="dispatch_now",
                severity="critical",
                reason="active water leak can damage units quickly",
            )
        if item.category in {"lockout", "hvac"} or item.hours_open >= 24:
            return ActionDecision(
                event_type="maintenance_request",
                action="review_today",
                severity="warning",
                reason="resident-facing issue needs same-day review",
            )
        return ActionDecision(
            event_type="maintenance_request",
            action="queue_backlog",
            severity="info",
            reason="request can wait for normal scheduling",
        )

    if event.tenant_document is not None:
        item = event.tenant_document
        if item.status in {"blurry", "missing_signature"}:
            return ActionDecision(
                event_type="tenant_document",
                action="request_reupload",
                severity="warning",
                reason="document is not ready for move-in review",
            )
        return ActionDecision(
            event_type="tenant_document",
            action="mark_document_ready",
            severity="info",
            reason="document is complete for the next review step",
        )

    item = event.inspection_reminder
    assert item is not None
    if item.days_until_due <= 2 and not item.tenant_confirmed:
        return ActionDecision(
            event_type="inspection_reminder",
            action="send_reminder",
            severity="warning",
            reason="inspection is close and still unconfirmed",
        )
    return ActionDecision(
        event_type="inspection_reminder",
        action="schedule_future_notice",
        severity="info",
        reason="inspection still has enough lead time",
    )


def process_portfolio_event(event: PortfolioEvent) -> ActionDecision:
    decision = decide_action(event)
    emit_observability(event, decision)
    return decision


def emit_observability(event: PortfolioEvent, decision: ActionDecision) -> None:
    event_name = decision.event_type
    log_payload: dict[str, Any] = {
        "source": "property-mvp-service",
        "message": f"{event_name}:{decision.action}",
        "level": decision.severity,
        "property_id": event.property_id,
        "tenant_id": event.tenant_id,
    }
    infrai.logs.ingest({"entries": [log_payload]})

    metric_payload = {
        "name": "property_workflow_action_total",
        "value": 1,
        "type": "counter",
    }
    infrai.metrics.report(metric_payload)

    cutover_enabled = is_cutover_enabled(CUTOVER_FLAG_KEY)
    if cutover_enabled:
        infrai.metrics.report(
            {
                "name": "property_cutover_action_total",
                "value": 1,
                "type": "counter",
            }
        )


def is_cutover_enabled(flag_key: str) -> bool:
    envelope = infrai.flags.is_enabled(flag_key)
    data = envelope.get("data") or {}
    if isinstance(data, bool):
        return data
    if isinstance(data, dict):
        for key in ("enabled", "is_enabled", "value"):
            value = data.get(key)
            if isinstance(value, bool):
                return value
    return False
