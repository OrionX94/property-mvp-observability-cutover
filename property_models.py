from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MaintenanceRequest(BaseModel):
    request_id: str
    category: Literal["water_leak", "hvac", "lockout", "cosmetic", "appliance"]
    summary: str
    hours_open: int = Field(ge=0)
    has_active_leak: bool = False


class TenantDocument(BaseModel):
    document_id: str
    document_type: Literal["lease", "id", "income_proof"]
    status: Literal["uploaded", "blurry", "missing_signature"]
    days_until_move_in: int


class InspectionReminder(BaseModel):
    reminder_id: str
    inspection_type: Literal["move_in", "move_out", "quarterly"]
    days_until_due: int
    tenant_confirmed: bool = False


class PortfolioEvent(BaseModel):
    property_id: str
    tenant_id: str
    maintenance_request: MaintenanceRequest | None = None
    tenant_document: TenantDocument | None = None
    inspection_reminder: InspectionReminder | None = None

    @model_validator(mode="after")
    def validate_single_payload(self) -> "PortfolioEvent":
        present = [
            self.maintenance_request is not None,
            self.tenant_document is not None,
            self.inspection_reminder is not None,
        ]
        if sum(present) != 1:
            raise ValueError("exactly one event payload must be provided")
        return self


class ActionDecision(BaseModel):
    event_type: Literal["maintenance_request", "tenant_document", "inspection_reminder"]
    action: str
    severity: Literal["info", "warning", "critical"]
    reason: str
