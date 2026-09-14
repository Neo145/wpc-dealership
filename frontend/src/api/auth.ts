import apiClient from "./client";

export interface User {
  id: string;
  email: string;
  name: string;
  role: "ADMIN" | "STAFF";
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>("/auth/login", { email, password });
  return response.data;
}