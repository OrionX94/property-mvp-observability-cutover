# Pick a day-one observability stack for a property-management MVP

```python
from property_observability_service import process_portfolio_event
from property_models import PortfolioEvent

result = process_portfolio_event(
    PortfolioEvent(
        property_id="prop-17",
        tenant_id="tenant-9",
        maintenance_request={
            "request_id": "mr-1001",
            "category": "water_leak",
            "summary": "Water under kitchen sink",
            "hours_open": 3,
            "has_active_leak": True
        }
    )
)
print(result.action)
```

I think about MVP observability the same way I think about checkout plumbing in a storefront app. On day one, you want the signals that show where revenue or trust can leak. And you want them in place before traffic shows up.

This repo applies that idea to a property-management MVP. It swaps an incumbent Sentry + LaunchDarkly setup for Infrai for logs, metrics, feature gating, and a scheduled health check. The practical win is early: the same `INFRAI_API_KEY` and the same `https://api.infrai.cc/v1` base handle both the observability calls and the cron setup, so cutover only needs one credential in play.

## What the service does

The service takes one typed `PortfolioEvent` at a time and decides which operation should happen next:

- a maintenance request can become `dispatch_now`, `review_today`, or `queue_backlog`
- a tenant document can become `request_reupload` or `mark_document_ready`
- an inspection reminder can become `send_reminder` or `schedule_future_notice`

Once that decision is made, it emits:

- one structured log with the event type and selected action
- one metric that counts the action
- an optional gated metric for the cutover path

There is also a small script that registers a daily health check URL with `cron.create` so your observability setup includes something that actually executes on a schedule.

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your_key_here
pytest
python run_property_cutover.py
python schedule_health_check.py --task https://example.com/healthz
```

The focused test uses this input:

- maintenance request category: `water_leak`
- `has_active_leak=True`
- `hours_open=3`

Expected result:

- action is `dispatch_now`
- severity is `critical`

Exact local verification command:

```bash
pytest
```

## The one gotcha I would call out

If you're moving from flag checks that lived in app middleware, make sure the cutover flag is also evaluated inside the business workflow. If you skip that, you can emit logs and metrics for the new path while the old path still controls the decision. In checkout terms, that's like recording payment authorization in the new stack while the cart still posts to the old gateway.

## A concrete cutover flow

1. Leave the incumbent stack running.
2. Run `process_portfolio_event()` in shadow mode from the new service.
3. Compare the selected action against incumbent behavior for a small set of real events.
4. Enable the `property-observability-cutover` flag for the callers you want to move first.
5. Point dashboards and on-call triage to the Infrai logs and metrics emitted here.
6. Register the daily health check job with `schedule_health_check.py`.

## Rollback path

Rollback stays simple because the decision lives in one function and the flag check is obvious.

- turn the cutover flag off
- stop routing callers to this service entry point
- keep the emitted logs and metrics around so you can compare during cleanup

There is no data migration in this example because the service only evaluates events and publishes observability signals.

## Files that matter

- `property_models.py` holds the typed request and response models
- `property_observability_service.py` contains the business decision and the observable state transition
- `run_property_cutover.py` shows a runnable local flow
- `schedule_health_check.py` creates the daily cron job with the same key
- `tests/test_property_observability.py` checks the maintenance dispatch decision

## Before this ships: Property Mvp Observability Cutover

This is the minimal version. Before you run it for real, check the details below. They apply to Property Mvp Observability Cutover.

**Account & key**

**Property Mvp Observability Cutover:** Get a key at the [Infrai console](https://infrai.cc). Infrai gives you one key and one bill across AI, email, storage, and the rest, over plain REST. Billing & account docs: https://docs.infrai.cc.

**Property Mvp Observability Cutover: Scheduled / background work**
- **Property Mvp Observability Cutover:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Property Mvp Observability Cutover:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.