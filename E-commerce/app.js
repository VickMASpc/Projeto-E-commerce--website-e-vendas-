/**
 * app.js — Lógica principal do E-commerce (Grand Parfum)
 * 
 * Módulos:
 *  1. Navbar (scroll + hamburger)
 *  2. Carrinho (localStorage)
 *  3. Renderização Dinâmica (Produtos)
 *  4. Animações de scroll (IntersectionObserver)
 *  5. Newsletter
 *  6. Firebase (Integração Real)
 * 
 * NOTA: Este arquivo agora é um MÓDULO (ES Module). 
 * Variáveis globais de outros scripts (como PRODUCTS_LIVE) continuam acessíveis.
 */

import { initializeApp } from 'firebase/app';
import { getFirestore, collection, getDocs, addDoc, query, limit, doc, setDoc } from 'firebase/firestore';
import firebaseConfig from './firebase-config.js';

// Inicializa Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

const FirebaseDB = {
  /** Busca produtos do Firestore */
  async getProducts(count = 8) {
    try {
      const q = query(collection(db, 'produtos'), limit(count));
      const snap = await getDocs(q);
      return snap.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    } catch (err) {
      console.error("Erro ao buscar produtos do Firebase:", err);
      return [];
    }
  },

  /** Adiciona e-mail na newsletter */
  async addNewsletterEmail(email) {
    try {
      await addDoc(collection(db, 'newsletter'), {
        email,
        createdAt: new Date()
      });
      return true;
    } catch (err) {
      console.error("Erro ao salvar newsletter:", err);
      return false;
    }
  },

  /** Registra pedido no Firestore */
  async createOrder(orderData) {
    try {
      // Gerando ID no padrão ord-xxx (3 números exatos)
      const randomThreeDigits = Math.floor(Math.random() * 900 + 100);
      const orderId = `ord-${randomThreeDigits}`;
      
      const pedidoTraduzido = {
        clienteNome: orderData.customer?.name || "Cliente",
        clienteEmail: orderData.customer?.email || "",
        clienteTelefone: orderData.customer?.phone || "",
        clienteEndereco: orderData.customer?.address || "",
        itens: (orderData.items || orderData.itens || []).map(it => ({
          produtoNome: it.name || it.nome || it.nome_prod || "Produto",
          preco: it.price || it.preco || it.preco_unit || 0,
          quantidade: it.quantity || it.quantidade || 1
        })),
        total: orderData.total,
        status: 'pendente',
        dataCriacao: new Date().toISOString()
      };

      await setDoc(doc(db, 'pedidos', orderId), pedidoTraduzido);
      return orderId;
    } catch (err) {
      console.error("Erro ao criar pedido no Firebase:", err);
      throw err;
    }
  },

  /** Inicializa produtos na página */
  async initProducts(containerId, maxCount = null) {
    const container = document.getElementById(containerId);
    if (!container) return;

    let products = [];
    try {
      // Tenta buscar do Firebase primeiro
      products = await this.getProducts(maxCount || 50);
    } catch (e) {
      console.error("Falha ao buscar produtos do Firebase, usando fallback local:", e);
    }

    // Fallback para mock local
    if (!products || products.length === 0) {
      const hasLive = (typeof PRODUCTS_LIVE !== 'undefined' && PRODUCTS_LIVE.length > 0);
      const staticData = (typeof PRODUCTS !== 'undefined') ? PRODUCTS : [];
      products = hasLive ? PRODUCTS_LIVE : staticData;
      if (maxCount) {
          products = products.slice(0, maxCount);
      }
    }

    // Armazena no window para a função de filtragem poder acessar
    window.CURRENT_PRODUCTS = products;
    
    if (typeof window.renderProducts === 'function') {
      window.renderProducts(containerId, products);
    }
  }
};

/* ============================================================
   1. NAVBAR — scroll effect + hamburger
   ============================================================ */
const navbar = document.getElementById('navbar');
const btnHamburger = document.getElementById('btn-hamburger');
const mobileMenu = document.getElementById('mobile-menu');
let menuOpen = false;

// Efeito de blur ao scrollar
window.addEventListener('scroll', () => {
  if (window.scrollY > 20) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
}, { passive: true });

// Hamburger toggle
if (btnHamburger) {
  btnHamburger.addEventListener('click', () => {
    menuOpen = !menuOpen;
    mobileMenu.style.display = menuOpen ? 'flex' : 'none';
    btnHamburger.setAttribute('aria-expanded', menuOpen);
    mobileMenu.setAttribute('aria-hidden', !menuOpen);
    document.body.style.overflow = menuOpen ? 'hidden' : '';
  });
}

