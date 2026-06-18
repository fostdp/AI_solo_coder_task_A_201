import type { DefectPrediction, NiyamaPoint } from "./api";

export const severityLabel: Record<string, string> = {
  low: "轻微",
  medium: "中等",
  high: "严重",
  critical: "极严重",
};

export const severityRow: Record<string, string> = {
  low: "bg-yellow-950/20 hover:bg-yellow-950/40",
  medium: "bg-orange-950/20 hover:bg-orange-950/40",
  high: "bg-red-950/30 hover:bg-red-950/50",
  critical: "bg-red-900/40 hover:bg-red-900/60",
};

export const severityText: Record<string, string> = {
  low: "text-yellow-400",
  medium: "text-orange-400",
  high: "text-red-400",
  critical: "text-red-300",
};

export const defectTypeLabel: Record<string, string> = {
  shrinkage_cavity: "缩孔",
  shrinkage_porosity: "缩松",
};

export const niyamaDescription =
  "Niyama = G / √R，其中 G 为温度梯度(°C/mm)，R 为冷却速率(°C/s)。当 Niyama < 1.0 时，单元存在缩孔缩松风险。";

export function sortDefectsBySeverity(defects: DefectPrediction[]): DefectPrediction[] {
  const rank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
  return [...defects].sort((a, b) => (rank[a.severity] ?? 4) - (rank[b.severity] ?? 4));
}

export interface DefectStats {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  totalVolume: number;
  criticalVolume: number;
}

export function computeDefectStats(defects: DefectPrediction[]): DefectStats {
  return {
    total: defects.length,
    critical: defects.filter((d) => d.severity === "critical").length,
    high: defects.filter((d) => d.severity === "high").length,
    medium: defects.filter((d) => d.severity === "medium").length,
    low: defects.filter((d) => d.severity === "low").length,
    totalVolume: defects.reduce((s, d) => s + d.volume, 0),
    criticalVolume: defects
      .filter((d) => d.severity === "critical" || d.severity === "high")
      .reduce((s, d) => s + d.volume, 0),
  };
}

export function buildNiyamaHistogramData(
  niyamaPoints: NiyamaPoint[],
  bins: number = 20,
  min: number = 0,
  max: number = 3
): { counts: number[]; labels: string[] } {
  const counts = new Array(bins).fill(0);
  niyamaPoints.forEach((p) => {
    const idx = Math.min(
      bins - 1,
      Math.max(0, Math.floor(((p.niyama - min) / (max - min)) * bins))
    );
    counts[idx]++;
  });
  const labels = counts.map((_, i) =>
    ((i * (max - min)) / bins + min).toFixed(2)
  );
  return { counts, labels };
}

export function formatVolume(volume: number): string {
  return `${volume.toFixed(2)} cm³`;
}

export function formatPosition(pos: { x: number; y: number; z: number }): string {
  return `(${pos.x.toFixed(2)}, ${pos.y.toFixed(2)}, ${pos.z.toFixed(2)})`;
}

export function formatNiyama(value: number): string {
  return value.toFixed(3);
}

export function defectSeverityRank(severity: string): number {
  const rank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
  return rank[severity] ?? 4;
}

export function getDefectTypeLabel(defectType: string): string {
  return defectTypeLabel[defectType] || defectType;
}

export function getSeverityLabel(severity: string): string {
  return severityLabel[severity] || severity;
}

export function filterDefectsBySeverity(
  defects: DefectPrediction[],
  severity?: string
): DefectPrediction[] {
  if (!severity) return defects;
  return defects.filter((d) => d.severity === severity);
}
