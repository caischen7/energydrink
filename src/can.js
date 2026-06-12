/*
 * Procedural 473ml sleek can: lathe-style primitive stack with a
 * CanvasTexture label. No external assets — the whole vessel is code.
 */
import * as THREE from 'three';

export const COLORWAYS = {
  volt: {
    bg: '#c6ff00',
    ink: '#0a0a0a',
    accent: '#0a0a0a',
    dim: 'rgba(10,10,10,0.55)',
    metal: 0xd8d8d8,
    flash: 0xc6ff00,
    label: 'VOLT-001',
    flavor: 'CITRUS STATIC',
    serial: 'Nº 000001 / 10000',
  },
  void: {
    bg: '#0d0d0d',
    ink: '#ededed',
    accent: '#c6ff00',
    dim: 'rgba(237,237,237,0.5)',
    metal: 0x8f8f8f,
    flash: 0xc6ff00,
    label: 'VOID-002',
    flavor: 'BLACKBERRY NULL',
    serial: 'Nº 000001 / 02500',
  },
  glacier: {
    bg: '#e9f2f5',
    ink: '#0a0a0a',
    accent: '#2491ff',
    dim: 'rgba(10,10,10,0.5)',
    metal: 0xe8e8e8,
    flash: 0x9fd8ff,
    label: 'GLCR-003',
    flavor: 'GLACIAL FREEZE',
    serial: 'Nº 000001 / 00500',
  },
};

/* deterministic rand so barcodes/QR match across colorways */
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const LABEL_W = 2048;
const LABEL_H = 1024;

function drawLabel(ctx, c) {
  const W = LABEL_W;
  const H = LABEL_H;
  const panelW = W / 2;

  ctx.fillStyle = c.bg;
  ctx.fillRect(0, 0, W, H);

  const mono = (px) => `${px}px "Space Mono", monospace`;
  const display = (px) => `900 ${px}px "Archivo Variable", "Arial Black", sans-serif`;
  try {
    ctx.fontStretch = 'ultra-expanded';
  } catch (e) {
    /* older canvas impl — expanded type is a progressive enhancement */
  }

  for (let p = 0; p < 2; p++) {
    const ox = p * panelW;
    const pad = 78;
    const innerW = panelW - pad * 2;

    /* header strip */
    ctx.fillStyle = c.dim;
    ctx.font = mono(24);
    ctx.textBaseline = 'alphabetic';
    ctx.textAlign = 'left';
    ctx.fillText('ION BEVERAGE SYSTEMS — EST. 2086', ox + pad, 96);
    ctx.textAlign = 'right';
    ctx.fillText('473 ML / 16 FL OZ', ox + panelW - pad, 96);
    ctx.fillStyle = c.ink;
    ctx.fillRect(ox + pad, 122, innerW, 3);

    /* wordmark */
    ctx.textAlign = 'left';
    ctx.fillStyle = c.ink;
    ctx.font = display(338);
    ctx.fillText('ION', ox + pad - 10, 462);
    ctx.font = mono(40);
    ctx.fillText('®', ox + pad + 660, 220);

    ctx.font = mono(34);
    ctx.fillStyle = c.ink;
    let ls = 0;
    try {
      ctx.letterSpacing = '22px';
      ls = 1;
    } catch (e) { /* no letterSpacing support */ }
    ctx.fillText(ls ? 'LIQUID HARDWARE' : 'L I Q U I D  H A R D W A R E', ox + pad, 548);
    try { ctx.letterSpacing = '0px'; } catch (e) { /* noop */ }

    /* accent bar + edition */
    ctx.fillStyle = c.accent;
    ctx.fillRect(ox + pad, 596, innerW * 0.62, 16);
    ctx.fillStyle = c.ink;
    ctx.font = mono(26);
    ctx.textAlign = 'right';
    ctx.fillText(`${c.label} — ${c.flavor}`, ox + panelW - pad, 610);

    /* spec block */
    ctx.textAlign = 'left';
    ctx.font = mono(23);
    ctx.fillStyle = c.dim;
    const specs = [
      'STRUCTURED HYDRATION SYSTEM // ALKALINE ARCH. PH 9.1',
      'ELECTROLYTE STACK 480MG :: NA+ / K+ / MG2+',
      'GLYCEMIC PAYLOAD 000G :: FOCUS COMPOUND 120MG',
      'SERVE AT 4°C :: SHAKE NOTHING :: TRUST THE LEDGER',
    ];
    specs.forEach((s, i) => ctx.fillText(s, ox + pad, 688 + i * 40));

    /* barcode (deterministic) */
    const rand = mulberry32(20860612);
    let bx = ox + pad;
    const by = 868;
    const bh = 96;
    ctx.fillStyle = c.ink;
    while (bx < ox + pad + 420) {
      const bw = 3 + Math.floor(rand() * 12);
      if (rand() > 0.42) ctx.fillRect(bx, by, bw, bh);
      bx += bw + 3;
    }
    ctx.font = mono(22);
    ctx.fillStyle = c.dim;
    ctx.fillText(`SERIAL ${c.serial}`, ox + pad, 996);

    /* data block (QR-ish), same seed every colorway */
    const qrand = mulberry32(473);
    const qs = 14;
    const qn = 13;
    const qx = ox + panelW - pad - qn * qs;
    const qy = 836;
    ctx.fillStyle = c.ink;
    for (let i = 0; i < qn; i++) {
      for (let j = 0; j < qn; j++) {
        if (qrand() > 0.52) ctx.fillRect(qx + i * qs, qy + j * qs, qs - 2, qs - 2);
      }
    }
    ctx.font = mono(20);
    ctx.fillStyle = c.dim;
    ctx.textAlign = 'right';
    ctx.fillText('SCAN TO VERIFY', ox + panelW - pad, 996);

    /* vertical edge tag */
    ctx.save();
    ctx.translate(ox + panelW - 26, 470);
    ctx.rotate(Math.PI / 2);
    ctx.font = mono(22);
    ctx.fillStyle = c.dim;
    ctx.textAlign = 'center';
    ctx.fillText('GENESIS DROP — DO NOT RESELL THIRST', 0, 0);
    ctx.restore();
  }

  /* fake ambient occlusion toward the can's ends */
  const gTop = ctx.createLinearGradient(0, 0, 0, 70);
  gTop.addColorStop(0, 'rgba(0,0,0,0.38)');
  gTop.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = gTop;
  ctx.fillRect(0, 0, W, 70);
  const gBot = ctx.createLinearGradient(0, H - 80, 0, H);
  gBot.addColorStop(0, 'rgba(0,0,0,0)');
  gBot.addColorStop(1, 'rgba(0,0,0,0.42)');
  ctx.fillStyle = gBot;
  ctx.fillRect(0, H - 80, W, 80);
}

