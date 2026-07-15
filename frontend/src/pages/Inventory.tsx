import { useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { Inventory as Inv } from "../api/types";

export default function Inventory() {
  const { data, loading, error, reload } = useList<Inv>("/inventory/");
  const [edits, setEdits] = useState<Record<number, number>>({});
  const [savingId, setSavingId] = useState<number | null>(null);

  async function save(item: Inv) {
    const value = edits[item.id];
    if (value === undefined || value === item.units_in_stock) return;
    setSavingId(item.id);
    try {
      await api.patch(`/inventory/${item.id}/`, { units_in_stock: value });
      reload();
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div className="card">
      <div className="section-head">
        <h2>Gestión de Inventarios</h2>
        <span className="muted">
          Las unidades se descuentan automáticamente al confirmarse el pago en Toka.
        </span>
      </div>

      {loading && <div className="loading">Cargando…</div>}
      {error && <div className="error-text">{error}</div>}

      {!loading && !error && (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Producto</th>
                <th>Unidades en inventario</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr key={item.id}>
                  <td>{item.sku}</td>
                  <td>{item.product_description}</td>
                  <td style={{ maxWidth: 160 }}>
                    <input
                      type="number"
                      min={0}
                      value={edits[item.id] ?? item.units_in_stock}
                      onChange={(e) =>
                        setEdits({
                          ...edits,
                          [item.id]: Number(e.target.value),
                        })
                      }
                    />
                  </td>
                  <td>
                    <button
                      className="btn secondary"
                      disabled={
                        savingId === item.id ||
                        (edits[item.id] ?? item.units_in_stock) ===
                          item.units_in_stock
                      }
                      onClick={() => save(item)}
                    >
                      {savingId === item.id ? "…" : "Guardar"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
