import {
  collection,
  doc,
  getDoc,
  getDocs,
  getFirestore,
  limit,
  query,
  setDoc,
  where,
} from "firebase/firestore";
import { onAuthStateChanged } from "firebase/auth";
import { app, auth } from "./firebase-config.js";

const db = getFirestore(app);
const PAGE = document.body.dataset.page || "";
const CART_KEY = "minhaloja_cart";
const COUPON_KEY = "minhaloja_cart_coupon";
let cartMutationObserver = null;

function observeCartMutations() {
  if (!cartMutationObserver || PAGE !== "cart") {
    return;
  }
  const cartRoot = document.getElementById("cart-content");
  if (!cartRoot) {
    return;
  }
  cartMutationObserver.observe(cartRoot, { childList: true, subtree: true });
}

function runWithCartObserverPaused(task) {
  if (!cartMutationObserver) {
    return task();
  }
  cartMutationObserver.disconnect();
  try {
    return task();
  } finally {
    observeCartMutations();
  }
}

function nowIsoString() {
  return new Date().toISOString();
}

function toNumber(value, fallback = 0) {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : fallback;
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

function parseDateValue(value) {
  if (!value) {
    return 0;
  }
  if (typeof value?.toDate === "function") {
    return value.toDate().getTime();
  }
  if (value instanceof Date) {
    return value.getTime();
  }
  const direct = Date.parse(String(value));
  return Number.isFinite(direct) ? direct : 0;
}

function readCartItems() {
  try {
    const raw = JSON.parse(localStorage.getItem(CART_KEY));
    const items = Array.isArray(raw) ? raw : Array.isArray(raw?.items) ? raw.items : [];
    return items.map((item) => ({
      id: item.id,
      name: item.name || "Produto",
      price: toNumber(item.price),
      qty: Math.max(1, Number.parseInt(item.qty, 10) || 1),
      brand: item.brand || "Maison",
      category: item.category || "Produto",
    }));
  } catch {
    return [];
  }
}

function readCoupon() {
  try {
    const coupon = JSON.parse(localStorage.getItem(COUPON_KEY));
    if (!coupon?.code) {
      return null;
    }
    return {
      code: String(coupon.code).trim().toUpperCase(),
      discount: toNumber(coupon.discount),
      adjustedTotal: toNumber(coupon.adjustedTotal),
      validatedSubtotal: toNumber(coupon.validatedSubtotal),
      stale: Boolean(coupon.stale),
      message: coupon.message || "",
    };
  } catch {
    return null;
  }
}

function writeCoupon(coupon) {
  if (!coupon?.code) {
    localStorage.removeItem(COUPON_KEY);
    return;
  }
  localStorage.setItem(COUPON_KEY, JSON.stringify(coupon));
}

function clearCoupon() {
  localStorage.removeItem(COUPON_KEY);
}

function getPricing(items = readCartItems(), coupon = readCoupon()) {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.qty, 0);
  const shipping = subtotal > 199 ? 0 : 25;
  const couponStillValid =
    coupon &&
    !coupon.stale &&
    Math.abs(toNumber(coupon.validatedSubtotal) - subtotal) < 0.01;
  const discount = couponStillValid ? Math.min(toNumber(coupon.discount), subtotal) : 0;
  return {
    subtotal,
    shipping,
    discount,
    total: Math.max(subtotal - discount + shipping, 0),
    couponStillValid,
  };
}

function syncCouponStaleness() {
  const coupon = readCoupon();
  if (!coupon) {
    return;
  }
  const subtotal = getPricing().subtotal;
  const stale = Math.abs(toNumber(coupon.validatedSubtotal) - subtotal) >= 0.01;
  if (stale !== coupon.stale) {
    writeCoupon({ ...coupon, stale });
  }
}

function showToast(message) {
  if (window.Cart?.showToast) {
    window.Cart.showToast(message);
    return;
  }
  window.alert(message);
}

async function applyCoupon() {
  const input = document.getElementById("coupon-code");
  const button = document.getElementById("coupon-apply");
  const code = input?.value.trim().toUpperCase() || "";
  const items = readCartItems();
  const pricing = getPricing(items, null);

  if (!code) {
    showToast("Informe um cupom.");
    return;
  }

  if (!items.length) {
    showToast("Adicione produtos ao carrinho antes de aplicar um cupom.");
    return;
  }

  button.disabled = true;
  button.textContent = "Validando...";
  try {
    const result = await window.FirebaseDB.validateCoupon(code, items, pricing.subtotal);
    if (!result.valid) {
      throw new Error(result.message || "Cupom invalido.");
    }
    writeCoupon({
      code: result.code,
      discount: result.discount,
      adjustedTotal: result.adjusted_total,
      validatedSubtotal: pricing.subtotal,
      stale: false,
      message: result.message || "",
    });
    renderCartCouponPanel();
    showToast(result.message || "Cupom aplicado com sucesso.");
  } catch (error) {
    showToast(error.message || "Nao foi possivel validar o cupom.");
  } finally {
    button.disabled = false;
    button.textContent = "Aplicar";
  }
}

