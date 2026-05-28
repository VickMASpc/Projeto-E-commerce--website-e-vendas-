const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const INTERMEDIATE = path.join(ROOT, '.understand-anything', 'intermediate');
const TMP = path.join(ROOT, '.understand-anything', 'tmp');
const batches = JSON.parse(fs.readFileSync(path.join(INTERMEDIATE, 'batches.json'), 'utf8')).batches;
const extractedByBatch = new Map();
for (const batch of batches) {
  extractedByBatch.set(batch.batchIndex, JSON.parse(fs.readFileSync(path.join(INTERMEDIATE, `batch-${batch.batchIndex}.json`), 'utf8')));
}

const fileMeta = new Map();
for (const batch of batches) {
  for (const file of batch.files) fileMeta.set(file.path, file);
}

const fileSummaries = {
  '.understand-anything/.understandignore': 'Defines optional exclusion patterns for the Understand Anything scan so generated graphs can ignore irrelevant files and folders.',
  'E-commerce/app.js': 'Implements the storefront client logic, including product normalization, page rendering, favorites, cart state, newsletter capture, and checkout submission to the local order API.',
  'E-commerce/carrinho.html': 'Provides the cart page shell that hosts the storefront cart experience and its checkout form.',
  'E-commerce/favoritos.html': 'Provides the wishlist page shell used to display products saved by the shopper.',
  'E-commerce/firebase-config.js': 'Exports the Firebase client configuration used by the storefront application to initialize Firestore access.',
  'E-commerce/index.html': 'Defines the landing page structure for the perfume storefront and hands interactive behavior to the shared frontend script.',
  'E-commerce/products_live.js': 'Stores the generated mock product and order snapshot that the storefront can use when Firestore data is unavailable.',
  'E-commerce/produto.html': 'Provides the product-detail page shell that the storefront script hydrates with a selected perfume record.',
  'E-commerce/produtos.html': 'Provides the catalog page shell with filters and search hooks for the storefront product grid.',
  'E-commerce/style.css': 'Contains the shared visual system and responsive styling for the static storefront pages.',
  'readme.md': 'Introduces the beta project, explains how the storefront, Python operations app, and analytics dashboard fit together, and documents the local API flow.',
  'Sistema de análise de vendas/React app/.env.example': 'Declares the optional environment variable used to override the analytics dashboard stats endpoint.',
  'Sistema de análise de vendas/React app/eslint.config.js': 'Defines the linting rules for the Vite React dashboard project.',
  'Sistema de análise de vendas/React app/index.html': 'Provides the Vite HTML shell that mounts the React analytics dashboard bundle.',
  'Sistema de análise de vendas/React app/package.json': 'Declares the React dashboard dependencies, scripts, and build tooling for the Vite application.',
  'Sistema de análise de vendas/React app/README.md': 'Documents the React dashboard workspace and the commands used to run, build, and lint it.',
  'Sistema de análise de vendas/React app/src/App.css': 'Adds component-level styling overrides for the React dashboard wrapper.',
  'Sistema de análise de vendas/React app/src/App.tsx': 'Provides a minimal application wrapper that renders the main sales dashboard component.',
  'Sistema de análise de vendas/React app/src/index.css': 'Loads the Tailwind-driven global styles used across the React dashboard.',
  'Sistema de análise de vendas/React app/src/main.tsx': 'Bootstraps the React dashboard into the DOM and loads the root stylesheet.',
  'Sistema de análise de vendas/React app/src/sistema_de_analise_de_vendas.tsx': 'Implements the main analytics dashboard with KPI cards, charts, recent activity, and offline fallback behavior backed by the local stats endpoint.',
  'Sistema de análise de vendas/React app/tsconfig.app.json': 'Configures TypeScript compiler options for the browser-side React dashboard source files.',
  'Sistema de análise de vendas/React app/tsconfig.json': 'Defines the root TypeScript project references for the React dashboard workspace.',
  'Sistema de análise de vendas/React app/tsconfig.node.json': 'Configures TypeScript behavior for Node-based tooling such as the Vite configuration file.',
  'Sistema de análise de vendas/React app/vite.config.ts': 'Configures Vite to build the React dashboard with the React and Tailwind plugins enabled.',
  'Sistema de análise de vendas/sistema_de_analise_de_vendas.tsx': 'Contains a standalone dashboard implementation outside the Vite app, likely serving as an earlier or alternate analytics view.',
  'Sistema de vendas/database.py': 'Implements product and order persistence, supports Firebase or JSON-backed storage, exports storefront data, and computes analytics payloads for the dashboard.',
  'Sistema de vendas/db_mock.json': 'Stores the mock catalog and order dataset used when the local sales system runs without Firebase.',
  'Sistema de vendas/serviceAccountKey.json': 'Stores the Firebase Admin service-account credentials required for the Python backend to access Firestore.',
  'Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py': 'Implements the Tkinter operations console for inventory and order management and starts the local HTTP endpoints consumed by the storefront and dashboard.'
};

