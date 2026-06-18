import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { useSimStore } from "@/store/simStore";
import type { DefectPrediction, TempPoint } from "@/lib/api";

interface Props {
  className?: string;
}

function tempToColor(t: number, min: number, max: number): THREE.Color {
  const ratio = Math.max(0, Math.min(1, (t - min) / (max - min + 1e-6)));
  const color = new THREE.Color();
  color.setHSL(0.65 - ratio * 0.65, 0.85, 0.45 + ratio * 0.2);
  return color;
}

function severityColor(severity: string): THREE.Color {
  switch (severity) {
    case "critical":
      return new THREE.Color(0xff1a1a);
    case "high":
      return new THREE.Color(0xff4d4d);
    case "medium":
      return new THREE.Color(0xff8c1a);
    default:
      return new THREE.Color(0xffd93d);
  }
}

function createZunPanGroup(): THREE.Group {
  const group = new THREE.Group();

  const outerGeo = new THREE.CylinderGeometry(1.6, 1.2, 0.4, 48, 1, false);
  group.add(new THREE.Mesh(outerGeo));

  const rimGeo = new THREE.TorusGeometry(1.5, 0.08, 12, 48);
  const rim = new THREE.Mesh(rimGeo);
  rim.rotation.x = Math.PI / 2;
  rim.position.y = 0.2;
  group.add(rim);

  const bodyGeo = new THREE.CylinderGeometry(1.2, 1.0, 0.6, 48, 2, false);
  const body = new THREE.Mesh(bodyGeo);
  body.position.y = -0.5;
  group.add(body);

  for (let i = 0; i < 16; i++) {
    const angle = (i / 16) * Math.PI * 2;
    const dragonGeo = new THREE.SphereGeometry(0.12, 8, 8);
    const dragon = new THREE.Mesh(dragonGeo);
    dragon.position.set(
      Math.cos(angle) * 1.35,
      0.15,
      Math.sin(angle) * 1.35
    );
    group.add(dragon);

    const patternGeo = new THREE.TorusGeometry(0.08, 0.015, 6, 12);
    const pattern = new THREE.Mesh(patternGeo);
    pattern.position.set(
      Math.cos(angle) * 1.1,
      -0.5,
      Math.sin(angle) * 1.1
    );
    group.add(pattern);
  }

  const stemGeo = new THREE.CylinderGeometry(0.5, 0.7, 0.3, 32);
  const stem = new THREE.Mesh(stemGeo);
  stem.position.y = -0.95;
  group.add(stem);

  const baseGeo = new THREE.CylinderGeometry(0.9, 1.1, 0.2, 48);
  const base = new THREE.Mesh(baseGeo);
  base.position.y = -1.2;
  group.add(base);

  return group;
}

