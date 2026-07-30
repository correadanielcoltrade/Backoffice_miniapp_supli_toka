import { useMemo, useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { Order } from "../api/types";
import { Pagination, usePagination } from "../components/Pagination";

// Pasos de entrega (deben coincidir con Order.DeliveryStatus del backend).
const DELIVERY_STATUSES = [
  { value: "PENDING", label: "Pendiente de despacho", badge: "gray" },
  { value: "LEFT_WAREHOUSE", label: "Salió de bodega", badge: "amber" },
  { value: "IN_TRANSIT", label: "En camino a WH Transport", badge: "blue" },
  { value: "OUT_FOR_DELIVERY", label: "En reparto al domicilio", badge: "blue" },
  { value: "DELIVERED", label: "Entregado", badge: "green" },
  { value: "EXCEPTION", label: "Novedad", badge: "red" },
] as const;

const BADGE: Record<string, string> = Object.fromEntries(
  DELIVERY_STATUSES.map((s) => [s.value, s.badge])
);

// Solo se gestiona la entrega de pedidos ya pagados en adelante.
const TRACKABLE = ["PAID", "PREPARING", "SHIPPED", "DELIVERED"];

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleString("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function Tracking() {
  const { data, loading, error, reload } = useList<Order>("/orders/");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [form, setForm] = useState({
    status: "PENDING",
    tracking_guide: "",
    carrier: "",
    note: "",
  });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const orders = useMemo(
    () => data.filter((o) => TRACKABLE.includes(o.status)),
    [data]
  );
  const pg = usePagination(orders);
  const selected = useMemo(
    () => orders.find((o) => o.id === selectedId) ?? null,
    [orders, selectedId]
  );

  function openManage(o: Order) {
    setSelectedId(o.id);
    setForm({
      status: o.tracking_status,
      tracking_guide: o.tracking_guide,
      carrier: o.carrier,
      note: "",
    });
    setFormError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setSaving(true);
    setFormError("");
    try {
      await api.post(`/orders/${selected.id}/tracking/`, {
        status: form.status,
        note: form.note,
        tracking_guide: form.tracking_guide,
        carrier: form.carrier,
      });
      setForm((f) => ({ ...f, note: "" }));
      reload();
    } catch (err: any) {
      const detail = err.response?.data;
      setFormError(
        detail?.note?.[0] ??
          detail?.status?.[0] ??
          "No se pudo registrar el paso de entrega."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      {selected && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-head">
            <h2 style={{ fontSize: 17 }}>
              Gestionar entrega ·{" "}
              <span style={{ color: "var(--primary, #1f3b57)" }}>
                {selected.order_number}
              </span>{" "}
              <span className="muted" style={{ fontWeight: 400 }}>
                — {selected.recipient_name}
              </span>
            </h2>
            <button className="btn secondary" onClick={() => setSelectedId(null)}>
              Cerrar
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            {/* Formulario de actualización */}
            <form onSubmit={submit}>
              <div className="field">
                <label>Nuevo estado de entrega</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                >
                  {DELIVERY_STATUSES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="split-grid">
                <div className="field">
                  <label>Guía de entrega</label>
                  <input
                    value={form.tracking_guide}
                    placeholder="N° de guía"
                    onChange={(e) =>
                      setForm({ ...form, tracking_guide: e.target.value })
                    }
                  />
                </div>
                <div className="field">
                  <label>Transportadora</label>
                  <input
                    value={form.carrier}
                    placeholder="Ej. WH Transport"
                    onChange={(e) => setForm({ ...form, carrier: e.target.value })}
                  />
                </div>
              </div>
              <div className="field">
                <label>
                  Nota{" "}
                  <span className="muted" style={{ fontWeight: 400 }}>
                    {form.status === "EXCEPTION"
                      ? "— obligatoria para una Novedad"
                      : "— opcional"}
                  </span>
                </label>
                <textarea
                  rows={3}
                  value={form.note}
                  placeholder="Detalle del paso o motivo de la novedad…"
                  onChange={(e) => setForm({ ...form, note: e.target.value })}
                  style={{
                    width: "100%",
                    padding: "9px 11px",
                    borderRadius: 8,
                    border: "1px solid var(--border)",
                    fontFamily: "inherit",
                    fontSize: 14,
                    resize: "vertical",
                  }}
                />
              </div>
              <button className="btn" disabled={saving}>
                {saving ? "Registrando…" : "Registrar paso"}
              </button>
              {formError && <div className="error-text">{formError}</div>}
            </form>

            {/* Historial de cambios */}
            <div>
              <h3 style={{ fontSize: 14, marginBottom: 12 }}>Historial de entrega</h3>
              {selected.tracking_events.length === 0 ? (
                <p className="muted" style={{ fontSize: 13 }}>
                  Aún no hay eventos registrados para este pedido.
                </p>
              ) : (
                <ol
                  style={{
                    listStyle: "none",
                    margin: 0,
                    padding: 0,
                    display: "flex",
                    flexDirection: "column",
                    gap: 12,
                  }}
                >
                  {selected.tracking_events
                    .slice()
                    .reverse()
                    .map((ev) => (
                      <li
                        key={ev.id}
                        style={{
                          borderLeft: "3px solid var(--border)",
                          paddingLeft: 12,
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span className={"badge " + (BADGE[ev.status] ?? "gray")}>
                            {ev.status_display}
                          </span>
                          <span className="muted" style={{ fontSize: 12 }}>
                            {fmtDate(ev.created_at)}
                          </span>
                        </div>
                        {ev.note && (
                          <div style={{ fontSize: 13, marginTop: 4 }}>{ev.note}</div>
                        )}
                        {ev.created_by_name && (
                          <div className="muted" style={{ fontSize: 11, marginTop: 2 }}>
                            por {ev.created_by_name}
                          </div>
                        )}
                      </li>
                    ))}
                </ol>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="section-head">
          <h2>Gestión de Tracking de Entregas</h2>
        </div>
        <p className="muted" style={{ marginTop: 0, marginBottom: 16, fontSize: 13 }}>
          Actualiza el paso a paso de la entrega de cada pedido pagado. El estado y
          el historial se exponen a la mini app del cliente.
        </p>

        {loading && <div className="loading">Cargando…</div>}
        {error && <div className="error-text">{error}</div>}

        {!loading && !error && (
          <>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>N° Pedido</th>
                  <th>Cliente</th>
                  <th>Estado de entrega</th>
                  <th>Guía</th>
                  <th>Transportadora</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {pg.pageItems.map((o) => (
                  <tr key={o.id} style={{ background: o.id === selectedId ? "#f5f8ff" : undefined }}>
                    <td style={{ whiteSpace: "nowrap", fontWeight: 600 }}>
                      {o.order_number}
                    </td>
                    <td>{o.recipient_name}</td>
                    <td>
                      <span className={"badge " + (BADGE[o.tracking_status] ?? "gray")}>
                        {o.tracking_status_display}
                      </span>
                    </td>
                    <td>{o.tracking_guide || "—"}</td>
                    <td>{o.carrier || "—"}</td>
                    <td>
                      <button
                        type="button"
                        onClick={() => openManage(o)}
                        style={{
                          border: "1px solid var(--border)",
                          background: "#fff",
                          borderRadius: 8,
                          padding: "6px 12px",
                          cursor: "pointer",
                          fontWeight: 500,
                          fontSize: 13,
                        }}
                      >
                        Gestionar
                      </button>
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr>
                    <td colSpan={6} className="muted">
                      No hay pedidos pagados para gestionar entrega.
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
    </>
  );
}