// Fecha menu mobile ao clicar em link
if (mobileMenu) {
  mobileMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      menuOpen = false;
      mobileMenu.style.display = 'none';
      mobileMenu.setAttribute('aria-hidden', 'true');
      btnHamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });
}


/* ============================================================
   2. CARRINHO — persistência em localStorage
   ============================================================ */
const CART_KEY = 'minhaloja_cart';

const Cart = {
  /** Retorna os itens do carrinho */
  getItems() {
    try {
      return JSON.parse(localStorage.getItem(CART_KEY)) || [];
    } catch {
      return [];
    }
  },

  /** Salva itens no localStorage */
  save(items) {
    localStorage.setItem(CART_KEY, JSON.stringify(items));
    this.updateBadge();
  },

  /** Adiciona ou incrementa um produto */
  addItem(productId, name, price, imageEmoji = '📦') {
    const items = this.getItems();
    const existing = items.find(i => i.id === productId);
    if (existing) {
      existing.qty += 1;
    } else {
      items.push({ id: productId, name, price, imageEmoji, qty: 1 });
    }
    this.save(items);
    this.showToast(`${name} adicionado ao carrinho! 🛒`);
  },

  /** Remove um item pelo id */
  removeItem(productId) {
    const items = this.getItems().filter(i => i.id !== productId);
    this.save(items);
  },

  /** Atualiza o badge numérico do ícone de carrinho */
  updateBadge() {
    const badge = document.getElementById('cart-count');
    if (!badge) return;
    const total = this.getItems().reduce((sum, i) => sum + i.qty, 0);
    badge.textContent = total;
    badge.style.display = total > 0 ? 'flex' : 'none';

    const btnCart = document.getElementById('btn-cart');
    if (btnCart) {
      btnCart.setAttribute('aria-label', `Carrinho de compras (${total} ${total === 1 ? 'item' : 'itens'})`);
    }
  },

  /** Limpa o carrinho */
  clear() {
    localStorage.removeItem(CART_KEY);
    this.updateBadge();
  },

  /** Mostra notificação temporária */
  showToast(message) {
    // Remove toast anterior se existir
    const old = document.getElementById('cart-toast');
    if (old) old.remove();

    const toast = document.createElement('div');
    toast.id = 'cart-toast';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.style.cssText = `
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      z-index: 9999;
      background: #fff;
      color: var(--clr-neutral-800, #27272a);
      padding: 1rem 1.5rem;
      border-radius: 0.75rem;
      box-shadow: 0 10px 30px rgba(0,0,0,0.2);
      font-family: Inter, sans-serif;
      font-size: 0.9rem;
      font-weight: 600;
      border-left: 4px solid #8533ff;
      max-width: 320px;
      animation: slideInRight 0.3s ease forwards;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    `;
    toast.innerHTML = `
      <svg width="18" height="18" fill="none" stroke="#22c55e" stroke-width="2.5" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M20 6 9 17l-5-5"/>
      </svg>
      ${message}
    `;

    // Adiciona keyframe de animação dinamicamente se necesário
    if (!document.getElementById('toast-styles')) {
      const style = document.createElement('style');
      style.id = 'toast-styles';
      style.textContent = `
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(100%); }
          to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes slideOutRight {
          from { opacity: 1; transform: translateX(0); }
          to   { opacity: 0; transform: translateX(100%); }
        }
      `;
      document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    // Auto-remove após 3s
    setTimeout(() => {
      toast.style.animation = 'slideOutRight 0.3s ease forwards';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
};

// Wishlist — Persistência em localStorage
const WISHLIST_KEY = 'minhaloja_wishlist';

const Wishlist = {
  getItems() {
    try { return JSON.parse(localStorage.getItem(WISHLIST_KEY)) || []; }
    catch { return []; }
  },
  save(items) { localStorage.setItem(WISHLIST_KEY, JSON.stringify(items)); },
  toggleItem(productId) {
    let items = this.getItems();
    if (items.includes(productId)) {
      items = items.filter(id => id !== productId);
    } else {
      items.push(productId);
    }
    this.save(items);
    return items.includes(productId);
  },
  hasItem(productId) {
    return this.getItems().includes(productId);
  }
};

window.Wishlist = Wishlist; // Exporta para uso global

// Wishlist (Usa delegação de evento para produtos dinâmicos)
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.product-card__wishlist');
  if (btn) {
    e.stopPropagation();
    const card = btn.closest('.product-card');
    if (!card) return;
    const productId = card.id;
    
    const isActive = Wishlist.toggleItem(productId);
    
    if (isActive) {
      btn.classList.add('wishlist-active');
      btn.style.color = '#ef4444';
      btn.querySelector('svg path')?.setAttribute('fill', '#ef4444');
      Cart.showToast('Adicionado aos favoritos ❤️');
    } else {
      btn.classList.remove('wishlist-active');
      btn.style.color = '';
      btn.querySelector('svg path')?.removeAttribute('fill');
    }
  }
});

/* ============================================================
   3. RENDERIZAÇÃO DINÂMICA — Produtos
   ============================================================ */

/**
 * Renderiza um card de produto
 * @param {Object} product Objeto de produto do products.js
 */
function createProductCard(product) {
  const { id, rating, reviews } = product;
  
  // Normalização de chaves (Suporte Português e Inglês)
  const name = product.nome || product.name || 'Produto';
  const price = parseFloat(product.preco || product.price || 0);
  const oldPrice = parseFloat(product.precoAntigo || product.oldPrice || 0);
  const category = product.categoria || product.category || 'Perfume';
  const imageEmoji = product.imageEmoji || '✨';
  const isSale = product.emOferta || product.isSale || false;
  const isNew = product.eNovo || product.isNew || false;
  
  const safeEmoji = imageEmoji || '📦';
  const safeRating = rating || 5.0;
  const safeReviews = reviews || 0;

  
  const badgeHTML = isSale 
    ? `<span class="product-card__badge product-card__badge--sale">-20%</span>`
    : isNew 
      ? `<span class="product-card__badge product-card__badge--new">Novo</span>`
      : '';

  const priceOldHTML = oldPrice 
    ? `<div class="product-card__price-old">R$ ${oldPrice.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</div>` 
    : '';

  const discountHTML = oldPrice 
    ? `<div class="product-card__discount">Economia R$ ${(oldPrice - price).toFixed(2)}</div>` 
    : `<div class="product-card__discount" style="color:var(--clr-primary-600)">12x sem juros</div>`;

  const inWishlist = typeof Wishlist !== 'undefined' ? Wishlist.hasItem(id) : false;
  const wishColor = inWishlist ? 'color: #ef4444;' : '';
  const wishFill = inWishlist ? 'fill="#ef4444"' : '';
  const wishClass = inWishlist ? 'wishlist-active' : '';

  return `
    <article class="product-card animate-on-scroll" id="${id}" aria-label="Produto: ${name}">
      <div class="product-card__image">
        <div style="width:100%;height:100%;background:linear-gradient(135deg,var(--clr-primary-100),var(--clr-primary-50));display:flex;align-items:center;justify-content:center;font-size:4rem;">${safeEmoji}</div>
        ${badgeHTML}
        <button class="product-card__wishlist ${wishClass}" style="${wishColor}" aria-label="Adicionar aos favoritos">
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path ${wishFill} d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
        </button>
        <button class="product-card__add-cart" data-product-id="${id}" aria-label="Adicionar ${name} ao carrinho">+ Adicionar ao Carrinho</button>
      </div>
      <div class="product-card__body">
        <div class="product-card__category">${category}</div>
        <h3 class="product-card__name">${name}</h3>
        <div class="product-card__rating">
          <div class="product-card__stars" aria-label="${rating} estrelas">★★★★★</div>
          <span class="product-card__rating-count">(${reviews})</span>
        </div>
        <div class="product-card__footer">
          <div>
            <div class="product-card__price-current">R$ ${price.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</div>
            ${priceOldHTML}
          </div>
          ${discountHTML}
        </div>
      </div>
    </article>
  `;
}

/**
 * Popula um container com produtos
 * @param {string} containerId ID do elemento Pai
 * @param {Array} productList Lista de produtos (opcional)
 */
function renderProducts(containerId, productList = null) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // Hierarquia de dados: 
  // 2. window.CURRENT_PRODUCTS (set by initProducts)
  // 3. PRODUCTS_LIVE (dados do sistema Python)
  // 4. PRODUCTS (fallback estático se o sistema estiver offline/vazio)
  
  const hasLive = (typeof PRODUCTS_LIVE !== 'undefined' && PRODUCTS_LIVE.length > 0);
  const liveData = hasLive ? PRODUCTS_LIVE : [];
  const staticData = (typeof PRODUCTS !== 'undefined') ? PRODUCTS : [];
  
  const data = productList || (window.CURRENT_PRODUCTS && window.CURRENT_PRODUCTS.length > 0 ? window.CURRENT_PRODUCTS : (hasLive ? liveData : staticData));
  
  if (data.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--clr-neutral-400);">
        <p class="section__subtitle">Nenhum produto cadastrado no momento.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = data.map(p => createProductCard(p)).join('');
  
  // Reinicializa o observer para os novos elementos
  if (typeof observer !== 'undefined') {
    container.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
  }
}

// Delegação de evento para "Adicionar ao Carrinho"
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.product-card__add-cart');
  if (btn) {
    e.stopPropagation();
    const productId = btn.dataset.productId;
    const allProducts = [...((typeof PRODUCTS_LIVE !== 'undefined') ? PRODUCTS_LIVE : []), ...((typeof PRODUCTS !== 'undefined') ? PRODUCTS : [])];
    const product = allProducts.find(p => p.id === productId);
    
    if (product) {
      // Normalização de chaves (suporta Inglês e Português vindos do Python/JSON)
      const pId = product.id;
      const pName = product.name || product.nome || 'Produto';
      const pPrice = parseFloat(product.price || product.preco || 0);
      const pEmoji = product.imageEmoji || '📦';
      
      Cart.addItem(pId, pName, pPrice, pEmoji);
    } else {
      // Fallback para elementos estáticos se existirem
      const card = btn.closest('.product-card');
      const name = card.querySelector('.product-card__name')?.textContent || 'Produto';
      const priceText = card.querySelector('.product-card__price-current')?.textContent || 'R$ 0';
      const price = parseFloat(priceText.replace('R$', '').replace('.', '').replace(',', '.').trim()) || 0;
      Cart.addItem(productId, name, price);
    }
  }
});