const fileTags = {
  '.understand-anything/.understandignore': ['tooling', 'analysis', 'ignore-rules'],
  'E-commerce/app.js': ['storefront', 'firebase', 'cart', 'checkout', 'dom'],
  'E-commerce/carrinho.html': ['storefront', 'cart', 'markup'],
  'E-commerce/favoritos.html': ['storefront', 'wishlist', 'markup'],
  'E-commerce/firebase-config.js': ['firebase', 'configuration', 'storefront'],
  'E-commerce/index.html': ['storefront', 'landing-page', 'markup'],
  'E-commerce/products_live.js': ['mock-data', 'catalog', 'storefront'],
  'E-commerce/produto.html': ['storefront', 'product-detail', 'markup'],
  'E-commerce/produtos.html': ['storefront', 'catalog', 'markup'],
  'E-commerce/style.css': ['storefront', 'styles', 'responsive'],
  'readme.md': ['documentation', 'entry-point', 'overview'],
  'Sistema de análise de vendas/React app/.env.example': ['configuration', 'environment', 'analytics'],
  'Sistema de análise de vendas/React app/eslint.config.js': ['configuration', 'linting', 'react'],
  'Sistema de análise de vendas/React app/index.html': ['entry-point', 'react', 'markup'],
  'Sistema de análise de vendas/React app/package.json': ['configuration', 'build-system', 'react'],
  'Sistema de análise de vendas/React app/README.md': ['documentation', 'react', 'setup'],
  'Sistema de análise de vendas/React app/src/App.css': ['styles', 'react', 'dashboard'],
  'Sistema de análise de vendas/React app/src/App.tsx': ['react', 'component', 'entry-point'],
  'Sistema de análise de vendas/React app/src/index.css': ['styles', 'tailwind', 'dashboard'],
  'Sistema de análise de vendas/React app/src/main.tsx': ['entry-point', 'react', 'bootstrap'],
  'Sistema de análise de vendas/React app/src/sistema_de_analise_de_vendas.tsx': ['analytics', 'dashboard', 'charts', 'react'],
  'Sistema de análise de vendas/React app/tsconfig.app.json': ['configuration', 'typescript', 'react'],
  'Sistema de análise de vendas/React app/tsconfig.json': ['configuration', 'typescript', 'workspace'],
  'Sistema de análise de vendas/React app/tsconfig.node.json': ['configuration', 'typescript', 'tooling'],
  'Sistema de análise de vendas/React app/vite.config.ts': ['configuration', 'vite', 'tailwind'],
  'Sistema de análise de vendas/sistema_de_analise_de_vendas.tsx': ['analytics', 'dashboard', 'react'],
  'Sistema de vendas/database.py': ['backend', 'persistence', 'inventory', 'orders', 'analytics'],
  'Sistema de vendas/db_mock.json': ['mock-data', 'inventory', 'orders'],
  'Sistema de vendas/serviceAccountKey.json': ['security', 'firebase', 'configuration'],
  'Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py': ['desktop-app', 'inventory', 'orders', 'api-server']
};

