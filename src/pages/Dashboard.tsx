import { StatCards } from "@/components/StatCards";
import { SensorCharts } from "@/components/SensorCharts";
import { AlertList } from "@/components/AlertList";
import { CastingViewer } from "@/components/CastingViewer";
import { useEffect } from "react";
import { api } from "@/lib/api";
import { useSimStore } from "@/store/simStore";
import { useSimulationWS } from "@/hooks/useSimulationWS";
import { Play, Square, RefreshCw } from "lucide-react";

export default function Dashboard() {
  const castingId = useSimStore((s) => s.castingId);
  const castingName = useSimStore((s) => s.castingName);
  const setCasting = useSimStore((s) => s.setCasting);
  const setLatestSensor = useSimStore((s) => s.setLatestSensor);
  const addSensorHistory = useSimStore((s) => s.addSensorHistory);
  const status = useSimStore((s) => s.status);
  const setStatus = useSimStore((s) => s.setStatus);

  useSimulationWS(castingId);

  useEffect(() => {
    (async () => {
      try {
        const tasks = await api.getCastings();
        if (tasks.length > 0) {
          const t = tasks[0];
          setCasting(t.id, t.name);
        } else {
          const newTask = await api.createCasting("曾侯乙尊盘复原实验", {
            material: "青铜",
            target_temp: 1180,
          });
          setCasting(newTask.id, newTask.name);
        }
      } catch {}
    })();
  }, [setCasting]);

  useEffect(() => {
    if (!castingId) return;
    const interval = window.setInterval(async () => {
      try {
        const latest = await api.getLatestSensor(castingId);
        if (latest) {
          setLatestSensor(latest);
          addSensorHistory(latest);
        }
        const st = await api.getSimulationStatus();
        setStatus(st);
      } catch {}
    }, 3000);
    return () => window.clearInterval(interval);
  }, [castingId, setLatestSensor, addSensorHistory, setStatus]);

  const handleStart = async () => {
    if (!castingId) return;
    await api.startSimulation(castingId);
  };
  const handleStop = async () => {
    await api.stopSimulation();
  };

  return (
    <div className="flex h-full flex-col gap-4 p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold tracking-wide text-amber-200">实时监控仪表盘</h1>
          <p className="mt-1 text-sm text-amber-200/60">{castingName || "加载中..."}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full border border-amber-700/40 bg-black/40 px-3 py-1 text-xs text-amber-300">
            {status.status === "running" ? "● 运行中" : status.status === "idle" ? "○ 待机" : "■ 已停止"}
          </span>
          <button
            onClick={handleStart}
            disabled={status.status === "running"}
            className="flex items-center gap-1.5 rounded-lg border border-amber-600/50 bg-amber-700/20 px-3 py-1.5 text-sm text-amber-200 transition hover:bg-amber-600/30 disabled:opacity-40"
          >
            <Play className="h-3.5 w-3.5" /> 启动仿真
          </button>
          <button
            onClick={handleStop}
            disabled={status.status !== "running"}
            className="flex items-center gap-1.5 rounded-lg border border-red-600/40 bg-red-700/20 px-3 py-1.5 text-sm text-red-200 transition hover:bg-red-600/30 disabled:opacity-40"
          >
            <Square className="h-3.5 w-3.5" /> 停止
          </button>
          <button className="flex items-center gap-1.5 rounded-lg border border-amber-700/30 bg-black/40 px-3 py-1.5 text-sm text-amber-300 transition hover:bg-amber-900/30">
            <RefreshCw className="h-3.5 w-3.5" /> 刷新
          </button>
        </div>
      </header>

      <StatCards />

      <div className="grid flex-1 grid-cols-12 gap-4 min-h-0">
        <div className="col-span-8 flex flex-col gap-4 min-h-0">
          <div className="flex-1 rounded-xl border border-amber-800/30 bg-gradient-to-br from-[#0f0b08]/80 to-[#050303]/80 p-1 shadow-[0_0_40px_rgba(184,115,51,0.08)] min-h-0">
            <CastingViewer className="h-full w-full rounded-lg" />
          </div>
          <div className="h-64 rounded-xl border border-amber-800/30 bg-[#0d0a07]/60 p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold tracking-wide text-amber-300">传感器实时数据</h3>
              <span className="text-xs text-amber-500/60">步骤: {status.current_step}/{status.total_steps}</span>
            </div>
            <div className="h-[calc(100%-2rem)]">
              <SensorCharts />
            </div>
          </div>
        </div>
        <div className="col-span-4 flex flex-col gap-4 min-h-0">
          <div className="flex-1 rounded-xl border border-amber-800/30 bg-[#0d0a07]/60 p-4 min-h-0">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold tracking-wide text-amber-300">实时告警</h3>
              <span className="text-xs text-amber-500/60">共 {useSimStore.getState().alerts.length} 条</span>
            </div>
            <div className="h-[calc(100%-2rem)] overflow-hidden">
              <AlertList />
            </div>
          </div>
          <div className="h-56 rounded-xl border border-amber-800/30 bg-gradient-to-br from-[#1a0f08]/60 to-[#0d0605]/80 p-4">
            <h3 className="mb-3 text-sm font-semibold tracking-wide text-amber-300">铸造工艺参数</h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              {[
                ["材质", "青铜 Cu-Sn 12%"],
                ["目标浇温", "1180 °C"],
                ["型壳层数", "9 层"],
                ["壳材", "硅溶胶+石英砂"],
                ["充型时间", "~60 s"],
                ["凝固时间", "~180 s"],
              ].map(([k, v]) => (
                <div key={k} className="rounded border border-amber-900/30 bg-black/30 px-3 py-2">
                  <div className="text-[10px] text-amber-500/60">{k}</div>
                  <div className="mt-0.5 font-mono text-sm text-amber-200">{v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