function renderCartCouponPanel() {
  return runWithCartObserverPaused(() => {
    if (PAGE !== "cart") {
      return;
    }

    syncCouponStaleness();
    const cartRoot = document.getElementById("cart-content");
    const summary = cartRoot?.querySelector(".cart-summary");
    const items = readCartItems();
    if (!summary || !items.length) {
      clearCoupon();
      return;
    }

    const coupon = readCoupon();
    const pricing = getPricing(items, coupon);

    let panel = document.getElementById("coupon-panel");
    if (!panel) {
      panel = document.createElement("div");
      panel.id = "coupon-panel";
      panel.className = "coupon-panel";
      const checkoutFields = summary.querySelector(".checkout-fields");
      if (checkoutFields) {
        summary.insertBefore(panel, checkoutFields);
      } else {
        summary.appendChild(panel);
      }
    }

    const couponMessage = coupon
      ? pricing.couponStillValid
        ? `Cupom ${coupon.code} aplicado.`
        : "O carrinho mudou. Reaplique o cupom."
      : "Use um cupom valido do sistema local.";

    panel.innerHTML = `
      <label class="coupon-panel__label" for="coupon-code">Cupom</label>
      <div class="coupon-panel__row">
        <input
          id="coupon-code"
          class="coupon-panel__input"
          type="text"
          value="${escapeHtml(coupon?.code || "")}"
          placeholder="Ex.: BEMVINDO10"
        >
        <button type="button" class="btn-outline btn-outline--dark" id="coupon-apply">Aplicar</button>
        <button type="button" class="btn-outline btn-outline--dark" id="coupon-remove" ${coupon ? "" : "disabled"}>Remover</button>
      </div>
      <p class="coupon-panel__message ${pricing.couponStillValid ? "is-success" : coupon ? "is-warning" : ""}">
        ${couponMessage}
      </p>
    `;

    const rows = [...summary.querySelectorAll(".cart-summary__row")];
    if (rows[0]) {
      rows[0].querySelector("strong").textContent = formatPrice(pricing.subtotal);
    }
    if (rows[1]) {
      rows[1].querySelector("strong").textContent =
        pricing.shipping === 0 ? "Gratis" : formatPrice(pricing.shipping);
    }

    let discountRow = document.getElementById("cart-discount-row");
    if (!discountRow) {
      discountRow = document.createElement("div");
      discountRow.id = "cart-discount-row";
      discountRow.className = "cart-summary__row cart-summary__row--discount";
      rows[1]?.insertAdjacentElement("afterend", discountRow);
    }
    discountRow.innerHTML = `
      <span>Desconto</span>
      <strong>${pricing.discount > 0 ? `- ${formatPrice(pricing.discount)}` : "R$ 0,00"}</strong>
    `;

    const totalRow = summary.querySelector(".cart-summary__row--total strong");
    if (totalRow) {
      totalRow.textContent = formatPrice(pricing.total);
    }
  });
}

async function handleEnhancedCheckout() {
  const name = document.getElementById("checkout-name")?.value.trim();
  const email = document.getElementById("checkout-email")?.value.trim();
  const phone = document.getElementById("checkout-phone")?.value.trim();
  const address = document.getElementById("checkout-address")?.value.trim();
  const button = document.getElementById("checkout-submit");
  const items = readCartItems();
  const coupon = readCoupon();
  const pricing = getPricing(items, coupon);

  if (!items.length) {
    showToast("Adicione produtos ao carrinho antes de finalizar.");
    return;
  }

  if (!name || !email || !phone || !address) {
    showToast("Preencha todos os dados de entrega.");
    return;
  }

  if (coupon && !pricing.couponStillValid) {
    showToast("Reaplique o cupom antes de finalizar.");
    return;
  }

  button.disabled = true;
  button.textContent = "Processando...";

  try {
    const orderId = await window.FirebaseDB.createOrder({
      customer: { name, email, phone, address },
      subtotal: pricing.subtotal,
      shipping: pricing.shipping,
      discount_total: pricing.discount,
      coupon_code: pricing.couponStillValid ? coupon?.code || null : null,
      total: pricing.total,
      items: items.map((item) => ({
        id: item.id,
        product_id: item.id,
        name: item.name,
        product_name: item.name,
        unit_price: item.price,
        quantity: item.qty,
      })),
      userId: window.AuthManager?.user?.uid || null,
    });

    window.Cart?.clear?.();
    clearCoupon();
    if (window.AuthManager?.user?.uid) {
      await setDoc(doc(db, "carts", window.AuthManager.user.uid), {
        ownerId: window.AuthManager.user.uid,
        schemaVersion: 2,
        updatedAt: nowIsoString(),
        items: [],
      }, { merge: true });
    }

    const cartRoot = document.getElementById("cart-content");
    if (cartRoot) {
      cartRoot.innerHTML = `
        <div class="empty-state">
          <h2>Pedido confirmado</h2>
          <p>Pedido ${orderId} registrado com sucesso.</p>
          <a class="btn-primary" href="produtos.html">Explorar produtos</a>
        </div>
      `;
    }
    showToast(`Pedido ${orderId} confirmado.`);
  } catch (error) {
    console.error(error);
    showToast(error.message || "Nao foi possivel concluir o pedido agora.");
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "Finalizar compra";
    }
  }
}

