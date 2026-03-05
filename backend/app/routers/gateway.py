"""
Endpoint consumed by BLE gateways to push device data.
Authentication: static API key passed in the X-API-Key header.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import settings
from ..schemas.measurement import GatewayPayload, MeasurementOut
from ..services.processing_service import process_gateway_payload

router = APIRouter(prefix="/gateway", tags=["gateway"])


def verify_gateway_key(x_api_key: str = Header(...)):
    if x_api_key != settings.GATEWAY_API_KEY:
        raise HTTPException(status_code=403, detail="Clé API invalide")


@router.post("/ingest", response_model=MeasurementOut, status_code=201)
async def ingest(
    payload: GatewayPayload,
    db: Session = Depends(get_db),
    _: None = Depends(verify_gateway_key),
):
    """
    Called by the BLE gateway after collecting a measurement from the device.
    Triggers storage + AI analysis + alert creation + WebSocket broadcast.
    """
    try:
        measurement = await process_gateway_payload(payload, db)
        return measurement
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
