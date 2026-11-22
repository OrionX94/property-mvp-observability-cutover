from property_models import PortfolioEvent
from property_observability_service import process_portfolio_event


def main() -> None:
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
    decision = process_portfolio_event(event)
    print({
        "event_type": decision.event_type,
        "action": decision.action,
        "severity": decision.severity,
        "reason": decision.reason,
    })


if __name__ == "__main__":
    main()
