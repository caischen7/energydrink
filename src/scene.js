/*
 * One persistent WebGL scene. The can is choreographed against scroll:
 * each section defines a pose (position in viewport-relative units,
 * tilt, scale, spin rate) and the renderer eases between poses, layering
 * pointer parallax, drag spin, float bob and click pulses on top.
 */
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { buildCan, COLORWAYS } from './can.js';

const SECTIONS = ['hero', 'manifesto', 'specs', 'drop', 'protocol', 'join'];

/* x/y are fractions of half-viewport at z=0; z in world units */
const POSES = {
  hero:      { x: 0,     y: -0.03, z: 0,    rotX: 0.07,  rotZ: 0.05,  scale: 1.14, spin: 0.3 },
  manifesto: { x: 0.40,  y: 0.02,  z: -0.6, rotX: 0.52,  rotZ: -0.38, scale: 0.66, spin: 0.12 },
  specs:     { x: -0.44, y: -0.02, z: -0.4, rotX: -0.06, rotZ: 0.12,  scale: 0.6,  spin: 0.45 },
  drop:      { x: 0.3,   y: -0.04, z: 0.2,  rotX: 0.12,  rotZ: -0.08, scale: 0.82, spin: 0.65 },
  protocol:  { x: 0.3,   y: 0.06,  z: -3.6, rotX: 0.0,   rotZ: 0.1,   scale: 1.0,  spin: 0.1 },
  join:      { x: 0,     y: -0.52, z: 0.9,  rotX: -0.5,  rotZ: 0.06,  scale: 1.2,  spin: 0.55 },
};

const lerp = (a, b, t) => a + (b - a) * t;
const smoothstep = (t) => t * t * (3 - 2 * t);

