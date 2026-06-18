import { create } from "zustand";
import type {
  SensorData,
  DefectPrediction,
  AlertItem,
  SimulationStatus,
  TempPoint,
  NiyamaPoint,
} from "@/lib/api";

export interface SimulationState {
  castingId: string | null;
  castingName: string;
  status: SimulationStatus;
  latestSensor: SensorData | null;
  sensorHistory: SensorData[];
  fillingRatio: number;
  temperaturePoints: TempPoint[];
  temperatureRange: { min: number; max: number };
  niyamaPoints: NiyamaPoint[];
  defects: DefectPrediction[];
  alerts: AlertItem[];
  autoRotate: boolean;
  showParticles: boolean;
  showTemperature: boolean;
  showDefects: boolean;
  selectedDefect: DefectPrediction | null;

  setCasting: (id: string, name: string) => void;
  setStatus: (s: Partial<SimulationStatus>) => void;
  setLatestSensor: (s: SensorData) => void;
  addSensorHistory: (s: SensorData) => void;
  setSensorHistory: (arr: SensorData[]) => void;
  setFillingRatio: (v: number) => void;
  setTemperatureData: (points: TempPoint[], min: number, max: number) => void;
  setNiyamaPoints: (pts: NiyamaPoint[]) => void;
  setDefects: (d: DefectPrediction[]) => void;
  addAlert: (a: AlertItem) => void;
  setAlerts: (arr: AlertItem[]) => void;
  acknowledgeAlert: (id: string) => void;
  setAutoRotate: (v: boolean) => void;
  toggleShowParticles: () => void;
  toggleShowTemperature: () => void;
  toggleShowDefects: () => void;
  setSelectedDefect: (d: DefectPrediction | null) => void;
}

export const useSimStore = create<SimulationState>((set) => ({
  castingId: null,
  castingName: "",
  status: {
    casting_id: null,
    status: "idle",
    filling_progress: 0,
    current_step: 0,
    total_steps: 60,
  },
  latestSensor: null,
  sensorHistory: [],
  fillingRatio: 0,
  temperaturePoints: [],
  temperatureRange: { min: 25, max: 1200 },
  niyamaPoints: [],
  defects: [],
  alerts: [],
  autoRotate: true,
  showParticles: true,
  showTemperature: true,
  showDefects: true,
  selectedDefect: null,

  setCasting: (id, name) => set({ castingId: id, castingName: name }),
  setStatus: (s) => set((state) => ({ status: { ...state.status, ...s } })),
  setLatestSensor: (s) => set({ latestSensor: s }),
  addSensorHistory: (s) =>
    set((state) => ({
      sensorHistory: [...state.sensorHistory.slice(-200), s],
    })),
  setSensorHistory: (arr) => set({ sensorHistory: arr }),
  setFillingRatio: (v) => set({ fillingRatio: v }),
  setTemperatureData: (points, min, max) =>
    set({ temperaturePoints: points, temperatureRange: { min, max } }),
  setNiyamaPoints: (pts) => set({ niyamaPoints: pts }),
  setDefects: (d) => set({ defects: d }),
  addAlert: (a) => set((state) => ({ alerts: [a, ...state.alerts] })),
  setAlerts: (arr) => set({ alerts: arr }),
  acknowledgeAlert: (id) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === id ? { ...a, acknowledged: true } : a
      ),
    })),
  setAutoRotate: (v) => set({ autoRotate: v }),
  toggleShowParticles: () => set((s) => ({ showParticles: !s.showParticles })),
  toggleShowTemperature: () => set((s) => ({ showTemperature: !s.showTemperature })),
  toggleShowDefects: () => set((s) => ({ showDefects: !s.showDefects })),
  setSelectedDefect: (d) => set({ selectedDefect: d }),
}));
