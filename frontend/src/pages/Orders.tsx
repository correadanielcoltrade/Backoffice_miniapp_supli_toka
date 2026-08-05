import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Order } from "../api/types";
import { Pagination, usePagination } from "../components/Pagination";

const API_ORIGIN = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api")
  .replace(/\/api\/?$/, "");

// Respeta URLs absolutas (R2); antepone el origen del API a rutas relativas.
function imgUrl(path: string): string {
  return path.startsWith("http") ? path : API_ORIGIN + path;
}

/** Trae TODOS los pedidos que cumplen los filtros, siguiendo la paginación DRF. */
async function fetchAllOrders(params: URLSearchParams): Promise<Order[]> {
  const acc: Order[] = [];
  let page = 1;
  for (let guard = 0; guard < 1000; guard++) {
    const p = new URLSearchParams(params);
    p.set("page_size", "100");
    p.set("page", String(page));
    const { data } = await api.get(`/orders/?${p.toString()}`);
    if (Array.isArray(data)) return data;
    acc.push(...data.results);
    if (!data.next) break;
    page += 1;
  }
  return acc;
}

const STATUS_BADGE: Record<string, string> = {
  PENDING: "amber",
  PAID: "green",
  PREPARING: "blue",
  SHIPPED: "blue",
  DELIVERED: "green",
  CANCELLED: "red",
};

// Colores del estado de ENTREGA (tracking), distinto del estado de pago.
const DELIVERY_BADGE: Record<string, string> = {
  PENDING: "gray",
  LEFT_WAREHOUSE: "amber",
  IN_TRANSIT: "blue",
  OUT_FOR_DELIVERY: "blue",
  DELIVERED: "green",
  EXCEPTION: "red",
};

// Opciones del filtro por estado de entrega.
const DELIVERY_OPTIONS = [
  { value: "", label: "Todos los estados de entrega" },
  { value: "PENDING", label: "Pendiente de despacho" },
  { value: "LEFT_WAREHOUSE", label: "Salió de bodega" },
  { value: "IN_TRANSIT", label: "En camino a WH Transport" },
  { value: "OUT_FOR_DELIVERY", label: "En reparto al domicilio" },
  { value: "DELIVERED", label: "Entregado" },
  { value: "EXCEPTION", label: "Novedad" },
];

type OrderFilters = { from: string; to: string; status: string; q: string };

// Cada cuánto se refresca la lista automáticamente (tiempo real por sondeo).
const POLL_MS = 15000;

