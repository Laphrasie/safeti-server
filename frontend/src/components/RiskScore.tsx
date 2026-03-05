import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from "recharts";
import { ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";

interface Props {
  score: number | null | undefined;
  recommendations?: string[];
}

export default function RiskScore({ score, recommendations }: Props) {
  const s = score ?? 0;

  const color = s >= 80 ? "#ef4444" : s >= 50 ? "#f59e0b" : "#22c55e";
  const Icon = s >= 80 ? ShieldX : s >= 50 ? ShieldAlert : ShieldCheck;
  const label = s >= 80 ? "Critique" : s >= 50 ? "Élevé" : "Normal";

  const data = [{ value: s, fill: color }];

  return (
    <div className="card flex flex-col items-center">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4 self-start">
        Score de risque IA
      </h3>

      <div className="relative w-40 h-40">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="70%"
            outerRadius="100%"
            barSize={12}
            data={data}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar background={{ fill: "#1f2937" }} dataKey="value" angleAxisId={0} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <Icon className="w-6 h-6 mb-1" style={{ color }} />
          <span className="text-3xl font-bold" style={{ color }}>
            {s.toFixed(0)}
          </span>
          <span className="text-xs text-gray-500">/100</span>
        </div>
      </div>

      <span
        className="mt-2 text-sm font-semibold"
        style={{ color }}
      >
        {label}
      </span>

      {recommendations && recommendations.length > 0 && (
        <div className="mt-4 w-full space-y-1">
          {recommendations.map((r, i) => (
            <p key={i} className="text-xs text-gray-400 flex gap-2">
              <span className="text-gray-600 flex-shrink-0">→</span>
              {r}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
