/*
 * FORMULATION MAP — the dashboard's per-brand spec view: caffeine × sugar,
 * not just flavor. A CPG buyer needs to know whether open market space is a
 * flavor gap or a *spec* gap (e.g. "high-caffeine zero-sugar" is crowded,
 * but "high-caffeine + zero-sugar + low-calorie" may not be).
 *
 * Serving sizes in the source CSV vary wildly (a 1.93oz shot vs a 16oz can),
 * and both report caffeine_mg/sugar_g as their as-labeled per-serving amount
 * — not normalized. Comparing those raw numbers across brands is misleading
 * (a tiny shot looks "low caffeine" only because the serving is tiny), so
 * every brand is normalized to a common per-8oz basis before plotting.
 */
import { scatter, panel, VOLT, ICE } from '../charts.js';

export function formulationMap(data) {
  const n = data.nutrition;

  const norm = n.map((d) => ({
    brand: d.brand,
    caffeine_mg_per_8oz: (d.caffeine_mg / d.serving_oz) * 8,
    sugar_g_per_8oz: (d.sugar_g / d.serving_oz) * 8,
    calories: d.calories,
    sweetener: d.sweetener,
  }));

  const pts = norm.map((d) => ({
    x: d.caffeine_mg_per_8oz,
    y: d.sugar_g_per_8oz,
    r: d.calories,
    label: d.brand,
    color: d.sugar_g_per_8oz === 0 ? VOLT : ICE,
  }));

  const chart = scatter(pts, {
    xLabel: 'CAFFEINE (MG PER 8 FL OZ)',
    yLabel: 'SUGAR (G PER 8 FL OZ)',
    xMin: 0,
    yMin: 0,
    xFmt: (v) => Math.round(v),
  });

  // Crowded cluster: moderate-high normalized caffeine (~130-150mg/8oz),
  // zero sugar, low calorie — Bang, Reign, Celsius, Alani Nu, Prime all land
  // within a tight band here.
  const zeroSugar = norm.filter((d) => d.sugar_g_per_8oz === 0);
  const crowdedBand = zeroSugar.filter((d) => d.caffeine_mg_per_8oz >= 100 && d.caffeine_mg_per_8oz <= 150);
  const sugared = norm.filter((d) => d.sugar_g_per_8oz > 0);

  // Open corner: very-high normalized caffeine (200mg+/8oz) zero-sugar
  // zero/near-zero calorie among canned/bottled formats — only the
  // shot-format outliers (5-hour Energy, Zipfizz) reach that range, and
  // their serving size is so small it's a different product category, not
  // a drinkable can/bottle.
  const shots = norm.filter((d) => d.caffeine_mg_per_8oz > 300);
  const highCafZeroSugarCans = zeroSugar.filter((d) => d.caffeine_mg_per_8oz > 150 && d.caffeine_mg_per_8oz <= 200);

  const openCornerNote = highCafZeroSugarCans.length
    ? `only ${highCafZeroSugarCans.map((d) => d.brand).join(', ')} reach it`
    : 'no canned/bottled brand reaches it';

  const insight = `The crowded spec is <b class="volt">${crowdedBand.length} brands</b> packed into ${Math.round(
    Math.min(...crowdedBand.map((d) => d.caffeine_mg_per_8oz))
  )}–${Math.round(Math.max(...crowdedBand.map((d) => d.caffeine_mg_per_8oz)))}mg caffeine / 8oz, zero sugar, low calorie (${crowdedBand
    .map((d) => d.brand)
    .join(', ')}) — that combination is solved. The sugared legacy cluster (${sugared.map((d) => d.brand).join(', ')}) is just as crowded at the opposite end: ~76–80mg/8oz caffeine but 12–32g/8oz sugar. The open corner is <b class="volt">high-caffeine, zero-sugar, in a normal drinkable format</b> — at 150–200mg/8oz zero-sugar, ${openCornerNote}; the only formulas that go higher (${shots
    .map((d) => d.brand)
    .join(', ')}) are tiny energy-shot servings, not a can — leaving real white space for a high-caffeine, zero-sugar, low-calorie product in a normal can format.`;

  return panel(
    'formulation',
    15,
    'FORMULATION MAP',
    'CAFFEINE × SUGAR, NORMALIZED PER 8 FL OZ · 15 BRANDS · PUBLIC NUTRITION LABELS',
    chart,
    insight
  );
}
