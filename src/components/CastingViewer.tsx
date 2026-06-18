import { useEffect, useRef, useState } from "react";
import { useSimStore } from "@/store/simStore";
import type { DefectPrediction } from "@/lib/api";
import {
  setupScene,
  updateAnnotations as computeAnnotations,
  updateParticles,
  updateTemperatureVisual,
  severityColorHex,
  severityLabel,
  type ScreenAnnotation,
  type SceneRef,
} from "@/lib/lost_wax_3d";

interface Props {
  className?: string;
}

export function CastingViewer({ className }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<SceneRef | null>(null);
  const castingMeshesRef = useRef<any[]>([]);

  const fillingRatio = useSimStore((s) => s.fillingRatio);
  const showParticles = useSimStore((s) => s.showParticles);
  const showTemperature = useSimStore((s) => s.showTemperature);
  const showDefects = useSimStore((s) => s.showDefects);
  const autoRotate = useSimStore((s) => s.autoRotate);
  const defects = useSimStore((s) => s.defects);
  const tempPoints = useSimStore((s) => s.temperaturePoints);
  const tempRange = useSimStore((s) => s.temperatureRange);
  const setSelectedDefect = useSimStore((s) => s.setSelectedDefect);
  const selectedDefect = useSimStore((s) => s.selectedDefect);

  const [annotations, setAnnotations] = useState<ScreenAnnotation[]>([]);

  useEffect(() => {
    if (!containerRef.current) return;

    const { sceneRef: sRef, castingMeshes, cleanup, rafIdRef } = setupScene(
      containerRef.current
    );
    sceneRef.current = sRef;
    castingMeshesRef.current = castingMeshes;

    const animate = () => {
      rafIdRef.value = requestAnimationFrame(animate);
      if (autoRotate) {
        sRef.castingGroup.rotation.y += 0.003;
      }
      sRef.controls.update();
      sRef.renderer.render(sRef.scene, sRef.camera);
      if (showDefects && defects.length > 0 && containerRef.current) {
        const anns = computeAnnotations(
          containerRef.current,
          defects,
          sRef,
          castingMeshes
        );
        setAnnotations(anns);
      }
    };
    animate();

    return cleanup;
  }, [autoRotate, showDefects, defects]);

  useEffect(() => {
    const ref = sceneRef.current;
    if (!ref || !ref.particleSystem) return;
    ref.particleSystem.visible = showParticles;
  }, [showParticles]);

  useEffect(() => {
    const ref = sceneRef.current;
    if (!ref) return;
    updateTemperatureVisual(ref, showTemperature, tempPoints, tempRange);
  }, [showTemperature, tempPoints, tempRange]);

  useEffect(() => {
    const ref = sceneRef.current;
    if (!ref) return;
    updateParticles(ref, fillingRatio);
  }, [fillingRatio]);

  const handleAnnotationClick = (defect: DefectPrediction) => {
    setSelectedDefect(selectedDefect?.id === defect.id ? null : defect);
  };

  return (
    <div ref={containerRef} className={`relative ${className ?? ""}`}>
      <div
        ref={overlayRef}
        className="absolute inset-0 pointer-events-none"
        style={{ zIndex: 10 }}
      >
        {showDefects &&
          annotations.map((ann) => {
            if (!ann.visible) return null;
            const color = severityColorHex(ann.defect.severity);
            const size = 14 + Math.min(20, ann.defect.volume * 3);
            const isSelected = selectedDefect?.id === ann.defect.id;
            return (
              <div
                key={ann.id}
                className="absolute pointer-events-auto cursor-pointer"
                style={{
                  left: ann.x,
                  top: ann.y,
                  transform: "translate(-50%, -50%)",
                  opacity: ann.occluded ? 0.35 : 1,
                  transition: "opacity 0.15s",
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  handleAnnotationClick(ann.defect);
                }}
              >
                <div
                  className="rounded-full animate-pulse"
                  style={{
                    width: size,
                    height: size,
                    background: color,
                    boxShadow: `0 0 ${isSelected ? 20 : 10}px ${color}, 0 0 ${isSelected ? 30 : 16}px ${color}66`,
                    border: isSelected
                      ? `2px solid #fff`
                      : `1px solid ${color}cc`,
                  }}
                />
                {(isSelected ||
                  ann.defect.severity === "critical" ||
                  ann.defect.severity === "high") && (
                  <div
                    className="absolute left-1/2 -translate-x-1/2 whitespace-nowrap rounded px-2 py-1 text-[10px] font-mono"
                    style={{
                      top: size + 4,
                      background: "rgba(10, 10, 15, 0.88)",
                      border: `1px solid ${color}88`,
                      color,
                      backdropFilter: "blur(4px)",
                    }}
                  >
                    <div className="font-bold">
                      {severityLabel(ann.defect.severity)}缺陷
                    </div>
                    <div className="opacity-75">
                      V={ann.defect.volume.toFixed(2)}cm³
                    </div>
                    <div className="opacity-75">
                      Niyama={ann.defect.niyama_value.toFixed(3)}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
      </div>
    </div>
  );
}
