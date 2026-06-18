import { useSimStore } from "@/store/simStore";
import type { DefectPrediction } from "@/lib/api";

const severityLabel: Record<string, string> = {
  low: "轻微",
  medium: "中等",
  high: "严重",
  critical: "极严重",
};

const severityRow: Record<string, string> = {
  low: "bg-yellow-950/20 hover:bg-yellow-950/40",
  medium: "bg-orange-950/20 hover:bg-orange-950/40",
  high: "bg-red-950/30 hover:bg-red-950/50",
  critical: "bg-red-900/40 hover:bg-red-900/60",
};

const severityText: Record<string, string> = {
  low: "text-yellow-400",
  medium: "text-orange-400",
  high: "text-red-400",
  critical: "text-red-300",
};

const defectTypeLabel: Record<string, string> = {
  shrinkage_cavity: "缩孔",
  shrinkage_porosity: "缩松",
};

export function DefectTable() {
  const defects = useSimStore((s) => s.defects);
  const selectedDefect = useSimStore((s) => s.selectedDefect);
  const setSelectedDefect = useSimStore((s) => s.setSelectedDefect);

  const sorted = [...defects].sort((a, b) => {
    const rank = { critical: 0, high: 1, medium: 2, low: 3 };
    return (rank[a.severity] ?? 4) - (rank[b.severity] ?? 4);
  });

  if (sorted.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center py-12 text-amber-300/40">
        <div className="mb-2 text-4xl">✦</div>
        <div className="text-sm">暂无缺陷检测结果</div>
      </div>
    );
  }

  const handleSelect = (d: DefectPrediction) => {
    setSelectedDefect(selectedDefect?.id === d.id ? null : d);
  };

  return (
    <div className="h-full overflow-auto pr-1">
      <table className="w-full text-left text-xs">
        <thead className="sticky top-0 z-10 bg-[#0d0d14] text-amber-200/70">
          <tr className="border-b border-amber-700/30">
            <th className="px-3 py-2 font-medium">严重度</th>
            <th className="px-3 py-2 font-medium">类型</th>
            <th className="px-3 py-2 font-medium">体积</th>
            <th className="px-3 py-2 font-medium">Niyama</th>
            <th className="px-3 py-2 font-medium">位置</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((d) => (
            <tr
              key={d.id}
              onClick={() => handleSelect(d)}
              className={`cursor-pointer border-b border-amber-900/20 transition ${severityRow[d.severity]} ${
                selectedDefect?.id === d.id ? "ring-1 ring-inset ring-amber-400/40" : ""
              }`}
            >
              <td className={`px-3 py-2 font-semibold ${severityText[d.severity]}`}>
                {severityLabel[d.severity]}
              </td>
              <td className="px-3 py-2 text-amber-100/90">{defectTypeLabel[d.defect_type] || d.defect_type}</td>
              <td className="px-3 py-2 font-mono text-amber-200">{d.volume.toFixed(2)} cm³</td>
              <td className="px-3 py-2 font-mono text-amber-200/80">{d.niyama_value.toFixed(3)}</td>
              <td className="px-3 py-2 font-mono text-amber-200/60">
                ({d.position.x.toFixed(2)}, {d.position.y.toFixed(2)}, {d.position.z.toFixed(2)})
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
