import { initializeApp } from "firebase/app";
import {
  addDoc,
  collection,
  doc,
  getDocs,
  getFirestore,
  limit,
  query,
  setDoc,
} from "firebase/firestore";
import firebaseConfig from "./firebase-config.js";

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

const PAGE = document.body.dataset.page || "home";
const CART_KEY = "minhaloja_cart";
const WISHLIST_KEY = "minhaloja_wishlist";
const DEFAULT_PRODUCT_LIMIT = 60;
const MAX_CART_QUANTITY = 99;

const CATEGORY_THEMES = {
  Masculino: { start: "#0f172a", end: "#1e293b", accent: "#d4af37", emoji: "🖤" },
  Feminino: { start: "#7f1d1d", end: "#be185d", accent: "#f9a8d4", emoji: "🌸" },
  Unissex: { start: "#243b53", end: "#486581", accent: "#d9e2ec", emoji: "🌙" },
  Nicho: { start: "#3f2a56", end: "#150b24", accent: "#f1d279", emoji: "💎" },
  Acessorios: { start: "#0f4c5c", end: "#1b9aaa", accent: "#f3c969", emoji: "🧳" },
  Promocoes: { start: "#7c2d12", end: "#ea580c", accent: "#fed7aa", emoji: "🏷️" },
  Perfume: { start: "#111827", end: "#374151", accent: "#f3d387", emoji: "✨" },
};

const PRODUCT_PRESETS = {
  "perf-1": {
    brand: "Chanel",
    tagline: "Assinatura fresca, amadeirada e precisa.",
    longDescription:
      "Bleu de Chanel abre com energia citrica e seca para um fundo elegante de cedro e incenso. Um perfume versatil, limpo e muito facil de usar em rotinas premium.",
    volumeMl: "100 ml",
    concentration: "Eau de Parfum",
    olfactiveFamily: "Aromatico Amadeirado",
    occasion: "Escritorio, encontros e noite",
    topNotes: ["Limao siciliano", "Menta", "Toranja"],
    heartNotes: ["Gengibre", "Noz-moscada", "Jasmin"],
    baseNotes: ["Incenso", "Cedro", "Sandalo"],
    highlights: [
      "Fixacao elegante de longa duracao",
      "Perfil sofisticado e versatil",
      "Excelente para uso diario premium",
    ],
    imageEmoji: "🧊",
    rating: 4.9,
    reviews: 187,
    oldPrice: 930,
    isSale: true,
  },
  "perf-2": {
    brand: "Dior",
    tagline: "Frescor mineral com assinatura intensa.",
    longDescription:
      "Dior Sauvage combina bergamota vibrante com especiarias e ambroxan. O resultado e um perfume limpo, expansivo e moderno, perfeito para quem quer presenca imediata.",
    volumeMl: "100 ml",
    concentration: "Eau de Toilette",
    olfactiveFamily: "Fougere Aromatico",
    occasion: "Dia a dia, viagens e eventos sociais",
    topNotes: ["Bergamota da Calabria", "Pimenta"],
    heartNotes: ["Lavanda", "Pimenta rosa", "Vetiver"],
    baseNotes: ["Ambroxan", "Cedro", "Labdano"],
    highlights: [
      "Saida fresca e marcante",
      "Projecao ampla sem perder refinamento",
      "Excelente assinatura masculina atual",
    ],
    imageEmoji: "🌌",
    rating: 4.8,
    reviews: 163,
    oldPrice: 850,
    isSale: true,
  },
  "perf-3": {
    brand: "Chanel",
    tagline: "O floral aldeidico mais iconico da perfumaria.",
    longDescription:
      "Chanel No. 5 equilibra aldeidos luminosos, flores nobres e um fundo cremoso. A composicao transmite classe imediata e permanece atual com um ar classico raro.",
    volumeMl: "100 ml",
    concentration: "Eau de Parfum",
    olfactiveFamily: "Floral Aldeidico",
    occasion: "Eventos, jantares e ocasioes especiais",
    topNotes: ["Aldeidos", "Neroli", "Ylang-ylang"],
    heartNotes: ["Rosa", "Jasmin", "Lirio-do-vale"],
    baseNotes: ["Baunilha", "Vetiver", "Sandalo"],
    highlights: [
      "Classico de altissima assinatura",
      "Acorde floral sofisticado",
      "Presenca memoravel e feminina",
    ],
    imageEmoji: "🌺",
    rating: 4.9,
    reviews: 204,
    isNew: true,
  },
  "perf-4": {
    brand: "Creed",
    tagline: "Frutado, amadeirado e extremamente prestigioso.",
    longDescription:
      "Aventus mistura abacaxi, bétula e musk em uma estrutura brilhante e poderosa. Um nicho de alto impacto, pensado para quem quer luxo reconhecivel e muito desempenho.",
    volumeMl: "100 ml",
    concentration: "Eau de Parfum",
    olfactiveFamily: "Frutado Chypre",
    occasion: "Noite, eventos premium e celebracoes",
    topNotes: ["Abacaxi", "Bergamota", "Groselha preta"],
    heartNotes: ["Betula", "Jasmin", "Patchouli"],
    baseNotes: ["Musgo de carvalho", "Baunilha", "Musk"],
    highlights: [
      "Nicho de altissimo reconhecimento",
      "Mistura luminosa e poderosa",
      "Acabamento luxuoso para ocasioes especiais",
    ],
    imageEmoji: "👑",
    rating: 5,
    reviews: 118,
  },
  "perf-5": {
    brand: "Tom Ford",
    tagline: "Gourmand intenso com cereja escura e licor.",
    longDescription:
      "Lost Cherry abre doce e provocante, evoluindo para um corpo aveludado com amendoa, especiarias e madeiras. Um perfume ousado e muito sensual.",
    volumeMl: "50 ml",
    concentration: "Eau de Parfum",
    olfactiveFamily: "Oriental Gourmand",
    occasion: "Noite, inverno e producoes marcantes",
    topNotes: ["Cereja negra", "Licor de cereja", "Amendoa amarga"],
    heartNotes: ["Rosa turca", "Jasmin sambac", "Ameixa"],
    baseNotes: ["Fava tonka", "Sandalo", "Vetiver"],
    highlights: [
      "Perfil gourmand sofisticado",
      "Assinatura sensual e moderna",
      "Excelente para clima frio ou noturno",
    ],
    imageEmoji: "🍒",
    rating: 4.8,
    reviews: 94,
  },
  "perf-6": {
    brand: "Calvin Klein",
    tagline: "Frescor compartilhavel com assinatura limpa.",
    longDescription:
      "CK One combina notas citricas, aromaticas e musk em uma estrutura minimalista. Um classico unissex muito facil de usar e ideal para dias quentes.",
    volumeMl: "100 ml",
    concentration: "Eau de Toilette",
    olfactiveFamily: "Citrico Aromatico",
    occasion: "Rotina leve, calor e viagens",
    topNotes: ["Bergamota", "Lima", "Abacaxi"],
    heartNotes: ["Cha verde", "Violeta", "Noz-moscada"],
    baseNotes: ["Musk", "Amber", "Cedro"],
    highlights: [
      "Leve, fresco e muito democratico",
      "Facil de reaplicar ao longo do dia",
      "Boa opcao de entrada para colecao",
    ],
    imageEmoji: "🤍",
    rating: 4.7,
    reviews: 151,
    oldPrice: 410,
    isSale: true,
  },
};

