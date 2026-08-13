import { useMemo, useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { Payment } from "../api/types";
import { Pagination, usePagination } from "../components/Pagination";

const BADGE: Record<string, string> = {
  CONFIRMED: "green",
  PENDING: "amber",
  FAILED: "red",
  REFUNDED: "gray",
};

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleString("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

// Fecha local (YYYY-MM-DD) para comparar contra los inputs de rango,
// coherente con la fecha que se muestra en la tabla.
function toLocalDate(iso: string): string {
  const d = new Date(iso);
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

export default function Payments() {
  const { data, loading, error } = useList<Payment>("/payments/");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const filtered = useMemo(
    () =>
      data.filter((p) => {
        const d = toLocalDate(p.created_at);
        return (!dateFrom || d >= dateFrom) && (!dateTo || d <= dateTo);
      }),
    [data, dateFrom, dateTo]
  );
  const pg = usePagination(filtered);
  const [downloading, setDownloading] = useState(false);

  function clearFilters() {
    setDateFrom("");
    setDateTo("");
  }

  async function downloadExcel() {
    setDownloading(true);
    try {
      const p = new URLSearchParams();
      if (dateFrom) p.append("created_after", dateFrom);
      if (dateTo) p.append("created_before", dateTo);
      const res = await api.get(`/payments/export/?${p.toString()}`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pagos.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="card">
      <div className="section-head">
        <div>
          <h2>Seguimiento de Transacciones de Pagos</h2>
          <span className="muted">
            Confirmados por el backend de Toka vía webhook.
          </span>
        </div>
        <div
          style={{
            display: "flex",
            gap: 10,
            alignItems: "flex-end",
            flexWrap: "wrap",
          }}
        >
          <div className="field" style={{ margin: 0 }}>
            <label>Desde</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div className="field" style={{ margin: 0 }}>
            <label>Hasta</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
          <button
            type="button"
            className="btn secondary"
            onClick={clearFilters}
            disabled={!dateFrom && !dateTo}
          >
            Limpiar
          </button>
          <button
            type="button"
            className="btn"
            onClick={downloadExcel}
            disabled={downloading || filtered.length === 0}
          >
            {downloading ? "Descargando…" : "⬇ Descargar Excel"}
          </button>
        </div>
      </div>

      {loading && <div className="loading">Cargando…</div>}
      {error && <div className="error-text">{error}</div>}

      {!loading && !error && (
        <>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Fecha de creación</th>
                <th>Id Cliente</th>
                <th>Nombre Cliente</th>
                <th># Pago</th>
                <th>Monto</th>
                <th>Estado de Pago</th>
                <th>Pedido</th>
              </tr>
            </thead>
            <tbody>
              {pg.pageItems.map((p) => (
                <tr key={p.id}>
                  <td style={{ whiteSpace: "nowrap" }}>{fmtDate(p.created_at)}</td>
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
                  <td>{p.order_number ?? (p.order ? `#${p.order}` : "—")}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="muted">
                    {dateFrom || dateTo
                      ? "No hay pagos en el rango de fechas seleccionado."
                      : "Aún no hay transacciones."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <Pagination pg={pg} />
        </>
      )}
    </div>
  );
}
