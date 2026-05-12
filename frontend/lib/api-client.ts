/**
 * API Client for MES Backend
 * Base URL: http://localhost:8000 (development)
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class APIError extends Error {
  constructor(
    public status: number,
    public data: any,
    message: string
  ) {
    super(message);
    this.name = "APIError";
  }
}

/**
 * Generic fetch wrapper with error handling
 */
async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new APIError(response.status, data, `API Error: ${response.status}`);
  }

  return response.json();
}

/**
 * Production Order API endpoints
 */
export const productionOrderAPI = {
  list: () => apiCall("/productionorder"),
  get: (id: number) => apiCall(`/productionorder/${id}`),
  create: (data: { quantity: number; article_id: number }) =>
    apiCall("/productionorder", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<{ quantity: number; status: string }>) =>
    apiCall(`/productionorder/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    apiCall(`/productionorder/${id}`, { method: "DELETE" }),
};

/**
 * Delivery Order API endpoints
 */
export const deliveryOrderAPI = {
  list: () => apiCall("/deliveryorder"),
  get: (id: number) => apiCall(`/deliveryorder/${id}`),
  create: (data: { quantity: number; article_id: number }) =>
    apiCall("/deliveryorder", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: number, data: Partial<{ quantity: number; status: string }>) =>
    apiCall(`/deliveryorder/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    apiCall(`/deliveryorder/${id}`, { method: "DELETE" }),
};

/**
 * Storage/Inventory API endpoints
 */
export const storageAPI = {
  list: () => apiCall("/storage"),
  get: (itemId: number) => apiCall(`/storage/${itemId}`),
  add: (itemId: number, quantity: number) =>
    apiCall(`/storage/${itemId}`, {
      method: "POST",
      body: JSON.stringify({ quantity }),
    }),
  update: (itemId: number, quantity: number) =>
    apiCall(`/storage/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    }),
  adjustAmount: (itemId: number, amount: number) =>
    apiCall(`/storage/${itemId}/${Math.abs(amount)}`, {
      method: "PATCH",
      body: JSON.stringify({ amount: amount > 0 ? amount : -amount }),
    }),
};

export default {
  productionOrderAPI,
  deliveryOrderAPI,
  storageAPI,
};
