import apiClient from "./client";

export interface RecentOrder {
  id: string;
  order_number: string;
  customer_name: string;
  status: string;
  total_quantity: number;
}

export interface DashboardSummary {
  total_products: number;
  total_available_stock: number;
  low_stock_products: number;
  out_of_stock_products: number;
  total_orders: number;
  pending_orders: number;
  completed_orders: number;
  recent_orders: RecentOrder[];
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const res = await apiClient.get<DashboardSummary>("/dashboard/summary");
  return res.data;
}