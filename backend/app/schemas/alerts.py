from pydantic import BaseModel


class NwsAlertOut(BaseModel):
    """One National Weather Service product, wording passed through verbatim."""

    id: str
    event: str
    severity: str
    headline: str
    what: str
    where: str
    when: str
    impacts: str
    additional_details: str
    instruction: str
    onset: str
    ends: str
    sent: str
    sender_name: str
    zones: list[str]
    link: str


class NwsAlertsResponse(BaseModel):
    alerts: list[NwsAlertOut]
    zones: list[str]
