import { CastingViewer } from "@/components/CastingViewer";
import { useSimStore } from "@/store/simStore";
import { Sparkles, Thermometer, Bug, RotateCw, Layers } from "lucide-react";

export default function SimulationView() {
  const fillingRatio = useSimStore((s) => s.fillingRatio);
  const autoRotate = useSimStore((s) => s.autoRotate);
  const setAutoRotate = useSimStore((s) => s.setAutoRotate);
  const showParticles = useSimStore((s) => s.showParticles);
  const toggleShowParticles = useSimStore((s) => s.toggleShowParticles);
  const showTemperature = useSimStore((s) => s.showTemperature);
  const toggleShowTemperature = useSimStore((s) => s.toggleShowTemperature);
  const showDefects = useSimStore((s) => s.showDefects);
  const toggleShowDefects = useSimStore((s) => s.toggleShowDefects);
  const selectedDefect = useSimStore((s) => s.selectedDefect);
  const status = useSimStore((s) => s.status);
  const defects = useSimStore((s) => s.defects);

  const ToggleBtn = ({
    active, onClick, icon: Icon, label,
  }: {
    active: boolean; onClick: () => void; icon: any; label: string;
  }) => (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs transition ${
        active
          ? "border-amber-500/70 bg-amber-600/25 text-amber-200 shadow-[0_0_12px_rgba(212,175,55,0.25)]"
          : "border-amber-800/40 bg-black/30 text-amber-300/70 hover:text-amber-200"
      }`}
    >
      <Icon className="h-3.5 w-3.5" /> {label}
    </button>
  );

  return (
    <div className="relative h-full w-full">
      <div className="absolute inset-0">
        <CastingViewer className="h-full w-full" />
      </div>

      <div className="absolute left-6 top-6 space-y-3">
        <div className="rounded-xl border border-amber-800/40 bg-black/60 px-4 py-3 backdrop-blur-md shadow-[0_0_30px_rgba(0,0,0,0.5)]">
          <div className="text-[10px] uppercase tracking-[0.2em] text-amber-500/70">充型进度</div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="font-mono text-3xl font-bold text-amber-300">
              {(fillingRatio * 100).toFixed(1)}
            </span>
            <span className="text-sm text-amber-400/70">%</span>
          </div>
          <div className="mt-2 h-1.5 w-48 overflow-hidden rounded-full bg-amber-950/60">
            <div
              className="h-full rounded-full bg-gradient-to-r from-amber-600 via-orange-500 to-red-500 transition-all duration-500"
              style={{ width: `${fillingRatio * 100}%` }}
            />
          </div>
          <div className="mt-2 text-[10px] text-amber-500/60">
            仿真步 {status.current_step} / {status.total_steps}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 rounded-xl border border-amber-800/40 bg-black/60 p-2 backdrop-blur-md">
          <ToggleBtn active={autoRotate} onClick={() => setAutoRotate(!autoRotate)} icon={RotateCw} label="自动旋转" />
          <ToggleBtn active={showParticles} onClick={toggleShowParticles} icon={Sparkles} label="充型粒子" />
          <ToggleBtn active={showTemperature} onClick={toggleShowTemperature} icon={Thermometer} label="温度场" />
          <ToggleBtn active={showDefects} onClick={toggleShowDefects} icon={Bug} label="缺陷标记" />
        </div>
      </div>

      <div className="absolute right-6 top-6 w-72 rounded-xl border border-amber-800/40 bg-black/60 p-4 backdrop-blur-md shadow-[0_0_30px_rgba(0,0,0,0.5)]">
        <div className="mb-3 flex items-center gap-2">
          <Layers className="h-4 w-4 text-amber-400" />
          <h3 className="text-sm font-semibold tracking-wide text-amber-200">缺陷信息</h3>
          <span className="ml-auto rounded-full border border-amber-700/40 px-2 py-0.5 text-[10px] text-amber-300">
            {defects.length} 处
          </span>
        </div>
        {selectedDefect ? (
          <div className="space-y-2 text-xs">
            <div className="rounded-lg border border-red-700/40 bg-red-950/30 px-3 py-2">
              <div className="flex items-center justify-between">
                <span className="text-amber-200/70">严重程度</span>
                <span className={`font-semibold ${
                  selectedDefect.severity === "critical" ? "text-red-400" :
                  selectedDefect.severity === "high" ? "text-red-300" :
                  selectedDefect.severity === "medium" ? "text-orange-300" : "text-yellow-300"
                }`}>
                  {selectedDefect.severity === "critical" ? "极严重" :
                   selectedDefect.severity === "high" ? "严重" :
                   selectedDefect.severity === "medium" ? "中等" : "轻微"}
                </span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Info label="缺陷类型" value={selectedDefect.defect_type === "shrinkage_cavity" ? "缩孔" : "缩松"} />
              <Info label="体积" value={`${selectedDefect.volume.toFixed(2)} cm³`} />
              <Info label="Niyama" value={selectedDefect.niyama_value.toFixed(3)} />
              <Info label="温度" value={`${(selectedDefect as any).mean_temperature?.toFixed(1) ?? "—"} °C`} />
            </div>
            <div className="rounded-lg border border-amber-900/30 bg-black/30 px-3 py-2 font-mono text-[11px] text-amber-200/70">
              位置: ({selectedDefect.position.x.toFixed(3)}, {selectedDefect.position.y.toFixed(3)}, {selectedDefect.position.z.toFixed(3)})
            </div>
          </div>
        ) : (
          <div className="py-6 text-center text-xs text-amber-400/50">
            点击模型上的红色标记查看缺陷详情
          </div>
        )}
      </div>

      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 rounded-xl border border-amber-800/40 bg-black/60 px-6 py-3 backdrop-blur-md shadow-[0_0_30px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-6 text-xs">
          <LegendDot color="#ff1a1a" label="极严重缺陷" />
          <LegendDot color="#ff4d4d" label="严重缺陷" />
          <LegendDot color="#ff8c1a" label="中等缺陷" />
          <LegendDot color="#ffd93d" label="轻微缺陷" />
          <div className="mx-2 h-4 w-px bg-amber-800/50" />
          <LegendDot color="#ff7a2e" label="铜液粒子" glow />
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-amber-900/30 bg-black/30 px-2.5 py-1.5">
      <div className="text-[10px] text-amber-500/60">{label}</div>
      <div className="mt-0.5 font-mono text-amber-200">{value}</div>
    </div>
  );
}

function LegendDot({ color, label, glow }: { color: string; label: string; glow?: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="inline-block h-2.5 w-2.5 rounded-full"
        style={{
          backgroundColor: color,
          boxShadow: glow ? `0 0 8px ${color}` : "none",
        }}
      />
      <span className="text-amber-200/80">{label}</span>
    </div>
  );
}
