import type { Measurement, GasThreshold, AIAnalysis } from "../types";
import { GAS_META } from "../types";
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";

interface Props {
  measurement: Measurement | null | undefined;
  thresholds?: GasThreshold[];
  analysis?: AIAnalysis | null;
  onSelectGas?: (gas: string) => void;
  selectedGas?: string;
}

function levelColor(value: number | null, warning: number, critical: number) {
  if (value == null) return "text-gray-500";
  if (value >= critical) return "text-red-400";
  if (value >= warning) return "text-yellow-400";
  return "text-green-400";
}

function levelBg(value: number | null, warning: number, critical: number) {
  if (value == null) return "border-gray-800 bg-gray-900/50";
  if (value >= critical) return "border-red-800 bg-red-950/30";
  if (value >= warning) return "border-yellow-800 bg-yellow-950/30";
  return "border-gray-800 bg-gray-900/50";
}

function TrendIcon({ trend }: { trend?: string }) {
  if (trend === "rising") return <TrendingUp className="w-3.5 h-3.5 text-red-400" />;
  if (trend === "falling") return <TrendingDown className="w-3.5 h-3.5 text-green-400" />;
  return <Minus className="w-3.5 h-3.5 text-gray-500" />;
}

const DEFAULT_THRESHOLDS: Record<string, { warning: number; critical: number }> = {
  co:  { warning: 25,   critical: 100  },
  co2: { warning: 1000, critical: 5000 },
  no2: { warning: 200,  critical: 1000 },
  o3:  { warning: 100,  critical: 300  },
  voc: { warning: 500,  critical: 2000 },
  ch4: { warning: 1000, critical: 5000 },
};

export default function GasGauges({
  measurement,
  thresholds,
  analysis,
  onSelectGas,
  selectedGas,
}: Props) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {Object.entries(GAS_META).map(([gas, meta]) => {
        const value = measurement ? (measurement as unknown as Record<string, unknown>)[gas] as number | null : null;
        const t = thresholds?.find((th) => th.gas_type === gas);
        const warnLevel = t?.warning_level ?? DEFAULT_THRESHOLDS[gas]?.warning ?? 0;
        const critLevel = t?.critical_level ?? DEFAULT_THRESHOLDS[gas]?.critical ?? 0;
        const isAnomaly = analysis?.anomaly_flags?.[gas];
        const trend = analysis?.trends?.[gas];
        const isSelected = selectedGas === gas;

        return (
          <button
            key={gas}
            onClick={() => onSelectGas?.(gas)}
            className={`card text-left transition-all hover:border-gray-600 relative ${
              isSelected ? "ring-2 ring-blue-500 ring-offset-2 ring-offset-gray-950" : ""
            } ${levelBg(value, warnLevel, critLevel)}`}
          >
            {isAnomaly && (
              <span className="absolute top-2 right-2">
                <AlertTriangle className="w-3.5 h-3.5 text-purple-400" />
              </span>
            )}
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">
              {meta.label}
            </p>
            <p
              className={`text-2xl font-bold mt-1 ${levelColor(value, warnLevel, critLevel)}`}
              style={{ color: value != null ? meta.color : undefined }}
            >
              {value != null ? value.toFixed(1) : "—"}
            </p>
            <div className="flex items-center justify-between mt-1">
              <p className="text-xs text-gray-600">{meta.unit}</p>
              <TrendIcon trend={trend} />
            </div>
          </button>
        );
      })}
    </div>
  );
}
