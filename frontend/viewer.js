import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const root = document.querySelector("[data-rig-viewer]");
if (root) {
  const canvas = root.querySelector("canvas");
  const controlsPanel = document.querySelector("[data-morph-controls]");
  const status = root.querySelector("[data-viewer-status]");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x07090c);
  const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 1000);
  camera.up.set(0, 1, 0);
  camera.position.set(0, 1.5, 6);
  const orbit = new OrbitControls(camera, canvas);
  orbit.enableDamping = true;
  orbit.screenSpacePanning = true;
  scene.add(new THREE.HemisphereLight(0xbae6fd, 0x16202a, 2.5));
  const key = new THREE.DirectionalLight(0xffffff, 3);
  key.position.set(3, -4, 5);
  scene.add(key);
  let modelRoot;
  let fullModelBox;
  const frameBox = (box, padding = 1.35) => {
    if (!box || box.isEmpty()) return;
    const center = box.getCenter(new THREE.Vector3());
    const dimensions = box.getSize(new THREE.Vector3());
    const extent = Math.max(dimensions.x, dimensions.y, dimensions.z, 0.01);
    const distance = (extent * padding) / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));
    orbit.target.copy(center);
    camera.position.set(center.x, center.y + extent * 0.04, center.z + distance);
    camera.near = Math.max(distance / 1000, 0.001);
    camera.far = Math.max(distance * 20, 100);
    camera.updateProjectionMatrix();
    orbit.update();
  };
  const findFaceBox = () => {
    if (!modelRoot) return null;
    const faceBox = new THREE.Box3();
    let found = false;
    modelRoot.traverse((object) => {
      if (!object.isMesh || !/(head|face)/i.test(object.name)) return;
      faceBox.expandByObject(object);
      found = true;
    });
    return found ? faceBox : null;
  };
  document.querySelector("[data-view-face]")?.addEventListener("click", () => frameBox(findFaceBox() || fullModelBox, 1.5));
  document.querySelector("[data-view-full]")?.addEventListener("click", () => frameBox(fullModelBox));
  const resize = () => {
    const width = root.clientWidth;
    const height = Math.max(420, Math.min(680, window.innerHeight * 0.68));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  };
  new ResizeObserver(resize).observe(root);
  new GLTFLoader().load(root.dataset.modelUrl, (gltf) => {
    modelRoot = gltf.scene;
    scene.add(gltf.scene);
    fullModelBox = new THREE.Box3().setFromObject(gltf.scene);
    const morphs = new Map();
    gltf.scene.traverse((object) => {
      if (!object.isMesh || !object.morphTargetDictionary) return;
      Object.entries(object.morphTargetDictionary).forEach(([name, index]) => {
        const controlName = name === "mouthFillJawFollow"
          ? "jawOpen" : name;
        if (!morphs.has(controlName)) morphs.set(controlName, []);
        morphs.get(controlName).push({ object, index });
      });
    });
    controlsPanel.innerHTML = morphs.size ? "" : '<p class="copy">No exported shape keys were found.</p>';
    morphs.forEach((targets, name) => {
      const label = document.createElement("label");
      label.className = "morph-control";
      label.innerHTML = `<span>${name}</span><output>0.00</output>`;
      const input = document.createElement("input");
      Object.assign(input, { type: "range", min: "0", max: "1", step: "0.01", value: "0" });
      input.addEventListener("input", () => {
        targets.forEach(({ object, index }) => { object.morphTargetInfluences[index] = Number(input.value); });
        label.querySelector("output").textContent = Number(input.value).toFixed(2);
        label.classList.toggle("is-active", Number(input.value) !== 0);
      });
      label.appendChild(input);
      controlsPanel.appendChild(label);
    });
    document.querySelector("[data-reset-morphs]")?.addEventListener("click", () => {
      controlsPanel.querySelectorAll('input[type="range"]').forEach((input) => {
        input.value = "0";
        input.dispatchEvent(new Event("input"));
      });
    });
    const faceBox = findFaceBox();
    frameBox(faceBox || fullModelBox, faceBox ? 1.5 : 1.35);
    status.textContent = morphs.size ? "Drag to orbit · Scroll to zoom · Shape keys available" : "Drag to orbit · Scroll to zoom";
  }, undefined, () => {
    status.textContent = "3D model failed to load";
    controlsPanel.innerHTML = '<p class="text-sm text-blackice-danger">Controls unavailable because the 3D model failed to load.</p>';
  });
  const animate = () => { orbit.update(); renderer.render(scene, camera); requestAnimationFrame(animate); };
  resize(); animate();
}
