import { useEffect, useState } from "react";
import { api } from "../api/client";

interface Summary {
  orders_by_status: { status: string; count: number }[];
  payments_by_status: { status: string; count: number }[];
}

export default function Reports() {
  const [s, setS] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Summary>("/reports/summary/")
      .then(({ data }) => setS(data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Cargando…</div>;

  return (
    <>
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="section-head">
          <h2>Reportes Posventa</h2>
          <span className="badge amber">Campos por confirmar</span>
        </div>
        <p className="muted">
          Resúmenes iniciales calculados a partir de pedidos y pagos. Los
          reportes definitivos de posventa están pendientes por confirmar.
        </p>
      </div>

      <div className="split-grid">
        <div className="card">
          <div className="section-head">
            <h2 style={{ fontSize: 17 }}>Pedidos por estado</h2>
          </div>
          <Rows rows={s?.orders_by_status ?? []} />
        </div>
        <div className="card">
          <div className="section-head">
            <h2 style={{ fontSize: 17 }}>Pagos por estado</h2>
          </div>
          <Rows rows={s?.payments_by_status ?? []} />
        </div>
      </div>
    </>
  );
}

function Rows({ rows }: { rows: { status: string; count: number }[] }) {
  return (
    <table className="data">
      <tbody>
        {rows.map((r) => (
          <tr key={r.status}>
            <td>{r.status}</td>
            <td>
              <strong>{r.count}</strong>
            </td>
          </tr>
        ))}
        {rows.length === 0 && (
          <tr>
            <td className="muted">Sin datos.</td>
          </tr>
        )}
      </tbody>
    </table>
  );
}