function basename(p) { return p.split('/').pop(); }
function span(item) { return (item.endLine || item.startLine || 0) - (item.startLine || 0) + 1; }
function complexityByLines(n) { if (n > 200) return 'complex'; if (n >= 50) return 'moderate'; return 'simple'; }
function complexityBySpan(n) { if (n > 40) return 'complex'; if (n >= 15) return 'moderate'; return 'simple'; }
function nodeTypeFor(fileCategory) {
  if (fileCategory === 'config') return 'config';
  if (fileCategory === 'docs') return 'document';
  return 'file';
}
function titleFromIdentifier(name) {
  return name
    .replace(/^_+/, '')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/_/g, ' ')
    .trim()
    .toLowerCase();
}
function ensureTags(tags, fallback) {
  const out = [...new Set((tags || []).filter(Boolean))];
  while (out.length < 3) {
    const next = fallback.shift();
    if (next && !out.includes(next)) out.push(next);
  }
  return out.slice(0, 5);
}
function fileSummary(filePath) { return fileSummaries[filePath] || `Implements project logic for ${basename(filePath)}.`; }
function fileNode(filePath) {
  const meta = fileMeta.get(filePath);
  const type = nodeTypeFor(meta.fileCategory, filePath);
  const id = `${type}:${filePath}`;
  return {
    id,
    type,
    name: basename(filePath),
    filePath,
    summary: fileSummary(filePath),
    tags: ensureTags(fileTags[filePath], [type, meta.language || 'project', 'project-file']),
    complexity: complexityByLines(meta.sizeLines || 0)
  };
}

