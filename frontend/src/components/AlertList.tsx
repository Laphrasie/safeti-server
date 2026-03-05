import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { CheckCircle, AlertTriangle, XCircle, Zap } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { Alert } from "../types";
import { acknowledgeAlert } from "../api/client";

interface Props {
  alerts: Alert[];
  queryKey?: (string | number)[];
}

const LEVEL_CONFIG = {
  warning: {
    icon: AlertTriangle,
    color: "text-yellow-400",
    bg: "bg-yellow-950/30 border-yellow-900",
    badge: "badge-warning",
    label: "Avertissement",
  },
  critical: {
    icon: XCircle,
    color: "text-red-400",
    bg: "bg-red-950/30 border-red-900",
    badge: "badge-critical",
    label: "Critique",
  },
  anomaly: {
    icon: Zap,
    color: "text-purple-400",
    bg: "bg-purple-950/30 border-purple-900",
    badge: "badge-anomaly",
    label: "Anomalie",
  },
};

export default function AlertList({ alerts, queryKey }: Props) {
  const queryClient = useQueryClient();
  const { mutate: ack } = useMutation({
    mutationFn: acknowledgeAlert,
    onSuccess: () => {
      if (queryKey) queryClient.invalidateQueries({ queryKey });
    },
  });

  if (!alerts.length) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-gray-600">
        <CheckCircle className="w-10 h-10 mb-2 text-green-700" />
        <p className="text-sm">Aucune alerte</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert) => {
        const config = LEVEL_CONFIG[alert.level] ?? LEVEL_CONFIG.warning;
        const Icon = config.icon;

        return (
          <div
            key={alert.id}
            className={`flex items-start gap-3 p-3 rounded-lg border transition-opacity ${config.bg} ${
              alert.acknowledged ? "opacity-50" : ""
            }`}
          >
            <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${config.color}`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={config.badge}>{config.label}</span>
                <span className="text-xs text-gray-500 uppercase tracking-wider">
                  {alert.gas_type}
                </span>
                {alert.value != null && (
                  <span className="text-xs text-gray-400">
                    {alert.value.toFixed(2)}
                    {alert.threshold ? ` / seuil ${alert.threshold}` : ""}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-200 mt-0.5 leading-snug">{alert.message}</p>
              <p className="text-xs text-gray-600 mt-1">
                {format(new Date(alert.timestamp), "dd MMM HH:mm", { locale: fr })}
              </p>
            </div>
            {!alert.acknowledged && (
              <button
                onClick={() => ack(alert.id)}
                className="flex-shrink-0 text-xs text-gray-500 hover:text-green-400 transition-colors border border-gray-700 hover:border-green-700 rounded px-2 py-1"
              >
                OK
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
