import { Thermometer, Flame, Wind, Gauge, AlertTriangle } from "lucide-react";
import { useSimStore } from "@/store/simStore";

interface StatCardProps {
  icon: React.ComponentType<{ className?: string; color?: string }>;
  label: string;
  value: string;
  unit: string;
  color: string;
  warning?: boolean;
}

function StatCard({ icon: Icon, label, value, unit, color, warning }: StatCardProps) {
  return (
    <div
      className={`relative overflow-hidden rounded-xl border px-4 py-3 backdrop-blur-sm transition-all ${
        warning
          ? "border-red-500/60 bg-red-950/30 shadow-[0_0_18px_rgba(230,57,70,0.25)]"
          : "border-amber-700/40 bg-gradient-to-br from-[#1a1410]/80 to-[#0f0a06]/80"
      }`}
    >
      <div className="flex items-center gap-3">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
          style={{ backgroundColor: `${color}22`, border: `1px solid ${color}55`, ["--icon-color" as any]: color }}
        >
          <Icon className="h-5 w-5 text-[color:var(--icon-color)]" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-xs font-medium tracking-wide text-amber-200/70">{label}</div>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold tabular-nums" style={{ color }}>
              {value}
            </span>
            <span className="text-xs text-amber-200/50">{unit}</span>
          </div>
        </div>
        {warning && <AlertTriangle className="h-5 w-5 animate-pulse text-red-400" />}
      </div>
      <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full opacity-10 blur-2xl" style={{ backgroundColor: color }} />
    </div>
  );
}

export function StatCards() {
  const latest = useSimStore((s) => s.latestSensor);
  const fillingRatio = useSimStore((s) => s.fillingRatio);
  const defects = useSimStore((s) => s.defects);
  const criticalCount = defects.filter((d) => d.severity === "critical" || d.severity === "high").length;

  return (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      <StatCard
        icon={Thermometer}
        label="蜡模温度"
        value={latest?.wax_temperature?.toFixed(1) ?? "—"}
        unit="°C"
        color="#ff8a3d"
      />
      <StatCard
        icon={Flame}
        label="浇铸温度"
        value={latest?.pouring_temperature?.toFixed(1) ?? "—"}
        unit="°C"
        color="#e63946"
      />
      <StatCard
        icon={Wind}
        label="型壳透气性"
        value={latest?.shell_permeability?.toFixed(1) ?? "—"}
        unit="%"
        color="#457b9d"
      />
      <StatCard
        icon={Gauge}
        label="充型进度"
        value={(fillingRatio * 100).toFixed(1)}
        unit="%"
        color="#d4af37"
        warning={fillingRatio < 0.95 || criticalCount > 0}
      />
    </div>
  );
}
