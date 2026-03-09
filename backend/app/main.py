from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .config import settings
from .core.security import decode_token
from .core.websocket_manager import manager
from .routers import auth, users, devices, measurements, alerts, gateway
from .models import User, UserRole, Device, GasThreshold
from .models.alert import GasThreshold
from .services.ai_service import DEFAULT_THRESHOLDS
from .core.security import hash_password

app = FastAPI(
    title="Gas Monitor API",
    description="Surveillance de gaz en temps réel — backend principal",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(devices.router)
app.include_router(measurements.router)
app.include_router(alerts.router)
app.include_router(gateway.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _seed_initial_data()


def _seed_initial_data():
    db = next(get_db())
    try:
        # Seed gas thresholds
        for gas, defaults in DEFAULT_THRESHOLDS.items():
            if not db.query(GasThreshold).filter(GasThreshold.gas_type == gas).first():
                db.add(GasThreshold(gas_type=gas, **defaults))

        # Seed demo users if none exist
        if not db.query(User).first():
            supervisor = User(
                email="supervisor@example.com",
                hashed_password=hash_password("supervisor123"),
                full_name="Marie Dupont",
                role=UserRole.supervisor,
            )
            db.add(supervisor)
            db.flush()

            doctor = User(
                email="doctor@example.com",
                hashed_password=hash_password("doctor123"),
                full_name="Dr. Jean Martin",
                role=UserRole.doctor,
            )
            db.add(doctor)
            db.flush()

            wearer = User(
                email="wearer@example.com",
                hashed_password=hash_password("wearer123"),
                full_name="Paul Lefebvre",
                role=UserRole.wearer,
                supervisor_id=supervisor.id,
            )
            db.add(wearer)
            db.flush()

            # Assign doctor -> patient
            doctor.patients.append(wearer)

            # Create a demo device
            device = Device(
                device_uid="DEMO-001",
                name="Capteur Démo",
                firmware_version="1.0.0",
                user_id=wearer.id,
            )
            db.add(device)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seed error (non-fatal): {e}")
    finally:
        db.close()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket for real-time updates.
    Connect with: ws://host/ws?token=<jwt>
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
        user_id = int(user_id)
    except HTTPException:
        await websocket.close(code=4001)
        return
    except (ValueError, TypeError):
        await websocket.close(code=4001)
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


@app.get("/health")
def health():
    return {"status": "ok"}
