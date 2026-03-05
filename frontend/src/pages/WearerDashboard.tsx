import { useState, useEffect, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Layout from "../components/Layout";
import GasGauges from "../components/GasGauges";
import GasChart from "../components/GasChart";
import AlertList from "../components/AlertList";
import DeviceStatus from "../components/DeviceStatus";
import RiskScore from "../components/RiskScore";
import { useAuth } from "../contexts/AuthContext";
import { createWebSocket, getMeasurements, getLatestMeasurement, getAlerts, getAIAnalysis, getThresholds, listDevices } from "../api/client";
import type { WsMessage } from "../types";
import { RefreshCw } from "lucide-react";

export default function WearerDashboard() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [selectedGas, setSelectedGas] = useState("co");
  const [liveAlert, setLiveAlert] = useState<string | null>(null);

  const { data: devices } = useQuery({ queryKey: ["devices"], queryFn: listDevices });
  const { data: latest } = useQuery({ queryKey: ["latest"], queryFn: () => getLatestMeasurement(), refetchInterval: 30_000 });
  const { data: measurements } = useQuery({ queryKey: ["measurements"], queryFn: () => getMeasurements({ limit: 100 }) });
  const { data: alerts } = useQuery({ queryKey: ["alerts"], queryFn: () => getAlerts({ limit: 50 }) });
  const { data: analysis } = useQuery({ queryKey: ["analysis"], queryFn: () => getAIAnalysis() });
  const { data: thresholds } = useQuery({ queryKey: ["thresholds"], queryFn: getThresholds });

  const unreadAlerts = alerts?.filter((a) => !a.acknowledged).length ?? 0;

  const handleWsMessage = useCallback(
    (raw: unknown) => {
      const msg = raw as WsMessage;
      if (msg.type !== "new_measurement") return;
      queryClient.invalidateQueries({ queryKey: ["latest"] });
      queryClient.invalidateQueries({ queryKey: ["measurements"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["analysis"] });
      if (msg.alerts?.length) {
        setLiveAlert(msg.alerts[0].message);
        setTimeout(() => setLiveAlert(null), 6000);
      }
    },
    [queryClient]
  );

  useEffect(() => {
    if (!token) return;
    const ws = createWebSocket(token, handleWsMessage);
    return () => ws.close();
  }, [token, handleWsMessage]);

  return (
    <Layout title="Mon tableau de bord" unreadAlerts={unreadAlerts}>
      {/* Live alert toast */}
      {liveAlert && (
        <div className="fixed top-20 right-4 z-50 bg-red-900 border border-red-700 text-red-100 text-sm rounded-lg px-4 py-3 shadow-xl max-w-sm animate-bounce">
          {liveAlert}
        </div>
      )}

      <div className="space-y-6">
        {/* Gas readings */}
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Concentrations actuelles
          </h2>
          <GasGauges
            measurement={latest}
            thresholds={thresholds}
            analysis={analysis}
            selectedGas={selectedGas}
            onSelectGas={setSelectedGas}
          />
        </div>

        {/* Chart + Risk score */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                Historique — {selectedGas.toUpperCase()}
              </h2>
              <button
                onClick={() => queryClient.invalidateQueries({ queryKey: ["measurements"] })}
                className="text-gray-600 hover:text-gray-300 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
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

        {/* Device status + Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DeviceStatus device={devices?.[0]} latest={latest} />

          <div className="card">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Alertes récentes
            </h2>
            <div className="max-h-72 overflow-y-auto pr-1 space-y-2">
              <AlertList alerts={alerts ?? []} queryKey={["alerts"]} />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
