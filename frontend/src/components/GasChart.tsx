import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import type { Measurement, GasThreshold } from "../types";
import { GAS_META } from "../types";

interface Props {
  measurements: Measurement[];
  thresholds?: GasThreshold[];
  selectedGas?: string;
}

export default function GasChart({ measurements, thresholds, selectedGas = "co" }: Props) {
  const meta = GAS_META[selectedGas];
  const threshold = thresholds?.find((t) => t.gas_type === selectedGas);

  const data = [...measurements]
    .reverse()
    .map((m) => ({
      time: format(new Date(m.timestamp), "HH:mm", { locale: fr }),
      value: (m as unknown as Record<string, unknown>)[selectedGas] as number | null,
      risk: m.risk_score,
    }))
    .filter((d) => d.value != null);

  const CustomTooltip = ({ active, payload, label }: {
    active?: boolean;
    payload?: { value: number }[];
    label?: string;
  }) => {
    if (active && payload?.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm shadow-xl">
          <p className="text-gray-400 mb-1">{label}</p>
          <p style={{ color: meta.color }} className="font-semibold">
            {payload[0].value?.toFixed(2)} {meta.unit}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-56">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            dataKey="time"
            tick={{ fill: "#6b7280", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: "#6b7280", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={45}
            tickFormatter={(v) => `${v}`}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Warning threshold */}
          {threshold && (
            <ReferenceLine
              y={threshold.warning_level}
              stroke="#f59e0b"
              strokeDasharray="4 4"
              label={{ value: "Alerte", fill: "#f59e0b", fontSize: 10, position: "right" }}
            />
          )}
          {/* Critical threshold */}
          {threshold && (
            <ReferenceLine
              y={threshold.critical_level}
              stroke="#ef4444"
              strokeDasharray="4 4"
              label={{ value: "Critique", fill: "#ef4444", fontSize: 10, position: "right" }}
            />
          )}

          <Line
            type="monotone"
            dataKey="value"
            stroke={meta.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: meta.color }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
