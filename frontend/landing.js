import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const diagnostic = document.querySelector("[data-live-diagnostic]");
if (diagnostic) {
  const viewport = diagnostic.querySelector(".live-viewport");
  const renderer = new THREE.WebGLRenderer({ canvas: diagnostic.querySelector("[data-live-canvas]"), antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, 0.01, 100);
  scene.add(new THREE.HemisphereLight(0xbae6fd, 0x07090c, 2.7));
  const key = new THREE.DirectionalLight(0xffffff, 3.2); key.position.set(3, -4, 5); scene.add(key);
  const rim = new THREE.DirectionalLight(0x38bdf8, 2); rim.position.set(-3, 2, 4); scene.add(rim);

  const states = [
    { phase:"inspect", model:"broken", control:"Neutral", morphs:[], value:0, frame:"FRAME 001", driver:"controls indexed", shape:"shape keys mapped", label:"Rig inventory", finding:"Reading controls, drivers and deformation targets", evidence:"sandbox copy opened", confidence:"N/A", status:"Inspecting", statusClass:"status-warn", tool:"→ discover_controls", activity:"Listing controls and choosing the first test." },
    { phase:"test", model:"broken", control:"eyeBlink", morphs:["eyeBlink_L"], value:.55, frame:"FRAME 018", driver:"driver: var", shape:"Eye_L.eyeBlink_L", label:"Control test", finding:"Left eyelid has no vertex response", evidence:"affected vertices: 0", confidence:"1.00", status:"Failed", statusClass:"status-bad", tool:"→ set_shape_key", activity:"Exercising both blink controls and recording their response." },
    { phase:"diagnose", model:"broken", control:"eyeBlink", morphs:["eyeBlink_L","eyeBlink_R"], value:.55, frame:"FRAME 024", driver:"driver: var", shape:"Eye_L.eyeBlink_L", label:"Rig fault", finding:"Left blink contains no deformation data", evidence:"left: 0 vertices / right: responsive", confidence:"1.00", status:"Diagnosed", statusClass:"status-bad", tool:"→ compare_mirrored_deformation", activity:"The working right eyelid provides a deterministic repair source." },
    { phase:"repair", model:"broken", control:"eyeBlink", morphs:[], value:0, frame:"PATCH 001", driver:"sandboxed copy", shape:"Eye_L.eyeBlink_L", label:"Guarded repair", finding:"Mirroring the working eyelid deformation", evidence:"source: eyeBlink_R", confidence:"1.00", status:"Repairing", statusClass:"status-warn", tool:"→ mirror_shape_key", activity:"Writing one controlled change to a new .blend copy." },
    { phase:"retest", model:"clean", control:"eyeBlink", morphs:["eyeBlink_L","eyeBlink_R"], value:.55, frame:"RETEST 024", driver:"driver: var", shape:"Eye_L.eyeBlink_L", label:"Repeat test", finding:"Testing both eyelids on the repaired copy", evidence:"left and right eyelids respond", confidence:"N/A", status:"Retesting", statusClass:"status-warn", tool:"→ render_preview", activity:"Running the same blink test again." },
    { phase:"verified", model:"clean", control:"eyeBlink", morphs:["eyeBlink_L","eyeBlink_R"], value:.55, frame:"VERIFIED", driver:"repair retained", shape:"Eye_L.eyeBlink_L", label:"Verification", finding:"Both eyelids now close together", evidence:"affected vertices: restored", confidence:"1.00", status:"Verified", statusClass:"status-ok", tool:"→ publish_repaired_copy", activity:"Verification passed. The original file remains unchanged." },
  ];
  const models = new Map();
  let activeState = states[0], stateIndex = 0, modelsReady = false;
  const setText = (selector, value) => { const el = diagnostic.querySelector(selector); if (el) el.textContent = value; };
  const resize = () => { const width = viewport.clientWidth; renderer.setSize(width, 320, false); camera.aspect = width / 320; camera.updateProjectionMatrix(); };
  new ResizeObserver(resize).observe(viewport);

  function updatePanel(state) {
    const values = {"[data-live-control]":state.control,"[data-live-value]":state.value.toFixed(2),"[data-live-frame]":state.frame,"[data-live-control-node]":state.control,"[data-live-driver-node]":state.driver,"[data-live-shape-node]":state.shape,"[data-live-result-label]":state.label,"[data-live-finding]":state.finding,"[data-live-evidence]":state.evidence,"[data-live-confidence]":state.confidence,"[data-live-status]":state.status,"[data-live-tool]":state.tool,"[data-live-activity]":state.activity,"[data-live-version]":state.model === "clean" ? "AFTER · REPAIRED COPY" : "BEFORE · BROKEN COPY","[data-live-run-status]":state.phase === "verified" ? "REPAIR VERIFIED" : `${state.phase.toUpperCase()} 3D RIG`};
    Object.entries(values).forEach(([selector,value]) => setText(selector,value));
    diagnostic.querySelector("[data-live-bar]").style.width = `${state.value * 100}%`;
    diagnostic.querySelector("[data-live-status]").className = `status-badge ${state.statusClass}`;
    diagnostic.classList.toggle("is-verified", state.phase === "verified");
    diagnostic.querySelectorAll("[data-control]").forEach(el => el.classList.toggle("is-active", el.dataset.control === state.control));
    const activeIndex = states.findIndex(item => item.phase === state.phase);
    diagnostic.querySelectorAll("[data-journey-phase]").forEach((el,index) => { el.classList.toggle("is-active", el.dataset.journeyPhase === state.phase); el.classList.toggle("is-complete", index < activeIndex); });
    models.forEach(({root},name) => { root.visible = name === state.model; });
  }
  function registerModel(name, root) {
    const morphs = new Map();
    root.traverse(object => {
      if (!object.isMesh || !object.morphTargetDictionary) return;
      Object.entries(object.morphTargetDictionary).forEach(([morphName,index]) => { if (!morphs.has(morphName)) morphs.set(morphName,[]); morphs.get(morphName).push({object,index}); });
    });
    models.set(name,{root,morphs}); scene.add(root);
  }
  const loader = new GLTFLoader();
  Promise.all([loader.loadAsync(viewport.dataset.brokenModelUrl),loader.loadAsync(viewport.dataset.cleanModelUrl)]).then(([broken,clean]) => {
    registerModel("broken",broken.scene); registerModel("clean",clean.scene);
    const bounds = new THREE.Box3();
    broken.scene.traverse(object => { if (object.isMesh && /(head|eye|brow|iris|pupil|lip|mouth|nose)/i.test(object.name)) bounds.expandByObject(object); });
    const center = bounds.getCenter(new THREE.Vector3()), size = bounds.getSize(new THREE.Vector3()), extent = Math.max(size.x,size.y,size.z);
    camera.position.set(center.x,center.y + extent * .04,center.z + extent * 2.25); camera.lookAt(center); modelsReady = true; updatePanel(activeState);
  }).catch(() => setText("[data-live-run-status]","3D PREVIEW UNAVAILABLE"));
  const chooseState = () => { activeState = states[stateIndex % states.length]; updatePanel(activeState); stateIndex += 1; };
  chooseState();
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) window.setInterval(chooseState,2600);
  const clock = new THREE.Clock();
  function animate() {
    const alpha = 1 - Math.exp(-clock.getDelta() * 7);
    models.forEach(({morphs}) => morphs.forEach((targets,name) => { const target = activeState.morphs.includes(name) ? activeState.value : 0; targets.forEach(({object,index}) => { object.morphTargetInfluences[index] = THREE.MathUtils.lerp(object.morphTargetInfluences[index],target,alpha); }); }));
    if (modelsReady) renderer.render(scene,camera); window.requestAnimationFrame(animate);
  }
  resize(); animate();
}
