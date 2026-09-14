import apiClient from "./client";

export interface OrderItem {
  id: string;
  product_id: string;
  product_name: string;
  product_code: string;
  quantity: number;
  unit_price_snapshot: string | null;
}

export interface Order {
  id: string;
  order_number: string;
  customer_name: string;
  customer_phone: string;
  status: "PENDING" | "CONFIRMED" | "COMPLETED" | "CANCELLED";
  notes: string | null;
  total_quantity: number;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface OrderItemInput {
  product_id: string;
  quantity: number;
}

export interface OrderInput {
  customer_name: string;
  customer_phone: string;
  notes?: string | null;
  items: OrderItemInput[];
}

export async function getOrders(): Promise<Order[]> {
  const res = await apiClient.get<Order[]>("/orders");
  return res.data;
}

export async function getOrder(id: string): Promise<Order> {
  const res = await apiClient.get<Order>(`/orders/${id}`);
  return res.data;
}

export async function createOrder(data: OrderInput): Promise<Order> {
  const res = await apiClient.post<Order>("/orders", data);
  return res.data;
}

export async function updateOrderStatus(id: string, newStatus: string): Promise<Order> {
  const res = await apiClient.put<Order>(`/orders/${id}/status`, { status: newStatus });
  return res.data;
}

export async function downloadInvoice(orderId: string, orderNumber: string): Promise<void> {
  const res = await apiClient.get(`/orders/${orderId}/invoice`, {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `${orderNumber}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}