export default function Orders() {
  // Listado de pedidos con filtros por fecha de creacion
  const [orders, setOrders] = useState<Order[]>([]);
  const pg = usePagination(orders);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [trackingStatus, setTrackingStatus] = useState("");
  const [search, setSearch] = useState("");
  const [downloading, setDownloading] = useState(false);

  // Estado de "tiempo real"
  const [newIds, setNewIds] = useState<Set<number>>(new Set());
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const activeParams = useRef<OrderFilters>({ from: "", to: "", status: "", q: "" });
  const knownIds = useRef<Set<number>>(new Set());
  const hasLoaded = useRef(false);

  function currentFilters(): OrderFilters {
    return { from: dateFrom, to: dateTo, status: trackingStatus, q: search };
  }

  function buildParams(f: OrderFilters) {
    const p = new URLSearchParams();
    if (f.from) p.append("created_after", f.from);
    if (f.to) p.append("created_before", f.to);
    if (f.status) p.append("tracking_status", f.status);
    if (f.q.trim()) p.append("q", f.q.trim());
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
    f: OrderFilters = currentFilters(),
    opts: { silent?: boolean } = {}
  ) {
    const { silent } = opts;
    activeParams.current = f;
    if (!silent) {
      setLoading(true);
      setError("");
    }
    fetchAllOrders(buildParams(f))
      .then((all) => applyOrders(all))
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
      loadOrders(activeParams.current, { silent: true });
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
    setTrackingStatus("");
    setSearch("");
    loadOrders({ from: "", to: "", status: "", q: "" });
  }

  async function downloadExcel() {
    setDownloading(true);
    try {
      const res = await api.get(
        `/orders/export/?${buildParams(currentFilters()).toString()}`,
        { responseType: "blob" }
      );
      const url = URL.createObjectURL(res.data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pedidos.xlsx";
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

  // Pedido seleccionado para ver su detalle (modal).
  const [detailOrder, setDetailOrder] = useState<Order | null>(null);

  return (
    <>
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="section-head">
          <h2>Gestión de Pedidos</h2>
        </div>
        <div className="info-note">
          <span>ℹ️</span>
          <span>
            Los pedidos creados desde la <b>Mini App</b> llegan aquí
            <b> automáticamente y en tiempo real</b>, con todos sus datos de
            entrega — no hay que traerlos ni dar clic a ningún botón. Haz clic en
            un pedido para ver su detalle.
          </span>
        </div>
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
            <div className="field" style={{ margin: 0, minWidth: 220 }}>
              <label>Buscar</label>
              <input
                type="text"
                value={search}
                placeholder="# pedido, cliente, dirección…"
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") loadOrders();
                }}
              />
            </div>
            <div className="field" style={{ margin: 0 }}>
              <label>Estado de entrega</label>
              <select
                value={trackingStatus}
                onChange={(e) => {
                  const status = e.target.value;
                  setTrackingStatus(status);
                  loadOrders({ ...currentFilters(), status });
                }}
              >
                {DELIVERY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
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
              onClick={downloadExcel}
              disabled={downloading || orders.length === 0}
            >
              {downloading ? "Descargando…" : "⬇ Descargar Excel"}
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
          <>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>N° Pedido</th>
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
                  <th>Estado de pago</th>
                  <th>Estado de entrega</th>
                </tr>
              </thead>
              <tbody>
                {pg.pageItems.map((o) => (
                  <tr
                    key={o.id}
                    className={
                      "clickable-row" + (newIds.has(o.id) ? " row-new" : "")
                    }
                    onClick={() => setDetailOrder(o)}
                    title="Ver detalle del pedido"
                  >
                    <td style={{ whiteSpace: "nowrap", fontWeight: 600 }}>
                      {o.order_number}
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
                    <td>
                      <span
                        className={
                          "badge " + (DELIVERY_BADGE[o.tracking_status] ?? "gray")
                        }
                      >
                        {o.tracking_status_display}
                      </span>
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr>
                    <td colSpan={13} className="muted">
                      {dateFrom || dateTo || trackingStatus || search
                        ? "No se encontraron pedidos con los filtros aplicados."
                        : "Aún no hay pedidos registrados."}
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

      {detailOrder && (
        <OrderDetailModal
          order={detailOrder}
          onClose={() => setDetailOrder(null)}
        />
      )}
    </>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-row">
      <span className="detail-label">{label}</span>
      <span className="detail-value">{value}</span>
    </div>
  );
}

function OrderDetailModal({
  order,
  onClose,
}: {
  order: Order;
  onClose: () => void;
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const money = (v: string | number) => "$" + Number(v).toLocaleString("es-MX");
  const fecha = new Date(order.created_at).toLocaleString("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <h2 style={{ margin: 0, fontSize: 20 }}>{order.order_number}</h2>
            <span className="muted" style={{ fontSize: 13 }}>
              Creado el {fecha}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span className={"badge " + (STATUS_BADGE[order.status] ?? "gray")}>
              {order.status_display}
            </span>
            <button
              type="button"
              className="modal-close"
              onClick={onClose}
              aria-label="Cerrar"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="modal-body">
          <div className="detail-grid">
            <section>
              <h3 className="detail-h">Cliente</h3>
              <DetailRow label="Cliente (ID Toka)" value={order.customer_name} />
              <DetailRow label="Nombre completo" value={order.recipient_name} />
              <DetailRow label="Contacto" value={order.contact_number} />
            </section>
            <section>
              <h3 className="detail-h">Entrega</h3>
              <DetailRow label="Dirección" value={order.full_address} />
              <DetailRow
                label="Complemento"
                value={order.address_complement || "—"}
              />
              <DetailRow label="Colonia" value={order.colonia} />
              <DetailRow label="Ciudad / Alcaldía" value={order.city_alcaldia} />
              <DetailRow label="Estado" value={order.state} />
              <DetailRow label="Código postal" value={order.postal_code} />
            </section>
          </div>

          {order.tracking_status && (
            <div style={{ marginTop: 8 }}>
              <h3 className="detail-h">Entrega / Tracking</h3>
              <DetailRow
                label="Estado de entrega"
                value={order.tracking_status_display}
              />
              {order.tracking_guide && (
                <DetailRow label="Guía" value={order.tracking_guide} />
              )}
              {order.carrier && (
                <DetailRow label="Transportadora" value={order.carrier} />
              )}
            </div>
          )}

          <h3 className="detail-h" style={{ marginTop: 20 }}>
            Productos ({order.items.length})
          </h3>
          <div className="table-wrap detail-products-wrap" style={{ marginTop: 4 }}>
            <table className="data detail-table">
              <thead>
                <tr>
                  <th>Imagen</th>
                  <th>Producto</th>
                  <th>SKU</th>
                  <th style={{ textAlign: "center" }}>Cantidad</th>
                  <th style={{ textAlign: "right" }}>Precio unitario</th>
                  <th style={{ textAlign: "right" }}>Total</th>
                </tr>
              </thead>
              <tbody>
                {order.items.map((it) => (
                  <tr key={it.id}>
                    <td>
                      <div className="detail-thumbs">
                        {it.images.length ? (
                          it.images.map((src, i) => (
                            <a
                              key={i}
                              href={imgUrl(src)}
                              target="_blank"
                              rel="noreferrer"
                              title="Abrir imagen"
                            >
                              <img src={imgUrl(src)} alt={it.product_description} />
                            </a>
                          ))
                        ) : (
                          <div className="detail-noimg">Sin imagen</div>
                        )}
                      </div>
                    </td>
                    <td style={{ whiteSpace: "normal", minWidth: 180, fontWeight: 500 }}>
                      {it.product_description}
                    </td>
                    <td>{it.sku}</td>
                    <td style={{ textAlign: "center" }}>{it.quantity}</td>
                    <td style={{ textAlign: "right" }}>{money(it.unit_price)}</td>
                    <td style={{ textAlign: "right", fontWeight: 600 }}>
                      {money(it.subtotal)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={5} style={{ textAlign: "right", fontWeight: 600 }}>
                    Total del pedido
                  </td>
                  <td style={{ textAlign: "right", fontWeight: 800 }}>
                    {money(order.total_amount)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
