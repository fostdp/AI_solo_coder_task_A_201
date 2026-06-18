import { CheckCircle, AlertCircle, XCircle, AlertTriangle, X } from "lucide-react";
import { useSimStore } from "@/store/simStore";
import { api, type AlertItem } from "@/lib/api";

const severityConfig = {
  warning: {
    icon: AlertTriangle,
    badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    ring: "ring-amber-500/30",
  },
  error: {
    icon: AlertCircle,
    badge: "bg-orange-500/20 text-orange-300 border-orange-500/40",
    ring: "ring-orange-500/30",
  },
  critical: {
    icon: XCircle,
    badge: "bg-red-500/20 text-red-300 border-red-500/40",
    ring: "ring-red-500/40",
  },
};

const typeLabels: Record<string, string> = {
  shrinkage_volume_exceeded: "缩孔体积超限",
  insufficient_filling: "充型不足",
  critical_defect: "严重缺陷",
  temperature_anomaly: "温度异常",
};

export function AlertList({ compact = false }: { compact?: boolean }) {
  const alerts = useSimStore((s) => s.alerts);
  const acknowledgeAlert = useSimStore((s) => s.acknowledgeAlert);
  const displayed = compact ? alerts.slice(0, 5) : alerts;

  const handleAck = async (a: AlertItem) => {
    await api.acknowledgeAlert(a.id);
    acknowledgeAlert(a.id);
  };

  if (displayed.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center py-8 text-amber-300/40">
        <CheckCircle className="mb-2 h-10 w-10" />
        <div className="text-sm">暂无告警</div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-2 ${compact ? "" : "max-h-full overflow-y-auto pr-1"}`}>
      {displayed.map((a) => {
        const cfg = severityConfig[a.severity as keyof typeof severityConfig] || severityConfig.warning;
        const Icon = cfg.icon;
        return (
          <div
            key={a.id}
            className={`relative rounded-lg border bg-black/40 p-3 ring-1 transition-all hover:bg-black/60 ${cfg.ring} ${
              a.acknowledged ? "opacity-60" : "animate-pulse-once"
            }`}
          >
            <div className="flex items-start gap-3">
              <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${cfg.badge.split(" ")[1]}`} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className={`rounded border px-2 py-0.5 text-[10px] font-medium ${cfg.badge}`}>
                    {typeLabels[a.alert_type] || a.alert_type}
                  </span>
                  <span className="text-[10px] text-amber-200/40">
                    {new Date(a.created_at).toLocaleTimeString("zh-CN", { hour12: false })}
                  </span>
                </div>
                <div className="mt-1.5 text-sm leading-relaxed text-amber-50">
                  {a.message}
                </div>
                {!compact && a.data && Object.keys(a.data).length > 0 && (
                  <div className="mt-2 rounded bg-black/40 px-2 py-1.5 font-mono text-[11px] text-amber-200/60">
                    {JSON.stringify(a.data, null, 0)}
                  </div>
                )}
              </div>
              {!a.acknowledged && (
                <button
                  onClick={() => handleAck(a)}
                  className="shrink-0 rounded-md border border-amber-700/40 px-2 py-1 text-[11px] text-amber-300 transition hover:bg-amber-600/20"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
