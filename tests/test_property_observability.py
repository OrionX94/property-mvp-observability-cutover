from property_models import PortfolioEvent
from property_observability_service import decide_action


def test_active_water_leak_dispatches_now() -> None:
    event = PortfolioEvent(
        property_id="prop-17",
        tenant_id="tenant-9",
        maintenance_request={
            "request_id": "mr-1001",
            "category": "water_leak",
            "summary": "Water under kitchen sink",
            "hours_open": 3,
            "has_active_leak": True,
        },
    )

    decision = decide_action(event)

    assert decision.event_type == "maintenance_request"
    assert decision.action == "dispatch_now"
    assert decision.severity == "critical"
    assert decision.reason == "active water leak can damage units quickly"