function symbolSummary(filePath, symbolName, kind) {
  const label = titleFromIdentifier(symbolName);
  if (filePath === 'Sistema de vendas/database.py') {
    if (symbolName === 'get_stats') return 'Builds the aggregated sales payload consumed by the analytics dashboard.';
    if (symbolName === 'create_local_order') return 'Normalizes and records a new order while updating local or Firebase-backed persistence.';
    if (symbolName === 'normalize_product') return 'Normalizes raw product records into the shape expected by the storefront and operations tools.';
    if (symbolName === 'normalize_order') return 'Normalizes incoming order payloads into a consistent structure for storage and reporting.';
    if (symbolName === '_export_to_frontend') return 'Serializes the current dataset into the generated storefront snapshot file used in mock mode.';
    if (symbolName.startsWith('get_')) return `Returns ${label.replace(/^get /, '')} data from the backend persistence layer.`;
    if (symbolName.startsWith('update_')) return `Updates ${label.replace(/^update /, '')} state in the backend persistence layer.`;
    if (symbolName.startsWith('add_')) return `Adds ${label.replace(/^add /, '')} data to the backend persistence layer.`;
    if (symbolName.startsWith('delete_')) return `Removes ${label.replace(/^delete /, '')} data from the backend persistence layer.`;
    if (symbolName.startsWith('listen_')) return `Subscribes the backend to ${label.replace(/^listen /, '')} updates from Firebase when realtime mode is enabled.`;
    if (symbolName.startsWith('_parse') || symbolName.startsWith('_to_')) return `Coerces and sanitizes values used by the backend data normalization flow for ${label}.`;
    if (symbolName.startsWith('_')) return `Supports backend data preparation for ${label}.`;
  }
  if (filePath === 'Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py' && symbolName === 'SistemaLogisticaApp') {
    return 'Coordinates the Tkinter interface for stock, orders, and dashboard views while also starting the local HTTP server used by the other apps.';
  }
  if (filePath.includes('sistema_de_analise_de_vendas.tsx')) {
    if (symbolName === 'SalesDashboard') return 'Renders the analytics dashboard, fetches the stats payload, and switches between live and offline presentation states.';
    if (symbolName === 'KPIItem') return 'Displays a single KPI card with a title, value, and short trend label.';
    if (symbolName === 'EmptyChartMessage') return 'Shows the empty-state placeholder used when a dashboard chart has no data.';
    if (symbolName === 'formatCurrency') return 'Formats numeric values as Brazilian real currency for dashboard display.';
  }
  if (filePath === 'E-commerce/app.js') {
    if (symbolName === 'normalizeProduct') return 'Transforms raw catalog records into the richer storefront shape used across product, cart, and search views.';
    if (symbolName === 'loadProductCatalog') return 'Loads the product catalog from Firestore and falls back to the generated local snapshot when needed.';
    if (symbolName === 'createProductCard') return 'Builds the storefront card markup and actions for a single product item.';
    if (symbolName === 'renderProducts') return 'Renders a list of normalized products into the requested storefront container.';
    if (symbolName === 'buildHeader') return 'Builds the shared storefront header, navigation, and quick-access action controls.';
    if (symbolName === 'buildFooter') return 'Builds the shared storefront footer and informational links.';
    if (symbolName === 'renderSiteChrome') return 'Injects the shared header and footer into the current storefront page shell.';
    if (symbolName === 'setupSiteSearch') return 'Wires the global storefront search form and live result panel to the loaded catalog.';
    if (symbolName === 'setupGlobalInteractions') return 'Registers delegated click handling for wishlist, cart, and general storefront interactions.';
    if (symbolName === 'initHomePage') return 'Initializes the storefront home page with its featured product content.';
    if (symbolName === 'initProductsPage') return 'Initializes the catalog page, including filters, query syncing, and dynamic product rendering.';
    if (symbolName === 'renderProductDetail') return 'Builds the detailed product experience, including gallery, specifications, and related items.';
    if (symbolName === 'initProductPage') return 'Loads the selected product and initializes the product detail page.';
    if (symbolName === 'initFavoritesPage') return 'Loads and renders the shopper wishlist view from locally stored favorites.';
    if (symbolName === 'renderCartPage') return 'Builds the cart page, totals, and checkout summary from the locally stored cart state.';
    if (symbolName === 'handleCheckout') return 'Validates checkout input and submits the order to the local backend or Firebase fallback flow.';
    if (symbolName === 'setupCartPageActions') return 'Connects cart quantity controls and checkout submission events to the cart workflow.';
    if (symbolName === 'initNewsletter') return 'Handles newsletter submission and persists subscriber addresses through Firebase.';
    if (symbolName === 'initPage') return 'Dispatches page-specific initialization after the shared storefront chrome and state are prepared.';
    if (symbolName.startsWith('init')) return `Initializes the ${titleFromIdentifier(symbolName).replace(/^init /, '')} storefront flow.`;
    if (symbolName.startsWith('render')) return `Renders the ${titleFromIdentifier(symbolName).replace(/^render /, '')} storefront view.`;
    if (symbolName.startsWith('create')) return `Builds the ${titleFromIdentifier(symbolName).replace(/^create /, '')} structure used by the storefront.`;
    if (symbolName.startsWith('setup')) return `Sets up the ${titleFromIdentifier(symbolName).replace(/^setup /, '')} behavior for the storefront.`;
    if (symbolName.startsWith('get')) return `Returns ${titleFromIdentifier(symbolName).replace(/^get /, '')} data for the storefront flow.`;
    if (symbolName.startsWith('build')) return `Builds the ${titleFromIdentifier(symbolName).replace(/^build /, '')} supporting structure for the storefront.`;
    return `Implements ${label} logic for the storefront application.`;
  }
  return `${kind === 'class' ? 'Defines' : 'Implements'} ${label} logic in ${basename(filePath)}.`;
}