let productCache = null;
let productCachePromise = null;
let searchState = { open: false };
let observer = null;

const FirebaseDB = {
  async getProducts(count = DEFAULT_PRODUCT_LIMIT) {
    try {
      const productsQuery = query(collection(db, "produtos"), limit(count));
      const snapshot = await getDocs(productsQuery);
      return snapshot.docs.map((entry) => ({ id: entry.id, ...entry.data() }));
    } catch (error) {
      console.error("Erro ao buscar produtos do Firebase:", error);
      return [];
    }
  },

  async addNewsletterEmail(email) {
    try {
      await addDoc(collection(db, "newsletter"), {
        email,
        createdAt: new Date(),
      });
      return true;
    } catch (error) {
      console.error("Erro ao salvar newsletter:", error);
      return false;
    }
  },

  async createOrder(orderData) {
    try {
      const localOrderPayload = {
        customer: orderData.customer || {},
        total: orderData.total || 0,
        items: (orderData.items || []).map((item) => ({
          product_id: item.product_id || item.id || "",
          product_name: item.name || item.product_name || "Produto",
          quantity: item.quantity || 1,
          unit_price: item.price || item.unit_price || 0,
        })),
      };

      let localResponse = null;
      try {
        localResponse = await fetch("http://localhost:5000/order", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(localOrderPayload),
        });
      } catch {
        localResponse = null;
      }

      if (localResponse) {
        const result = await localResponse.json().catch(() => ({}));
        if (!localResponse.ok) {
          throw new Error(result.message || "Pedido recusado pelo sistema local.");
        }
        return result.order_id;
      }

      const orderId = `ord-${Date.now().toString().slice(-6)}`;
      const payload = {
        clienteNome: orderData.customer?.name || "Cliente",
        clienteEmail: orderData.customer?.email || "",
        clienteTelefone: orderData.customer?.phone || "",
        clienteEndereco: orderData.customer?.address || "",
        itens: (orderData.items || []).map((item) => ({
          produtoId: item.product_id || item.id || "",
          produtoNome: item.name || item.product_name || "Produto",
          preco: item.price || item.unit_price || 0,
          quantidade: item.quantity || 1,
        })),
        total: orderData.total || 0,
        status: "pendente",
        dataCriacao: new Date().toISOString(),
      };

      await setDoc(doc(db, "pedidos", orderId), payload);
      return orderId;
    } catch (error) {
      console.error("Erro ao criar pedido:", error);
      throw error;
    }
  },

  async initProducts(containerId, maxCount = null) {
    const products = await loadProductCatalog(maxCount);
    const scopedProducts = maxCount ? products.slice(0, maxCount) : products;
    window.CURRENT_PRODUCTS = scopedProducts;

    if (containerId) {
      renderProducts(containerId, scopedProducts);
    }
  },
};

function normalizeText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function toNumber(value, fallback = 0) {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function toBoolean(value) {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return value === 1;
  }
  return ["true", "1", "sim", "yes"].includes(normalizeText(value));
}

function parseList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  if (!value) {
    return [];
  }
  return String(value)
    .split(/\r?\n|,|;|\|/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function guessBrand(productName) {
  const name = String(productName || "");
  const matches = ["Chanel", "Dior", "Creed", "Tom Ford", "Calvin Klein"];
  return matches.find((brand) => name.includes(brand)) || "Maison";
}

function toCategoryKey(category) {
  const normalized = normalizeText(category || "Perfume");
  const found = Object.keys(CATEGORY_THEMES).find(
    (key) => normalizeText(key) === normalized,
  );
  return found || "Perfume";
}

function getCategoryTheme(category) {
  return CATEGORY_THEMES[toCategoryKey(category)] || CATEGORY_THEMES.Perfume;
}

function buildDefaultNotes(name) {
  if (normalizeText(name).includes("cherry")) {
    return {
      topNotes: ["Frutas escuras", "Especiarias suaves"],
      heartNotes: ["Flor branca", "Acorde licoroso"],
      baseNotes: ["Madeiras quentes", "Fava tonka"],
    };
  }
  return {
    topNotes: ["Citricos nobres", "Especiarias leves"],
    heartNotes: ["Acorde aromatico", "Flor transparente"],
    baseNotes: ["Madeiras refinadas", "Musk limpo"],
  };
}

function normalizeProduct(rawProduct) {
  const preset = PRODUCT_PRESETS[rawProduct.id] || {};
  const merged = { ...preset, ...rawProduct };
  const defaultNotes = buildDefaultNotes(merged.name || merged.nome);
  const category = merged.category || merged.categoria || "Perfume";
  const theme = getCategoryTheme(category);
  const gallery = parseList(
    merged.images ||
      merged.image_urls ||
      merged.imageUrls ||
      merged.gallery ||
      merged.galeria,
  );
  const imageUrl = merged.image_url || merged.imageUrl || gallery[0] || "";
  const highlights = parseList(merged.highlights || merged.destaques);

  const product = {
    id: merged.id,
    name: merged.name || merged.nome || "Produto",
    brand: merged.brand || merged.marca || guessBrand(merged.name || merged.nome),
    tagline: merged.tagline || merged.subtitulo || "",
    description: merged.description || merged.descricao || "Sem descricao informada.",
    longDescription:
      merged.longDescription ||
      merged.descricao_longa ||
      merged.descricaoLonga ||
      merged.description ||
      merged.descricao ||
      "Sem descricao detalhada informada.",
    price: toNumber(merged.price ?? merged.preco),
    oldPrice: toNumber(merged.oldPrice ?? merged.precoAntigo),
    stock: Number.parseInt(merged.stock ?? merged.estoque ?? 0, 10) || 0,
    category,
    sku: merged.sku || merged.codigo || merged.id?.toUpperCase() || "SEM-SKU",
    volumeMl: merged.volumeMl || merged.volume_ml || merged.tamanho || "100 ml",
    concentration:
      merged.concentration || merged.concentracao || "Eau de Parfum",
    olfactiveFamily:
      merged.olfactiveFamily || merged.familiaOlfativa || "Amadeirado",
    occasion:
      merged.occasion ||
      merged.ocasiao ||
      merged.ocasiacao ||
      "Uso versatil ao longo do dia",
    topNotes:
      parseList(merged.topNotes || merged.notasTopo).length > 0
        ? parseList(merged.topNotes || merged.notasTopo)
        : defaultNotes.topNotes,
    heartNotes:
      parseList(merged.heartNotes || merged.notasCoracao).length > 0
        ? parseList(merged.heartNotes || merged.notasCoracao)
        : defaultNotes.heartNotes,
    baseNotes:
      parseList(merged.baseNotes || merged.notasBase).length > 0
        ? parseList(merged.baseNotes || merged.notasBase)
        : defaultNotes.baseNotes,
    highlights:
      highlights.length > 0
        ? highlights
        : [
            "Curadoria premium com envio cuidadoso",
            "Produto original com garantia de procedencia",
            "Detalhes completos disponiveis na pagina do item",
          ],
    rating: toNumber(merged.rating, 4.8),
    reviews: Number.parseInt(merged.reviews, 10) || 96,
    isSale: toBoolean(merged.isSale || merged.emOferta) || toNumber(merged.oldPrice ?? merged.precoAntigo) > 0,
    isNew: toBoolean(merged.isNew || merged.eNovo),
    imageEmoji: merged.imageEmoji || merged.emoji || theme.emoji,
    imageUrl,
    images: imageUrl ? [imageUrl, ...gallery.filter((item) => item !== imageUrl)] : gallery,
  };

  return product;
}

function productMatchesQuery(product, term) {
  const queryText = normalizeText(term);
  if (!queryText) {
    return true;
  }

  const haystack = [
    product.name,
    product.brand,
    product.category,
    product.tagline,
    product.description,
    product.longDescription,
    product.olfactiveFamily,
    product.occasion,
    product.topNotes.join(" "),
    product.heartNotes.join(" "),
    product.baseNotes.join(" "),
    product.highlights.join(" "),
  ]
    .map((item) => normalizeText(item))
    .join(" ");

  return haystack.includes(queryText);
}

async function loadProductCatalog(limitCount = null) {
  if (productCache && (!limitCount || productCache.length <= limitCount)) {
    return limitCount ? productCache.slice(0, limitCount) : productCache;
  }

  if (!productCachePromise) {
    productCachePromise = (async () => {
      let products = await FirebaseDB.getProducts(DEFAULT_PRODUCT_LIMIT);
      if (!products.length && Array.isArray(window.PRODUCTS_LIVE)) {
        products = window.PRODUCTS_LIVE;
      }
      productCache = products.map(normalizeProduct);
      window.CURRENT_PRODUCTS = productCache;
      return productCache;
    })().finally(() => {
      productCachePromise = null;
    });
  }

  const catalog = await productCachePromise;
  return limitCount ? catalog.slice(0, limitCount) : catalog;
}

function formatPrice(value) {
  return `R$ ${toNumber(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
  })}`;
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (char) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return entities[char] || char;
  });
}

