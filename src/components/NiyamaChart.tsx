import ReactECharts from "echarts-for-react";
import { useMemo } from "react";
import { useSimStore } from "@/store/simStore";

export function NiyamaChart() {
  const niyamaPoints = useSimStore((s) => s.niyamaPoints);
  const threshold = 1.0;

  const option = useMemo(() => {
    const bins = new Array(20).fill(0);
    const min = 0;
    const max = 3;
    niyamaPoints.forEach((p) => {
      const idx = Math.min(19, Math.max(0, Math.floor(((p.niyama - min) / (max - min)) * 20)));
      bins[idx]++;
    });
    const xLabels = bins.map((_, i) => ((i * (max - min)) / 20 + min).toFixed(2));

    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(13,13,20,0.92)",
        borderColor: "#b87333",
        textStyle: { color: "#e8d5a3" },
      },
      grid: { left: 48, right: 20, top: 20, bottom: 36 },
      xAxis: {
        type: "category",
        data: xLabels,
        name: "Niyama值",
        axisLine: { lineStyle: { color: "#5a4a2a" } },
        axisLabel: { color: "#c9b27a", fontSize: 9, rotate: 30 },
        nameTextStyle: { color: "#d4af37" },
      },
      yAxis: {
        type: "value",
        name: "单元数",
        axisLine: { lineStyle: { color: "#5a4a2a" } },
        splitLine: { lineStyle: { color: "rgba(184,115,51,0.08)" } },
        axisLabel: { color: "#c9b27a", fontSize: 10 },
        nameTextStyle: { color: "#d4af37" },
      },
      series: [
        {
          type: "bar",
          data: bins.map((v, i) => {
            const center = (i / 20) * (max - min) + min;
            return {
              value: v,
              itemStyle: {
                color:
                  center < threshold
                    ? "rgba(230,57,70,0.75)"
                    : "rgba(212,175,55,0.55)",
              },
            };
          }),
          barWidth: "78%",
          markLine: {
            symbol: "none",
            lineStyle: { color: "#e63946", type: "dashed", width: 2 },
            label: {
              formatter: `阈值 ${threshold}`,
              color: "#ff6b6b",
              fontSize: 10,
            },
            data: [{ xAxis: threshold.toFixed(2) }],
          },
        },
      ],
    };
  }, [niyamaPoints, threshold]);

  return <ReactECharts option={option} style={{ height: "100%", width: "100%" }} notMerge />;
}
