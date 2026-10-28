// Build S / M / L design-system packs from extracted tokens + components.
// Invariant: L ⊇ M ⊇ S (by name).
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, 'out');
const tokens = JSON.parse(readFileSync(join(out, 'tokens.json'), 'utf8'));
const components = JSON.parse(readFileSync(join(out, 'components.json'), 'utf8'));
const lifecycle = JSON.parse(readFileSync(join(out, 'lifecycle.json'), 'utf8'));

const byName = (arr) => Object.fromEntries(arr.map((x) => [x.name, x]));
const tokenByName = byName(tokens.tokens);
const componentByName = byName(components.components);

const pickTokens = (names) =>
  names.map((n) => {
    const t = tokenByName[n];
    if (!t) throw new Error(`unknown token: ${n}`);
    return t;
  });
const pickComponents = (names) =>
  names.map((n) => {
    const c = componentByName[n];
    if (!c) throw new Error(`unknown component: ${n}`);
    return c;
  });

// S: a floor comparable to Cha & Jo's 23-component system — core color/spacing/type + 10 primitives.
const S_TOKENS = [
  'background',
  'layer-01',
  'layer-02',
  'field-01',
  'text-primary',
  'text-secondary',
  'text-on-color',
  'text-helper',
  'text-error',
  'text-disabled',
  'icon-primary',
  'icon-secondary',
  'link-primary',
  'border-subtle-01',
  'border-strong-01',
  'focus',
  'interactive',
  'support-error',
  'support-success',
  'support-warning',
  'support-info',
  'button-primary',
  'button-secondary',
  'button-danger-primary',
  'button-disabled',
  'overlay',
  'background-hover',
  'layer-hover-01',
  'highlight',
  'spacing-03',
  'spacing-04',
  'spacing-05',
  'spacing-06',
  'spacing-07',
  'spacing-08',
  'spacing-09',
  'container-01',
  'container-02',
  'container-04',
  'container-05',
  'breakpoint-sm',
  'breakpoint-md',
  'breakpoint-lg',
  'body-compact-01',
  'body-01',
  'heading-compact-01',
  'heading-01',
  'heading-03',
  'label-01',
  'helper-text-01',
];
const S_COMPONENTS = [
  'Button',
  'TextInput',
  'Form',
  'Tag',
  'Grid',
  'Column',
  'Modal',
  'DataTable',
  'InlineNotification',
  'Header',
];

// M: the components the 80-task suite actually needs, plus a broader token slice.
const M_COMPONENTS = [
  ...S_COMPONENTS,
  'ButtonSet',
  'ModalHeader',
  'ModalBody',
  'ModalFooter',
  'FormGroup',
  'FormLabel',
  'TextArea',
  'Dropdown',
  'Select',
  'SelectItem',
  'Checkbox',
  'RadioButton',
  'RadioButtonGroup',
  'NumberInput',
  'PasswordInput',
  'Search',
  'Pagination',
  'Table',
  'TableHead',
  'TableBody',
  'TableRow',
  'TableHeader',
  'TableCell',
  'TableToolbar',
  'TableBatchActions',
  'TableToolbarContent',
  'TableToolbarSearch',
  'TableSelectAll',
  'TableSelectRow',
  'Tile',
  'ClickableTile',
  'TileGroup',
  'ProgressIndicator',
  'ProgressStep',
  'Breadcrumb',
  'BreadcrumbItem',
  'SideNav',
  'SideNavItems',
  'SideNavLink',
  'HeaderName',
  'HeaderGlobalBar',
  'HeaderMenuButton',
  'Content',
  'Tabs',
  'Tab',
  'TabList',
  'TabPanels',
  'TabPanel',
  'OverflowMenu',
  'OverflowMenuItem',
  'Toggle',
  'Link',
  'Loading',
  'InlineLoading',
  'ActionableNotification',
  'ToastNotification',
  'Accordion',
  'AccordionItem',
  'ComboBox',
  'MultiSelect',
  'DatePicker',
  'DatePickerInput',
  'FileUploader',
  'Slider',
  'Tooltip',
  'ComposedModal',
];

