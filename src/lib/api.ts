const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const WS_BASE = import.meta.env.VITE_WS_BASE || "ws://localhost:8000";

export interface SensorData {
  id?: string;
  casting_id: string;
  timestamp: string;
  wax_temperature: number;
  pouring_temperature: number;
  shell_permeability: number;
  filling_progress: number;
}

export interface DefectPrediction {
  id: string;
  casting_id: string;
  position: { x: number; y: number; z: number };
  niyama_value: number;
  volume: number;
  severity: "low" | "medium" | "high" | "critical";
  defect_type: "shrinkage_cavity" | "shrinkage_porosity";
  detected_at: string;
  mean_temperature?: number;
}

export interface AlertItem {
  id: string;
  casting_id: string;
  alert_type: string;
  severity: "warning" | "error" | "critical";
  message: string;
  data: Record<string, any>;
  acknowledged: boolean;
  acknowledged_at?: string;
  created_at: string;
}

export interface CastingTask {
  id: string;
  name: string;
  status: string;
  created_at: string;
  completed_at?: string;
  parameters: Record<string, any>;
}

export interface SimulationStatus {
  casting_id: string | null;
  status: string;
  filling_progress: number;
  current_step: number;
  total_steps: number;
}

export interface TempPoint {
  x: number;
  y: number;
  z: number;
  temperature: number;
}

export interface NiyamaPoint {
  x: number;
  y: number;
  z: number;
  niyama: number;
}

export interface SimulationStep {
  step: number;
  filling_ratio: number;
  heat: {
    points: TempPoint[];
    max_temperature: number;
    min_temperature: number;
    mean_temperature: number;
  };
  niyama: {
    points: NiyamaPoint[];
    mean_niyama: number;
  };
  defects: DefectPrediction[];
  alerts: AlertItem[];
}

async function request<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  getCastings: () => request<CastingTask[]>("/api/castings"),
  createCasting: (name: string, parameters: Record<string, any>) =>
    request<CastingTask>("/api/castings", {
      method: "POST",
      body: JSON.stringify({ name, parameters }),
    }),
  getLatestSensor: (castingId: string) =>
    request<SensorData>(`/api/sensor/latest?casting_id=${castingId}`),
  getSensorHistory: (castingId: string, limit = 100) =>
    request<SensorData[]>(`/api/sensor/history?casting_id=${castingId}&limit=${limit}`),
  getSimulationStatus: () => request<SimulationStatus>("/api/simulation/status"),
  startSimulation: (castingId: string) =>
    request("/api/simulation/start", {
      method: "POST",
      body: JSON.stringify({ casting_id: castingId }),
    }),
  stopSimulation: () => request("/api/simulation/stop", { method: "POST" }),
  getFillingData: (castingId: string) =>
    request<any[]>(`/api/simulation/filling?casting_id=${castingId}`),
  getTemperatureData: (castingId: string) =>
    request<any[]>(`/api/simulation/temperature?casting_id=${castingId}`),
  getDefects: (castingId: string, severity?: string) =>
    request<DefectPrediction[]>(
      `/api/defects/predictions?casting_id=${castingId}${severity ? `&severity=${severity}` : ""}`
    ),
  getNiyama: (castingId: string) =>
    request<any[]>(`/api/defects/niyama?casting_id=${castingId}`),
  getAlerts: (castingId?: string, unacknowledgedOnly = false) =>
    request<AlertItem[]>(
      `/api/alerts?${castingId ? `casting_id=${castingId}&` : ""}unacknowledged_only=${unacknowledgedOnly}`
    ),
  acknowledgeAlert: (alertId: string) =>
    request(`/api/alerts/${alertId}/acknowledge`, { method: "POST" }),
};

export const ws = {
  simulationUrl: `${WS_BASE}/ws/simulation`,
  alertsUrl: `${WS_BASE}/ws/alerts`,
};