/* ============================================================
   4. ANIMAÇÕES DE SCROLL — IntersectionObserver
   ============================================================ */
const animatedEls = document.querySelectorAll('.animate-on-scroll');

const observerOptions = {
  root: null,
  rootMargin: '0px 0px -60px 0px',
  threshold: 0.1
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      // Escalonamento de delay para grupos de cards
      const siblings = Array.from(entry.target.parentElement.querySelectorAll('.animate-on-scroll'));
      const index = siblings.indexOf(entry.target);
      const delay = Math.min(index * 80, 400); // max 400ms

      setTimeout(() => {
        entry.target.classList.add('is-visible');
      }, delay);

      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

animatedEls.forEach(el => observer.observe(el));


/* ============================================================
   4. NEWSLETTER — validação e feedback
   ============================================================ */
const newsletterForm = document.getElementById('newsletter-form');

if (newsletterForm) {
  newsletterForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const emailInput = document.getElementById('newsletter-email');
    const submitBtn = document.getElementById('btn-newsletter-submit');
    const email = emailInput?.value?.trim();

    if (!email || !isValidEmail(email)) {
      emailInput.style.outline = '2px solid #ef4444';
      emailInput.placeholder = 'E-mail inválido, tente novamente';
      setTimeout(() => {
        emailInput.style.outline = '';
        emailInput.placeholder = 'seu@email.com';
      }, 2500);
      return;
    }

    // Feedback visual
    submitBtn.textContent = 'Aguarde...';
    submitBtn.disabled = true;

    // Integração Real com Firebase
    const success = await FirebaseDB.addNewsletterEmail(email);

    if (success) {
        submitBtn.textContent = '✓ Inscrito!';
        submitBtn.style.background = '#22c55e';
        submitBtn.style.color = '#fff';
        emailInput.value = '';
    } else {
        submitBtn.textContent = 'Erro ao salvar';
        submitBtn.style.background = '#ef4444';
    }

    setTimeout(() => {
      submitBtn.textContent = 'Quero Ofertas';
      submitBtn.style.background = '';
      submitBtn.style.color = '';
      submitBtn.disabled = false;
    }, 4000);
  });
}

/** Valida formato de e-mail */
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/** Simula delay de rede */
function fakeDelay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


// Exporta funções úteis para uso global se necessário (para compatibilidade com scripts inline)
window.renderProducts = renderProducts;
window.FirebaseDB = FirebaseDB;
window.Cart = Cart;


/* ============================================================
   6. BUSCA (stub para expansão futura)
   ============================================================ */
const btnSearch = document.getElementById('btn-search');

if (btnSearch) {
  btnSearch.addEventListener('click', () => {
    // TODO: abrir modal ou redirecionar para /produtos.html?q=
    console.log('Busca clicada — implementar modal');
  });
}


/* ============================================================
   7. LOG DE INICIALIZAÇÃO (desenvolvimento)
   ============================================================ */
console.log('%cMinhaLoja Dev Mode 🚀', 'color: #8533ff; font-size: 1rem; font-weight: bold;');
console.log('Carrinho:', Cart.getItems());
