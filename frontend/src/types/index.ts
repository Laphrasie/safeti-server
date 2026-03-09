export type UserRole = "wearer" | "doctor" | "supervisor";
export type AlertLevel = "warning" | "critical" | "anomaly";
export type TrendDirection = "rising" | "falling" | "stable" | "n/a";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  supervisor_id: number | null;
}

export interface Device {
  id: number;
  device_uid: string;
  name: string;
  firmware_version: string | null;
  is_active: boolean;
  last_seen: string | null;
  battery_level: number | null;
  user_id: number;
}

export interface Measurement {
  id: number;
  device_id: number;
  timestamp: string;
  hcn: number | null;
  h2s: number | null;
  co: number | null;
  ch2o: number | null;
  c3h4o: number | null;
  voc: number | null;
  battery_level: number | null;
  signal_strength: number | null;
  log: string | null;
  risk_score: number | null;
  anomaly_detected: number | null;
}

export interface Alert {
  id: number;
  device_id: number;
  measurement_id: number | null;
  timestamp: string;
  gas_type: string;
  value: number | null;
  threshold: number | null;
  level: AlertLevel;
  message: string;
  acknowledged: boolean;
  acknowledged_by: number | null;
  acknowledged_at: string | null;
}

export interface AIAnalysis {
  risk_score: number;
  anomaly_flags: Record<string, boolean>;
  trends: Record<string, TrendDirection>;
  recommendations: string[];
}

export interface GasThreshold {
  id: number;
  gas_type: string;
  unit: string;
  warning_level: number;
  critical_level: number;
}

export interface WsMessage {
  type: "new_measurement";
  device_uid: string;
  wearer_id: number;
  measurement: Measurement;
  alerts: { gas_type: string; level: AlertLevel; message: string }[];
  trends: Record<string, TrendDirection>;
  recommendations: string[];
}

export const GAS_META: Record<
  string,
  { label: string; unit: string; color: string }
> = {
  hcn:  { label: "HCN",   unit: "ppm", color: "#f97316" },
  h2s: { label: "H₂S",  unit: "ppm", color: "#3b82f6" },
  co: { label: "CO",  unit:"ppm", color: "#a855f7" },
  ch2o:  { label: "CH₂O",   unit: "ppm", color: "#06b6d4" },
  c3h4o: { label: "C₃H₄O",  unit: "ppm", color: "#eab308" },
  voc: { label: "VOC",  unit: "ppm", color: "#ec4899" },
};