const M_TOKEN_ROLES = new Set([
  'background',
  'layer',
  'layer-accent',
  'layer-selected',
  'field',
  'text',
  'text-on-color',
  'icon',
  'icon-on-color',
  'link',
  'border',
  'border-subtle',
  'border-strong',
  'focus',
  'interactive',
  'support',
  'button',
  'button-primary',
  'button-secondary',
  'button-danger',
  'button-tertiary',
  'overlay',
  'highlight',
  'skeleton',
  'status',
  'notification',
  'tag',
  'layout',
  'spacing',
  'fluid-spacing',
  'container',
  'icon-size',
  'breakpoint',
  'type',
]);

const unique = (arr) => [...new Map(arr.map((x) => [x.name, x])).values()];

const sTokens = unique(pickTokens(S_TOKENS.filter((n) => tokenByName[n])));
const sComponents = unique(pickComponents(S_COMPONENTS.filter((n) => componentByName[n])));

const mTokens = unique([
  ...sTokens,
  ...tokens.tokens.filter((t) => M_TOKEN_ROLES.has(t.role) || M_TOKEN_ROLES.has(t.category)),
]).slice(0, 320);
const mComponents = unique([
  ...sComponents,
  ...pickComponents(M_COMPONENTS.filter((n) => componentByName[n] && !S_COMPONENTS.includes(n))),
]);

const lTokens = tokens.tokens;
const lComponents = components.components.filter((c) => !/Skeleton$|TooltipAlignments$|TooltipPositions$/.test(c.name));

const assertSubset = (inner, outer, kind) => {
  const o = new Set(outer.map((x) => x.name));
  const missing = inner.filter((x) => !o.has(x.name)).map((x) => x.name);
  if (missing.length) throw new Error(`${kind} subset broken: ${missing.join(', ')}`);
};
assertSubset(sTokens, mTokens, 'token S⊆M');
assertSubset(mTokens, lTokens, 'token M⊆L');
assertSubset(sComponents, mComponents, 'component S⊆M');
assertSubset(mComponents, lComponents, 'component M⊆L');

const pack = (id, description, tok, comp) => ({
  id,
  description,
  source: { tokens: tokens.source, components: components.source, lifecycle: lifecycle.source },
  counts: { tokens: tok.length, components: comp.length },
  tokens: tok.map((t) => ({
    name: t.name,
    scss: t.scss,
    css: t.css,
    category: t.category,
    role: t.role,
    status: t.status,
    value: t.value ?? t.values?.white,
  })),
  components: comp.map((c) => ({
    name: c.name,
    status: c.status,
    description: c.description,
    props: (c.props ?? []).map((p) => ({ name: p.name, type: p.type, required: p.required, values: p.values })),
  })),
  lifecycle: {
    forbiddenV10Names: lifecycle.forbiddenV10Names,
    renameMap: lifecycle.renameMap,
    removedComponents: lifecycle.removedComponents,
  },
});

const packs = {
  S: pack('S', '~50 core tokens / 10 primitives; Cha & Jo-comparable floor', sTokens, sComponents),
  M: pack('M', '~300 tokens / task-suite components', mTokens, mComponents),
  L: pack('L', 'full Carbon v11 extract', lTokens, lComponents),
};

for (const [id, p] of Object.entries(packs)) {
  writeFileSync(join(out, `pack-${id}.json`), JSON.stringify(p, null, 2));
  console.log(`pack-${id}.json: ${p.counts.tokens} tokens, ${p.counts.components} components`);
}
writeFileSync(
  join(out, 'packs.json'),
  JSON.stringify(
    {
      invariant: 'L ⊇ M ⊇ S',
      packs: Object.fromEntries(Object.entries(packs).map(([k, v]) => [k, v.counts])),
      extractedAt: new Date().toISOString(),
    },
    null,
    2,
  ),
);
