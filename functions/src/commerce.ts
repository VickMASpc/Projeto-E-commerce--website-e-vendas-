export const SHIPPING_THRESHOLD = 199;
export const DEFAULT_SHIPPING = 25;

export type NormalizedOrderItem = {
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
};

export type ProductRecord = {
  id: string;
  name: string;
  price: number;
  stock: number;
};

export type CouponRecord = {
  code: string;
  type: "percent" | "fixed";
  value: number;
  active: boolean;
  min_order_total: number;
  max_discount: number | null;
  usage_limit: number | null;
  used_count: number;
  starts_at: string | null;
  expires_at: string | null;
};

export type CouponValidationResult = {
  valid: boolean;
  code: string | null;
  discount: number;
  message: string;
  adjusted_total: number;
};

export type CanonicalOrderDocument = {
  id: string;
  customer_id: string | null;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  customer_address: string;
  items: NormalizedOrderItem[];
  subtotal: number;
  shipping: number;
  discount_total: number;
  coupon_code: string | null;
  total: number;
  status: string;
  created_at: string;
  updated_at: string;
  schema_version: number;
};

const ORDER_STATUSES = {
  paid: "pago",
} as const;

function toNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function toInteger(value: unknown, fallback = 0): number {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function nowIsoString(): string {
  return new Date().toISOString();
}

function normalizeCouponType(value: unknown): "percent" | "fixed" {
  return String(value || "percent").trim().toLowerCase() === "fixed" ? "fixed" : "percent";
}

export function normalizeOrderItems(items: unknown): NormalizedOrderItem[] {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .map((item) => {
      const row = (item || {}) as Record<string, unknown>;
      return {
        product_id: String(
          row.product_id ?? row.produto_id ?? row.produtoId ?? row.id ?? "",
        ).trim(),
        product_name: String(
          row.product_name ?? row.produtoNome ?? row.nome_prod ?? row.name ?? "Produto",
        ).trim() || "Produto",
        quantity: Math.max(0, toInteger(row.quantity ?? row.quantidade ?? 0, 0)),
        unit_price: Math.max(0, toNumber(row.unit_price ?? row.preco_unit ?? row.preco ?? 0, 0)),
      };
    })
    .filter((item) => item.product_id);
}

export function normalizeProductRecord(id: string, data: Record<string, unknown>): ProductRecord {
  return {
    id,
    name: String(data.name ?? data.nome ?? id).trim() || id,
    price: Math.max(0, toNumber(data.price ?? data.preco ?? 0, 0)),
    stock: Math.max(0, toInteger(data.stock ?? data.estoque ?? 0, 0)),
  };
}

export function normalizeCouponRecord(code: string, data: Record<string, unknown>): CouponRecord {
  const minOrderTotal = Math.max(
    0,
    toNumber(data.min_order_total ?? data.min_subtotal ?? 0, 0),
  );
  const rawMaxDiscount = data.max_discount;
  const rawUsageLimit = data.usage_limit;
  return {
    code: String(data.code ?? code ?? "").trim().toUpperCase(),
    type: normalizeCouponType(data.type),
    value: Math.max(0, toNumber(data.value ?? 0, 0)),
    active: Boolean(data.active),
    min_order_total: minOrderTotal,
    max_discount:
      rawMaxDiscount === null || rawMaxDiscount === undefined || rawMaxDiscount === ""
        ? null
        : Math.max(0, toNumber(rawMaxDiscount, 0)),
    usage_limit:
      rawUsageLimit === null || rawUsageLimit === undefined || rawUsageLimit === ""
        ? null
        : Math.max(0, toInteger(rawUsageLimit, 0)),
    used_count: Math.max(0, toInteger(data.used_count ?? 0, 0)),
    starts_at: data.starts_at ? String(data.starts_at) : null,
    expires_at: data.expires_at ? String(data.expires_at) : null,
  };
}

export function computeShipping(subtotal: number): number {
  return subtotal > SHIPPING_THRESHOLD ? 0 : DEFAULT_SHIPPING;
}

function parseOptionalDate(value: string | null): number | null {
  if (!value) {
    return null;
  }
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function validateCouponRecord(
  coupon: CouponRecord | null,
  subtotal: number,
  now = new Date(),
): CouponValidationResult {
  const normalizedSubtotal = Math.max(0, subtotal);

  if (!coupon) {
    return {
      valid: false,
      code: null,
      discount: 0,
      message: "Cupom não encontrado.",
      adjusted_total: normalizedSubtotal,
    };
  }

  if (!coupon.active) {
    return {
      valid: false,
      code: coupon.code,
      discount: 0,
      message: "Cupom inativo.",
      adjusted_total: normalizedSubtotal,
    };
  }

  const nowValue = now.getTime();
  const startsAt = parseOptionalDate(coupon.starts_at);
  const expiresAt = parseOptionalDate(coupon.expires_at);

  if (startsAt && startsAt > nowValue) {
    return {
      valid: false,
      code: coupon.code,
      discount: 0,
      message: "Este cupom ainda não está válido.",
      adjusted_total: normalizedSubtotal,
    };
  }

  if (expiresAt && expiresAt < nowValue) {
    return {
      valid: false,
      code: coupon.code,
      discount: 0,
      message: "Cupom expirado.",
      adjusted_total: normalizedSubtotal,
    };
  }

  if (normalizedSubtotal < coupon.min_order_total) {
    return {
      valid: false,
      code: coupon.code,
      discount: 0,
      message: `Cupom disponível apenas para pedidos acima de R$ ${coupon.min_order_total.toFixed(2)}.`,
      adjusted_total: normalizedSubtotal,
    };
  }

  if (coupon.usage_limit !== null && coupon.used_count >= coupon.usage_limit) {
    return {
      valid: false,
      code: coupon.code,
      discount: 0,
      message: "Cupom esgotado.",
      adjusted_total: normalizedSubtotal,
    };
  }

  let discount =
    coupon.type === "fixed"
      ? coupon.value
      : normalizedSubtotal * (coupon.value / 100);

  if (coupon.max_discount !== null) {
    discount = Math.min(discount, coupon.max_discount);
  }

  discount = Math.max(0, Math.min(discount, normalizedSubtotal));

  return {
    valid: true,
    code: coupon.code,
    discount: Number(discount.toFixed(2)),
    message: "Cupom aplicado com sucesso.",
    adjusted_total: Number(Math.max(0, normalizedSubtotal - discount).toFixed(2)),
  };
}

export function computeOrderTotals(
  items: NormalizedOrderItem[],
  productsById: Map<string, ProductRecord>,
  coupon: CouponRecord | null,
): {
  normalizedItems: NormalizedOrderItem[];
  subtotal: number;
  shipping: number;
  discount_total: number;
  total: number;
  couponResult: CouponValidationResult | null;
} {
  const normalizedItems = items.map((item) => {
    const product = productsById.get(item.product_id);
    return {
      product_id: item.product_id,
      product_name: product?.name || item.product_name || "Produto",
      quantity: item.quantity,
      unit_price: product?.price ?? item.unit_price,
    };
  });

  const subtotal = Number(
    normalizedItems
      .reduce((sum, item) => sum + item.quantity * item.unit_price, 0)
      .toFixed(2),
  );
  const shipping = computeShipping(subtotal);
  const couponResult = coupon ? validateCouponRecord(coupon, subtotal) : null;
  const discountTotal = couponResult?.valid ? couponResult.discount : 0;
  const total = Number(Math.max(0, subtotal - discountTotal + shipping).toFixed(2));

  return {
    normalizedItems,
    subtotal,
    shipping,
    discount_total: discountTotal,
    total,
    couponResult,
  };
}

export function validateClientTotals(
  client: { subtotal?: unknown; shipping?: unknown; discount_total?: unknown; total?: unknown },
  server: { subtotal: number; shipping: number; discount_total: number; total: number },
): boolean {
  const epsilon = 0.01;
  return (
    Math.abs(toNumber(client.subtotal, 0) - server.subtotal) <= epsilon &&
    Math.abs(toNumber(client.shipping, 0) - server.shipping) <= epsilon &&
    Math.abs(toNumber(client.discount_total, 0) - server.discount_total) <= epsilon &&
    Math.abs(toNumber(client.total, 0) - server.total) <= epsilon
  );
}

export function buildOrderDocument(input: {
  orderId: string;
  customer: Record<string, unknown>;
  customerId: string | null;
  items: NormalizedOrderItem[];
  subtotal: number;
  shipping: number;
  discount_total: number;
  coupon_code: string | null;
  total: number;
}): CanonicalOrderDocument {
  const timestamp = nowIsoString();
  return {
    id: input.orderId,
    customer_id: input.customerId,
    customer_name: String(input.customer.name ?? "Cliente").trim() || "Cliente",
    customer_email: String(input.customer.email ?? "").trim(),
    customer_phone: String(input.customer.phone ?? "").trim(),
    customer_address: String(input.customer.address ?? "").trim(),
    items: input.items,
    subtotal: input.subtotal,
    shipping: input.shipping,
    discount_total: input.discount_total,
    coupon_code: input.coupon_code,
    total: input.total,
    status: ORDER_STATUSES.paid,
    created_at: timestamp,
    updated_at: timestamp,
    schema_version: 2,
  };
}
