export type Pt = [number, number];
const W = 2400, STEP = 12, INSET = 40;      // svg is 2400 x 80; baseline at y = 40
const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));

export function mulberry32(a: number) {
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function makeTear(seed: number, amp = 16): Pt[] {
  const r = mulberry32(seed), n = W / STEP, pts: Pt[] = [];
  let drift = 0;
  for (let i = 0; i <= n; i++) {
    drift = drift * 0.93 + (r() - 0.5) * 5;                      // big, slow waves
    const tooth = (r() - 0.5) * amp;                              // fine teeth
    const notch = r() < 0.05 ? (r() - 0.5) * amp * 2.4 : 0;      // occasional deep notch
    pts.push([i * STEP, drift * 3 + tooth + notch]);
  }
  const y0 = pts[0][1];                                           // blend the end into the start
  for (let k = 0; k < 8; k++) { const w = (8 - k) / 8; pts[n - k][1] = pts[n - k][1] * (1 - w) + y0 * w; }
  return pts;
}

const px = (x: number) => `${((x / W) * 100).toFixed(3)}%`;

export function clipPolygon(pts: Pt[], edge: 'bottom' | 'top'): string {
  if (edge === 'bottom') {
    const line = pts.map(([x, y]) => `${px(x)} calc(100% - ${INSET}px + ${y.toFixed(1)}px)`).reverse();
    return `polygon(0 0, 100% 0, ${line.join(', ')})`;
  }
  const line = pts.map(([x, y]) => `${px(x)} calc(${INSET}px + ${y.toFixed(1)}px)`);
  return `polygon(${line.join(', ')}, 100% 100%, 0 100%)`;
}

const cache = new Map<string, ReturnType<typeof build>>();
function build(seed: number, edge: 'bottom' | 'top') {
  const A = makeTear(seed), r = mulberry32(seed + 99), dir = edge === 'bottom' ? 1 : -1;
  let th = 10;
  const B: Pt[] = A.map(([x, y]) => { th = clamp(th + (r() - 0.5) * 3, 6, 16); return [x, y + dir * th]; });
  const S: Pt[] = B.map(([x, y]) => [x, y + dir * (6 + (r() - 0.5) * 3)]);
  const line = (p: Pt[]) => p.map(([x, y], i) => `${i ? 'L' : 'M'}${x} ${(y + INSET).toFixed(1)}`).join('');
  const band = (a: Pt[], b: Pt[]) => line(a) + [...b].reverse().map(([x, y]) => `L${x} ${(y + INSET).toFixed(1)}`).join('') + 'Z';
  return { clip: clipPolygon(A, edge), fibre: band(A, B), shadow: band(B, S) };
}

export function getTear(seed: number, edge: 'bottom' | 'top') {
  const k = `${seed}:${edge}`;
  if (!cache.has(k)) cache.set(k, build(seed, edge));
  return cache.get(k)!;
}