function getProductGallery(product) {
  if (product.images.length > 0) {
    return product.images.map((url, index) => ({
      type: "image",
      url,
      label: index === 0 ? "Frasco" : `Vista ${index + 1}`,
    }));
  }

  return [
    { type: "placeholder", label: "Frasco", caption: product.concentration },
    { type: "placeholder", label: "Detalhe", caption: product.olfactiveFamily },
    { type: "placeholder", label: "Colecao", caption: product.brand },
  ];
}

function createProductVisual(product, variant = "card", asset = null) {
  const theme = getCategoryTheme(product.category);
  const label = asset?.label || product.brand;
  const meta = asset?.caption || product.concentration;

  if (asset?.type === "image" && asset.url) {
    return `
      <div class="product-visual product-visual--${variant}">
        <img class="product-visual__image" src="${asset.url}" alt="${product.name}">
      </div>
    `;
  }

  return `
    <div
      class="product-visual product-visual--${variant}"
      style="--visual-start:${theme.start}; --visual-end:${theme.end}; --visual-accent:${theme.accent};"
    >
      <div class="product-visual__halo"></div>
      <span class="product-visual__label">${label}</span>
      <div class="product-visual__emoji">${product.imageEmoji}</div>
      <strong class="product-visual__title">${product.name}</strong>
      <span class="product-visual__meta">${meta}</span>
    </div>
  `;
}

function createProductCard(product) {
  const badge = product.isSale
    ? `<span class="product-card__badge product-card__badge--sale">Oferta</span>`
    : product.isNew
      ? `<span class="product-card__badge product-card__badge--new">Novo</span>`
      : "";
  const oldPrice = product.oldPrice
    ? `<div class="product-card__price-old">${formatPrice(product.oldPrice)}</div>`
    : "";
  const wishlistActive = Wishlist.hasItem(product.id);
  const isAvailable = product.stock > 0;
  const wishlistLabel = wishlistActive ? "Remover dos favoritos" : "Adicionar aos favoritos";

  return `
    <article class="product-card animate-on-scroll" id="${product.id}" aria-label="Produto: ${product.name}">
      <div class="product-card__image">
        ${createProductVisual(product, "card", getProductGallery(product)[0])}
        ${badge}
        <button
          class="product-card__wishlist ${wishlistActive ? "wishlist-active" : ""}"
          aria-label="${wishlistLabel}: ${product.name}"
          title="${wishlistLabel}"
        >
          <svg width="16" height="16" fill="${wishlistActive ? "currentColor" : "none"}" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
          </svg>
        </button>
        <button
          class="product-card__add-cart"
          data-product-id="${product.id}"
          ${isAvailable ? "" : "disabled"}
        >
          ${isAvailable ? "Adicionar ao carrinho" : "Indisponivel"}
        </button>
      </div>
      <div class="product-card__body">
        <div class="product-card__category-row">
          <span class="product-card__category">${product.category}</span>
          <span class="product-card__stock ${product.stock > 0 ? "" : "is-empty"}">
            ${product.stock > 0 ? `${product.stock} em estoque` : "Sem estoque"}
          </span>
        </div>
        <h3 class="product-card__name">${product.name}</h3>
        <p class="product-card__copy">${product.tagline || product.description}</p>
        <div class="product-card__rating">
          <span class="product-card__stars" aria-label="${product.rating} estrelas">★★★★★</span>
          <span class="product-card__rating-count">(${product.reviews})</span>
        </div>
        <div class="product-card__footer">
          <div>
            <div class="product-card__price-current">${formatPrice(product.price)}</div>
            ${oldPrice}
          </div>
          <div class="product-card__installments">12x sem juros</div>
        </div>
      </div>
    </article>
  `;
}

