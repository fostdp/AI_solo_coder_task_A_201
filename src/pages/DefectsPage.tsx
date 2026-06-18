import { DefectTable } from "@/components/DefectTable";
import { NiyamaChart } from "@/components/NiyamaChart";
import { useEffect } from "react";
import { api } from "@/lib/api";
import { useSimStore } from "@/store/simStore";
import { AlertTriangle, ScanLine, Target } from "lucide-react";
import { computeDefectStats, niyamaDescription } from "@/lib/defect_panel";

export default function DefectsPage() {
  const defects = useSimStore((s) => s.defects);
  const setDefects = useSimStore((s) => s.setDefects);
  const setNiyamaPoints = useSimStore((s) => s.setNiyamaPoints);
  const castingId = useSimStore((s) => s.castingId);

  useEffect(() => {
    if (!castingId) return;
    (async () => {
      try {
        const d = await api.getDefects(castingId);
        setDefects(d);
        const niyamaData = await api.getNiyama(castingId);
        if (niyamaData.length > 0) {
          const last = niyamaData[niyamaData.length - 1];
          setNiyamaPoints(last.niyama?.points || []);
        }
      } catch {}
    })();
  }, [castingId, setDefects, setNiyamaPoints]);

  const stats = computeDefectStats(defects);

  return (
    <div className="flex h-full flex-col gap-5 p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold tracking-wide text-amber-200">
            缺陷预测分析
          </h1>
          <p className="mt-1 text-sm text-amber-200/60">
            基于 Niyama 判据的缩孔缩松预测
          </p>
        </div>
      </header>

      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          icon={Target}
          label="总缺陷数"
          value={stats.total.toString()}
          unit="处"
          color="#d4af37"
        />
        <MetricCard
          icon={AlertTriangle}
          label="极严重"
          value={stats.critical.toString()}
          unit="处"
          color="#ff1a1a"
          highlight={stats.critical > 0}
        />
        <MetricCard
          icon={AlertTriangle}
          label="严重"
          value={stats.high.toString()}
          unit="处"
          color="#ff4d4d"
          highlight={stats.high > 0}
        />
        <MetricCard
          icon={ScanLine}
          label="总缩孔体积"
          value={stats.totalVolume.toFixed(2)}
          unit="cm³"
          color="#ff8a3d"
          highlight={stats.totalVolume > 5}
        />
      </div>

      <div className="grid flex-1 grid-cols-5 gap-4 min-h-0">
        <div className="col-span-2 flex flex-col rounded-xl border border-amber-800/30 bg-[#0d0a07]/60 p-4 min-h-0">
          <h3 className="mb-3 text-sm font-semibold tracking-wide text-amber-300">
            Niyama 判据分布
          </h3>
          <p className="mb-3 text-[11px] leading-relaxed text-amber-400/60">
            {niyamaDescription}
          </p>
          <div className="flex-1 min-h-0">
            <NiyamaChart />
          </div>
        </div>
        <div className="col-span-3 flex flex-col rounded-xl border border-amber-800/30 bg-[#0d0a07]/60 p-4 min-h-0">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold tracking-wide text-amber-300">
            <span>缺陷列表</span>
            <span className="ml-2 rounded-full border border-amber-700/40 px-2 py-0.5 text-[10px] text-amber-400/80">
              点击行可在三维视图中定位
            </span>
          </h3>
          <div className="flex-1 min-h-0">
            <DefectTable />
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  color,
  highlight,
}: {
  icon: any;
  label: string;
  value: string;
  unit: string;
  color: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`relative overflow-hidden rounded-xl border p-4 backdrop-blur-sm transition-all ${
        highlight
          ? "border-red-500/50 bg-red-950/20 shadow-[0_0_24px_rgba(230,57,70,0.2)]"
          : "border-amber-700/30 bg-gradient-to-br from-[#1a1410]/70 to-[#0f0a06]/70"
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-amber-200/70">{label}</div>
          <div className="mt-1.5 flex items-baseline gap-1.5">
            <span
              className="font-mono text-3xl font-bold"
              style={{ color }}
            >
              {value}
            </span>
            <span className="text-xs text-amber-300/60">{unit}</span>
          </div>
        </div>
        <div
          className="flex h-11 w-11 items-center justify-center rounded-lg"
          style={{ backgroundColor: `${color}18`, border: `1px solid ${color}40` }}
        >
          <Icon className="h-5 w-5" style={{ color }} />
        </div>
      </div>
      <div
        className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full opacity-10 blur-3xl"
        style={{ backgroundColor: color }}
      />
    </div>
  );
}
