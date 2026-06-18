import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { DefectPrediction, TempPoint } from "./api";

export interface ScreenAnnotation {
  id: string;
  x: number;
  y: number;
  visible: boolean;
  occluded: boolean;
  defect: DefectPrediction;
}

export interface SceneRef {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  controls: OrbitControls;
  castingGroup: THREE.Group;
  particleSystem: THREE.Points | null;
  tempPointCloud: THREE.Points | null;
  raycaster: THREE.Raycaster;
  ndcVec: THREE.Vector3;
}

export const SCALE = 2.2;
export const DEFECT_WORLD_OFFSET = new THREE.Vector3(
  -SCALE * 0.5,
  -SCALE * 0.5 - 0.3,
  -SCALE * 0.5
);

export function tempToColor(t: number, min: number, max: number): THREE.Color {
  const ratio = Math.max(0, Math.min(1, (t - min) / (max - min + 1e-6)));
  const color = new THREE.Color();
  color.setHSL(0.65 - ratio * 0.65, 0.85, 0.45 + ratio * 0.2);
  return color;
}

export function severityColorHex(severity: string): string {
  switch (severity) {
    case "critical":
      return "#ff1a1a";
    case "high":
      return "#ff4d4d";
    case "medium":
      return "#ff8c1a";
    default:
      return "#ffd93d";
  }
}

export function severityLabel(severity: string): string {
  switch (severity) {
    case "critical":
      return "严重";
    case "high":
      return "高危";
    case "medium":
      return "中等";
    default:
      return "轻微";
  }
}

export function createZunPanGroup(): THREE.Group {
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

export function defectToWorld(defect: DefectPrediction): THREE.Vector3 {
  return new THREE.Vector3(
    (defect.position.x - 0.5) * SCALE,
    (defect.position.z - 0.5) * SCALE - 0.3,
    (defect.position.y - 0.5) * SCALE
  );
}

export function setupScene(container: HTMLDivElement): {
  sceneRef: SceneRef;
  castingMeshes: THREE.Mesh[];
  cleanup: () => void;
  rafIdRef: { value: number };
} {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0a0f);
  scene.fog = new THREE.FogExp2(0x0a0a0f, 0.08);

  const camera = new THREE.PerspectiveCamera(
    45,
    container.clientWidth / container.clientHeight,
    0.1,
    100
  );
  camera.position.set(4, 2.5, 4);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.appendChild(renderer.domElement);

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
  const raycaster = new THREE.Raycaster();
  const ndcVec = new THREE.Vector3();

  const castingMeshes: THREE.Mesh[] = [];
  castingGroup.traverse((obj) => {
    if ((obj as THREE.Mesh).isMesh) castingMeshes.push(obj as THREE.Mesh);
  });

  const sceneRef: SceneRef = {
    scene,
    camera,
    renderer,
    controls,
    castingGroup,
    particleSystem,
    tempPointCloud,
    raycaster,
    ndcVec,
  };

  const rafIdRef = { value: 0 };

  const handleResize = () => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  };
  window.addEventListener("resize", handleResize);

  const cleanup = () => {
    cancelAnimationFrame(rafIdRef.value);
    window.removeEventListener("resize", handleResize);
    renderer.dispose();
    if (container && renderer.domElement.parentNode === container) {
      container.removeChild(renderer.domElement);
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

  return { sceneRef, castingMeshes, cleanup, rafIdRef };
}

export function updateAnnotations(
  container: HTMLDivElement,
  defects: DefectPrediction[],
  sceneRef: SceneRef,
  castingMeshes: THREE.Mesh[]
): ScreenAnnotation[] {
  const rect = container.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;
  const { camera, raycaster, ndcVec } = sceneRef;

  return defects.map((defect) => {
    const worldPos = defectToWorld(defect);
    const projected = worldPos.clone().project(camera);
    const screenX = (projected.x * 0.5 + 0.5) * width;
    const screenY = (-projected.y * 0.5 + 0.5) * height;
    const visible =
      projected.z >= -1 &&
      projected.z <= 1 &&
      screenX >= 0 &&
      screenX <= width &&
      screenY >= 0 &&
      screenY <= height;

    let occluded = false;
    if (visible) {
      ndcVec.set(
        (screenX / width) * 2 - 1,
        -(screenY / height) * 2 + 1,
        projected.z
      );
      raycaster.setFromCamera(new THREE.Vector2(ndcVec.x, ndcVec.y), camera);
      const intersects = raycaster.intersectObjects(castingMeshes, false);
      if (intersects.length > 0) {
        const defectDist = camera.position.distanceTo(worldPos);
        occluded = intersects[0].distance + 0.05 < defectDist;
      }
    }

    return {
      id: defect.id,
      x: screenX,
      y: screenY,
      visible,
      occluded,
      defect,
    };
  });
}

export function updateParticles(
  sceneRef: SceneRef,
  fillingRatio: number
): void {
  if (!sceneRef.particleSystem) return;
  const pos = sceneRef.particleSystem.geometry.attributes.position
    .array as Float32Array;
  const vel = sceneRef.particleSystem.geometry.attributes.velocity
    .array as Float32Array;
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
  sceneRef.particleSystem.geometry.attributes.position.needsUpdate = true;
}

export function updateTemperatureVisual(
  sceneRef: SceneRef,
  showTemperature: boolean,
  tempPoints: TempPoint[],
  tempRange: { min: number; max: number }
): void {
  sceneRef.castingGroup.traverse((obj) => {
    if ((obj as THREE.Mesh).isMesh) {
      const mat = (obj as THREE.Mesh).material as THREE.MeshStandardMaterial;
      if (showTemperature && tempPoints.length > 0) {
        const bronze = new THREE.Color(0xb87333);
        const avgTemp =
          tempPoints.reduce((s, p) => s + p.temperature, 0) / tempPoints.length;
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
}
