import { useEffect, useRef, useCallback } from "react";
import { ws, api } from "@/lib/api";
import { useSimStore } from "@/store/simStore";

export function useSimulationWS(castingId: string | null) {
  const simWsRef = useRef<WebSocket | null>(null);
  const alertWsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<number | null>(null);

  const addSensorHistory = useSimStore((s) => s.addSensorHistory);
  const setFillingRatio = useSimStore((s) => s.setFillingRatio);
  const setTemperatureData = useSimStore((s) => s.setTemperatureData);
  const setNiyamaPoints = useSimStore((s) => s.setNiyamaPoints);
  const setDefects = useSimStore((s) => s.setDefects);
  const addAlert = useSimStore((s) => s.addAlert);
  const setStatus = useSimStore((s) => s.setStatus);

  const connectSimulation = useCallback(() => {
    if (simWsRef.current) simWsRef.current.close();
    const wsSim = new WebSocket(ws.simulationUrl);
    simWsRef.current = wsSim;

    wsSim.onopen = () => {
      if (heartbeatRef.current) window.clearInterval(heartbeatRef.current);
      heartbeatRef.current = window.setInterval(() => {
        if (wsSim.readyState === WebSocket.OPEN) {
          wsSim.send(JSON.stringify({ type: "ping" }));
        }
      }, 30000);
    };

    wsSim.onmessage = (e) => {
      try {
        const msg: any = JSON.parse(e.data);
        if (msg.type === "simulation_step") {
          setStatus({ current_step: msg.step, total_steps: msg.total_steps });
          setFillingRatio(msg.filling_ratio);
          if (msg.heat) {
            setTemperatureData(msg.heat.points, msg.heat.min_temperature, msg.heat.max_temperature);
          }
          if (msg.niyama) {
            setNiyamaPoints(msg.niyama.points);
          }
          if (msg.defects && msg.defects.length) {
            setDefects(msg.defects);
          }
          if (msg.alerts) {
            msg.alerts.forEach((a: any) => addAlert(a));
          }
        }
      } catch (err) {
        console.warn("WS parse error", err);
      }
    };

    wsSim.onclose = () => {
      if (heartbeatRef.current) window.clearInterval(heartbeatRef.current);
    };
  }, [setFillingRatio, setTemperatureData, setNiyamaPoints, setDefects, addAlert, setStatus]);

  const connectAlerts = useCallback(() => {
    if (alertWsRef.current) alertWsRef.current.close();
    const wsAlert = new WebSocket(ws.alertsUrl);
    alertWsRef.current = wsAlert;
    wsAlert.onmessage = (e) => {
      try {
        const a = JSON.parse(e.data);
        addAlert(a);
      } catch {}
    };
  }, [addAlert]);

  useEffect(() => {
    if (!castingId) return;
    connectSimulation();
    connectAlerts();
    api.getSensorHistory(castingId, 100).then((data) => {
      useSimStore.getState().setSensorHistory(data.reverse());
    });
    api.getDefects(castingId).then((data) => setDefects(data));
    api.getAlerts(castingId, true).then((data) => useSimStore.getState().setAlerts(data));

    return () => {
      simWsRef.current?.close();
      alertWsRef.current?.close();
      if (heartbeatRef.current) window.clearInterval(heartbeatRef.current);
    };
  }, [castingId, connectSimulation, connectAlerts, setDefects]);

  return { simWsRef, alertWsRef };
}
