// Extract the public @carbon/react component catalog into carbon/out/components.json.
// Public API = named exports of lib/index.d.ts. Props come from react-docgen-typescript
// run over the shipped .d.ts files. Ground truth is extracted, never hand-written.
import { createRequire } from 'node:module';
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';
import docgen from 'react-docgen-typescript';

const require = createRequire(import.meta.url);
const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, 'out');
mkdirSync(out, { recursive: true });

const pkgRoot = dirname(require.resolve('@carbon/react/package.json'));
const indexDts = join(pkgRoot, 'lib', 'index.d.ts');
const version = require('@carbon/react/package.json').version;

// ---- 1. public export list from lib/index.d.ts, resolved through the type checker
// so `export * from './components/X'` is expanded and aliases are followed to their
// declaring .d.ts file.
const program = ts.createProgram([indexDts], { esModuleInterop: true, skipLibCheck: true, jsx: ts.JsxEmit.React });
const checker = program.getTypeChecker();
const indexSf = program.getSourceFile(indexDts);
const moduleSym = checker.getSymbolAtLocation(indexSf);
const exportsMap = new Map(); // exportedName -> { module (file), local }
for (const sym of checker.getExportsOfModule(moduleSym)) {
  const name = sym.getName();
  let target = sym;
  if (sym.flags & ts.SymbolFlags.Alias) {
    try {
      target = checker.getAliasedSymbol(sym);
    } catch {
      /* keep sym */
    }
  }
  const decl = target.declarations?.[0] ?? sym.declarations?.[0];
  if (!decl) continue;
  const file = decl.getSourceFile().fileName;
  // Components are values (function/const/class), not pure types.
  const isValue = !!(target.flags & (ts.SymbolFlags.Function | ts.SymbolFlags.Variable | ts.SymbolFlags.Class | ts.SymbolFlags.Property));
  if (!isValue) continue;
  exportsMap.set(name, { module: file, local: target.getName() });
}
const isComponentName = (n) => /^[A-Z]/.test(n) && !/Props$|Kind$|Kinds$|Size$|Sizes$|Type$|Types$|Context$|TranslationKey$|Component$|^unstable__|^preview__|^unstable_|^preview_/.test(n);
const componentNames = [...exportsMap.keys()].filter(isComponentName);

// ---- 2. docgen over component .d.ts files
const parser = docgen.withCompilerOptions(
  { esModuleInterop: true, jsx: ts.JsxEmit.React, skipLibCheck: true, allowJs: false },
  {
    savePropValueAsString: true,
    shouldExtractLiteralValuesFromEnum: true,
    shouldRemoveUndefinedFromOptional: true,
    propFilter: (prop) => {
      // keep Carbon's own props and the common HTML ones agents actually use
      if (!prop.parent) return true;
      const f = prop.parent.fileName;
      if (/node_modules\/@types\/react/.test(f)) {
        return ['className', 'id', 'onClick', 'onChange', 'disabled', 'aria-label', 'children', 'role', 'type', 'href', 'name', 'value', 'placeholder', 'title'].includes(prop.name);
      }
      return true;
    },
  },
);

const resolveDts = (mod) => (existsSync(mod) ? mod : undefined);

const byModule = new Map();
for (const name of componentNames) {
  const { module } = exportsMap.get(name);
  if (!byModule.has(module)) byModule.set(module, []);
  byModule.get(module).push(name);
}

const components = [];
const missing = [];
for (const [mod, names] of byModule) {
  const file = resolveDts(mod);
  if (!file) {
    for (const n of names) missing.push({ name: n, module: mod, reason: 'no .d.ts' });
    continue;
  }
  let docs = [];
  try {
    docs = parser.parse(file);
  } catch (e) {
    for (const n of names) missing.push({ name: n, module: mod, reason: String(e.message).slice(0, 120) });
    continue;
  }
  const docByName = new Map(docs.map((d) => [d.displayName, d]));
  for (const name of names) {
    const local = exportsMap.get(name).local;
    const d = docByName.get(local) ?? docByName.get(name) ?? (docs.length === 1 ? docs[0] : undefined);
    const props = d
      ? Object.values(d.props).map((p) => {
          const vals = p.type?.value && Array.isArray(p.type.value) ? p.type.value.map((v) => String(v.value).replace(/^"|"$/g, '')) : undefined;
          return {
            name: p.name,
            type: p.type?.name ?? 'unknown',
            required: !!p.required,
            description: (p.description ?? '').trim(),
            ...(vals && vals.length <= 32 ? { values: vals } : {}),
            ...(p.defaultValue?.value != null ? { default: String(p.defaultValue.value) } : {}),
          };
        })
      : [];
    const deprecated = /deprecated/i.test(d?.description ?? '') || /Deprecated$/.test(name);
    components.push({
      name,
      module: mod,
      file: file.replace(pkgRoot + '/', ''),
      description: (d?.description ?? '').trim(),
      status: deprecated ? 'deprecated' : 'active',
      propsExtracted: !!d,
      props,
    });
  }
}

components.sort((a, b) => a.name.localeCompare(b.name));
const result = {
  source: { '@carbon/react': version },
  extractedAt: new Date().toISOString(),
  count: components.length,
  withProps: components.filter((c) => c.propsExtracted).length,
  missing,
  components,
};
writeFileSync(join(out, 'components.json'), JSON.stringify(result, null, 2));
console.log(`components.json: ${components.length} components, ${result.withProps} with props, ${missing.length} unresolved`);