function setupCartEnhancements() {
  if (PAGE !== "cart") {
    return;
  }

  const cartRoot = document.getElementById("cart-content");
  if (!cartRoot) {
    return;
  }

  cartMutationObserver = new MutationObserver(() => {
    renderCartCouponPanel();
  });
  observeCartMutations();
  renderCartCouponPanel();

  document.addEventListener("click", (event) => {
    if (event.target.id === "coupon-apply") {
      event.preventDefault();
      applyCoupon();
      return;
    }

    if (event.target.id === "coupon-remove") {
      event.preventDefault();
      clearCoupon();
      renderCartCouponPanel();
      showToast("Cupom removido.");
    }
  });

  document.addEventListener("click", (event) => {
    if (event.target.id !== "checkout-submit") {
      return;
    }
    event.preventDefault();
    event.stopImmediatePropagation();
    handleEnhancedCheckout();
  }, true);
}

async function loadReviews(productId) {
  const snapshot = await getDocs(
    query(collection(db, "reviews"), where("product_id", "==", productId), limit(50)),
  );
  const entries = snapshot.docs
    .map((entry) => ({ id: entry.id, ...entry.data() }))
    .sort((left, right) => {
      const leftValue = parseDateValue(left.updated_at || left.created_at);
      const rightValue = parseDateValue(right.updated_at || right.created_at);
      return rightValue - leftValue;
    });

  const count = entries.length;
  const average = count
    ? entries.reduce((sum, entry) => sum + toNumber(entry.score, 0), 0) / count
    : 0;
  return { entries, count, average };
}

function reviewFormValues() {
  return {
    score: document.getElementById("review-score")?.value || "5",
    title: document.getElementById("review-title")?.value || "",
    comment: document.getElementById("review-comment")?.value || "",
  };
}

async function saveReview(productId) {
  const values = reviewFormValues();
  const user = auth.currentUser;
  if (!user) {
    throw new Error("Entre na sua conta para avaliar.");
  }
  if (!values.comment.trim()) {
    throw new Error("Escreva um comentario para publicar a avaliacao.");
  }

  const reviewRef = doc(db, "reviews", `${user.uid}__${productId}`);
  const existing = await getDoc(reviewRef);
  const payload = {
    product_id: productId,
    user_id: user.uid,
    user_name: user.displayName || user.email || "Cliente",
    score: Math.max(1, Math.min(5, Number.parseInt(values.score, 10) || 5)),
    title: values.title.trim(),
    comment: values.comment.trim(),
    updated_at: nowIsoString(),
    created_at: existing.exists() ? existing.data().created_at || nowIsoString() : nowIsoString(),
  };

  await setDoc(reviewRef, payload, { merge: true });
  const reviewState = await loadReviews(productId);
  await setDoc(doc(db, "produtos", productId), {
    rating: reviewState.count ? Number(reviewState.average.toFixed(1)) : 0,
    reviews: reviewState.count,
    updatedAt: nowIsoString(),
  }, { merge: true });

  if (Array.isArray(window.CURRENT_PRODUCTS)) {
    const product = window.CURRENT_PRODUCTS.find((entry) => entry.id === productId);
    if (product) {
      product.rating = reviewState.count ? Number(reviewState.average.toFixed(1)) : 0;
      product.reviews = reviewState.count;
    }
  }
}

function reviewStars(score) {
  const count = Math.max(1, Math.min(5, Number.parseInt(score, 10) || 5));
  return "★".repeat(count) + "☆".repeat(5 - count);
}

