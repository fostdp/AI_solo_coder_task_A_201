import ReactECharts from "echarts-for-react";
import { useMemo } from "react";
import { useSimStore } from "@/store/simStore";

export function SensorCharts() {
  const history = useSimStore((s) => s.sensorHistory);

  const option = useMemo(() => {
    const times = history.map((d) =>
      new Date(d.timestamp).toLocaleTimeString("zh-CN", { hour12: false })
    );
    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(13,13,20,0.92)",
        borderColor: "#b87333",
        textStyle: { color: "#e8d5a3" },
      },
      legend: {
        data: ["蜡模温度", "浇铸温度", "透气性", "充型进度"],
        textStyle: { color: "#d4af37" },
        top: 0,
      },
      grid: { left: 48, right: 56, top: 36, bottom: 28 },
      xAxis: {
        type: "category",
        data: times,
        axisLine: { lineStyle: { color: "#5a4a2a" } },
        axisLabel: { color: "#c9b27a", fontSize: 10 },
      },
      yAxis: [
        {
          type: "value",
          name: "温度 °C",
          axisLine: { lineStyle: { color: "#5a4a2a" } },
          splitLine: { lineStyle: { color: "rgba(184,115,51,0.08)" } },
          axisLabel: { color: "#c9b27a", fontSize: 10 },
          nameTextStyle: { color: "#d4af37" },
        },
        {
          type: "value",
          name: "%",
          max: 100,
          axisLine: { lineStyle: { color: "#5a4a2a" } },
          splitLine: { show: false },
          axisLabel: { color: "#c9b27a", fontSize: 10 },
          nameTextStyle: { color: "#d4af37" },
        },
      ],
      series: [
        {
          name: "蜡模温度",
          type: "line",
          smooth: true,
          showSymbol: false,
          data: history.map((d) => d.wax_temperature),
          lineStyle: { color: "#ff8a3d", width: 2 },
          itemStyle: { color: "#ff8a3d" },
          areaStyle: {
            color: {
              type: "linear",
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(255,138,61,0.35)" },
                { offset: 1, color: "rgba(255,138,61,0)" },
              ],
            },
          },
        },
        {
          name: "浇铸温度",
          type: "line",
          smooth: true,
          showSymbol: false,
          data: history.map((d) => d.pouring_temperature),
          lineStyle: { color: "#e63946", width: 2 },
          itemStyle: { color: "#e63946" },
        },
        {
          name: "透气性",
          type: "line",
          smooth: true,
          showSymbol: false,
          yAxisIndex: 1,
          data: history.map((d) => d.shell_permeability),
          lineStyle: { color: "#457b9d", width: 2 },
          itemStyle: { color: "#457b9d" },
        },
        {
          name: "充型进度",
          type: "line",
          smooth: true,
          showSymbol: false,
          yAxisIndex: 1,
          data: history.map((d) => d.filling_progress),
          lineStyle: { color: "#d4af37", width: 3 },
          itemStyle: { color: "#d4af37" },
        },
      ],
    };
  }, [history]);

  return (
    <div className="h-full w-full">
      <ReactECharts option={option} style={{ height: "100%", width: "100%" }} notMerge />
    </div>
  );
}
