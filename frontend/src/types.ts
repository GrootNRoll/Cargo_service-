export type OrderStatus = "draft" | "confirmed" | "fulfilled" | "cancelled";
export type UserRole = "admin" | "worker";

export interface UserPublic {
  id: number;
  username: string;
  role: UserRole;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserPublic;
}

export interface Summary {
  products: number;
  warehouses: number;
  stock_rows: number;
  orders: number;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  unit: string;
}

export interface Warehouse {
  id: number;
  name: string;
  address: string | null;
}

export interface StockItem {
  id: number;
  warehouse_id: number;
  product_id: number;
  quantity: number;
}

export interface OrderLine {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: string;
}

export interface Order {
  id: number;
  warehouse_id: number;
  status: OrderStatus;
  created_at: string;
  lines: OrderLine[];
}
