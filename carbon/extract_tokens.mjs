// Extract IBM Carbon v11 design tokens into carbon/out/tokens.json.
// Sources: @carbon/themes (color + component tokens, per theme), @carbon/layout
// (spacing, layout, container, icon sizes, breakpoints), @carbon/type (type styles).
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const themes = require('@carbon/themes');
const layout = require('@carbon/layout');
const type = require('@carbon/type');

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, 'out');
mkdirSync(out, { recursive: true });

const kebab = (s) =>
  s.replace(/([a-z0-9])([A-Z])/g, '$1-$2').replace(/([A-Z])([A-Z][a-z])/g, '$1-$2').replace(/(\D)(\d)/g, '$1-$2').toLowerCase();

// Role groups for color tokens: used by the taxonomy (R1 "token role") and by
// pack construction. First matching prefix wins.
const COLOR_ROLES = [
  ['ai', 'ai'],
  ['chat', 'chat'],
  ['background', 'background'],
  ['layerAccent', 'layer-accent'],
  ['layerSelected', 'layer-selected'],
  ['layer', 'layer'],
  ['field', 'field'],
  ['borderSubtle', 'border-subtle'],
  ['borderStrong', 'border-strong'],
  ['borderTile', 'border-tile'],
  ['border', 'border'],
  ['textOnColor', 'text-on-color'],
  ['text', 'text'],
  ['linkPrimary', 'link'],
  ['link', 'link'],
  ['iconOnColor', 'icon-on-color'],
  ['icon', 'icon'],
  ['supportCautionMajor', 'support'],
  ['supportCautionMinor', 'support'],
  ['supportCautionUndefined', 'support'],
  ['support', 'support'],
  ['buttonDanger', 'button-danger'],
  ['buttonPrimary', 'button-primary'],
  ['buttonSecondary', 'button-secondary'],
  ['buttonTertiary', 'button-tertiary'],
  ['button', 'button'],
  ['tag', 'tag'],
  ['notification', 'notification'],
  ['status', 'status'],
  ['focus', 'focus'],
  ['interactive', 'interactive'],
  ['highlight', 'highlight'],
  ['overlay', 'overlay'],
  ['toggleOff', 'toggle'],
  ['skeleton', 'skeleton'],
  ['shadow', 'shadow'],
  ['content', 'content'],
];
const roleOf = (name) => {
  for (const [prefix, role] of COLOR_ROLES) if (name.startsWith(prefix)) return role;
  return 'misc';
};

const tokens = [];
const seen = new Set();
const push = (t) => {
  if (seen.has(t.name)) return;
  seen.add(t.name);
  tokens.push(t);
};

// ---- color tokens from themes (v11 metadata lists them; values from 4 themes)
const themeNames = ['white', 'g10', 'g90', 'g100'];
const meta = themes.unstable_metadata?.v11 ?? [];
const metaType = new Map(meta.map((m) => [m.name, m.type]));
for (const camel of Object.keys(themes.white)) {
  const k = kebab(camel);
  const mt = metaType.get(k);
  const value = themes.white[camel];
  const isColor = typeof value === 'string' && /^(#|rgb|hsl)/.test(value);
  const isTypeStyle = typeof value === 'object' && value !== null && 'fontSize' in value;
  const isSpacing = typeof value === 'string' && /rem$|px$/.test(value) && !isColor;
  let category = mt ?? (isColor ? 'color' : isTypeStyle ? 'type' : isSpacing ? 'layout' : 'misc');
  if (category === 'color' && !isColor) category = 'misc';
  const entry = {
    name: k,
    camel,
    scss: `$${k}`,
    css: `--cds-${k}`,
    category,
    role: category === 'color' ? roleOf(camel) : category,
    status: 'active',
  };
  if (category === 'type') entry.value = value;
  else entry.values = Object.fromEntries(themeNames.map((th) => [th, themes[th][camel]]));
  push(entry);
}

// ---- component tokens exported as groups
for (const group of ['buttonTokens', 'tagTokens', 'notificationTokens', 'statusTokens', 'contentSwitcherTokens']) {
  const g = themes[group];
  if (!g) continue;
  for (const camel of Object.keys(g)) {
    const k = kebab(camel);
    const v = g[camel];
    push({
      name: k,
      camel,
      scss: `$${k}`,
      css: `--cds-${k}`,
      category: 'component',
      component: group.replace('Tokens', ''),
      role: roleOf(camel),
      status: 'active',
      values: typeof v === 'object' && v !== null && !('fontSize' in v) ? v : { white: v },
    });
  }
}

// ---- layout tokens
const layoutGroups = {
  spacing: /^spacing\d{2}$/,
  'fluid-spacing': /^fluidSpacing\d{2}$/,
  layout: /^layout\d{2}$/,
  container: /^container\d{2}$/,
  'icon-size': /^iconSize\d{2}$/,
  'border-radius': /^borderRadius\d{2}$|^borderRadiusMax$/,
};
for (const [grp, re] of Object.entries(layoutGroups)) {
  for (const camel of Object.keys(layout)) {
    if (!re.test(camel)) continue;
    const k = kebab(camel);
    push({ name: k, camel, scss: `$${k}`, css: `--cds-${k}`, category: 'layout', role: grp, status: 'active', value: layout[camel] });
  }
}
for (const [bp, def] of Object.entries(layout.breakpoints ?? {})) {
  push({ name: `breakpoint-${bp}`, camel: `breakpoint${bp.toUpperCase()}`, scss: `$${bp}`, css: null, category: 'breakpoint', role: 'breakpoint', status: 'active', value: def });
}

// ---- type tokens
const typeStyleNames = Object.keys(type).filter((k) => {
  const v = type[k];
  return typeof v === 'object' && v !== null && 'fontSize' in v;
});
for (const camel of typeStyleNames) {
  const k = kebab(camel);
  push({ name: k, camel, scss: `$${k}`, css: `--cds-${k}`, category: 'type', role: 'type', status: 'active', value: type[camel] });
}

const summary = tokens.reduce((acc, t) => ((acc[t.category] = (acc[t.category] ?? 0) + 1), acc), {});
const result = {
  source: {
    '@carbon/themes': require('@carbon/themes/package.json').version,
    '@carbon/layout': require('@carbon/layout/package.json').version,
    '@carbon/type': require('@carbon/type/package.json').version,
  },
  extractedAt: new Date().toISOString(),
  count: tokens.length,
  byCategory: summary,
  tokens,
};
writeFileSync(join(out, 'tokens.json'), JSON.stringify(result, null, 2));
console.log(`tokens.json: ${tokens.length} tokens`, summary);
