import { useList } from "../api/useList";
import type { Payment } from "../api/types";

const BADGE: Record<string, string> = {
  CONFIRMED: "green",
  PENDING: "amber",
  FAILED: "red",
  REFUNDED: "gray",
};

export default function Payments() {
  const { data, loading, error } = useList<Payment>("/payments/");

  return (
    <div className="card">
      <div className="section-head">
        <h2>Seguimiento de Transacciones de Pagos</h2>
        <span className="muted">Confirmados por el backend de Toka vía webhook.</span>
      </div>

      {loading && <div className="loading">Cargando…</div>}
      {error && <div className="error-text">{error}</div>}

      {!loading && !error && (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Id Cliente</th>
                <th>Nombre Cliente</th>
                <th># Pago</th>
                <th>Monto</th>
                <th>Estado de Pago</th>
                <th>Pedido</th>
              </tr>
            </thead>
            <tbody>
              {data.map((p) => (
                <tr key={p.id}>
                  <td>{p.toka_customer_id}</td>
                  <td>{p.customer_name}</td>
                  <td>{p.payment_number}</td>
                  <td>
                    {p.amount
                      ? `$${Number(p.amount).toLocaleString("es-MX")}`
                      : "—"}
                  </td>
                  <td>
                    <span className={"badge " + (BADGE[p.status] ?? "gray")}>
                      {p.status_display}
                    </span>
                  </td>
                  <td>{p.order ? `#${p.order}` : "—"}</td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan={6} className="muted">
                    Aún no hay transacciones.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
