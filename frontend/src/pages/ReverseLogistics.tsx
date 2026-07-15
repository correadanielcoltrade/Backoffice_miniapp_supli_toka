import { useList } from "../api/useList";

interface ReturnRequest {
  id: number;
  order: number;
  reason: string;
  status: string;
  status_display: string;
  created_at: string;
}

export default function ReverseLogistics() {
  const { data, loading, error } = useList<ReturnRequest>("/returns/");

  return (
    <div className="card">
      <div className="section-head">
        <h2>Logística Inversa</h2>
        <span className="badge amber">Campos por confirmar</span>
      </div>

      <p className="muted" style={{ marginBottom: 18 }}>
        Estructura base para devoluciones. Al aprobar una devolución se puede
        reingresar stock al inventario. Los campos definitivos están pendientes
        por confirmar con el negocio.
      </p>

      {loading && <div className="loading">Cargando…</div>}
      {error && <div className="error-text">{error}</div>}

      {!loading && !error && (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>#</th>
                <th>Pedido</th>
                <th>Motivo</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {data.map((r) => (
                <tr key={r.id}>
                  <td>{r.id}</td>
                  <td>#{r.order}</td>
                  <td>{r.reason || "—"}</td>
                  <td>
                    <span className="badge gray">{r.status_display}</span>
                  </td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan={4} className="muted">
                    Sin solicitudes de devolución.
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