export function initScene(canvas) {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: true,
    powerPreference: 'high-performance',
  });
  renderer.setClearColor(0x000000, 0);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 50);
  camera.position.set(0, 0, 9);

  /* image-based lighting from the procedural room — no asset downloads */
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();

  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(3, 4, 6);
  scene.add(key);
  const rim = new THREE.PointLight(0xc6ff00, 26, 0, 1.8);
  rim.position.set(-5, 2, -4);
  scene.add(rim);
  const fill = new THREE.PointLight(0xffffff, 8, 0, 2);
  fill.position.set(4, -2, 4);
  scene.add(fill);

  const can = buildCan(renderer.capabilities.getMaxAnisotropy());
  const rig = new THREE.Group(); // pose: position / tilt / scale
  rig.add(can.group); //          can.group: continuous spin
  scene.add(rig);

  /* ---------- scroll keyframes ---------- */
  let keyScroll = SECTIONS.map((_, i) => i * 1000);
  let halfH = 1;
  let halfW = 1;
  let narrow = false;

  function measure() {
    const vh = window.innerHeight;
    keyScroll = SECTIONS.map((id) => {
      const el = document.getElementById(id);
      if (!el) return 0;
      return Math.max(0, el.offsetTop + el.offsetHeight / 2 - vh / 2);
    });
    halfH = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.position.z;
    halfW = halfH * camera.aspect;
    narrow = window.innerWidth < 900;
  }

  function poseAt(scroll) {
    let k = 0;
    while (k < keyScroll.length - 2 && scroll > keyScroll[k + 1]) k++;
    const a = POSES[SECTIONS[k]];
    const b = POSES[SECTIONS[k + 1]];
    const span = Math.max(1, keyScroll[k + 1] - keyScroll[k]);
    const t = smoothstep(Math.min(1, Math.max(0, (scroll - keyScroll[k]) / span)));
    const xDamp = narrow ? 0.18 : 1; // keep the can near centre on phones
    return {
      x: lerp(a.x, b.x, t) * halfW * xDamp,
      y: lerp(a.y, b.y, t) * halfH,
      z: lerp(a.z, b.z, t),
      rotX: lerp(a.rotX, b.rotX, t),
      rotZ: lerp(a.rotZ, b.rotZ, t),
      scale: lerp(a.scale, b.scale, t) * (narrow ? 0.82 : 1),
      spin: lerp(a.spin, b.spin, t),
    };
  }

  /* ---------- pointer ---------- */
  const pointer = { x: 0, y: 0, sx: 0, sy: 0 };
  let dragVel = 0;
  let dragging = false;
  let dragLastX = 0;
  let downAt = { x: 0, y: 0, t: 0 };

  window.addEventListener('pointermove', (e) => {
    pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
    pointer.y = (e.clientY / window.innerHeight) * 2 - 1;
    if (dragging) {
      dragVel += ((e.clientX - dragLastX) / window.innerWidth) * 0.55;
      dragLastX = e.clientX;
    }
  });

  const INTERACTIVE = 'a, button, input, textarea, select, .edition, nav, form';
  window.addEventListener('pointerdown', (e) => {
    if (e.target.closest(INTERACTIVE)) return;
    dragging = true;
    dragLastX = e.clientX;
    downAt = { x: e.clientX, y: e.clientY, t: performance.now() };
  });
  window.addEventListener('pointerup', (e) => {
    if (!dragging) return;
    dragging = false;
    const moved = Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y);
    if (moved < 6 && performance.now() - downAt.t < 400) tryPulse(e);
  });
  window.addEventListener('pointercancel', () => { dragging = false; });

  /* ---------- click pulse (raycast) ---------- */
  const raycaster = new THREE.Raycaster();
  let squash = 0;
  let flash = 0;

  function tryPulse(e) {
    const ndc = new THREE.Vector2(
      (e.clientX / window.innerWidth) * 2 - 1,
      -(e.clientY / window.innerHeight) * 2 + 1
    );
    raycaster.setFromCamera(ndc, camera);
    if (raycaster.intersectObject(can.group, true).length) pulse();
  }

  function pulse() {
    squash = 1;
    flash = 1;
    dragVel += 0.12;
  }

  /* ---------- colorway ---------- */
  function setColorway(name) {
    if (can.setColorway(name)) {
      flash = Math.max(flash, 0.7);
      dragVel += 0.18; // a little kick so the swap reads as an event
      listeners.colorway.forEach((cb) => cb(name));
    }
  }

  const listeners = { colorway: [], fps: [] };

  /* ---------- frame loop ---------- */
  const clock = new THREE.Clock();
  let smooth = window.scrollY;
  let spinAccum = 0.6;
  let frames = 0;
  let fpsAt = performance.now();
  let running = true;
  let rafId = 0;

  function frame() {
    rafId = requestAnimationFrame(frame);
    const dt = Math.min(clock.getDelta(), 0.05);
    const t = clock.elapsedTime;

    const ease = reduceMotion ? 1 : 1 - Math.pow(0.0018, dt); // ~0.1 @ 60fps
    smooth = lerp(smooth, window.scrollY, ease);
    const pose = poseAt(smooth);

    pointer.sx = lerp(pointer.sx, pointer.x, reduceMotion ? 1 : 1 - Math.pow(0.002, dt));
    pointer.sy = lerp(pointer.sy, pointer.y, reduceMotion ? 1 : 1 - Math.pow(0.002, dt));

    /* spin + drag momentum */
    dragVel *= Math.pow(0.04, dt); // friction
    spinAccum += (reduceMotion ? pose.spin * 0.15 : pose.spin) * dt + dragVel * dt * 60 * 0.05;
    can.group.rotation.y = spinAccum;

    /* pose + float + pointer tilt */
    const bob = reduceMotion ? 0 : Math.sin(t * 1.3) * 0.05;
    rig.position.set(pose.x, pose.y + bob, pose.z);
    rig.rotation.x = pose.rotX + pointer.sy * 0.16 + (reduceMotion ? 0 : Math.sin(t * 0.9) * 0.015);
    rig.rotation.z = pose.rotZ + pointer.sx * -0.06;
    rig.rotation.y = pointer.sx * 0.22;

    /* squash & stretch pulse */
    squash = Math.max(0, squash - dt * 2.2);
    const sq = Math.sin(squash * Math.PI) * 0.1;
    rig.scale.set(pose.scale * (1 + sq), pose.scale * (1 - sq), pose.scale * (1 + sq));

    /* emissive flash on colorway swap / tap */
    flash = Math.max(0, flash - dt * 2.4);
    const f = flash * flash * 0.5;
    can.labelMat.emissive.setHex(COLORWAYS[can.getColorway()].flash);
    can.labelMat.emissiveIntensity = f;

    /* camera parallax */
    camera.position.x = pointer.sx * 0.2;
    camera.position.y = pointer.sy * -0.14;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);

    frames++;
    const now = performance.now();
    if (now - fpsAt >= 1000) {
      listeners.fps.forEach((cb) => cb(Math.round((frames * 1000) / (now - fpsAt))));
      frames = 0;
      fpsAt = now;
    }
  }

  function resize() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    measure();
  }

  window.addEventListener('resize', resize);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && running) {
      cancelAnimationFrame(rafId);
      running = false;
    } else if (!document.hidden && !running) {
      running = true;
      clock.getDelta();
      frame();
    }
  });

  resize();
  frame();

  return {
    setColorway,
    pulse,
    refresh: measure,
    redrawLabels: can.redrawLabels,
    onColorway: (cb) => listeners.colorway.push(cb),
    onFps: (cb) => listeners.fps.push(cb),
  };
}