function symbolTags(filePath, symbolName, kind) {
  const base = kind === 'class' ? ['class'] : ['function'];
  if (filePath === 'E-commerce/app.js') {
    const extra = ['storefront'];
    if (/render|create|build/i.test(symbolName)) extra.push('ui');
    if (/cart|checkout/i.test(symbolName)) extra.push('cart');
    if (/search|query/i.test(symbolName)) extra.push('search');
    if (/init|setup/i.test(symbolName)) extra.push('event-handler');
    if (/normalize|parse|format|guess|matches/i.test(symbolName)) extra.push('utility');
    return ensureTags([...extra, ...base], ['dom', 'frontend']);
  }
  if (filePath === 'Sistema de vendas/database.py') {
    const extra = ['backend'];
    if (/order|pedido/i.test(symbolName)) extra.push('orders');
    if (/product|produto|stock|estoque/i.test(symbolName)) extra.push('inventory');
    if (/stats/i.test(symbolName)) extra.push('analytics');
    if (/normalize|parse|to_/i.test(symbolName)) extra.push('validation');
    return ensureTags([...extra, ...base], ['persistence', 'python']);
  }
  if (filePath.includes('sistema_de_analise_de_vendas.tsx')) {
    const extra = ['analytics', 'dashboard'];
    if (/KPI|Empty/i.test(symbolName)) extra.push('component');
    if (/format/i.test(symbolName)) extra.push('utility');
    if (/SalesDashboard/i.test(symbolName)) extra.push('entry-point');
    return ensureTags([...extra, ...base], ['react']);
  }
  if (filePath.includes('sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py')) {
    return ensureTags(['desktop-app', 'inventory', 'orders', ...base], ['api-server', 'python']);
  }
  return ensureTags(base, ['project-logic', 'internal']);
}

function shouldCreateFunction(result, fn) {
  const exported = new Set((result.exports || []).map(e => e.name));
  return span(fn) >= 10 || exported.has(fn.name);
}
function shouldCreateClass(result, cls) {
  const exported = new Set((result.exports || []).map(e => e.name));
  return span(cls) >= 20 || ((cls.methods || []).length >= 2) || exported.has(cls.name);
}

