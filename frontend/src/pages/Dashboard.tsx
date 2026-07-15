import {
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  ShoppingBag,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";

interface Summary {
  orders_total: number;
  orders_by_status: { status: string; count: number }[];
  payments_by_status: { status: string; count: number }[];
  revenue_paid_orders: string | number;
  low_stock_products: {
    product__sku: string;
    product__description: string;
    units_in_stock: number;
  }[];
}

export default function Dashboard() {
  const [s, setS] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Summary>("/reports/summary/")
      .then(({ data }) => setS(data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Cargando dashboard...</div>;
  if (!s) return <div className="loading">Sin datos.</div>;

  const paid =
    s.payments_by_status.find((p) => p.status === "CONFIRMED")?.count ?? 0;

  return (
    <>
      <section className="dashboard-hero">
        <div>
          <span className="eyebrow">Resumen operativo</span>
          <h2>Control diario de la operacion Supli</h2>
          <p>
            Monitorea ventas, pagos confirmados e inventario critico desde un
            solo panel.
          </p>
        </div>
        <div className="hero-signal">
          <span>{s.low_stock_products.length}</span>
          <small>productos con bajo stock</small>
        </div>
      </section>

      <div className="kpi-grid">
        <Kpi label="Pedidos totales" value={s.orders_total} icon={ShoppingBag} />
        <Kpi label="Pagos confirmados" value={paid} icon={CheckCircle2} />
        <Kpi
          label="Ingresos pagados"
          value={`$${Number(s.revenue_paid_orders).toLocaleString("es-MX")}`}
          icon={DollarSign}
        />
        <Kpi
          label="Bajo stock"
          value={s.low_stock_products.length}
          icon={AlertTriangle}
        />
      </div>

      <div className="card">
        <div className="section-head">
          <div>
            <span className="eyebrow">Inventario</span>
            <h2>Productos con bajo stock</h2>
          </div>
        </div>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Producto</th>
                <th>Unidades</th>
              </tr>
            </thead>
            <tbody>
              {s.low_stock_products.map((p) => (
                <tr key={p.product__sku}>
                  <td>{p.product__sku}</td>
                  <td>{p.product__description}</td>
                  <td>
                    <span className="badge amber">{p.units_in_stock}</span>
                  </td>
                </tr>
              ))}
              {s.low_stock_products.length === 0 && (
                <tr>
                  <td colSpan={3} className="muted">
                    Todo el inventario esta por encima del umbral.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

function Kpi({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
}) {
  return (
    <div className="kpi">
      <div className="kpi-icon">
        <Icon size={20} />
      </div>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}