function renderProducts(containerId, productList = []) {
  const container = document.getElementById(containerId);
  if (!container) {
    return;
  }

  if (!productList.length) {
    container.innerHTML = `
      <div class="empty-state empty-state--inline">
        <h3>Nenhum produto encontrado</h3>
        <p>Tente ajustar os filtros ou use um termo de busca diferente.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = productList.map(createProductCard).join("");
  observeAnimatedElements(container);
}

const Cart = {
  getProduct(productId) {
    return productCache?.find((entry) => entry.id === productId) || null;
  },

  getStockLimit(productId) {
    const product = this.getProduct(productId);
    if (!product) {
      return MAX_CART_QUANTITY;
    }
    return Math.max(0, Number.parseInt(product.stock, 10) || 0);
  },

  getItems() {
    try {
      const saved = JSON.parse(localStorage.getItem(CART_KEY)) || [];
      return saved.map((item) => ({
        id: item.id,
        name: item.name || "Produto",
        price: toNumber(item.price),
        imageEmoji: item.imageEmoji || "📦",
        imageUrl: item.imageUrl || "",
        category: item.category || "Produto",
        brand: item.brand || "Maison",
        stock: Number.parseInt(item.stock, 10) || this.getStockLimit(item.id),
        qty: Math.max(1, Number.parseInt(item.qty, 10) || 1),
      }));
    } catch {
      return [];
    }
  },

  save(items) {
    const normalizedItems = items
      .map((item) => {
        const stockLimit = Math.min(
          MAX_CART_QUANTITY,
          Number.parseInt(item.stock, 10) || this.getStockLimit(item.id),
        );
        const qty = Math.max(1, Math.min(Number.parseInt(item.qty, 10) || 1, stockLimit || 1));
        return { ...item, stock: stockLimit, qty };
      })
      .filter((item) => item.stock !== 0);

    localStorage.setItem(CART_KEY, JSON.stringify(normalizedItems));
    this.updateBadge();
  },

  addItem(productOrId, name, price, imageEmoji = "📦", quantity = 1) {
    const product =
      typeof productOrId === "object"
        ? normalizeProduct(productOrId)
        : {
            id: productOrId,
            name,
            price,
            imageEmoji,
            category: "Produto",
            brand: "Maison",
            imageUrl: "",
            stock: MAX_CART_QUANTITY,
          };

    const stockLimit = Math.min(MAX_CART_QUANTITY, Number.parseInt(product.stock, 10) || 0);
    if (stockLimit <= 0) {
      this.showToast(`${product.name} esta indisponivel no momento.`);
      return false;
    }

    const items = this.getItems();
    const existing = items.find((entry) => entry.id === product.id);
    const requestedQty = Math.max(1, Number.parseInt(quantity, 10) || 1);
    if (existing) {
      existing.stock = stockLimit;
      existing.qty = Math.min(existing.qty + requestedQty, stockLimit);
    } else {
      items.push({
        id: product.id,
        name: product.name,
        price: product.price,
        imageEmoji: product.imageEmoji,
        imageUrl: product.imageUrl,
        category: product.category,
        brand: product.brand,
        stock: stockLimit,
        qty: Math.min(requestedQty, stockLimit),
      });
    }
    this.save(items);
    this.showToast(
      requestedQty > stockLimit
        ? `${product.name} adicionado com limite de estoque.`
        : `${product.name} adicionado ao carrinho.`,
    );
    return true;
  },

  removeItem(productId) {
    this.save(this.getItems().filter((item) => item.id !== productId));
  },

  clear() {
    localStorage.removeItem(CART_KEY);
    this.updateBadge();
  },

  updateBadge() {
    const badge = document.getElementById("cart-count");
    const count = this.getItems().reduce((sum, item) => sum + item.qty, 0);

    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? "inline-flex" : "none";
    }

    const cartButton = document.getElementById("btn-cart");
    if (cartButton) {
      cartButton.setAttribute(
        "aria-label",
        `Carrinho de compras (${count} ${count === 1 ? "item" : "itens"})`,
      );
    }
  },

  showToast(message) {
    const oldToast = document.getElementById("cart-toast");
    if (oldToast) {
      oldToast.remove();
    }

    const toast = document.createElement("div");
    toast.id = "cart-toast";
    toast.className = "site-toast";
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    toast.textContent = message;
    document.body.appendChild(toast);

    window.setTimeout(() => {
      toast.classList.add("is-hiding");
      window.setTimeout(() => toast.remove(), 250);
    }, 2400);
  },
};

const Wishlist = {
  getItems() {
    try {
      return JSON.parse(localStorage.getItem(WISHLIST_KEY)) || [];
    } catch {
      return [];
    }
  },

  save(items) {
    localStorage.setItem(WISHLIST_KEY, JSON.stringify(items));
    this.updateBadge();
  },

  hasItem(productId) {
    return this.getItems().includes(productId);
  },

  toggleItem(productId) {
    const items = this.getItems();
    const exists = items.includes(productId);
    const nextItems = exists ? items.filter((id) => id !== productId) : [...items, productId];
    this.save(nextItems);
    return !exists;
  },

  updateBadge() {
    const badge = document.getElementById("wishlist-count");
    if (!badge) {
      return;
    }

    const count = this.getItems().length;
    badge.textContent = count;
    badge.style.display = count > 0 ? "inline-flex" : "none";
  },
};

function navHref(anchor) {
  if (PAGE === "home") {
    return anchor;
  }
  return `index.html${anchor}`;
}

function buildHeader() {
  const links = [
    { label: "Home", href: "index.html", page: "home" },
    { label: "Produtos", href: "produtos.html", page: "products" },
    { label: "Categorias", href: navHref("#categorias"), page: "" },
    { label: "Sobre", href: navHref("#sobre"), page: "" },
    { label: "Contato", href: navHref("#contato"), page: "" },
  ];

  return `
    <nav class="navbar ${PAGE === "home" ? "" : "scrolled"}" id="navbar" aria-label="Menu principal">
      <div class="navbar__inner">
        <a class="navbar__logo" href="index.html" aria-label="Grand Parfum - Home">
          Grand<span>Parfum</span>
        </a>

        <form class="navbar__search" id="site-search-form" role="search" novalidate>
          <label class="sr-only" for="site-search-input">Buscar produtos</label>
          <svg class="navbar__search-icon" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
          <input
            class="navbar__search-input"
            id="site-search-input"
            type="search"
            placeholder="Buscar fragrancias, marcas ou notas..."
            autocomplete="off"
          >
          <div class="navbar__search-results" id="site-search-results" hidden></div>
        </form>

        <div class="navbar__right">
          <ul class="navbar__links" role="list">
            ${links
              .map(
                (link) => `
                  <li>
                    <a class="navbar__link ${PAGE === link.page ? "is-active" : ""}" href="${link.href}">
                      ${link.label}
                    </a>
                  </li>
                `,
              )
              .join("")}
          </ul>

          <div class="navbar__actions">
            <a href="favoritos.html" class="navbar__icon-btn" aria-label="Lista de desejos">
              <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
              <span class="navbar__cart-badge" id="wishlist-count">0</span>
            </a>
            <a href="carrinho.html" class="navbar__icon-btn" id="btn-cart" aria-label="Carrinho de compras (0 itens)">
              <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="9" cy="21" r="1"></circle>
                <circle cx="20" cy="21" r="1"></circle>
                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
              </svg>
              <span class="navbar__cart-badge" id="cart-count">0</span>
            </a>
            <a href="#" class="navbar__btn-primary" data-toast="Area de clientes em breve.">
              Minha conta
            </a>
          </div>
        </div>

        <button class="navbar__hamburger" id="btn-hamburger" aria-label="Abrir menu" aria-expanded="false" aria-controls="mobile-menu">
          <span></span><span></span><span></span>
        </button>
      </div>

      <div class="mobile-menu" id="mobile-menu" hidden>
        ${links
          .map((link) => `<a href="${link.href}" class="mobile-menu__link">${link.label}</a>`)
          .join("")}
        <a href="favoritos.html" class="mobile-menu__link">Favoritos</a>
        <a href="carrinho.html" class="mobile-menu__link">Carrinho</a>
        <a href="#" class="mobile-menu__cta" data-toast="Area de clientes em breve.">Minha conta</a>
      </div>
    </nav>
  `;
}

function buildFooter() {
  return `
    <footer class="footer" id="footer" aria-label="Rodape">
      <div class="footer__grid">
        <div>
          <div class="footer__brand-name">Grand<span>Parfum</span></div>
          <p class="footer__desc">
            Curadoria de fragrancias de luxo com experiencia consistente do catalogo ao checkout.
          </p>
          <div class="footer__social" aria-label="Redes sociais">
            <a href="#" class="footer__social-link" aria-label="Instagram">IG</a>
            <a href="#" class="footer__social-link" aria-label="WhatsApp">WA</a>
            <a href="#" class="footer__social-link" aria-label="Facebook">FB</a>
          </div>
        </div>

        <div>
          <h3 class="footer__col-title">Loja</h3>
          <ul class="footer__links" role="list">
            <li><a href="produtos.html" class="footer__link">Todos os produtos</a></li>
            <li><a href="produtos.html?filter=sale" class="footer__link">Ofertas</a></li>
            <li><a href="produtos.html?filter=new" class="footer__link">Lancamentos</a></li>
            <li><a href="favoritos.html" class="footer__link">Favoritos</a></li>
          </ul>
        </div>

        <div>
          <h3 class="footer__col-title">Suporte</h3>
          <ul class="footer__links" role="list">
            <li><a href="#" class="footer__link" data-toast="Central de ajuda em breve.">Central de ajuda</a></li>
            <li><a href="#" class="footer__link" data-toast="Rastreio em manutencao.">Rastrear pedido</a></li>
            <li><a href="#" class="footer__link" data-toast="Politica de devolucao: 30 dias.">Politica de devolucao</a></li>
            <li><a href="${navHref("#contato")}" class="footer__link">Fale conosco</a></li>
          </ul>
        </div>

        <div>
          <h3 class="footer__col-title">Empresa</h3>
          <ul class="footer__links" role="list">
            <li><a href="${navHref("#sobre")}" class="footer__link">Sobre nos</a></li>
            <li><a href="#" class="footer__link" data-toast="Conteudos editoriais em breve.">Blog</a></li>
            <li><a href="#" class="footer__link" data-toast="Programa de afiliados em breve.">Afiliados</a></li>
            <li><a href="#" class="footer__link" data-toast="Atendimento premium por WhatsApp em breve.">Atendimento premium</a></li>
          </ul>
        </div>
      </div>

      <div class="footer__bottom">
        <p class="footer__copy">© 2026 Grand Parfum. Todos os direitos reservados.</p>
        <nav class="footer__bottom-links" aria-label="Links legais">
          <a href="#" class="footer__bottom-link" data-toast="Politica de privacidade em atualizacao.">Privacidade</a>
          <a href="#" class="footer__bottom-link" data-toast="Termos de uso em atualizacao.">Termos</a>
          <a href="#" class="footer__bottom-link" data-toast="Utilizamos apenas cookies essenciais.">Cookies</a>
        </nav>
      </div>
    </footer>
  `;
}

function renderSiteChrome() {
  const headerSlot = document.querySelector("[data-site-header]");
  const footerSlot = document.querySelector("[data-site-footer]");

  if (headerSlot) {
    headerSlot.innerHTML = buildHeader();
  }
  if (footerSlot) {
    footerSlot.innerHTML = buildFooter();
  }
}

function setupNavbarBehavior() {
  const navbar = document.getElementById("navbar");
  const hamburger = document.getElementById("btn-hamburger");
  const mobileMenu = document.getElementById("mobile-menu");

  if (!navbar) {
    return;
  }

  const syncNavbarState = () => {
    const shouldBeScrolled = PAGE !== "home" || window.scrollY > 18;
    navbar.classList.toggle("scrolled", shouldBeScrolled);
  };

  syncNavbarState();
  window.addEventListener("scroll", syncNavbarState, { passive: true });

  if (hamburger && mobileMenu) {
    hamburger.addEventListener("click", () => {
      const isOpen = mobileMenu.hidden === false;
      mobileMenu.hidden = isOpen;
      hamburger.setAttribute("aria-expanded", String(!isOpen));
      document.body.classList.toggle("menu-open", !isOpen);
    });

    mobileMenu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        mobileMenu.hidden = true;
        hamburger.setAttribute("aria-expanded", "false");
        document.body.classList.remove("menu-open");
      });
    });
  }
}

function renderSearchResults(resultsContainer, products, queryText) {
  if (!queryText.trim()) {
    resultsContainer.hidden = true;
    resultsContainer.innerHTML = "";
    searchState.open = false;
    return;
  }

  const matches = products.filter((product) => productMatchesQuery(product, queryText)).slice(0, 6);
  if (!matches.length) {
    resultsContainer.innerHTML = `
      <div class="search-results__empty">
        <strong>Nada encontrado.</strong>
        <span>Tente buscar por marca, categoria ou notas.</span>
      </div>
    `;
    resultsContainer.hidden = false;
    searchState.open = true;
    return;
  }

  resultsContainer.innerHTML = `
    <div class="search-results__list">
      ${matches
        .map(
          (product) => `
            <a class="search-result" href="produto.html?id=${encodeURIComponent(product.id)}">
              <div class="search-result__media">
                ${createProductVisual(product, "search", getProductGallery(product)[0])}
              </div>
              <div class="search-result__content">
                <strong>${product.name}</strong>
                <span>${product.brand} · ${product.category}</span>
              </div>
              <span class="search-result__price">${formatPrice(product.price)}</span>
            </a>
          `,
        )
        .join("")}
    </div>
    <a class="search-results__all" href="produtos.html?q=${encodeURIComponent(queryText)}">
      Ver todos os resultados para "${queryText}"
    </a>
  `;
  resultsContainer.hidden = false;
  searchState.open = true;
}

async function setupSiteSearch() {
  const searchForm = document.getElementById("site-search-form");
  const searchInput = document.getElementById("site-search-input");
  const searchResults = document.getElementById("site-search-results");
  if (!searchForm || !searchInput || !searchResults) {
    return;
  }

  const products = await loadProductCatalog();
  const currentQuery = new URLSearchParams(window.location.search).get("q");
  if (currentQuery) {
    searchInput.value = currentQuery;
  }

  searchInput.addEventListener("input", (event) => {
    renderSearchResults(searchResults, products, event.target.value);
  });

  searchInput.addEventListener("focus", (event) => {
    renderSearchResults(searchResults, products, event.target.value);
  });

  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const queryValue = searchInput.value.trim();
    window.location.href = queryValue
      ? `produtos.html?q=${encodeURIComponent(queryValue)}`
      : "produtos.html";
  });

  document.addEventListener("click", (event) => {
    if (!searchForm.contains(event.target) && searchState.open) {
      searchResults.hidden = true;
      searchResults.innerHTML = "";
      searchState.open = false;
    }
  });
}

function setupIntersectionObserver() {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    {
      rootMargin: "0px 0px -60px 0px",
      threshold: 0.1,
    },
  );

  observeAnimatedElements(document);
}

function observeAnimatedElements(scope) {
  if (!observer) {
    return;
  }
  scope.querySelectorAll(".animate-on-scroll").forEach((element) => observer.observe(element));
}

function setupGlobalInteractions() {
  document.addEventListener("click", (event) => {
    const toastLink = event.target.closest("[data-toast]");
    if (toastLink) {
      event.preventDefault();
      Cart.showToast(toastLink.dataset.toast);
      return;
    }

    const wishlistButton = event.target.closest(".product-card__wishlist");
    if (wishlistButton) {
      event.preventDefault();
      event.stopPropagation();
      const card = wishlistButton.closest(".product-card");
      if (!card) {
        return;
      }
      const isActive = Wishlist.toggleItem(card.id);
      wishlistButton.classList.toggle("wishlist-active", isActive);
      Cart.showToast(isActive ? "Produto salvo nos favoritos." : "Produto removido dos favoritos.");
      if (PAGE === "favorites") {
        initFavoritesPage();
      }
      return;
    }

    const addCartButton = event.target.closest(".product-card__add-cart");
    if (addCartButton) {
      event.preventDefault();
      event.stopPropagation();
      const productId = addCartButton.dataset.productId;
      const product = productCache?.find((entry) => entry.id === productId);
      if (product) {
        Cart.addItem(product);
      }
      return;
    }

    const productCard = event.target.closest(".product-card");
    if (productCard) {
      window.location.href = `produto.html?id=${encodeURIComponent(productCard.id)}`;
    }
  });
}

function getFeaturedProducts(products, count = 4) {
  const scored = [...products].sort((left, right) => {
    const leftScore = (left.isSale ? 2 : 0) + left.rating;
    const rightScore = (right.isSale ? 2 : 0) + right.rating;
    return rightScore - leftScore;
  });
  return scored.slice(0, count);
}

async function initHomePage() {
  const featuredGrid = document.getElementById("featured-products");
  if (!featuredGrid) {
    return;
  }

  const products = await loadProductCatalog();
  renderProducts("featured-products", getFeaturedProducts(products, 4));
}

function matchesCategory(product, category) {
  if (!category || normalizeText(category) === "all") {
    return true;
  }
  return normalizeText(product.category) === normalizeText(category);
}

async function initProductsPage() {
  const gridId = "all-products-grid";
  const grid = document.getElementById(gridId);
  if (!grid) {
    return;
  }

  const params = new URLSearchParams(window.location.search);
  const pageSearch = document.getElementById("products-page-search");
  const resultsCount = document.getElementById("products-count");
  const filterButtons = [...document.querySelectorAll("[data-category-filter]")];
  const viewButtons = [...document.querySelectorAll("[data-product-filter]")];
  const products = await loadProductCatalog();

  let activeCategory = params.get("cat") || "all";
  let queryText = params.get("q") || "";
  let activeFilter = params.get("filter") || "all";

  if (pageSearch) {
    pageSearch.value = queryText;
  }

  function syncButtons() {
    filterButtons.forEach((button) => {
      button.classList.toggle(
        "active",
        normalizeText(button.dataset.categoryFilter) === normalizeText(activeCategory),
      );
    });
    viewButtons.forEach((button) => {
      button.classList.toggle(
        "active",
        normalizeText(button.dataset.productFilter) === normalizeText(activeFilter),
      );
    });
  }

  function syncUrl() {
    const nextParams = new URLSearchParams();
    if (normalizeText(activeCategory) !== "all") {
      nextParams.set("cat", activeCategory);
    }
    if (queryText) {
      nextParams.set("q", queryText);
    }
    if (normalizeText(activeFilter) !== "all") {
      nextParams.set("filter", activeFilter);
    }
    const nextQuery = nextParams.toString();
    window.history.replaceState({}, "", `produtos.html${nextQuery ? `?${nextQuery}` : ""}`);
  }

  function renderPageProducts() {
    let filtered = products
      .filter((product) => matchesCategory(product, activeCategory))
      .filter((product) => productMatchesQuery(product, queryText));

    if (normalizeText(activeFilter) === "sale") {
      filtered = filtered.filter((product) => product.isSale);
    }
    if (normalizeText(activeFilter) === "new") {
      filtered = filtered.filter((product) => product.isNew);
    }
    if (normalizeText(activeFilter) === "wishlist") {
      const wishlistIds = Wishlist.getItems();
      filtered = filtered.filter((product) => wishlistIds.includes(product.id));
    }

    renderProducts(gridId, filtered);
    if (resultsCount) {
      resultsCount.textContent = `${filtered.length} produto${filtered.length === 1 ? "" : "s"}`;
    }
    syncButtons();
    syncUrl();
  }

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.categoryFilter;
      renderPageProducts();
    });
  });

  viewButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeFilter = button.dataset.productFilter;
      renderPageProducts();
    });
  });

  pageSearch?.addEventListener("input", (event) => {
    queryText = event.target.value.trim();
    renderPageProducts();
  });

  renderPageProducts();
}

function createListChips(items) {
  return items.map((item) => `<span class="detail-chip">${item}</span>`).join("");
}

function createSpecificationItem(label, value) {
  return `
    <div class="spec-item">
      <span class="spec-item__label">${label}</span>
      <strong class="spec-item__value">${value}</strong>
    </div>
  `;
}

function getStockCopy(product) {
  if (product.stock <= 0) {
    return "Produto indisponivel";
  }
  if (product.stock < 8) {
    return `Ultimas ${product.stock} unidades`;
  }
  return `${product.stock} unidades em estoque`;
}

function renderGalleryStage(product, asset) {
  return `
    <div class="detail-stage__frame">
      ${createProductVisual(product, "detail", asset)}
    </div>
  `;
}

function renderProductDetail(product) {
  const detailRoot = document.getElementById("product-detail");
  const relatedRoot = document.getElementById("related-products");
  if (!detailRoot || !relatedRoot) {
    return;
  }

  const gallery = getProductGallery(product);
  detailRoot.innerHTML = `
    <div class="product-detail">
      <div class="product-detail__gallery">
        <div class="product-breadcrumbs">
          <a href="index.html">Home</a>
          <span>/</span>
          <a href="produtos.html?cat=${encodeURIComponent(product.category)}">${product.category}</a>
          <span>/</span>
          <strong>${product.name}</strong>
        </div>

        <div class="detail-stage" id="detail-stage">
          ${renderGalleryStage(product, gallery[0])}
        </div>

        <div class="detail-thumbs" id="detail-thumbs">
          ${gallery
            .map(
              (asset, index) => `
                <button class="detail-thumb ${index === 0 ? "is-active" : ""}" type="button" data-gallery-index="${index}">
                  ${createProductVisual(product, "thumb", asset)}
                </button>
              `,
            )
            .join("")}
        </div>
      </div>

      <div class="product-detail__summary">
        <div class="detail-kicker">${product.brand} · ${product.category}</div>
        <h1 class="detail-title">${product.name}</h1>
        <p class="detail-tagline">${product.tagline || product.description}</p>

        <div class="detail-rating-row">
          <span class="detail-rating">★★★★★</span>
          <span>${product.rating.toFixed(1)} · ${product.reviews} avaliacoes</span>
        </div>

        <div class="detail-price-row">
          <strong class="detail-price">${formatPrice(product.price)}</strong>
          ${product.oldPrice ? `<span class="detail-old-price">${formatPrice(product.oldPrice)}</span>` : ""}
          ${product.isSale ? `<span class="detail-discount-badge">Oferta ativa</span>` : ""}
        </div>

        <div class="detail-stock-row ${product.stock > 0 ? "" : "is-empty"}">
          ${getStockCopy(product)}
        </div>

        <p class="detail-copy">${product.longDescription}</p>

        <div class="detail-chip-list">
          ${createListChips(product.highlights)}
        </div>

        <div class="detail-actions">
          <label class="detail-qty">
            <span>Qtd.</span>
            <input id="detail-qty" type="number" min="1" max="${Math.max(product.stock, 1)}" value="${product.stock > 0 ? 1 : 0}" ${product.stock > 0 ? "" : "disabled"}>
          </label>
          <button class="btn-primary" id="detail-add-cart" ${product.stock > 0 ? "" : "disabled"}>
            ${product.stock > 0 ? "Adicionar ao carrinho" : "Indisponivel"}
          </button>
          <button class="btn-outline btn-outline--dark" id="detail-favorite">
            ${Wishlist.hasItem(product.id) ? "Remover favorito" : "Salvar favorito"}
          </button>
        </div>

        <div class="detail-spec-grid">
          ${createSpecificationItem("Volume", product.volumeMl)}
          ${createSpecificationItem("Concentracao", product.concentration)}
          ${createSpecificationItem("Familia", product.olfactiveFamily)}
          ${createSpecificationItem("Ocasião", product.occasion)}
          ${createSpecificationItem("SKU", product.sku)}
          ${createSpecificationItem("Marca", product.brand)}
        </div>
      </div>
    </div>

    <div class="detail-sections">
      <section class="detail-section">
        <div class="detail-section__header">
          <h2>Construção olfativa</h2>
          <p>Uma leitura rapida das notas principais do perfume.</p>
        </div>
        <div class="notes-grid">
          <article class="note-card">
            <h3>Saida</h3>
            <div class="detail-chip-list">${createListChips(product.topNotes)}</div>
          </article>
          <article class="note-card">
            <h3>Coracao</h3>
            <div class="detail-chip-list">${createListChips(product.heartNotes)}</div>
          </article>
          <article class="note-card">
            <h3>Fundo</h3>
            <div class="detail-chip-list">${createListChips(product.baseNotes)}</div>
          </article>
        </div>
      </section>

      <section class="detail-section detail-section--split">
        <article class="detail-info-card">
          <h2>Por que escolher este item</h2>
          <ul class="detail-points">
            ${product.highlights.map((item) => `<li>${item}</li>`).join("")}
          </ul>
        </article>
        <article class="detail-info-card">
          <h2>Entrega e trocas</h2>
          <ul class="detail-points">
            <li>Envio premium com rastreio e embalagem discreta.</li>
            <li>Troca em ate 30 dias para produtos lacrados.</li>
            <li>Suporte especializado para indicacao e pos-venda.</li>
          </ul>
        </article>
      </section>
    </div>
  `;

  const sameCategory = productCache.filter(
    (entry) => entry.id !== product.id && normalizeText(entry.category) === normalizeText(product.category),
  );
  const fallbackProducts = productCache.filter(
    (entry) =>
      entry.id !== product.id &&
      !sameCategory.some((related) => related.id === entry.id),
  );
  const relatedProducts = [...sameCategory, ...fallbackProducts].slice(0, 4);
  renderProducts("related-products", relatedProducts);

  const stage = document.getElementById("detail-stage");
  const thumbs = [...document.querySelectorAll("[data-gallery-index]")];
  thumbs.forEach((thumbButton) => {
    thumbButton.addEventListener("click", () => {
      const nextIndex = Number.parseInt(thumbButton.dataset.galleryIndex, 10);
      thumbs.forEach((button) => button.classList.remove("is-active"));
      thumbButton.classList.add("is-active");
      stage.innerHTML = renderGalleryStage(product, gallery[nextIndex]);
    });
  });

  document.getElementById("detail-add-cart")?.addEventListener("click", () => {
    const quantityInput = document.getElementById("detail-qty");
    const quantity = Number.parseInt(quantityInput?.value || "1", 10) || 1;
    if (quantity > product.stock && quantityInput) {
      quantityInput.value = String(product.stock);
      Cart.showToast(`Ajustamos para o estoque disponivel: ${product.stock}.`);
    }
    Cart.addItem(product, undefined, undefined, undefined, quantity);
  });

  document.getElementById("detail-favorite")?.addEventListener("click", (event) => {
    const active = Wishlist.toggleItem(product.id);
    event.currentTarget.textContent = active ? "Remover favorito" : "Salvar favorito";
    Cart.showToast(active ? "Produto salvo nos favoritos." : "Produto removido dos favoritos.");
  });
}

async function initProductPage() {
  const productRoot = document.getElementById("product-detail");
  if (!productRoot) {
    return;
  }

  const productId = new URLSearchParams(window.location.search).get("id");
  const products = await loadProductCatalog();
  const product = products.find((entry) => entry.id === productId);

  if (!product) {
    productRoot.innerHTML = `
      <div class="empty-state">
        <h2>Produto nao encontrado</h2>
        <p>O item pode ter sido removido ou o link esta incompleto.</p>
        <a class="btn-primary" href="produtos.html">Voltar ao catalogo</a>
      </div>
    `;
    return;
  }

  document.title = `${product.name} - Grand Parfum`;
  renderProductDetail(product);
}

async function initFavoritesPage() {
  const favoritesGrid = document.getElementById("favorites-grid");
  if (!favoritesGrid) {
    return;
  }

  const ids = Wishlist.getItems();
  const products = await loadProductCatalog();
  const favoriteProducts = products.filter((product) => ids.includes(product.id));

  if (!favoriteProducts.length) {
    favoritesGrid.innerHTML = `
      <div class="empty-state">
        <h2>Sua lista esta vazia</h2>
        <p>Use o coracao nos cards para salvar perfumes e comparar depois.</p>
        <a class="btn-primary" href="produtos.html">Explorar produtos</a>
      </div>
    `;
    return;
  }

  renderProducts("favorites-grid", favoriteProducts);
}

function createCartMedia(item) {
  const theme = getCategoryTheme(item.category);
  return `
    <div
      class="cart-item__visual"
      style="--visual-start:${theme.start}; --visual-end:${theme.end}; --visual-accent:${theme.accent};"
    >
      <span>${item.imageEmoji}</span>
    </div>
  `;
}

function readCheckoutDraft() {
  return {
    name: document.getElementById("checkout-name")?.value.trim() || "",
    email: document.getElementById("checkout-email")?.value.trim() || "",
    phone: document.getElementById("checkout-phone")?.value.trim() || "",
    address: document.getElementById("checkout-address")?.value.trim() || "",
  };
}

function renderCartPage(checkoutDraft = readCheckoutDraft()) {
  const cartRoot = document.getElementById("cart-content");
  if (!cartRoot) {
    return;
  }

  const items = Cart.getItems();
  if (!items.length) {
    cartRoot.innerHTML = `
      <div class="empty-state">
        <h2>Seu carrinho esta vazio</h2>
        <p>Adicione produtos ao carrinho para ver o resumo da compra aqui.</p>
        <a class="btn-primary" href="produtos.html">Explorar produtos</a>
      </div>
    `;
    return;
  }

  const subtotal = items.reduce((sum, item) => sum + item.price * item.qty, 0);
  const shipping = subtotal > 199 ? 0 : 25;
  const total = subtotal + shipping;

  cartRoot.innerHTML = `
    <div class="cart-layout">
      <section class="cart-items">
        ${items
          .map(
            (item) => `
              <article class="cart-item" data-cart-id="${item.id}">
                ${createCartMedia(item)}
                <div class="cart-item__body">
                  <h3>${item.name}</h3>
                  <p>${item.brand} · ${item.category}</p>
                  <strong>${formatPrice(item.price)}</strong>
                </div>
                <div class="cart-item__controls">
                  <button type="button" class="qty-btn" data-cart-action="decrease" data-cart-id="${item.id}">-</button>
                  <span class="qty-value">${item.qty}</span>
                  <button type="button" class="qty-btn" data-cart-action="increase" data-cart-id="${item.id}">+</button>
                </div>
                <button type="button" class="cart-remove" data-cart-action="remove" data-cart-id="${item.id}">
                  Remover
                </button>
              </article>
            `,
          )
          .join("")}
      </section>

      <aside class="cart-summary">
        <h2>Resumo da compra</h2>
        <div class="cart-summary__row">
          <span>Subtotal</span>
          <strong>${formatPrice(subtotal)}</strong>
        </div>
        <div class="cart-summary__row">
          <span>Frete</span>
          <strong>${shipping === 0 ? "Gratis" : formatPrice(shipping)}</strong>
        </div>
        <div class="cart-summary__row cart-summary__row--total">
          <span>Total</span>
          <strong>${formatPrice(total)}</strong>
        </div>

        <div class="checkout-fields">
          <input id="checkout-name" type="text" placeholder="Nome completo" value="${escapeHtml(checkoutDraft.name || "")}">
          <input id="checkout-email" type="email" placeholder="E-mail" value="${escapeHtml(checkoutDraft.email || "")}">
          <input id="checkout-phone" type="tel" placeholder="Telefone" value="${escapeHtml(checkoutDraft.phone || "")}">
          <input id="checkout-address" type="text" placeholder="Endereco de entrega" value="${escapeHtml(checkoutDraft.address || "")}">
        </div>

        <button class="btn-primary btn-block" id="checkout-submit">Finalizar compra</button>
        <a class="btn-outline btn-outline--dark btn-block" href="produtos.html">Continuar comprando</a>
      </aside>
    </div>
  `;
}

function updateCartQuantity(productId, delta) {
  const items = Cart.getItems();
  const item = items.find((entry) => entry.id === productId);
  if (!item) {
    return;
  }
  const checkoutDraft = readCheckoutDraft();

  const stockLimit = Math.min(MAX_CART_QUANTITY, item.stock || Cart.getStockLimit(productId));
  const nextQty = item.qty + delta;
  if (delta > 0 && nextQty > stockLimit) {
    Cart.showToast(`Limite de estoque atingido para ${item.name}.`);
    return;
  }

  item.qty = nextQty;
  if (item.qty <= 0) {
    Cart.removeItem(productId);
  } else {
    Cart.save(items);
  }
  renderCartPage(checkoutDraft);
}

async function handleCheckout() {
  const name = document.getElementById("checkout-name")?.value.trim();
  const email = document.getElementById("checkout-email")?.value.trim();
  const phone = document.getElementById("checkout-phone")?.value.trim();
  const address = document.getElementById("checkout-address")?.value.trim();
  const button = document.getElementById("checkout-submit");
  const items = Cart.getItems();

  if (!items.length) {
    Cart.showToast("Adicione produtos ao carrinho antes de finalizar.");
    renderCartPage();
    return;
  }

  if (!name || !email || !phone || !address) {
    Cart.showToast("Preencha todos os dados de entrega.");
    return;
  }

  const subtotal = items.reduce((sum, item) => sum + item.price * item.qty, 0);
  const shipping = subtotal > 199 ? 0 : 25;
  const total = subtotal + shipping;

  button.disabled = true;
  button.textContent = "Processando...";

  try {
    const orderId = await FirebaseDB.createOrder({
      customer: { name, email, phone, address },
      total,
      items: items.map((item) => ({
        id: item.id,
        product_id: item.id,
        name: item.name,
        product_name: item.name,
        unit_price: item.price,
        quantity: item.qty,
      })),
    });

    Cart.clear();
    renderCartPage();
    Cart.showToast(`Pedido ${orderId} confirmado.`);
  } catch (error) {
    console.error(error);
    Cart.showToast(error.message || "Nao foi possivel concluir o pedido agora.");
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "Finalizar compra";
    }
  }
}

function setupCartPageActions() {
  document.addEventListener("click", (event) => {
    if (PAGE !== "cart") {
      return;
    }

    const actionButton = event.target.closest("[data-cart-action]");
    if (actionButton) {
      const checkoutDraft = readCheckoutDraft();
      const action = actionButton.dataset.cartAction;
      const productId = actionButton.dataset.cartId;
      if (action === "remove") {
        Cart.removeItem(productId);
        renderCartPage(checkoutDraft);
      }
      if (action === "increase") {
        updateCartQuantity(productId, 1);
      }
      if (action === "decrease") {
        updateCartQuantity(productId, -1);
      }
      return;
    }

    if (event.target.id === "checkout-submit") {
      handleCheckout();
    }
  });
}

function initNewsletter() {
  const form = document.getElementById("newsletter-form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.getElementById("newsletter-email");
    const button = document.getElementById("btn-newsletter-submit");
    const email = input?.value.trim() || "";

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      Cart.showToast("Informe um e-mail valido.");
      return;
    }

    button.disabled = true;
    button.textContent = "Enviando...";
    const saved = await FirebaseDB.addNewsletterEmail(email);
    button.disabled = false;
    button.textContent = saved ? "Inscrito" : "Tentar novamente";
    if (saved) {
      input.value = "";
    }
  });
}

async function initPage() {
  renderSiteChrome();
  setupNavbarBehavior();
  Cart.updateBadge();
  Wishlist.updateBadge();
  setupIntersectionObserver();
  setupGlobalInteractions();
  setupCartPageActions();
  initNewsletter();
  await setupSiteSearch();

  if (PAGE === "home") {
    await initHomePage();
  }
  if (PAGE === "products") {
    await initProductsPage();
  }
  if (PAGE === "product") {
    await initProductPage();
  }
  if (PAGE === "favorites") {
    await initFavoritesPage();
  }
  if (PAGE === "cart") {
    renderCartPage();
  }
}

window.FirebaseDB = FirebaseDB;
window.renderProducts = renderProducts;
window.Cart = Cart;
window.Wishlist = Wishlist;

initPage();
