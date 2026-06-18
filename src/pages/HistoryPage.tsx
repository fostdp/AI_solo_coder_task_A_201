import { useEffect, useState } from "react";
import { api, type CastingTask } from "@/lib/api";
import { useSimStore } from "@/store/simStore";
import { CastingViewer } from "@/components/CastingViewer";
import { SensorCharts } from "@/components/SensorCharts";
import { History, Play, ChevronRight } from "lucide-react";

export default function HistoryPage() {
  const [tasks, setTasks] = useState<CastingTask[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [playing, setPlaying] = useState(false);
  const setCasting = useSimStore((s) => s.setCasting);
  const setSensorHistory = useSimStore((s) => s.setSensorHistory);
  const setFillingRatio = useSimStore((s) => s.setFillingRatio);

  useEffect(() => {
    (async () => {
      const data = await api.getCastings();
      setTasks(data);
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    const task = tasks.find((t) => t.id === selectedId);
    if (task) setCasting(task.id, task.name);
    (async () => {
      const history = await api.getSensorHistory(selectedId, 200);
      const sorted = history.reverse();
      setSensorHistory(sorted);
    })();
  }, [selectedId, tasks, setCasting, setSensorHistory]);

  useEffect(() => {
    if (!playing) return;
    const interval = window.setInterval(() => {
      setProgress((p) => {
        if (p >= 100) {
          setPlaying(false);
          return 100;
        }
        setFillingRatio((p + 2) / 100);
        return p + 2;
      });
    }, 120);
    return () => window.clearInterval(interval);
  }, [playing, setFillingRatio]);

  return (
    <div className="flex h-full gap-4 p-6">
      <aside className="w-72 shrink-0 rounded-xl border border-amber-800/30 bg-[#0d0a07]/60 p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold tracking-wide text-amber-300">
          <History className="h-4 w-4" /> 历史铸造任务
        </div>
        <div className="space-y-2">
          {tasks.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelectedId(t.id)}
              className={`w-full rounded-lg border p-3 text-left transition ${
                selectedId === t.id
                  ? "border-amber-500/60 bg-amber-700/15 text-amber-200"
                  : "border-amber-900/30 bg-black/30 text-amber-100/80 hover:border-amber-700/40"
              }`}
            >
              <div className="flex items-center gap-2">
                <ChevronRight className={`h-3.5 w-3.5 transition ${selectedId === t.id ? "rotate-90" : ""}`} />
                <span className="truncate text-sm font-medium">{t.name}</span>
              </div>
              <div className="mt-1 pl-5 text-[10px] text-amber-400/60">
                {new Date(t.created_at).toLocaleString("zh-CN")}
              </div>
              <div className="mt-1 pl-5">
                <span className={`rounded px-1.5 py-0.5 text-[9px] ${
                  t.status === "completed" ? "bg-emerald-900/40 text-emerald-300" :
                  t.status === "running" ? "bg-amber-900/40 text-amber-300" :
                  "bg-gray-800/60 text-gray-400"
                }`}>
                  {t.status === "completed" ? "已完成" : t.status === "running" ? "运行中" : t.status}
                </span>
              </div>
            </button>
          ))}
          {tasks.length === 0 && (
            <div className="py-8 text-center text-xs text-amber-400/40">暂无历史记录</div>
          )}
        </div>
      </aside>

      <div className="flex flex-1 flex-col gap-4 min-h-0">
        <div className="flex-1 grid grid-cols-5 gap-4 min-h-0">
          <div className="col-span-3 rounded-xl border border-amber-800/30 bg-gradient-to-br from-[#0f0b08]/70 to-[#050303]/70 p-1 min-h-0">
            <CastingViewer className="h-full w-full rounded-lg" />
          </div>
          <div className="col-span-2 rounded-xl border border-amber-800/30 bg-[#0d0a07]/60 p-4 min-h-0">
            <h3 className="mb-3 text-sm font-semibold tracking-wide text-amber-300">传感器历史曲线</h3>
            <div className="h-[calc(100%-2rem)]">
              <SensorCharts />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-amber-800/30 bg-[#0d0a07]/60 p-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => {
                if (progress >= 100) setProgress(0);
                setPlaying(!playing);
              }}
              className="flex h-10 w-10 items-center justify-center rounded-full border border-amber-600/50 bg-amber-700/25 text-amber-200 transition hover:bg-amber-600/40"
            >
              <Play className={`h-4 w-4 ${playing ? "fill-current" : ""}`} />
            </button>
            <div className="flex-1">
              <div className="mb-1 flex justify-between text-xs text-amber-400/70">
                <span>回放进度</span>
                <span className="font-mono">{progress.toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={progress}
                onChange={(e) => {
                  const v = Number(e.target.value);
                  setProgress(v);
                  setFillingRatio(v / 100);
                }}
                className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-amber-950 accent-amber-500"
              />
            </div>
            <span className="font-mono text-xs text-amber-300/70">
              {Math.floor((progress / 100) * 60).toString().padStart(2, "0")}:
              {((progress / 100 * 60) % 1 * 60).toFixed(0).padStart(2, "0")} / 01:00
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
