import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";
import { Battery, Signal, Cpu, Clock, Wifi } from "lucide-react";
import type { Device, Measurement } from "../types";

interface Props {
  device: Device | null | undefined;
  latest: Measurement | null | undefined;
}

function BatteryBar({ level }: { level: number | null | undefined }) {
  if (level == null) return <span className="text-gray-600">—</span>;
  const color =
    level > 50 ? "bg-green-500" : level > 20 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all`}
          style={{ width: `${Math.min(100, Math.max(0, level))}%` }}
        />
      </div>
      <span className="text-gray-300 text-sm">{level.toFixed(0)}%</span>
    </div>
  );
}

export default function DeviceStatus({ device, latest }: Props) {
  const lastSeen = device?.last_seen
    ? formatDistanceToNow(new Date(device.last_seen), { addSuffix: true, locale: fr })
    : "inconnu";

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
        Statut du capteur
      </h3>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <Cpu className="w-4 h-4" />
            <span>Identifiant</span>
          </div>
          <span className="text-gray-200 text-sm font-mono">
            {device?.device_uid ?? "—"}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <Battery className="w-4 h-4" />
            <span>Batterie</span>
          </div>
          <BatteryBar level={latest?.battery_level ?? device?.battery_level} />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <Signal className="w-4 h-4" />
            <span>Signal BLE</span>
          </div>
          <span className="text-gray-300 text-sm">
            {latest?.signal_strength != null
              ? `${latest.signal_strength.toFixed(0)} dBm`
              : "—"}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <Clock className="w-4 h-4" />
            <span>Dernière synchro</span>
          </div>
          <span className="text-gray-300 text-sm">{lastSeen}</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <Wifi className="w-4 h-4" />
            <span>Firmware</span>
          </div>
          <span className="text-gray-300 text-sm font-mono">
            {device?.firmware_version ?? "—"}
          </span>
        </div>

      </div>

      {/* Online indicator */}
      <div className="mt-4 pt-3 border-t border-gray-800 flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            device?.is_active ? "bg-green-500 animate-pulse" : "bg-gray-600"
          }`}
        />
        <span className="text-xs text-gray-500">
          {device?.is_active ? "En ligne" : "Hors ligne"}
        </span>
      </div>
    </div>
  );
}
