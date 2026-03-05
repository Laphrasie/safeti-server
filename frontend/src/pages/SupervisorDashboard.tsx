import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  updateThreshold,
} from "../api/client";
import type { User, WsMessage, GasThreshold } from "../types";
import { GAS_META } from "../types";
import { Users, ChevronRight, Settings, ShieldAlert, Activity } from "lucide-react";

type Tab = "overview" | "worker" | "thresholds";

function ThresholdEditor({ thresholds }: { thresholds: GasThreshold[] }) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Record<string, { warning: string; critical: string }>>({});

  const { mutate: save } = useMutation({
    mutationFn: ({ gas, w, c }: { gas: string; w: number; c: number }) =>
      updateThreshold(gas, { warning_level: w, critical_level: c }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["thresholds"] }),
  });

  return (
    <div className="card">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
        Seuils d'alerte
      </h2>
      <div className="space-y-3">
        {thresholds.map((t) => {
          const meta = GAS_META[t.gas_type];
          const e = editing[t.gas_type];
          return (
            <div key={t.gas_type} className="flex items-center gap-4 p-3 bg-gray-800/50 rounded-lg">
              <span
                className="w-10 text-sm font-bold text-center"
                style={{ color: meta?.color ?? "#fff" }}
              >
                {meta?.label ?? t.gas_type.toUpperCase()}
              </span>
              <div className="flex-1 grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-yellow-500 mb-1 block">Avertissement ({t.unit})</label>
                  <input
                    type="number"
                    defaultValue={t.warning_level}
                    onChange={(ev) =>
                      setEditing((prev) => ({
                        ...prev,
                        [t.gas_type]: { warning: ev.target.value, critical: e?.critical ?? String(t.critical_level) },
                      }))
                    }
                    className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-white text-sm focus:outline-none focus:border-yellow-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-red-500 mb-1 block">Critique ({t.unit})</label>
                  <input
                    type="number"
                    defaultValue={t.critical_level}
                    onChange={(ev) =>
                      setEditing((prev) => ({
                        ...prev,
                        [t.gas_type]: { warning: e?.warning ?? String(t.warning_level), critical: ev.target.value },
                      }))
                    }
                    className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-white text-sm focus:outline-none focus:border-red-500"
                  />
                </div>
              </div>
              <button
                onClick={() => {
                  const w = parseFloat(e?.warning ?? String(t.warning_level));
                  const c = parseFloat(e?.critical ?? String(t.critical_level));
                  save({ gas: t.gas_type, w, c });
                }}
                className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded transition-colors"
              >
                Sauver
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function WorkerCard({
  worker,
  onSelect,
  isSelected,
  alertCount,
  riskScore,
}: {
  worker: User;
  onSelect: () => void;
  isSelected: boolean;
  alertCount: number;
  riskScore?: number | null;
}) {
  const riskColor =
    (riskScore ?? 0) >= 80 ? "text-red-400" : (riskScore ?? 0) >= 50 ? "text-yellow-400" : "text-green-400";

  return (
    <button
      onClick={onSelect}
      className={`card text-left w-full transition-all hover:border-gray-600 ${
        isSelected ? "ring-2 ring-blue-500 ring-offset-2 ring-offset-gray-950" : ""
      }`}
    >
      <div className="flex justify-between items-start">
        <div>
          <p className="font-medium text-white text-sm">{worker.full_name}</p>
          <p className="text-xs text-gray-500 mt-0.5">{worker.email}</p>
        </div>
        {alertCount > 0 && (
          <span className="bg-red-600 text-white text-xs font-bold rounded-full px-2 py-0.5">
            {alertCount}
          </span>
        )}
      </div>
      <div className="flex items-center justify-between mt-3">
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <Activity className="w-3.5 h-3.5" />
          <span>Risque</span>
        </div>
        <span className={`text-sm font-bold ${riskColor}`}>
          {riskScore != null ? `${riskScore.toFixed(0)}/100` : "—"}
        </span>
      </div>
    </button>
  );
}

export default function SupervisorDashboard() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("overview");
  const [selectedWorker, setSelectedWorker] = useState<User | null>(null);
  const [selectedGas, setSelectedGas] = useState("co");

  const { data: workers } = useQuery({ queryKey: ["workers"], queryFn: listUsers });
  const { data: devices } = useQuery({ queryKey: ["devices"], queryFn: listDevices });
  const { data: thresholds } = useQuery({ queryKey: ["thresholds"], queryFn: getThresholds });

  const allAlerts = useQuery({ queryKey: ["all-alerts"], queryFn: () => getAlerts({ limit: 500 }) });
  const unread = allAlerts.data?.filter((a) => !a.acknowledged).length ?? 0;

  const workerId = selectedWorker?.id;
  const { data: latest } = useQuery({
    queryKey: ["latest", workerId],
    queryFn: () => getLatestMeasurement(workerId),
    enabled: workerId != null && tab === "worker",
    refetchInterval: 30_000,
  });
  const { data: measurements } = useQuery({
    queryKey: ["measurements", workerId],
    queryFn: () => getMeasurements({ wearer_id: workerId, limit: 100 }),
    enabled: workerId != null && tab === "worker",
  });
  const { data: workerAlerts } = useQuery({
    queryKey: ["alerts", workerId],
    queryFn: () => getAlerts({ wearer_id: workerId }),
    enabled: workerId != null && tab === "worker",
  });
  const { data: analysis } = useQuery({
    queryKey: ["analysis", workerId],
    queryFn: () => getAIAnalysis(workerId),
    enabled: workerId != null && tab === "worker",
  });

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

  useEffect(() => {
    if (workers?.length && !selectedWorker) setSelectedWorker(workers[0]);
  }, [workers, selectedWorker]);

  const workerDevice = devices?.find((d) => d.user_id === workerId);

  const getWorkerAlertCount = (w: User) =>
    allAlerts.data?.filter((a) => {
      const d = devices?.find((dev) => dev.id === a.device_id);
      return d?.user_id === w.id && !a.acknowledged;
    }).length ?? 0;

  const getWorkerRisk = (w: User) => {
    const d = devices?.find((dev) => dev.user_id === w.id);
    if (!d) return null;
    return null;
  };

  return (
    <Layout title="Supervision" unreadAlerts={unread}>
      {/* Tab bar */}
      <div className="flex gap-1 mb-6 bg-gray-900 rounded-xl p-1 w-fit">
        {(
          [
            { id: "overview", label: "Vue d'ensemble", icon: Users },
            { id: "worker", label: "Détail travailleur", icon: Activity },
            { id: "thresholds", label: "Seuils", icon: Settings },
          ] as const
        ).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === id
                ? "bg-blue-600 text-white"
                : "text-gray-400 hover:text-white hover:bg-gray-800"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Overview tab */}
      {tab === "overview" && (
        <div className="space-y-6">
          {/* Summary stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="card text-center">
              <p className="text-3xl font-bold text-white">{workers?.length ?? 0}</p>
              <p className="text-xs text-gray-500 mt-1">Travailleurs</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-green-400">{devices?.filter((d) => d.is_active).length ?? 0}</p>
              <p className="text-xs text-gray-500 mt-1">Capteurs actifs</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-yellow-400">{unread}</p>
              <p className="text-xs text-gray-500 mt-1">Alertes non lues</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-red-400">
                {allAlerts.data?.filter((a) => a.level === "critical" && !a.acknowledged).length ?? 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">Critiques</p>
            </div>
          </div>

          {/* Workers grid */}
          <div>
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Travailleurs
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {workers?.map((w) => (
                <WorkerCard
                  key={w.id}
                  worker={w}
                  onSelect={() => { setSelectedWorker(w); setTab("worker"); }}
                  isSelected={selectedWorker?.id === w.id}
                  alertCount={getWorkerAlertCount(w)}
                  riskScore={getWorkerRisk(w)}
                />
              ))}
            </div>
          </div>

          {/* Recent critical alerts */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <ShieldAlert className="w-4 h-4 text-red-400" />
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                Alertes critiques récentes
              </h2>
            </div>
            <div className="max-h-64 overflow-y-auto">
              <AlertList
                alerts={(allAlerts.data ?? []).filter((a) => a.level === "critical").slice(0, 20)}
                queryKey={["all-alerts"]}
              />
            </div>
          </div>
        </div>
      )}

      {/* Worker detail tab */}
      {tab === "worker" && (
        <div className="flex gap-6">
          <aside className="w-56 flex-shrink-0">
            <div className="card h-fit sticky top-24">
              <div className="flex items-center gap-2 mb-4">
                <Users className="w-4 h-4 text-gray-500" />
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                  Équipe
                </h2>
              </div>
              <div className="space-y-1">
                {workers?.map((w) => (
                  <button
                    key={w.id}
                    onClick={() => setSelectedWorker(w)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors flex items-center justify-between ${
                      selectedWorker?.id === w.id
                        ? "bg-blue-600/20 text-white border border-blue-700"
                        : "text-gray-400 hover:bg-gray-800 hover:text-white"
                    }`}
                  >
                    <span className="text-sm truncate">{w.full_name}</span>
                    <div className="flex items-center gap-1">
                      {getWorkerAlertCount(w) > 0 && (
                        <span className="bg-red-600 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                          {getWorkerAlertCount(w)}
                        </span>
                      )}
                      <ChevronRight className="w-3.5 h-3.5" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </aside>

          {selectedWorker ? (
            <div className="flex-1 min-w-0 space-y-6">
              <div>
                <h1 className="text-xl font-bold text-white">{selectedWorker.full_name}</h1>
                <p className="text-sm text-gray-500">{selectedWorker.email}</p>
              </div>
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
                  <GasChart measurements={measurements ?? []} thresholds={thresholds} selectedGas={selectedGas} />
                </div>
                <RiskScore score={latest?.risk_score ?? analysis?.risk_score} recommendations={analysis?.recommendations} />
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <DeviceStatus device={workerDevice} latest={latest} />
                <div className="card">
                  <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                    Alertes
                  </h2>
                  <div className="max-h-72 overflow-y-auto">
                    <AlertList alerts={workerAlerts ?? []} queryKey={["alerts", workerId ?? 0]} />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-600">
              Sélectionnez un travailleur
            </div>
          )}
        </div>
      )}

      {/* Thresholds tab */}
      {tab === "thresholds" && (
        <div className="max-w-2xl">
          {thresholds && <ThresholdEditor thresholds={thresholds} />}
        </div>
      )}
    </Layout>
  );
}