export function CastingViewer({ className }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<{
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  controls: OrbitControls;
  castingGroup: THREE.Group;
  particleSystem: THREE.Points | null;
    defectMeshes: THREE.Group;
    tempPointCloud: THREE.Points | null;
  } | null>(null);

  const fillingRatio = useSimStore((s) => s.fillingRatio);
  const showParticles = useSimStore((s) => s.showParticles);
  const showTemperature = useSimStore((s) => s.showTemperature);
  const showDefects = useSimStore((s) => s.showDefects);
  const autoRotate = useSimStore((s) => s.autoRotate);
  const defects = useSimStore((s) => s.defects);
  const tempPoints = useSimStore((s) => s.temperaturePoints);
  const tempRange = useSimStore((s) => s.temperatureRange);
  const setSelectedDefect = useSimStore((s) => s.setSelectedDefect);

  useEffect(() => {
    if (!containerRef.current) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0f);
    scene.fog = new THREE.FogExp2(0x0a0a0f, 0.08);

    const camera = new THREE.PerspectiveCamera(
      45,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      100
    );
    camera.position.set(4, 2.5, 4);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    containerRef.current.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 2;
    controls.maxDistance = 10;
    controls.target.set(0, -0.3, 0);

    const ambient = new THREE.AmbientLight(0x404060, 0.6);
    scene.add(ambient);

    const keyLight = new THREE.DirectionalLight(0xffeedd, 1.2);
    keyLight.position.set(5, 8, 5);
    keyLight.castShadow = true;
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x8899ff, 0.4);
    fillLight.position.set(-5, 2, -3);
    scene.add(fillLight);

    const rimLight = new THREE.PointLight(0xd4af37, 1.5, 10);
    rimLight.position.set(0, 1, -4);
    scene.add(rimLight);

    const castingGroup = createZunPanGroup();
    castingGroup.traverse((obj) => {
      if ((obj as THREE.Mesh).isMesh) {
        const mesh = obj as THREE.Mesh;
        mesh.material = new THREE.MeshStandardMaterial({
          color: 0xb87333,
          metalness: 0.85,
          roughness: 0.35,
          envMapIntensity: 1,
        });
        mesh.castShadow = true;
        mesh.receiveShadow = true;
      }
    });
    scene.add(castingGroup);

    const defectMeshes = new THREE.Group();
    scene.add(defectMeshes);

    const particleCount = 3000;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const velocities = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 2;
      positions[i * 3 + 1] = -1.5 + Math.random() * 0.2;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 2;
      velocities[i * 3] = (Math.random() - 0.5) * 0.01;
      velocities[i * 3 + 1] = 0.005 + Math.random() * 0.015;
      velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.01;
    }
    particleGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute("velocity", new THREE.BufferAttribute(velocities, 3));

    const particleMat = new THREE.PointsMaterial({
      color: 0xff7a2e,
      size: 0.04,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    });
    const particleSystem = new THREE.Points(particleGeo, particleMat);
    scene.add(particleSystem);

    const tempPointCloud: THREE.Points | null = null;

    sceneRef.current = {
      scene,
      camera,
      renderer,
      controls,
      castingGroup,
      particleSystem,
      defectMeshes,
      tempPointCloud,
    };

    let rafId: number;
    const animate = () => {
      rafId = requestAnimationFrame(animate);
      if (autoRotate) {
        castingGroup.rotation.y += 0.003;
      }
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!containerRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    const handleClick = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(defectMeshes.children);
      if (intersects.length > 0) {
        const defectObj = intersects[0].object as any;
        if (defectObj.userData?.defect) {
          setSelectedDefect(defectObj.userData.defect as DefectPrediction);
        }
      } else {
        setSelectedDefect(null);
      }
    };
    renderer.domElement.addEventListener("click", handleClick);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", handleResize);
      renderer.domElement.removeEventListener("click", handleClick);
      renderer.dispose();
      if (containerRef.current && renderer.domElement.parentNode === containerRef.current) {
        containerRef.current.removeChild(renderer.domElement);
      }
      castingGroup.traverse((obj) => {
        if ((obj as THREE.Mesh).isMesh) {
          const mesh = obj as THREE.Mesh;
          mesh.geometry?.dispose?.();
          if (Array.isArray(mesh.material)) {
            mesh.material.forEach((m) => m.dispose());
          } else {
            (mesh.material as THREE.Material)?.dispose?.();
          }
        }
      });
      particleGeo.dispose();
      particleMat.dispose();
    };
  }, [autoRotate, setSelectedDefect]);

  useEffect(() => {
    const ref = sceneRef.current;
    if (!ref || !ref.particleSystem) return;
    ref.particleSystem.visible = showParticles;
  }, [showParticles]);

  useEffect(() => {
    const ref = sceneRef.current;
    if (!ref) return;
    ref.castingGroup.traverse((obj) => {
      if ((obj as THREE.Mesh).isMesh) {
        const mat = (obj as THREE.Mesh).material as THREE.MeshStandardMaterial;
        if (showTemperature && tempPoints.length > 0) {
          const bronze = new THREE.Color(0xb87333);
          const avgTemp = tempPoints.reduce((s, p) => s + p.temperature, 0) / tempPoints.length;
          const heatColor = tempToColor(avgTemp, tempRange.min, tempRange.max);
          mat.color.copy(bronze.lerp(heatColor, 0.4));
          mat.emissive = heatColor;
          mat.emissiveIntensity = 0.25;
        } else {
          mat.color.setHex(0xb87333);
          mat.emissive.setHex(0x000000);
          mat.emissiveIntensity = 0;
        }
      }
    });
  }, [showTemperature, tempPoints, tempRange]);

  useEffect(() => {
    const ref = sceneRef.current;
    if (!ref) return;
    ref.defectMeshes.clear();
    if (!showDefects) return;

    const scale = 2.2;
    defects.forEach((defect) => {
      const r = 0.08 + Math.min(0.25, defect.volume * 0.04);
      const geo = new THREE.SphereGeometry(r, 16, 16);
      const color = severityColor(defect.severity);
      const mat = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.85,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(
        (defect.position.x - 0.5) * scale,
        (defect.position.z - 0.5) * scale - 0.3,
        (defect.position.y - 0.5) * scale
      );
      mesh.userData = { defect };
      ref.defectMeshes.add(mesh);

      const light = new THREE.PointLight(color, defect.severity === "critical" ? 2.5 : 1.2, 1.5);
      light.position.copy(mesh.position);
      ref.defectMeshes.add(light);

      const haloGeo = new THREE.SphereGeometry(r * 1.8, 16, 16);
      const haloMat = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.18,
      });
      const halo = new THREE.Mesh(haloGeo, haloMat);
      halo.position.copy(mesh.position);
      ref.defectMeshes.add(halo);
    });
  }, [defects, showDefects]);

  useEffect(() => {
    const ref = sceneRef.current;
    if (!ref || !ref.particleSystem) return;
    const pos = ref.particleSystem.geometry.attributes.position.array as Float32Array;
    const vel = ref.particleSystem.geometry.attributes.velocity.array as Float32Array;
    const count = pos.length / 3;
    const maxY = -1.3 + fillingRatio * 2.6;

    for (let i = 0; i < count; i++) {
      pos[i * 3] += vel[i * 3];
      pos[i * 3 + 1] += vel[i * 3 + 1];
      pos[i * 3 + 2] += vel[i * 3 + 2];

      if (pos[i * 3 + 1] > maxY || Math.random() < 0.008) {
        pos[i * 3] = (Math.random() - 0.5) * (1.6 * Math.max(0.2, fillingRatio));
        pos[i * 3 + 1] = -1.45;
        pos[i * 3 + 2] = (Math.random() - 0.5) * (1.6 * Math.max(0.2, fillingRatio));
      }
      if (Math.abs(pos[i * 3]) > 1.2) vel[i * 3] *= -0.7;
      if (Math.abs(pos[i * 3 + 2]) > 1.2) vel[i * 3 + 2] *= -0.7;
    }
    ref.particleSystem.geometry.attributes.position.needsUpdate = true;
  }, [fillingRatio]);

  return <div ref={containerRef} className={className} />;
}
