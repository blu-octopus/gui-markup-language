// Parse Carbon v11 migration tables into carbon/out/lifecycle.json.
// Ground truth is Carbon's own docs/migration/v11.md (vendored under sources/).
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, 'out');
mkdirSync(out, { recursive: true });

const md = readFileSync(join(here, 'sources', 'v11-migration.md'), 'utf8');

const parseRows = (block) => {
  const lines = block.split('\n').filter((l) => l.startsWith('|') && !/^\|\s*-/.test(l));
  if (lines.length < 2) return { headers: [], rows: [] };
  const split = (line) =>
    line
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((c) => c.trim().replace(/`/g, '').replace(/—/g, '').replace(/–/g, ''));
  const headers = split(lines[0]).map((h) => h.toLowerCase());
  const rows = lines.slice(1).map((l) => {
    const cells = split(l);
    const obj = {};
    headers.forEach((h, i) => (obj[h] = cells[i] ?? ''));
    return obj;
  });
  return { headers, rows };
};

const section = (startHeading, endHeading) => {
  const start = md.indexOf(startHeading);
  if (start < 0) return '';
  const from = start + startHeading.length;
  const end = endHeading ? md.indexOf(endHeading, from) : md.length;
  return md.slice(from, end < 0 ? md.length : end);
};

// ---- color tokens table
const colorSec = section('### Design Tokens', '### Compatibility');
const colorTable = parseRows(colorSec);
const tokens = [];
for (const r of colorTable.rows) {
  const v10 = (r['v10 token name'] ?? '').trim();
  const v11 = (r['v11 token name'] ?? '').trim();
  const contextual = (r['v11 contextual token'] ?? '').trim();
  const status = (r['status'] ?? '').trim() || 'Updated';
  if (!v10 && !v11) continue;
  tokens.push({
    kind: 'token',
    category: 'color',
    v10: v10 || null,
    v11: v11 || null,
    contextual: contextual || null,
    status: status.toLowerCase().replace(/\s+/g, '-'),
  });
}

// ---- type tokens table
const typeSec = section('## Type tokens', '');
const typeTable = parseRows(typeSec);
const typeTokens = [];
let lastCat = '';
for (const r of typeTable.rows) {
  const cat = (r['category'] ?? '').trim() || lastCat;
  lastCat = cat;
  const v10 = (r['v10 token name'] ?? '').trim();
  const v11 = (r['v11 token name'] ?? '').trim();
  const status = (r['status'] ?? '').trim() || 'Updated';
  if (!v10 && !v11) continue;
  typeTokens.push({
    kind: 'token',
    category: 'type',
    group: cat || null,
    v10: v10 || null,
    v11: v11 || null,
    status: status.toLowerCase().replace(/\s+/g, '-'),
  });
}

// ---- react component changes table
const reactSec = section('## carbon-components-react', '### AccordionItem');
const reactTable = parseRows(reactSec);
const components = [];
for (const r of reactTable.rows) {
  const name = (r['component'] ?? '').trim();
  const changes = (r['changes'] ?? '').trim();
  if (!name) continue;
  const removed = /^removed$/i.test(changes);
  components.push({
    kind: 'component',
    name,
    status: removed ? 'removed' : 'updated',
    notes: changes,
    package: { v10: 'carbon-components-react', v11: '@carbon/react' },
  });
}

// Convenience lookups used by graders and trap tasks
const forbiddenV10Names = [
  ...new Set(
    [...tokens, ...typeTokens]
      .filter((t) => t.v10 && t.status !== 'no-change' && t.v10 !== t.v11)
      .map((t) => t.v10),
  ),
];
const renameMap = {};
for (const t of [...tokens, ...typeTokens]) {
  if (!t.v10 || !t.v11) continue;
  if (!renameMap[t.v10]) renameMap[t.v10] = [];
  if (!renameMap[t.v10].includes(t.v11)) renameMap[t.v10].push(t.v11);
}
const removedComponents = components.filter((c) => c.status === 'removed').map((c) => c.name);

const result = {
  source: {
    file: 'carbon/sources/v11-migration.md',
    upstream: 'https://github.com/carbon-design-system/carbon/blob/main/docs/migration/v11.md',
    note: 'v10 packages reached end of support 2024-09-30',
  },
  extractedAt: new Date().toISOString(),
  tokens: [...tokens, ...typeTokens],
  components,
  forbiddenV10Names,
  renameMap,
  removedComponents,
  counts: {
    tokenRows: tokens.length + typeTokens.length,
    componentRows: components.length,
    forbiddenV10Names: forbiddenV10Names.length,
    removedComponents: removedComponents.length,
  },
};
writeFileSync(join(out, 'lifecycle.json'), JSON.stringify(result, null, 2));
console.log('lifecycle.json:', result.counts);
