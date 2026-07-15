export type Role = "ADMINISTRADOR" | "PROCUREMENT" | "LOGISTIC" | "SALES";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  role: Role;
  role_display: string;
  is_active: boolean;
  date_joined: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Category {
  id: number;
  name: string;
  sort_order: number;
  icon: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Brand {
  id: number;
  name: string;
  sort_order: number;
  logo: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ProductSpec {
  key: string;
  value: string;
}

export interface Product {
  id: number;
  description: string;
  long_description: string;
  sku: string;
  category: number;
  category_name: string;
  brand: number | null;
  brand_name: string;
  sale_price: string;
  units_in_stock: number | null;
  features: string[];
  specifications: ProductSpec[];
  is_featured: boolean;
  is_on_offer: boolean;
  show_stock: boolean;
  images: string[];
  is_active: boolean;
}

export interface Inventory {
  id: number;
  product: number;
  product_description: string;
  sku: string;
  units_in_stock: number;
  reorder_level: number;
  updated_at: string;
}

export interface CustomerAddress {
  id: number;
  label: "HOME" | "OFFICE" | "UNIVERSITY" | "OTHER";
  custom_label: string;
  complete_address: string;
  no_street_number: boolean;
  state: string;
  municipality: string;
  locality: string;
  suburb: string;
  zip_code: string;
  unknown_zip_code: boolean;
  supplementary_address: string;
  delivery_instructions: string;
  is_default: boolean;
}

export interface Customer {
  id: number;
  toka_customer_id: string;
  full_name: string;
  contact_number: string;
  email: string;
  addresses: CustomerAddress[];
}

export interface Order {
  id: number;
  customer: number;
  customer_name: string;
  recipient_name: string;
  contact_number: string;
  full_address: string;
  address_complement: string;
  colonia: string;
  city_alcaldia: string;
  state: string;
  postal_code: string;
  status: string;
  status_display: string;
  total_amount: string;
  stock_deducted: boolean;
  created_at: string;
}

export interface Payment {
  id: number;
  toka_customer_id: string;
  customer_name: string;
  payment_number: string;
  amount: string | null;
  status: string;
  status_display: string;
  order: number | null;
  created_at: string;
}

export interface CarouselImage {
  id: number;
  image: string;
  link_url: string;
  position: number;
}

export interface Carousel {
  id: number;
  name: string;
  width: number;
  height: number;
  is_active: boolean;
  images: CarouselImage[];
}
