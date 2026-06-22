/*
 * Procedural 473ml sleek can: lathe-style primitive stack with a
 * CanvasTexture label. No external assets — the whole vessel is code.
 */
import * as THREE from 'three';

export const COLORWAYS = {
  // Bogus Banana flavors — the hero (volt) matches the red-orange mascot
  volt: {
    bg: '#ef4a23',                  // original — red-orange (mascot)
    ink: '#ffffff',
    accent: '#ffd23f',              // banana yellow
    dim: 'rgba(255,255,255,0.6)',
    metal: 0xe2e4e8,
    flash: 0xffd23f,
    label: 'BB-01',
    flavor: 'ORIGINAL BLAST',
    serial: 'Nº 000001 / 10000',
  },
  void: {
    bg: '#4a1d40',                  // midnight berry — deep plum
    ink: '#ffffff',
    accent: '#ffd23f',
    dim: 'rgba(255,255,255,0.55)',
    metal: 0x9aa0a8,
    flash: 0xffd23f,
    label: 'BB-02',
    flavor: 'MIDNIGHT BERRY',
    serial: 'Nº 000001 / 02500',
  },
  glacier: {
    bg: '#ffcf33',                  // frozen banana — yellow
    ink: '#3a2a10',
    accent: '#ef4a23',
    dim: 'rgba(58,42,16,0.55)',
    metal: 0xeaeaec,
    flash: 0xef4a23,
    label: 'BB-03',
    flavor: 'FROZEN BANANA',
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

/* mascot artwork painted onto the label; loads async then triggers a relabel */
const mascotImg = typeof Image !== 'undefined' ? new Image() : null;
let mascotReady = false;
let mascotOnReady = null;
if (mascotImg) {
  mascotImg.onload = () => {
    mascotReady = true;
    if (mascotOnReady) mascotOnReady();
  };
  mascotImg.src = '/mascot.svg';
}

function drawLabel(ctx, c) {
  const W = LABEL_W;
  const H = LABEL_H;
  const panelW = W / 2;

  ctx.fillStyle = c.bg;
  ctx.fillRect(0, 0, W, H);

  const mono = (px) => `${px}px "Inter Variable", system-ui, sans-serif`;
  const display = (px) => `800 ${px}px "Inter Variable", system-ui, sans-serif`;

  for (let p = 0; p < 2; p++) {
    const ox = p * panelW;
    const pad = 78;
    const innerW = panelW - pad * 2;

    /* header strip */
    ctx.fillStyle = c.dim;
    ctx.font = mono(24);
    ctx.textBaseline = 'alphabetic';
    ctx.textAlign = 'left';
    ctx.fillText('BOGUS BANANA CO. — EST. 2026', ox + pad, 96);
    ctx.textAlign = 'right';
    ctx.fillText('473 ML / 16 FL OZ', ox + panelW - pad, 96);
    ctx.fillStyle = c.ink;
    ctx.fillRect(ox + pad, 122, innerW, 3);

    /* wordmark */
    /* mascot emblem — white badge so it reads on any flavor color */
    const ecx = ox + pad + 150;
    const ecy = 348;
    const er = 152;
    ctx.save();
    ctx.beginPath();
    ctx.arc(ecx, ecy, er, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.lineWidth = 6;
    ctx.strokeStyle = c.accent;
    ctx.stroke();
    if (mascotReady && mascotImg) {
      const ms = 250;
      ctx.drawImage(mascotImg, ecx - ms / 2, ecy - ms / 2 + 4, ms, ms);
    } else {
      ctx.fillStyle = c.bg;
      ctx.font = display(150);
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('BB', ecx, ecy);
      ctx.textBaseline = 'alphabetic';
    }
    ctx.restore();

    /* wordmark */
    ctx.textAlign = 'left';
    ctx.fillStyle = c.ink;
    ctx.font = mono(34);
    let ls = 0;
    try {
      ctx.letterSpacing = '14px';
      ls = 1;
    } catch (e) { /* no letterSpacing support */ }
    ctx.fillText(ls ? 'BOGUS BANANA' : 'B O G U S  B A N A N A', ox + pad, 548);
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
      'ENERGY + ELECTROLYTE DRINK :: PH 9.1',
      'ELECTROLYTE STACK 480MG :: NA+ / K+ / MG2+',
      'ZERO SUGAR :: CLEAN CAFFEINE 120MG',
      'SERVE COLD :: NO CRASH :: FLEX YOUR THIRST',
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
    ctx.fillText('BOGUS BANANA — RIDICULOUSLY GOOD ENERGY', 0, 0);
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

  /* canvas fonts / mascot art may finish loading after first draw — repaint labels */
  function redrawLabels() {
    for (const [name, c] of Object.entries(COLORWAYS)) {
      drawLabel(labels[name].canvas.getContext('2d'), c);
      labels[name].tex.needsUpdate = true;
    }
  }
  mascotOnReady = redrawLabels;
  if (mascotReady) redrawLabels();

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