function makeLabelTexture(colorway, maxAnisotropy) {
  const canvas = document.createElement('canvas');
  canvas.width = LABEL_W;
  canvas.height = LABEL_H;
  drawLabel(canvas.getContext('2d'), colorway);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = Math.min(8, maxAnisotropy || 1);
  tex.wrapS = THREE.RepeatWrapping;
  return { canvas, tex };
}

export function buildCan(maxAnisotropy) {
  const group = new THREE.Group();

  const labels = {};
  for (const [name, c] of Object.entries(COLORWAYS)) {
    labels[name] = makeLabelTexture(c, maxAnisotropy);
  }

  const metalMat = new THREE.MeshStandardMaterial({
    color: COLORWAYS.volt.metal,
    metalness: 1.0,
    roughness: 0.3,
  });
  const lidMat = new THREE.MeshStandardMaterial({
    color: 0xcfcfcf,
    metalness: 1.0,
    roughness: 0.38,
  });
  const labelMat = new THREE.MeshPhysicalMaterial({
    map: labels.volt.tex,
    metalness: 0.55,
    roughness: 0.34,
    clearcoat: 0.8,
    clearcoatRoughness: 0.22,
  });

  const R = 0.5; // body radius
  const NECK = 0.43; // rim radius
  const BODY_H = 2.0;

  const add = (geo, mat, y = 0, rx = 0) => {
    const m = new THREE.Mesh(geo, mat);
    m.position.y = y;
    m.rotation.x = rx;
    group.add(m);
    return m;
  };

  // label wrap
  add(new THREE.CylinderGeometry(R, R, BODY_H, 96, 1, true), labelMat, 0);
  // shoulder + base tapers
  add(new THREE.CylinderGeometry(NECK, R, 0.16, 96, 1, true), metalMat, BODY_H / 2 + 0.08);
  add(new THREE.CylinderGeometry(R, NECK, 0.14, 96, 1, true), metalMat, -BODY_H / 2 - 0.07);
  // rims
  add(new THREE.TorusGeometry(NECK, 0.024, 24, 96), metalMat, BODY_H / 2 + 0.17, Math.PI / 2);
  add(new THREE.TorusGeometry(NECK, 0.024, 24, 96), metalMat, -BODY_H / 2 - 0.15, Math.PI / 2);
  // lid + panel groove
  add(new THREE.CircleGeometry(NECK, 96), lidMat, BODY_H / 2 + 0.155, -Math.PI / 2);
  add(new THREE.TorusGeometry(0.3, 0.012, 16, 96), lidMat, BODY_H / 2 + 0.162, Math.PI / 2);
  // bottom cap
  add(new THREE.CircleGeometry(NECK, 96), lidMat, -BODY_H / 2 - 0.14, Math.PI / 2);

  // pull tab
  const tab = new THREE.Group();
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.062, 0.014, 16, 48), lidMat);
  ring.rotation.x = Math.PI / 2;
  tab.add(ring);
  const rivet = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.02, 24), lidMat);
  rivet.position.set(-0.095, 0.004, 0);
  tab.add(rivet);
  const stem = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.012, 0.05), lidMat);
  stem.position.set(-0.05, 0.002, 0);
  tab.add(stem);
  tab.position.set(0.09, BODY_H / 2 + 0.172, 0);
  tab.rotation.y = 0.6;
  group.add(tab);

  let current = 'volt';

  function setColorway(name) {
    if (!labels[name] || name === current) return false;
    current = name;
    labelMat.map = labels[name].tex;
    labelMat.needsUpdate = true;
    metalMat.color.setHex(COLORWAYS[name].metal);
    return true;
  }

  /* canvas fonts may finish loading after first draw — repaint labels */
  function redrawLabels() {
    for (const [name, c] of Object.entries(COLORWAYS)) {
      drawLabel(labels[name].canvas.getContext('2d'), c);
      labels[name].tex.needsUpdate = true;
    }
  }

  return {
    group,
    setColorway,
    redrawLabels,
    getColorway: () => current,
    labelMat,
    metalMat,
    height: BODY_H + 0.35,
  };
}
