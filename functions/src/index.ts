import { initializeApp } from "firebase-admin/app";
import { DocumentSnapshot, FieldValue, getFirestore, Transaction } from "firebase-admin/firestore";
import { HttpsError, onRequest } from "firebase-functions/v2/https";
import corsLib from "cors";

const cors = corsLib({ origin: true });

import {
  buildOrderDocument,
  computeOrderTotals,
  normalizeCouponRecord,
  normalizeOrderItems,
  normalizeProductRecord,
  validateClientTotals,
  validateCouponRecord,
} from "./commerce";

initializeApp();

const db = getFirestore();
const region = "southamerica-east1";



function asObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function requireCouponCode(value: unknown): string {
  const code = String(value || "").trim().toUpperCase();
  if (!code) {
    throw new HttpsError("invalid-argument", "Informe um cupom.", {
      reason: "invalid-coupon",
    });
  }
  return code;
}

async function loadCouponByCode(code: string, tx?: Transaction) {
  const ref = db.collection("cupons").doc(code);
  const snapshot = tx ? await tx.get(ref) : await ref.get();
  if (!snapshot.exists) {
    return null;
  }
  return normalizeCouponRecord(snapshot.id, snapshot.data() || {});
}

export const health = onRequest({ region }, (request, response) => {
  cors(request as any, response as any, () => {
    response.json({
      ok: true,
      service: "grand-parfum-functions",
      timestamp: new Date().toISOString(),
    });
  });
});

export const validateCoupon = onRequest({ region }, (request, response) => {
  cors(request as any, response as any, async () => {
    try {
      const payload = asObject(request.body?.data ?? request.body);
      const code = requireCouponCode(payload.code);
      const items = normalizeOrderItems(payload.items);
      const subtotalFromItems = items.reduce(
        (sum, item) => sum + item.quantity * item.unit_price,
        0,
      );
      const subtotal = Math.max(
        Number(payload.subtotal ?? subtotalFromItems) || subtotalFromItems,
        0,
      );

      const coupon = await loadCouponByCode(code);
      const result = validateCouponRecord(coupon, subtotal);
      if (!result.valid) {
        response.json({ data: result });
        return;
      }

      response.json({
        data: {
          ...result,
          ok: true,
          subtotal,
          items,
        }
      });
    } catch (error: any) {
      console.error("Error in validateCoupon:", error);
      response.status(error.code === "invalid-argument" ? 400 : 500).json({
        error: {
          message: error.message,
          status: error.code || "internal",
        }
      });
    }
  });
});

export const createOrder = onRequest({ region }, (request, response) => {
  cors(request as any, response as any, async () => {
    try {
      const payload = asObject(request.body?.data ?? request.body);
      const customer = asObject(payload.customer);
      const customerId = String(
        payload.customer_id ?? payload.customerId ?? payload.userId ?? customer.id ?? "",
      ).trim() || null;
      const items = normalizeOrderItems(payload.items);
      const couponCode = String(payload.coupon_code ?? payload.couponCode ?? "").trim().toUpperCase() || null;

      if (!items.length || !items.some((item) => item.product_id && item.quantity > 0)) {
        throw new HttpsError("invalid-argument", "Pedido sem itens válidos.", {
          reason: "invalid-order",
        });
      }

      const result = await db.runTransaction(async (tx: Transaction) => {
        const uniqueProductIds = [...new Set(items.map((item) => item.product_id))];
        const productSnapshots = await Promise.all(
          uniqueProductIds.map((productId) => tx.get(db.collection("produtos").doc(productId))),
        );

        const productsById = new Map<string, ReturnType<typeof normalizeProductRecord>>();
        const missingProducts: string[] = [];

        productSnapshots.forEach((snapshot: DocumentSnapshot) => {
          if (!snapshot.exists) {
            missingProducts.push(snapshot.id);
            return;
          }
          productsById.set(snapshot.id, normalizeProductRecord(snapshot.id, snapshot.data() || {}));
        });

        if (missingProducts.length) {
          throw new HttpsError("not-found", `Produtos não encontrados: ${missingProducts.join(", ")}.`, {
            reason: "invalid-order",
          });
        }

        const insufficientStock: string[] = [];
        for (const item of items) {
          const product = productsById.get(item.product_id);
          if (!product || product.stock < item.quantity) {
            insufficientStock.push(product?.name || item.product_name || item.product_id);
          }
        }

        if (insufficientStock.length) {
          throw new HttpsError(
            "failed-precondition",
            `Estoque insuficiente para: ${insufficientStock.join(", ")}.`,
            { reason: "insufficient-stock" },
          );
        }

        const coupon = couponCode ? await loadCouponByCode(couponCode, tx) : null;
        const totals = computeOrderTotals(items, productsById, coupon);

        if (couponCode && (!totals.couponResult || !totals.couponResult.valid)) {
          throw new HttpsError(
            "failed-precondition",
            totals.couponResult?.message || "Cupom inválido.",
            { reason: "invalid-coupon" },
          );
        }

        if (
          !validateClientTotals(
            {
              subtotal: payload.subtotal,
              shipping: payload.shipping,
              discount_total: payload.discount_total ?? payload.discountTotal,
              total: payload.total,
            },
            totals,
          )
        ) {
          throw new HttpsError(
            "invalid-argument",
            "Total do pedido diverge do cálculo do servidor.",
            { reason: "tampered-total" },
          );
        }

        const orderRef = db.collection("pedidos").doc(`ord-${Date.now()}`);
        const orderDocument = buildOrderDocument({
          orderId: orderRef.id,
          customer,
          customerId,
          items: totals.normalizedItems,
          subtotal: totals.subtotal,
          shipping: totals.shipping,
          discount_total: totals.discount_total,
          coupon_code: couponCode,
          total: totals.total,
        });

        for (const item of totals.normalizedItems) {
          const productRef = db.collection("produtos").doc(item.product_id);
          const product = productsById.get(item.product_id)!;
          tx.update(productRef, {
            stock: product.stock - item.quantity,
            updated_at: orderDocument.updated_at,
          });
        }

        if (couponCode && coupon) {
          tx.set(
            db.collection("cupons").doc(couponCode),
            {
              used_count: FieldValue.increment(1),
              updated_at: orderDocument.updated_at,
            },
            { merge: true },
          );
        }

        tx.set(orderRef, orderDocument);

        return {
          ok: true,
          order_id: orderRef.id,
        };
      });

      response.json({ data: result });
    } catch (error: any) {
      console.error("Error in createOrder:", error);
      response.status(error.code === "not-found" ? 404 : (error.code === "invalid-argument" ? 400 : 500)).json({
        error: {
          message: error.message,
          status: error.code || "internal",
          details: error.details,
        }
      });
    }
  });
});
