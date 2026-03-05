Architecture générée
Structure du projet

gas-monitor/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI + WebSocket + seed DB
│   │   ├── config.py                # Variables d'environnement
│   │   ├── database.py              # SQLAlchemy engine
│   │   ├── models/                  # User, Device, Measurement, Alert, GasThreshold
│   │   ├── schemas/                 # Pydantic (user, measurement, alert)
│   │   ├── routers/                 # auth, users, devices, measurements, alerts, gateway
│   │   ├── services/
│   │   │   ├── ai_service.py        # Analyse IA (Z-score, tendances, score risque)
│   │   │   ├── processing_service.py # Pipeline gateway → stockage → alertes → WS
│   │   │   └── auth_service.py
│   │   └── core/
│   │       ├── security.py          # JWT, hashing, RBAC
│   │       └── websocket_manager.py # Broadcast temps-réel
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    └── src/
        ├── pages/
        │   ├── Login.tsx             # Auth avec comptes démo
        │   ├── WearerDashboard.tsx   # Vue porteur
        │   ├── DoctorDashboard.tsx   # Vue médecin (liste patients)
        │   └── SupervisorDashboard.tsx # Vue superviseur (équipe + seuils)
        ├── components/
        │   ├── GasGauges.tsx         # 6 jauges de gaz avec couleurs
        │   ├── GasChart.tsx          # Graphique Recharts avec seuils
        │   ├── AlertList.tsx         # Liste alertes avec acquittement
        │   ├── DeviceStatus.tsx      # Batterie, signal, firmware
        │   └── RiskScore.tsx         # Score IA radial 0-100
        └── api/client.ts             # Axios + WebSocket
Services IA (ai_service.py)
Détection de seuils : avertissement / critique par gaz
Anomalie statistique : Z-score sur une fenêtre glissante de 100 mesures
Analyse de tendance : régression linéaire → montant / descendant / stable
Score de risque global : 0–100 combinant les 6 gaz
API Gateway (gateway.py)
POST /gateway/ingest avec header X-API-Key
Payload BLE → stockage → IA → alertes → broadcast WebSocket
Pour démarrer

cd gas-monitor
cp backend/.env.example backend/.env
docker-compose up --build
Accès : http://localhost:3000

Rôle	Email	Mot de passe
Porteur	wearer@example.com	wearer123
Médecin	doctor@example.com	doctor123
Responsable	supervisor@example.com	supervisor123
API docs : http://localhost:8000/docs