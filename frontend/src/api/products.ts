import apiClient from "./client";

export interface Product {
  id: string;
  product_code: string;
  name: string;
  category: string;
  description: string | null;
  unit: string;
  available_quantity: number;
  minimum_stock_level: number;
  price: string | null;
  status: "IN_STOCK" | "LOW_STOCK" | "OUT_OF_STOCK";
  created_at: string;
  updated_at: string;
}

export interface ProductInput {
  product_code: string;
  name: string;
  category: string;
  description?: string | null;
  unit: string;
  available_quantity: number;
  minimum_stock_level: number;
  price?: number | null;
}

export async function getProducts(): Promise<Product[]> {
  const res = await apiClient.get<Product[]>("/products");
  return res.data;
}

export async function createProduct(data: ProductInput): Promise<Product> {
  const res = await apiClient.post<Product>("/products", data);
  return res.data;
}

export async function updateProduct(id: string, data: Partial<ProductInput>): Promise<Product> {
  const res = await apiClient.put<Product>(`/products/${id}`, data);
  return res.data;
}

export async function deleteProduct(id: string): Promise<void> {
  await apiClient.delete(`/products/${id}`);
}