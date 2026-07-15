import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Ads from "./pages/Ads";
import Brands from "./pages/Brands";
import Catalog from "./pages/Catalog";
import Categories from "./pages/Categories";
import Dashboard from "./pages/Dashboard";
import Inventory from "./pages/Inventory";
import Login from "./pages/Login";
import Orders from "./pages/Orders";
import Payments from "./pages/Payments";
import Reports from "./pages/Reports";
import ReverseLogistics from "./pages/ReverseLogistics";
import Settings from "./pages/Settings";
import Users from "./pages/Users";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/usuarios" element={<Users />} />
        <Route path="/pedidos" element={<Orders />} />
        <Route path="/inventario" element={<Inventory />} />
        <Route path="/catalogo" element={<Catalog />} />
        <Route path="/categorias" element={<Categories />} />
        <Route path="/marcas" element={<Brands />} />
        <Route path="/pagos" element={<Payments />} />
        <Route path="/logistica-inversa" element={<ReverseLogistics />} />
        <Route path="/ads" element={<Ads />} />
        <Route path="/reportes" element={<Reports />} />
        <Route path="/configuracion" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
