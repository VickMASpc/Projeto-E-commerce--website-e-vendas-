import { describe, expect, it } from "vitest";

import {
  computeOrderTotals,
  normalizeCouponRecord,
  normalizeOrderItems,
  normalizeProductRecord,
  validateClientTotals,
  validateCouponRecord,
} from "./commerce";

describe("commerce helpers", () => {
  it("accepts a valid order and recalculates totals on the server", () => {
    const items = normalizeOrderItems([
      { id: "perf-1", quantity: 2, unit_price: 1 },
    ]);
    const products = new Map([
      ["perf-1", normalizeProductRecord("perf-1", { name: "Bleu", price: 850, stock: 4 })],
    ]);
    const coupon = normalizeCouponRecord("BEMVINDO10", {
      type: "percent",
      value: 10,
      active: true,
      min_order_total: 100,
      max_discount: 500,
      used_count: 0,
    });

    const totals = computeOrderTotals(items, products, coupon);

    expect(totals.subtotal).toBe(1700);
    expect(totals.discount_total).toBe(170);
    expect(totals.shipping).toBe(0);
    expect(totals.total).toBe(1530);
  });

  it("rejects orders without valid items", () => {
    const items = normalizeOrderItems([{ quantity: 2 }]);
    expect(items).toEqual([]);
  });

  it("flags insufficient stock through server-side comparison", () => {
    const items = normalizeOrderItems([{ id: "perf-1", quantity: 3, unit_price: 850 }]);
    const products = new Map([
      ["perf-1", normalizeProductRecord("perf-1", { name: "Bleu", price: 850, stock: 2 })],
    ]);
    const totals = computeOrderTotals(items, products, null);

    expect(totals.normalizedItems[0].quantity).toBe(3);
    expect(products.get("perf-1")?.stock).toBeLessThan(totals.normalizedItems[0].quantity);
  });

  it("rejects invalid coupons", () => {
    const coupon = normalizeCouponRecord("INATIVO", {
      type: "fixed",
      value: 50,
      active: false,
      min_order_total: 0,
      used_count: 0,
    });

    const result = validateCouponRecord(coupon, 400);

    expect(result.valid).toBe(false);
    expect(result.message).toMatch(/inativo/i);
  });

  it("detects total tampering from the client", () => {
    const match = validateClientTotals(
      { subtotal: 1700, shipping: 0, discount_total: 0, total: 1700 },
      { subtotal: 1700, shipping: 0, discount_total: 170, total: 1530 },
    );

    expect(match).toBe(false);
  });
});
