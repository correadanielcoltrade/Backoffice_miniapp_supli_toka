import type { Role } from "../api/types";
import {
  Award,
  BadgeDollarSign,
  BarChart3,
  Boxes,
  Image,
  LayoutDashboard,
  PackageCheck,
  RotateCcw,
  Settings,
  ShoppingBag,
  Tags,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  roles: Role[] | "ALL";
}

// Modulos del back office y roles que pueden verlos.
// El rol ADMINISTRADOR siempre ve todo.
export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, roles: "ALL" },
  {
    to: "/usuarios",
    label: "Usuarios y Roles",
    icon: Users,
    roles: ["ADMINISTRADOR"],
  },
  {
    to: "/pedidos",
    label: "Pedidos",
    icon: ShoppingBag,
    roles: ["SALES", "LOGISTIC"],
  },
  {
    to: "/inventario",
    label: "Inventario",
    icon: Boxes,
    roles: ["PROCUREMENT", "LOGISTIC"],
  },
  {
    to: "/catalogo",
    label: "Catalogo",
    icon: PackageCheck,
    roles: ["PROCUREMENT"],
  },
  {
    to: "/categorias",
    label: "Categorias",
    icon: Tags,
    roles: ["PROCUREMENT"],
  },
  {
    to: "/marcas",
    label: "Marcas",
    icon: Award,
    roles: ["PROCUREMENT"],
  },
  {
    to: "/pagos",
    label: "Pagos",
    icon: BadgeDollarSign,
    roles: ["SALES", "LOGISTIC"],
  },
  {
    to: "/logistica-inversa",
    label: "Logistica inversa",
    icon: RotateCcw,
    roles: ["LOGISTIC"],
  },
  {
    to: "/ads",
    label: "Ads / Carrusel",
    icon: Image,
    roles: ["SALES"],
  },
  { to: "/reportes", label: "Reportes", icon: BarChart3, roles: "ALL" },
  { to: "/configuracion", label: "Configuración", icon: Settings, roles: "ALL" },
];

export function canSee(item: NavItem, role: Role): boolean {
  if (role === "ADMINISTRADOR") return true;
  if (item.roles === "ALL") return true;
  return item.roles.includes(role);
}