async function renderReviews(productId) {
  if (PAGE !== "product") {
    return;
  }
  const detailRoot = document.getElementById("product-detail");
  if (!detailRoot) {
    return;
  }

  const reviewState = await loadReviews(productId);
  const user = auth.currentUser;
  const currentUserReview = user
    ? reviewState.entries.find((entry) => entry.user_id === user.uid) || null
    : null;

  let section = document.getElementById("product-reviews");
  if (!section) {
    section = document.createElement("section");
    section.id = "product-reviews";
    section.className = "detail-section detail-section--reviews";
    detailRoot.appendChild(section);
  }

  section.innerHTML = `
    <div class="detail-section__header">
      <h2>Avaliacoes</h2>
      <p>${reviewState.count ? `${reviewState.average.toFixed(1)} de 5 em ${reviewState.count} avaliacao${reviewState.count === 1 ? "" : "oes"}` : "Seja a primeira pessoa a avaliar este produto."}</p>
    </div>

    <div class="reviews-live">
      <div class="reviews-live__list">
        ${reviewState.entries.length ? reviewState.entries.slice(0, 6).map((entry) => `
          <article class="review-live-card">
            <div class="review-live-card__top">
              <strong>${escapeHtml(entry.user_name || "Cliente")}</strong>
              <span>${reviewStars(entry.score)}</span>
            </div>
            ${entry.title ? `<h3>${escapeHtml(entry.title)}</h3>` : ""}
            <p>${escapeHtml(entry.comment || "")}</p>
          </article>
        `).join("") : `
          <div class="empty-state empty-state--inline">
            <h3>Nenhuma avaliacao ainda</h3>
            <p>Assim que alguem publicar uma opiniao, ela aparece aqui.</p>
          </div>
        `}
      </div>

      <div class="review-form-card">
        ${user ? `
          <h3>${currentUserReview ? "Atualize sua avaliacao" : "Avalie este produto"}</h3>
          <div class="review-form">
            <label>
              <span>Nota</span>
              <select id="review-score">
                ${[5, 4, 3, 2, 1].map((score) => `
                  <option value="${score}" ${Number(currentUserReview?.score || 5) === score ? "selected" : ""}>${score}</option>
                `).join("")}
              </select>
            </label>
            <label>
              <span>Titulo</span>
              <input id="review-title" type="text" placeholder="Resumo curto" value="${escapeHtml(currentUserReview?.title || "")}">
            </label>
            <label>
              <span>Comentario</span>
              <textarea id="review-comment" rows="5" placeholder="Conte como foi a experiencia">${escapeHtml(currentUserReview?.comment || "")}</textarea>
            </label>
            <button type="button" class="btn-primary" id="review-submit">Publicar avaliacao</button>
          </div>
        ` : `
          <div class="review-form-card__locked">
            <h3>Entre para avaliar</h3>
            <p>As avaliacoes ficam disponiveis para leitura publica, mas a publicacao exige conta autenticada.</p>
            <a class="btn-primary" href="auth.html">Entrar</a>
          </div>
        `}
      </div>
    </div>
  `;

  const ratingRow = detailRoot.querySelector(".detail-rating-row span:last-child");
  if (ratingRow) {
    ratingRow.textContent = reviewState.count
      ? `${reviewState.average.toFixed(1)} · ${reviewState.count} avaliacoes`
      : "Sem avaliacoes ainda";
  }
}

function setupProductReviews() {
  if (PAGE !== "product") {
    return;
  }

  const productId = new URLSearchParams(window.location.search).get("id");
  if (!productId) {
    return;
  }

  const boot = () => renderReviews(productId).catch(console.error);
  const productObserver = new MutationObserver(() => {
    if (document.querySelector(".detail-title")) {
      boot();
    }
  });
  const detailRoot = document.getElementById("product-detail");
  if (detailRoot) {
    productObserver.observe(detailRoot, { childList: true, subtree: true });
  }
  boot();

  document.addEventListener("click", async (event) => {
    if (event.target.id !== "review-submit") {
      return;
    }
    event.preventDefault();
    const button = event.target;
    button.disabled = true;
    button.textContent = "Publicando...";
    try {
      await saveReview(productId);
      await renderReviews(productId);
      showToast("Avaliacao publicada.");
    } catch (error) {
      console.error(error);
      showToast(error.message || "Nao foi possivel salvar a avaliacao.");
    } finally {
      button.disabled = false;
      button.textContent = "Publicar avaliacao";
    }
  });

  onAuthStateChanged(auth, () => {
    renderReviews(productId).catch(console.error);
  });
}

setupCartEnhancements();
setupProductReviews();
