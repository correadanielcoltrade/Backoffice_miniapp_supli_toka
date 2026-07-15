import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { Customer, CustomerAddress, Order, Product } from "../api/types";

const STATUS_BADGE: Record<string, string> = {
  PENDING: "amber",
  PAID: "green",
  PREPARING: "blue",
  SHIPPED: "blue",
  DELIVERED: "green",
  CANCELLED: "red",
};

// Cada cuánto se refresca la lista automáticamente (tiempo real por sondeo).
const POLL_MS = 15000;

// Los 8 campos de entrega del pedido (traidos de Toka, editables)
const EMPTY_DELIVERY = {
  recipient_name: "",
  contact_number: "",
  full_address: "",
  address_complement: "",
  colonia: "",
  city_alcaldia: "",
  state: "",
  postal_code: "",
};

interface ItemLine {
  product: string;
  quantity: number;
}

export default function Orders() {
  const { data: customers } = useList<Customer>("/customers/");
  const { data: products } = useList<Product>("/products/");

  // Listado de pedidos con filtros por fecha de creacion
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [downloading, setDownloading] = useState(false);

  // Estado de "tiempo real"
  const [newIds, setNewIds] = useState<Set<number>>(new Set());
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const activeParams = useRef({ from: "", to: "" });
  const knownIds = useRef<Set<number>>(new Set());
  const hasLoaded = useRef(false);

  function buildParams(from: string, to: string) {
    const p = new URLSearchParams();
    if (from) p.append("created_after", from);
    if (to) p.append("created_before", to);
    return p;
  }

  // Integra la nueva lista y detecta pedidos que llegaron desde la última carga.
  function applyOrders(list: Order[]) {
    setOrders(list);
    setLastUpdated(new Date());

    const incomingIds = list.map((o) => o.id);
    if (hasLoaded.current) {
      const fresh = incomingIds.filter((id) => !knownIds.current.has(id));
      if (fresh.length) {
        setNewIds((prev) => {
          const next = new Set(prev);
          fresh.forEach((id) => next.add(id));
          return next;
        });
        // Quita el resaltado a los ~12s.
        window.setTimeout(() => {
          setNewIds((prev) => {
            const next = new Set(prev);
            fresh.forEach((id) => next.delete(id));
            return next;
          });
        }, 12000);
      }
    }
    knownIds.current = new Set(incomingIds);
    hasLoaded.current = true;
  }

  function loadOrders(
    from = dateFrom,
    to = dateTo,
    opts: { silent?: boolean } = {}
  ) {
    const { silent } = opts;
    activeParams.current = { from, to };
    if (!silent) {
      setLoading(true);
      setError("");
    }
    api
      .get(`/orders/?${buildParams(from, to).toString()}`)
      .then(({ data }) => applyOrders(Array.isArray(data) ? data : data.results))
      .catch(() => {
        if (!silent) setError("No se pudo cargar la información.");
      })
      .finally(() => {
        if (!silent) setLoading(false);
      });
  }

  // Carga inicial
  useEffect(() => {
    loadOrders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Tiempo real: sondeo periódico silencioso + refresco al volver a la pestaña.
  useEffect(() => {
    function refresh() {
      loadOrders(activeParams.current.from, activeParams.current.to, {
        silent: true,
      });
    }
    const interval = window.setInterval(refresh, POLL_MS);
    function onVisible() {
      if (document.visibilityState === "visible") refresh();
    }
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", onVisible);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", onVisible);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function clearFilters() {
    setDateFrom("");
    setDateTo("");
    loadOrders("", "");
  }

  async function downloadCsv() {
    setDownloading(true);
    try {
      const res = await api.get(
        `/orders/export/?${buildParams(dateFrom, dateTo).toString()}`,
        { responseType: "blob" }
      );
      const url = URL.createObjectURL(res.data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pedidos.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      setError("No se pudo descargar el archivo.");
    } finally {
      setDownloading(false);
    }
  }

  const reload = () => loadOrders();

  const [showForm, setShowForm] = useState(false);
  const [customerId, setCustomerId] = useState<string>("");
  const [delivery, setDelivery] = useState({ ...EMPTY_DELIVERY });
  const [items, setItems] = useState<ItemLine[]>([]);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const selectedCustomer = useMemo(
    () => customers.find((c) => String(c.id) === customerId),
    [customers, customerId]
  );

  function setField(k: keyof typeof EMPTY_DELIVERY, v: string) {
    setDelivery((d) => ({ ...d, [k]: v }));
  }

  function resetForm() {
    setCustomerId("");
    setDelivery({ ...EMPTY_DELIVERY });
    setItems([]);
    setFormError("");
  }

  // Prellenar desde una direccion guardada del cliente
  function useSavedAddress(addr: CustomerAddress) {
    setDelivery({
      recipient_name: selectedCustomer?.full_name ?? delivery.recipient_name,
      contact_number:
        selectedCustomer?.contact_number ?? delivery.contact_number,
      full_address: addr.complete_address,
      address_complement: addr.supplementary_address,
      colonia: addr.suburb,
      city_alcaldia: addr.municipality,
      state: addr.state,
      postal_code: addr.zip_code,
    });
  }

  function addItem() {
    setItems((it) => [...it, { product: "", quantity: 1 }]);
  }
  function updateItem(i: number, patch: Partial<ItemLine>) {
    setItems((it) => it.map((row, idx) => (idx === i ? { ...row, ...patch } : row)));
  }
  function removeItem(i: number) {
    setItems((it) => it.filter((_, idx) => idx !== i));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    if (!customerId) {
      setFormError("Selecciona un cliente.");
      return;
    }
    setSaving(true);
    try {
      await api.post("/orders/", {
        customer: Number(customerId),
        ...delivery,
        items: items
          .filter((it) => it.product)
          .map((it) => ({ product: Number(it.product), quantity: it.quantity })),
      });
      resetForm();
      setShowForm(false);
      reload();
    } catch (err: any) {
      setFormError(JSON.stringify(err.response?.data ?? "Error al crear el pedido"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="section-head">
          <h2>Gestión de Pedidos</h2>
          <button
            className="btn secondary"
            onClick={() => {
              resetForm();
              setShowForm((v) => !v);
            }}
          >
            {showForm ? "Cerrar" : "+ Captura manual"}
          </button>
        </div>

        <div className="info-note">
          <span>ℹ️</span>
          <span>
            Los pedidos creados desde la <b>Mini App</b> llegan aquí
            <b> automáticamente y en tiempo real</b>, con todos sus datos de
            entrega — no hay que traerlos ni dar clic a ningún botón. Esta captura
            manual es solo para casos excepcionales (p. ej. pedidos telefónicos).
          </span>
        </div>

        {showForm && (
          <form onSubmit={submit}>
            {/* Cliente + direccion guardada */}
            <div className="split-grid" style={{ marginBottom: 6 }}>
              <div className="field">
                <label>Cliente</label>
                <select
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                >
                  <option value="">Selecciona un cliente…</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.full_name} · {c.toka_customer_id}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Usar dirección guardada</label>
                <select
                  value=""
                  disabled={!selectedCustomer?.addresses?.length}
                  onChange={(e) => {
                    const addr = selectedCustomer?.addresses.find(
                      (a) => String(a.id) === e.target.value
                    );
                    if (addr) useSavedAddress(addr);
                  }}
                >
                  <option value="">
                    {selectedCustomer?.addresses?.length
                      ? "Selecciona una dirección previa…"
                      : "Sin direcciones guardadas"}
                  </option>
                  {selectedCustomer?.addresses?.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.label ? `${a.label}: ` : ""}
                      {a.complete_address}, {a.suburb}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Los 8 campos de entrega */}
            <div className="form-grid">
              <Field label="Nombre Completo *" v={delivery.recipient_name} on={(v) => setField("recipient_name", v)} required />
              <Field label="Número de contacto *" v={delivery.contact_number} on={(v) => setField("contact_number", v)} required />
              <Field label="Dirección Completa *" v={delivery.full_address} on={(v) => setField("full_address", v)} required />
              <Field label="Complemento de dirección (opcional)" v={delivery.address_complement} on={(v) => setField("address_complement", v)} />
              <Field label="Colonia *" v={delivery.colonia} on={(v) => setField("colonia", v)} required />
              <Field label="Ciudad / Alcaldía *" v={delivery.city_alcaldia} on={(v) => setField("city_alcaldia", v)} required />
              <Field label="Estado *" v={delivery.state} on={(v) => setField("state", v)} required />
              <Field label="Código postal *" v={delivery.postal_code} on={(v) => setField("postal_code", v)} required />
            </div>

            {/* Productos del pedido */}
            <div className="section-head" style={{ marginTop: 18, marginBottom: 10 }}>
              <label style={{ margin: 0 }}>Productos del pedido</label>
              <button type="button" className="btn secondary" onClick={addItem}>
                + Agregar producto
              </button>
            </div>
            {items.map((row, i) => (
              <div key={i} className="line-row">
                <select
                  value={row.product}
                  onChange={(e) => updateItem(i, { product: e.target.value })}
                >
                  <option value="">Producto…</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.sku} · {p.description} (${Number(p.sale_price).toLocaleString("es-MX")})
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min={1}
                  value={row.quantity}
                  onChange={(e) => updateItem(i, { quantity: Number(e.target.value) })}
                />
                <button type="button" className="btn secondary" onClick={() => removeItem(i)}>
                  ✕
                </button>
              </div>
            ))}

            {formError && <div className="error-text">{formError}</div>}

            <div style={{ marginTop: 16 }}>
              <button className="btn" disabled={saving}>
                {saving ? "Guardando…" : "Crear pedido"}
              </button>
            </div>
          </form>
        )}
      </div>

      <div className="card">
        <div className="section-head">
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <h2 style={{ fontSize: 18 }}>Pedidos registrados</h2>
            <span className="live-chip">
              <span className="live-dot" />
              En vivo
            </span>
            {lastUpdated && (
              <span className="live-updated">
                Actualizado {lastUpdated.toLocaleTimeString("es-MX")}
              </span>
            )}
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
              <label>Creado desde</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div className="field" style={{ margin: 0 }}>
              <label>Creado hasta</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
            <button
              type="button"
              className="btn secondary"
              onClick={() => loadOrders()}
            >
              Filtrar
            </button>
            <button
              type="button"
              className="btn secondary"
              onClick={clearFilters}
            >
              Limpiar
            </button>
            <button
              type="button"
              className="btn"
              onClick={downloadCsv}
              disabled={downloading || orders.length === 0}
            >
              {downloading ? "Descargando…" : "⬇ Descargar CSV"}
            </button>
          </div>
        </div>

        {newIds.size > 0 && (
          <div className="new-banner">
            <span>🔔</span>
            <span>
              {newIds.size} pedido{newIds.size > 1 ? "s" : ""} nuevo
              {newIds.size > 1 ? "s" : ""} recibido{newIds.size > 1 ? "s" : ""} de
              la Mini App
            </span>
            <button
              type="button"
              className="close"
              onClick={() => setNewIds(new Set())}
              aria-label="Descartar aviso"
            >
              ✕
            </button>
          </div>
        )}

        {loading && <div className="loading">Cargando…</div>}
        {error && <div className="error-text">{error}</div>}
        {!loading && !error && (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Cliente</th>
                  <th>Nombre Completo</th>
                  <th>Número de contacto</th>
                  <th>Dirección Completa</th>
                  <th>Complemento</th>
                  <th>Colonia</th>
                  <th>Ciudad / Alcaldía</th>
                  <th>Estado</th>
                  <th>Código postal</th>
                  <th>Total</th>
                  <th>Estado pedido</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id} className={newIds.has(o.id) ? "row-new" : undefined}>
                    <td>
                      {o.id}
                      {newIds.has(o.id) && (
                        <span className="badge green" style={{ marginLeft: 6 }}>
                          Nuevo
                        </span>
                      )}
                    </td>
                    <td>{o.customer_name}</td>
                    <td>{o.recipient_name}</td>
                    <td>{o.contact_number}</td>
                    <td>{o.full_address}</td>
                    <td>{o.address_complement || "—"}</td>
                    <td>{o.colonia}</td>
                    <td>{o.city_alcaldia}</td>
                    <td>{o.state}</td>
                    <td>{o.postal_code}</td>
                    <td>${Number(o.total_amount).toLocaleString("es-MX")}</td>
                    <td>
                      <span className={"badge " + (STATUS_BADGE[o.status] ?? "gray")}>
                        {o.status_display}
                      </span>
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr>
                    <td colSpan={12} className="muted">
                      Aún no hay pedidos registrados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

function Field({
  label,
  v,
  on,
  required = false,
}: {
  label: string;
  v: string;
  on: (v: string) => void;
  required?: boolean;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <input value={v} onChange={(e) => on(e.target.value)} required={required} />
    </div>
  );
}