const manualEdges = [
  ['file:E-commerce/app.js', 'file:E-commerce/products_live.js', 'depends_on', 0.6],
  ['file:E-commerce/app.js', 'file:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py', 'depends_on', 0.6],
  ['file:Sistema de análise de vendas/React app/src/sistema_de_analise_de_vendas.tsx', 'file:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py', 'depends_on', 0.6],
  ['file:Sistema de análise de vendas/sistema_de_analise_de_vendas.tsx', 'file:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py', 'depends_on', 0.6],
  ['config:Sistema de análise de vendas/React app/.env.example', 'file:Sistema de análise de vendas/React app/src/sistema_de_analise_de_vendas.tsx', 'configures', 0.6],
  ['config:Sistema de análise de vendas/React app/package.json', 'file:Sistema de análise de vendas/React app/vite.config.ts', 'configures', 0.6],
  ['config:Sistema de análise de vendas/React app/package.json', 'file:Sistema de análise de vendas/React app/src/main.tsx', 'configures', 0.6],
  ['config:Sistema de análise de vendas/React app/tsconfig.app.json', 'file:Sistema de análise de vendas/React app/src/sistema_de_analise_de_vendas.tsx', 'configures', 0.6],
  ['config:Sistema de análise de vendas/React app/tsconfig.json', 'file:Sistema de análise de vendas/React app/src/main.tsx', 'configures', 0.6],
  ['config:Sistema de análise de vendas/React app/tsconfig.node.json', 'file:Sistema de análise de vendas/React app/vite.config.ts', 'configures', 0.6],
  ['config:Sistema de análise de vendas/React app/eslint.config.js'.replace('config:','file:'), 'file:Sistema de análise de vendas/React app/src/App.tsx', 'depends_on', 0.6],
  ['document:readme.md', 'file:E-commerce/app.js', 'documents', 0.5],
  ['document:readme.md', 'file:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py', 'documents', 0.5],
  ['document:readme.md', 'file:Sistema de análise de vendas/React app/src/sistema_de_analise_de_vendas.tsx', 'documents', 0.5],
  ['document:Sistema de análise de vendas/React app/README.md', 'file:Sistema de análise de vendas/React app/src/main.tsx', 'documents', 0.5],
  ['config:Sistema de vendas/db_mock.json', 'file:Sistema de vendas/database.py', 'configures', 0.6],
  ['config:Sistema de vendas/serviceAccountKey.json', 'file:Sistema de vendas/database.py', 'configures', 0.6],
  ['file:Sistema de análise de vendas/React app/index.html', 'file:Sistema de análise de vendas/React app/src/main.tsx', 'depends_on', 0.6],
  ['file:E-commerce/index.html', 'file:E-commerce/app.js', 'depends_on', 0.6],
  ['file:E-commerce/index.html', 'file:E-commerce/style.css', 'depends_on', 0.6],
  ['file:E-commerce/produtos.html', 'file:E-commerce/app.js', 'depends_on', 0.6],
  ['file:E-commerce/produtos.html', 'file:E-commerce/style.css', 'depends_on', 0.6],
  ['file:E-commerce/produto.html', 'file:E-commerce/app.js', 'depends_on', 0.6],
  ['file:E-commerce/produto.html', 'file:E-commerce/style.css', 'depends_on', 0.6],
  ['file:E-commerce/carrinho.html', 'file:E-commerce/app.js', 'depends_on', 0.6],
  ['file:E-commerce/carrinho.html', 'file:E-commerce/style.css', 'depends_on', 0.6],
  ['file:E-commerce/favoritos.html', 'file:E-commerce/app.js', 'depends_on', 0.6],
  ['file:E-commerce/favoritos.html', 'file:E-commerce/style.css', 'depends_on', 0.6],
  ['class:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py:SistemaLogisticaApp', 'function:Sistema de vendas/database.py:get_products', 'calls', 0.8],
  ['class:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py:SistemaLogisticaApp', 'function:Sistema de vendas/database.py:get_orders', 'calls', 0.8],
  ['class:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py:SistemaLogisticaApp', 'function:Sistema de vendas/database.py:add_product', 'calls', 0.8],
  ['class:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py:SistemaLogisticaApp', 'function:Sistema de vendas/database.py:update_product', 'calls', 0.8],
  ['class:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py:SistemaLogisticaApp', 'function:Sistema de vendas/database.py:update_product_stock', 'calls', 0.8],
  ['class:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py:SistemaLogisticaApp', 'function:Sistema de vendas/database.py:delete_product', 'calls', 0.8],
  ['class:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py:SistemaLogisticaApp', 'function:Sistema de vendas/database.py:update_order_status', 'calls', 0.8],
  ['class:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py:SistemaLogisticaApp', 'function:Sistema de vendas/database.py:get_stats', 'calls', 0.8],
  ['class:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py:SistemaLogisticaApp', 'function:Sistema de vendas/database.py:create_local_order', 'calls', 0.8],
  ['class:Sistema de vendas/sistema_de_registro_de_vendas_e_gerenciamento_de_estoque.py:SistemaLogisticaApp', 'function:Sistema de vendas/database.py:listen_to_orders', 'calls', 0.8]
].map(([source, target, type, weight]) => ({ source, target, type, direction: 'forward', weight }));

const outputs = new Map();
const allNodeIds = new Set();
const nodeFilePath = new Map();

