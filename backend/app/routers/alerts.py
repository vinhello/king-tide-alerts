from dataclasses import asdict

from fastapi import APIRouter

from app.schemas.alerts import NwsAlertOut, NwsAlertsResponse
from app.services import nws

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/nws", response_model=NwsAlertsResponse)
async def nws_alerts():
    """Active NWS coastal flood products for the path's zones, quoted verbatim.

    Empty when nothing is in effect or NWS cannot be reached.
    """
    alerts = await nws.get_coastal_flood_alerts()
    return NwsAlertsResponse(
        alerts=[NwsAlertOut(**asdict(alert)) for alert in alerts],
        zones=nws.zones(),
    )
