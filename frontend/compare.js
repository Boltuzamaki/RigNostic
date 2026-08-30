import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const root = document.querySelector("[data-compare-root]");
if (root) {
  const changed = new Set(JSON.parse(root.dataset.changedControls || "[]"));
  const viewers = [];
  let syncing = false;
  let controlsBuilt = false;
  const controlsPanel = document.querySelector("[data-comparison-controls]");

  const buildControls = () => {
    if (controlsBuilt || viewers.length !== 2 || viewers.some((viewer) => !viewer.ready)) return;
    controlsBuilt = true;
    const shared = [...viewers[0].morphs.keys()]
      .filter((name) => viewers.every((viewer) => viewer.morphs.has(name)))
      .sort((a, b) => Number(changed.has(b)) - Number(changed.has(a)) || a.localeCompare(b));
    controlsPanel.innerHTML = shared.length ? "" : '<p class="copy">No shared shape keys were exported.</p>';
    shared.forEach((name) => {
      const label = document.createElement("label");
      label.className = `morph-control${changed.has(name) ? " is-active" : ""}`;
      label.innerHTML = `<span>${name}${changed.has(name) ? " · repaired" : ""}</span><output>0.00</output>`;
      const input = document.createElement("input");
      Object.assign(input, { type: "range", min: "0", max: "1", step: "0.01", value: "0" });
      input.addEventListener("input", () => {
        viewers.forEach((viewer) => viewer.morphs.get(name).forEach(({ object, index }) => {
          object.morphTargetInfluences[index] = Number(input.value);
        }));
        label.querySelector("output").textContent = Number(input.value).toFixed(2);
      });
      label.appendChild(input);
      controlsPanel.appendChild(label);
    });
  };

  const createViewer = (element) => {
    const canvas = element.querySelector("canvas");
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x07090c);
    scene.add(new THREE.HemisphereLight(0xbae6fd, 0x16202a, 2.5));
    const light = new THREE.DirectionalLight(0xffffff, 3);
    light.position.set(3, -4, 5);
    scene.add(light);
    const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 1000);
    const orbit = new OrbitControls(camera, canvas);
    orbit.enableDamping = true;
    const viewer = { element, renderer, scene, camera, orbit, morphs: new Map(), ready: false };
    const resize = () => {
      const width = element.clientWidth;
      const height = Math.max(360, Math.min(560, window.innerHeight * 0.55));
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    new ResizeObserver(resize).observe(element);
    orbit.addEventListener("change", () => {
      if (syncing) return;
      syncing = true;
      viewers.filter((other) => other !== viewer).forEach((other) => {
        other.camera.position.copy(camera.position);
        other.camera.quaternion.copy(camera.quaternion);
        other.orbit.target.copy(orbit.target);
        other.orbit.update();
      });
      syncing = false;
    });
    new GLTFLoader().load(element.dataset.modelUrl, (gltf) => {
      scene.add(gltf.scene);
      gltf.scene.traverse((object) => {
        if (!object.isMesh || !object.morphTargetDictionary) return;
        Object.entries(object.morphTargetDictionary).forEach(([name, index]) => {
          const controlName = name === "mouthFillJawFollow"
            ? "jawOpen" : name;
          if (!viewer.morphs.has(controlName)) viewer.morphs.set(controlName, []);
          viewer.morphs.get(controlName).push({ object, index });
        });
      });
      const box = new THREE.Box3().setFromObject(gltf.scene);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const extent = Math.max(size.x, size.y, size.z, 0.01);
      const distance = extent * 1.45 / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));
      orbit.target.copy(center);
      camera.position.set(center.x, center.y - distance, center.z + extent * 0.08);
      orbit.update();
      viewer.ready = true;
      element.querySelector("[data-viewer-status]").textContent = "Drag to orbit · Cameras synchronized";
      buildControls();
    }, undefined, () => { element.querySelector("[data-viewer-status]").textContent = "3D model failed to load"; });
    const animate = () => { orbit.update(); renderer.render(scene, camera); requestAnimationFrame(animate); };
    resize(); animate();
    return viewer;
  };

  document.querySelectorAll("[data-compare-viewer]").forEach((panel) => viewers.push(createViewer(panel)));
  document.querySelector("[data-reset-comparison]")?.addEventListener("click", () => {
    controlsPanel.querySelectorAll('input[type="range"]').forEach((input) => {
      input.value = "0";
      input.dispatchEvent(new Event("input"));
    });
  });
}
