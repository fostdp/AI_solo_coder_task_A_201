import { useEffect, useState } from "react";
import { api, type AlertItem } from "@/lib/api";
import { AlertList } from "@/components/AlertList";
import { AlertOctagon, Bell, BellOff, Filter } from "lucide-react";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [filter, setFilter] = useState<"all" | "unack" | "critical">("all");
  const castingId = useSimStore((s) => s.castingId);
  const acknowledgeAlert = useSimStore((s) => s.acknowledgeAlert);

  useEffect(() => {
    if (!castingId) return;
    (async () => {
      const data = await api.getAlerts(castingId, false);
      setAlerts(data);
    })();
  }, [castingId]);

  const filtered = alerts.filter((a) => {
    if (filter === "unack") return !a.acknowledged;
    if (filter === "critical") return a.severity === "critical";
    return true;
  });

  const handleAck = async (a: AlertItem) => {
    await api.acknowledgeAlert(a.id);
    acknowledgeAlert(a.id);
    setAlerts((prev) => prev.map((x) => (x.id === a.id ? { ...x, acknowledged: true } : x)));
  };

  const stats = {
    total: alerts.length,
    unack: alerts.filter((a) => !a.acknowledged).length,
    critical: alerts.filter((a) => a.severity === "critical").length,
  };

  return (
    <div className="flex h-full flex-col gap-5 p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold tracking-wide text-amber-200">告警中心</h1>
          <p className="mt-1 text-sm text-amber-200/60">缩孔超限、充型不足等异常事件记录</p>
        </div>
        <div className="flex items-center gap-2">
          <FilterBtn active={filter === "all"} onClick={() => setFilter("all")} icon={AlertOctagon} label={`全部 ${stats.total}`} />
          <FilterBtn active={filter === "unack"} onClick={() => setFilter("unack")} icon={Bell} label={`未确认 ${stats.unack}`} color="#e63946" />
          <FilterBtn active={filter === "critical"} onClick={() => setFilter("critical")} icon={BellOff} label={`极严重 ${stats.critical}`} color="#ff1a1a" />
        </div>
      </header>

      <div className="grid grid-cols-3 gap-4">
        {[
          { k: "缩孔体积超限", v: alerts.filter((a) => a.alert_type === "shrinkage_volume_exceeded").length, c: "#ff4d4d" },
          { k: "充型不足", v: alerts.filter((a) => a.alert_type === "insufficient_filling").length, c: "#ff8a3d" },
          { k: "严重缺陷", v: alerts.filter((a) => a.alert_type === "critical_defect").length, c: "#ff1a1a" },
        ].map((s) => (
          <div key={s.k} className="rounded-xl border border-amber-800/30 bg-gradient-to-br from-[#1a1410]/70 to-[#0f0a06]/70 p-4">
            <div className="text-xs text-amber-200/70">{s.k}</div>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="font-mono text-3xl font-bold" style={{ color: s.c }}>{s.v}</span>
              <span className="text-xs text-amber-300/60">次</span>
            </div>
          </div>
        ))}
      </div>

      <div className="flex-1 rounded-xl border border-amber-800/30 bg-[#0d0a07]/60 p-4 min-h-0 overflow-hidden">
        <AlertList />
        {filtered.length > 0 && (
          <div className="sr-only">
            {filtered.map((a) => (
              <button key={a.id} onClick={() => handleAck(a)} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import { useSimStore } from "@/store/simStore";

function FilterBtn({ active, onClick, icon: Icon, label, color }: any) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs transition ${
        active
          ? "border-amber-500/60 bg-amber-600/20 text-amber-200"
          : "border-amber-800/30 bg-black/30 text-amber-300/70 hover:text-amber-200"
      }`}
    >
      <Icon className="h-3.5 w-3.5" style={color ? { color } : undefined} /> {label}
    </button>
  );
}
