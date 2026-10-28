#!/usr/bin/env node
// Sidecar: tsc --noEmit plus optional Playwright+axe at 1440 and 375.
// Usage: node index.mjs --tsx path/to/file.tsx --out grades-runtime.json
import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const get = (flag) => {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : undefined;
};
const tsxPath = get('--tsx');
const outPath = get('--out') || join(here, 'last.json');
if (!tsxPath) {
  console.error('usage: node index.mjs --tsx <file.tsx> [--out grades.json] [--runtime]');
  process.exit(2);
}

const fixture = join(here, '..', 'fixture');
const dest = join(fixture, 'src', 'TaskView.tsx');
if (existsSync(join(fixture, 'src'))) {
  writeFileSync(dest, readFileSync(tsxPath));
}

const tsc = spawnSync('npx', ['tsc', '--noEmit', '-p', fixture], { cwd: fixture, encoding: 'utf8' });
const result = {
  compile_ok: tsc.status === 0,
  compile_stderr: (tsc.stderr || tsc.stdout || '').slice(0, 4000),
};

if (args.includes('--runtime')) {
  try {
    const { chromium } = await import('playwright');
    const AxeBuilder = (await import('@axe-core/playwright')).default;
    const browser = await chromium.launch();
    const page = await browser.newPage();
    const url = process.env.FIXTURE_URL || 'http://127.0.0.1:5173';
    const viewports = { 1440: { width: 1440, height: 900 }, 375: { width: 375, height: 812 } };
    result.violations = [];
    for (const [w, size] of Object.entries(viewports)) {
      await page.setViewportSize(size);
      await page.goto(url, { waitUntil: 'networkidle' });
      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
      for (const v of axe.violations) {
        result.violations.push({ id: v.id, impact: v.impact, nodes: v.nodes.length, viewport: Number(w) });
      }
      if (Number(w) === 375) {
        const metrics = await page.evaluate(() => {
          const nodes = [...document.querySelectorAll('*')].slice(0, 400);
          const rects = nodes.map((n) => n.getBoundingClientRect()).filter((r) => r.width && r.height);
          let overlap = 0;
          for (let i = 0; i < rects.length; i++) {
            for (let j = i + 1; j < Math.min(rects.length, i + 12); j++) {
              const a = rects[i], b = rects[j];
              const x = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
              const y = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
              if (x * y > 20 && x * y > 0.8 * Math.min(a.width * a.height, b.width * b.height)) overlap++;
            }
          }
          return { overlap, overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 2 };
        });
        result.overlap_375 = metrics.overlap;
        result.overflow_375 = metrics.overflow;
      }
    }
    await browser.close();
  } catch (e) {
    result.runtime_error = String(e);
  }
}

writeFileSync(outPath, JSON.stringify(result, null, 2));
console.log(JSON.stringify({ compile_ok: result.compile_ok, out: outPath }));
process.exit(result.compile_ok ? 0 : 1);