for (const batch of batches) {
  const extracted = extractedByBatch.get(batch.batchIndex);
  const nodes = [];
  const edges = [];
  const created = new Set();
  for (const result of extracted.results) {
    const file = fileNode(result.path);
    nodes.push(file);
    created.add(file.id);
    allNodeIds.add(file.id);
    nodeFilePath.set(file.id, result.path);

    const exported = new Set((result.exports || []).map(e => e.name));

    for (const fn of (result.functions || [])) {
      if (!shouldCreateFunction(result, fn)) continue;
      const id = `function:${result.path}:${fn.name}`;
      const node = {
        id,
        type: 'function',
        name: fn.name,
        filePath: result.path,
        lineRange: [fn.startLine, fn.endLine],
        summary: symbolSummary(result.path, fn.name, 'function'),
        tags: symbolTags(result.path, fn.name, 'function'),
        complexity: complexityBySpan(span(fn))
      };
      nodes.push(node);
      created.add(id);
      allNodeIds.add(id);
      nodeFilePath.set(id, result.path);
      edges.push({ source: file.id, target: id, type: 'contains', direction: 'forward', weight: 1.0 });
      if (exported.has(fn.name)) {
        edges.push({ source: file.id, target: id, type: 'exports', direction: 'forward', weight: 0.8 });
      }
    }

    for (const cls of (result.classes || [])) {
      if (!shouldCreateClass(result, cls)) continue;
      const id = `class:${result.path}:${cls.name}`;
      const node = {
        id,
        type: 'class',
        name: cls.name,
        filePath: result.path,
        lineRange: [cls.startLine, cls.endLine],
        summary: symbolSummary(result.path, cls.name, 'class'),
        tags: symbolTags(result.path, cls.name, 'class'),
        complexity: complexityBySpan(span(cls))
      };
      nodes.push(node);
      created.add(id);
      allNodeIds.add(id);
      nodeFilePath.set(id, result.path);
      edges.push({ source: file.id, target: id, type: 'contains', direction: 'forward', weight: 1.0 });
      if (exported.has(cls.name)) {
        edges.push({ source: file.id, target: id, type: 'exports', direction: 'forward', weight: 0.8 });
      }
    }
  }

  for (const [src, targets] of Object.entries(batch.batchImportData || {})) {
    for (const target of targets) {
      edges.push({ source: `file:${src}`, target: `file:${target}`, type: 'imports', direction: 'forward', weight: 0.7 });
    }
  }

  outputs.set(batch.batchIndex, { nodes, edges });
}

for (const [batchIndex, out] of outputs) {
  const seen = new Set(out.nodes.map(n => n.id));
  for (const edge of manualEdges) {
    if (!seen.has(edge.source)) continue;
    if (!allNodeIds.has(edge.target)) continue;
    if (edge.source === edge.target) continue;
    out.edges.push(edge);
  }
  const dedup = new Map();
  for (const edge of out.edges) {
    const key = `${edge.source}|${edge.target}|${edge.type}|${edge.direction}`;
    if (!dedup.has(key)) dedup.set(key, edge);
  }
  out.edges = [...dedup.values()];
}

for (const batch of batches) {
  const out = outputs.get(batch.batchIndex);
  for (const name of fs.readdirSync(INTERMEDIATE)) {
    if (new RegExp(`^batch-${batch.batchIndex}(?:-part-\\d+)?\\.json$`).test(name)) {
      fs.unlinkSync(path.join(INTERMEDIATE, name));
    }
  }

  const nodeCount = out.nodes.length;
  const edgeCount = out.edges.length;
  if (nodeCount <= 60 && edgeCount <= 120) {
    fs.writeFileSync(path.join(INTERMEDIATE, `batch-${batch.batchIndex}.json`), JSON.stringify(out, null, 2));
    continue;
  }

  const parts = Math.ceil(Math.max(nodeCount / 60, edgeCount / 120));
  const sortedFiles = [...new Set(batch.files.map(f => f.path))].sort((a, b) => a.localeCompare(b));
  const chunkSize = Math.ceil(sortedFiles.length / parts);
  for (let i = 0; i < parts; i++) {
    const fileChunk = new Set(sortedFiles.slice(i * chunkSize, (i + 1) * chunkSize));
    const partNodes = out.nodes.filter(n => fileChunk.has(n.filePath));
    const partNodeIds = new Set(partNodes.map(n => n.id));
    const partEdges = out.edges.filter(e => partNodeIds.has(e.source));
    fs.writeFileSync(path.join(INTERMEDIATE, `batch-${batch.batchIndex}-part-${i + 1}.json`), JSON.stringify({ nodes: partNodes, edges: partEdges }, null, 2));
  }
}

const summary = [];
for (const batch of batches) {
  const batchFiles = fs.readdirSync(INTERMEDIATE).filter(name => new RegExp(`^batch-${batch.batchIndex}(?:-part-\\d+)?\\.json$`).test(name));
  summary.push({ batch: batch.batchIndex, files: batchFiles });
}
console.log(JSON.stringify(summary, null, 2));
