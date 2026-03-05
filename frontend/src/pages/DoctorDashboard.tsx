import { useState, useEffect, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Layout from "../components/Layout";
import GasGauges from "../components/GasGauges";
import GasChart from "../components/GasChart";
import AlertList from "../components/AlertList";
import DeviceStatus from "../components/DeviceStatus";
import RiskScore from "../components/RiskScore";
import { useAuth } from "../contexts/AuthContext";
import {
  createWebSocket,
  listUsers,
  listDevices,
  getMeasurements,
  getLatestMeasurement,
  getAlerts,
  getAIAnalysis,
  getThresholds,
} from "../api/client";
import type { User, WsMessage } from "../types";
import { Users, ChevronRight } from "lucide-react";

export default function DoctorDashboard() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [selectedPatient, setSelectedPatient] = useState<User | null>(null);
  const [selectedGas, setSelectedGas] = useState("co");

  const { data: patients } = useQuery({ queryKey: ["patients"], queryFn: listUsers });
  const { data: devices } = useQuery({ queryKey: ["devices"], queryFn: listDevices });
  const { data: thresholds } = useQuery({ queryKey: ["thresholds"], queryFn: getThresholds });

  const patientId = selectedPatient?.id;
  const { data: latest } = useQuery({
    queryKey: ["latest", patientId],
    queryFn: () => getLatestMeasurement(patientId),
    enabled: patientId != null,
    refetchInterval: 30_000,
  });
  const { data: measurements } = useQuery({
    queryKey: ["measurements", patientId],
    queryFn: () => getMeasurements({ wearer_id: patientId, limit: 100 }),
    enabled: patientId != null,
  });
  const { data: alerts } = useQuery({
    queryKey: ["alerts", patientId],
    queryFn: () => getAlerts({ wearer_id: patientId, limit: 50 }),
    enabled: patientId != null,
  });
  const { data: analysis } = useQuery({
    queryKey: ["analysis", patientId],
    queryFn: () => getAIAnalysis(patientId),
    enabled: patientId != null,
  });

  const allAlerts = useQuery({ queryKey: ["all-alerts"], queryFn: () => getAlerts({ limit: 200 }) });
  const unread = allAlerts.data?.filter((a) => !a.acknowledged).length ?? 0;

  const handleWsMessage = useCallback(
    (raw: unknown) => {
      const msg = raw as WsMessage;
      if (msg.type !== "new_measurement") return;
      queryClient.invalidateQueries({ queryKey: ["latest", msg.wearer_id] });
      queryClient.invalidateQueries({ queryKey: ["measurements", msg.wearer_id] });
      queryClient.invalidateQueries({ queryKey: ["alerts", msg.wearer_id] });
      queryClient.invalidateQueries({ queryKey: ["analysis", msg.wearer_id] });
      queryClient.invalidateQueries({ queryKey: ["all-alerts"] });
    },
    [queryClient]
  );

  useEffect(() => {
    if (!token) return;
    const ws = createWebSocket(token, handleWsMessage);
    return () => ws.close();
  }, [token, handleWsMessage]);

  // Auto-select first patient
  useEffect(() => {
    if (patients?.length && !selectedPatient) setSelectedPatient(patients[0]);
  }, [patients, selectedPatient]);

  const patientDevice = devices?.find((d) => d.user_id === patientId);

  return (
    <Layout title="Suivi patients" unreadAlerts={unread}>
      <div className="flex gap-6 h-full">
        {/* Patient list sidebar */}
        <aside className="w-56 flex-shrink-0">
          <div className="card h-fit sticky top-24">
            <div className="flex items-center gap-2 mb-4">
              <Users className="w-4 h-4 text-gray-500" />
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                Patients ({patients?.length ?? 0})
              </h2>
            </div>
            <div className="space-y-1">
              {patients?.map((p) => {
                const pAlerts = allAlerts.data?.filter((a) => {
                  const d = devices?.find((dev) => dev.id === a.device_id);
                  return d?.user_id === p.id && !a.acknowledged;
                });
                return (
                  <button
                    key={p.id}
                    onClick={() => setSelectedPatient(p)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors flex items-center justify-between group ${
                      selectedPatient?.id === p.id
                        ? "bg-blue-600/20 text-white border border-blue-700"
                        : "text-gray-400 hover:bg-gray-800 hover:text-white"
                    }`}
                  >
                    <span className="text-sm truncate">{p.full_name}</span>
                    <div className="flex items-center gap-1">
                      {pAlerts && pAlerts.length > 0 && (
                        <span className="bg-red-600 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                          {pAlerts.length}
                        </span>
                      )}
                      <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100" />
                    </div>
                  </button>
                );
              })}
              {!patients?.length && (
                <p className="text-xs text-gray-600 py-2">Aucun patient assigné</p>
              )}
            </div>
          </div>
        </aside>

        {/* Main content */}
        {selectedPatient ? (
          <div className="flex-1 min-w-0 space-y-6">
            <div>
              <h1 className="text-xl font-bold text-white">{selectedPatient.full_name}</h1>
              <p className="text-sm text-gray-500">{selectedPatient.email}</p>
            </div>

            {/* Gauges */}
            <GasGauges
              measurement={latest}
              thresholds={thresholds}
              analysis={analysis}
              selectedGas={selectedGas}
              onSelectGas={setSelectedGas}
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 card">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                  Historique — {selectedGas.toUpperCase()}
                </h2>
                <GasChart
                  measurements={measurements ?? []}
                  thresholds={thresholds}
                  selectedGas={selectedGas}
                />
              </div>
              <RiskScore
                score={latest?.risk_score ?? analysis?.risk_score}
                recommendations={analysis?.recommendations}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <DeviceStatus device={patientDevice} latest={latest} />
              <div className="card">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                  Alertes du patient
                </h2>
                <div className="max-h-72 overflow-y-auto pr-1">
                  <AlertList alerts={alerts ?? []} queryKey={["alerts", patientId ?? 0]} />
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-600">
            Sélectionnez un patient
          </div>
        )}
      </div>
    </Layout>
  );
}
