import axios from "axios";
import type {
  User,
  Device,
  Measurement,
  Alert,
  AIAnalysis,
  GasThreshold,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// Auth
export const login = async (email: string, password: string) => {
  const form = new URLSearchParams({ username: email, password });
  const { data } = await api.post("/auth/token", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data as { access_token: string; token_type: string; user: User };
};

// Users
export const getMe = () => api.get<User>("/users/me").then((r) => r.data);
export const listUsers = () => api.get<User[]>("/users/").then((r) => r.data);
export const getUser = (id: number) =>
  api.get<User>(`/users/${id}`).then((r) => r.data);
export const assignPatient = (doctorId: number, patientId: number) =>
  api.post(`/users/${doctorId}/patients/${patientId}`);

// Devices
export const listDevices = () =>
  api.get<Device[]>("/devices/").then((r) => r.data);

// Measurements
export const getMeasurements = (params?: {
  wearer_id?: number;
  device_id?: number;
  from_dt?: string;
  to_dt?: string;
  limit?: number;
}) => api.get<Measurement[]>("/measurements/", { params }).then((r) => r.data);

export const getLatestMeasurement = (wearer_id?: number) =>
  api
    .get<Measurement | null>("/measurements/latest", {
      params: wearer_id ? { wearer_id } : {},
    })
    .then((r) => r.data);

export const getAIAnalysis = (wearer_id?: number) =>
  api
    .get<AIAnalysis>("/measurements/analysis", {
      params: wearer_id ? { wearer_id } : {},
    })
    .then((r) => r.data);

// Alerts
export const getAlerts = (params?: {
  wearer_id?: number;
  unacknowledged_only?: boolean;
  limit?: number;
}) => api.get<Alert[]>("/alerts/", { params }).then((r) => r.data);

export const acknowledgeAlert = (id: number) =>
  api.patch<Alert>(`/alerts/${id}/acknowledge`, { acknowledged: true }).then((r) => r.data);

export const getThresholds = () =>
  api.get<GasThreshold[]>("/alerts/thresholds").then((r) => r.data);

export const updateThreshold = (
  gas_type: string,
  payload: { warning_level: number; critical_level: number }
) =>
  api
    .patch<GasThreshold>(`/alerts/thresholds/${gas_type}`, payload)
    .then((r) => r.data);

// WebSocket
export function createWebSocket(token: string, onMessage: (data: unknown) => void): WebSocket {
  const wsBase = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";
  const ws = new WebSocket(`${wsBase}/ws?token=${token}`);
  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data));
    } catch {
      // ignore non-JSON frames
    }
  };
  // Heartbeat
  const hb = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) ws.send("ping");
  }, 30000);
  ws.onclose = () => clearInterval(hb);
  return ws;
}

export default api;
