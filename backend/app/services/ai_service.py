"""
AI/ML processing service for gas measurements.
Implements:
  - Threshold-based alerting
  - Statistical anomaly detection (Z-score on a rolling window)
  - Trend analysis (linear regression)
  - Composite risk scoring
"""
from typing import Optional
import numpy as np
from sqlalchemy.orm import Session
from ..models.measurement import Measurement
from ..models.alert import GasThreshold

GAS_FIELDS = ["hcn", 
              "h2s", 
              "co", 
              "ch2o", 
              "c3h4o", 
              "voc"]

# Anomaly bit positions per gas (for the bitmask stored in measurement.anomaly_detected)
GAS_BITS = {gas: (1 << i) for i, gas in enumerate(GAS_FIELDS)}

# Default thresholds used if none are found in DB
DEFAULT_THRESHOLDS = {
    "hcn":  {"unit": "ppm",  "warning_level": 25.0,   "critical_level": 100.0},
    "h2s": {"unit": "ppm",  "warning_level": 1000.0, "critical_level": 5000.0},
    "co": {"unit": "ppm",  "warning_level": 200.0,  "critical_level": 1000.0},
    "ch2o":  {"unit": "ppm",  "warning_level": 100.0,  "critical_level": 300.0},
    "c3h4o": {"unit": "ppm",  "warning_level": 500.0,  "critical_level": 2000.0},
    "voc": {"unit": "ppm",  "warning_level": 1000.0, "critical_level": 5000.0},
}

ROLLING_WINDOW = 100  # number of past measurements used for statistics


def get_thresholds(db: Session) -> dict:
    thresholds = {}
    for gas, defaults in DEFAULT_THRESHOLDS.items():
        row = db.query(GasThreshold).filter(GasThreshold.gas_type == gas).first()
        if row:
            thresholds[gas] = {
                "unit": row.unit,
                "warning_level": row.warning_level,
                "critical_level": row.critical_level,
            }
        else:
            thresholds[gas] = defaults
    return thresholds


def fetch_recent_values(db: Session, device_id: int, gas: str, limit: int = ROLLING_WINDOW) -> list[float]:
    rows = (
        db.query(Measurement)
        .filter(
            Measurement.device_id == device_id,
            getattr(Measurement, gas).isnot(None),
        )
        .order_by(Measurement.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [float(getattr(r, gas)) for r in reversed(rows)]


def detect_anomaly_zscore(values: list[float], z_threshold: float = 3.0) -> bool:
    """Return True if the last value is a statistical outlier."""
    if len(values) < 10:
        return False
    arr = np.array(values[:-1])
    mean, std = arr.mean(), arr.std()
    if std < 1e-9:
        return False
    z = abs(values[-1] - mean) / std
    return z > z_threshold


def analyze_trend(values: list[float]) -> str:
    """Linear regression on the series. Returns 'rising', 'falling', or 'stable'."""
    if len(values) < 5:
        return "stable"
    x = np.arange(len(values), dtype=float)
    y = np.array(values, dtype=float)
    slope = np.polyfit(x, y, 1)[0]
    # Relative slope
    mean_val = y.mean() if y.mean() != 0 else 1.0
    rel_slope = slope / abs(mean_val)
    if rel_slope > 0.02:
        return "rising"
    if rel_slope < -0.02:
        return "falling"
    return "stable"


def compute_risk_score(measurement: Measurement, thresholds: dict) -> float:
    """
    Compute a composite risk score 0-100.
    Each gas contributes proportionally to its proximity to critical level.
    """
    scores = []
    for gas in GAS_FIELDS:
        value = getattr(measurement, gas)
        if value is None:
            continue
        t = thresholds.get(gas, {})
        warning = t.get("warning_level", 1)
        critical = t.get("critical_level", 2)
        if value <= warning:
            score = (value / warning) * 30.0  # 0-30 in safe zone
        elif value <= critical:
            score = 30.0 + ((value - warning) / (critical - warning)) * 50.0  # 30-80
        else:
            score = min(100.0, 80.0 + ((value - critical) / critical) * 20.0)  # 80-100
        scores.append(score)
    return round(sum(scores) / len(scores), 2) if scores else 0.0


def run_analysis(db: Session, measurement: Measurement) -> dict:
    """
    Full analysis pipeline for a new measurement.
    Returns a dict with:
      - alerts: list of alert dicts to create
      - risk_score: float
      - anomaly_detected: int (bitmask)
      - trends: dict
      - anomaly_flags: dict
    """
    thresholds = get_thresholds(db)
    alerts_to_create = []
    anomaly_bitmask = 0
    anomaly_flags = {}
    trends = {}

    for gas in GAS_FIELDS:
        value = getattr(measurement, gas)
        if value is None:
            trends[gas] = "n/a"
            anomaly_flags[gas] = False
            continue

        t = thresholds[gas]
        history = fetch_recent_values(db, measurement.device_id, gas)
        history.append(value)  # include current reading

        # Trend
        trends[gas] = analyze_trend(history)

        # Anomaly
        is_anomaly = detect_anomaly_zscore(history)
        anomaly_flags[gas] = is_anomaly
        if is_anomaly:
            anomaly_bitmask |= GAS_BITS[gas]

        # Threshold alerts
        if value >= t["critical_level"]:
            alerts_to_create.append({
                "gas_type": gas,
                "value": value,
                "threshold": t["critical_level"],
                "level": "critical",
                "message": (
                    f"Niveau critique de {gas.upper()} : {value:.2f} {t['unit']} "
                    f"(seuil : {t['critical_level']} {t['unit']})"
                ),
            })
        elif value >= t["warning_level"]:
            alerts_to_create.append({
                "gas_type": gas,
                "value": value,
                "threshold": t["warning_level"],
                "level": "warning",
                "message": (
                    f"Niveau d'avertissement de {gas.upper()} : {value:.2f} {t['unit']} "
                    f"(seuil : {t['warning_level']} {t['unit']})"
                ),
            })
        elif is_anomaly:
            alerts_to_create.append({
                "gas_type": gas,
                "value": value,
                "threshold": None,
                "level": "anomaly",
                "message": (
                    f"Anomalie statistique détectée pour {gas.upper()} : "
                    f"valeur {value:.2f} {t['unit']} significativement hors norme"
                ),
            })

    risk_score = compute_risk_score(measurement, thresholds)

    # Global risk alert
    if risk_score >= 80:
        alerts_to_create.append({
            "gas_type": "risk",
            "value": risk_score,
            "threshold": 80.0,
            "level": "critical",
            "message": f"Score de risque global critique : {risk_score:.1f}/100",
        })
    elif risk_score >= 50:
        alerts_to_create.append({
            "gas_type": "risk",
            "value": risk_score,
            "threshold": 50.0,
            "level": "warning",
            "message": f"Score de risque global élevé : {risk_score:.1f}/100",
        })

    # Build recommendations
    recommendations = []
    if any(a["level"] == "critical" for a in alerts_to_create):
        recommendations.append("Quitter immédiatement la zone exposée.")
        recommendations.append("Alerter le responsable de sécurité.")
    elif any(a["level"] == "warning" for a in alerts_to_create):
        recommendations.append("Augmenter la ventilation de la zone.")
        recommendations.append("Surveiller l'évolution des concentrations.")
    if anomaly_bitmask:
        recommendations.append("Des variations inhabituelles ont été détectées — vérifier l'équipement.")

    return {
        "alerts": alerts_to_create,
        "risk_score": risk_score,
        "anomaly_detected": anomaly_bitmask,
        "trends": trends,
        "anomaly_flags": anomaly_flags,
        "recommendations": recommendations,
    }
