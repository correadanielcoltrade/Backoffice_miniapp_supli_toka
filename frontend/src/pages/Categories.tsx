import { useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { Category } from "../api/types";
import { Switch } from "../components/Switch";

const API_ORIGIN = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api")
  .replace(/\/api\/?$/, "");

const EMPTY = { name: "", sort_order: "0", is_active: true };

function iconUrl(icon: string | null): string | null {
  if (!icon) return null;
  return icon.startsWith("http") ? icon : API_ORIGIN + icon;
}

export default function Categories() {
  const { data, loading, error, reload } = useList<Category>("/categories/");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(EMPTY);
  const [icon, setIcon] = useState<File | null>(null);
  const [currentIcon, setCurrentIcon] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  function openCreate() {
    setEditingId(null);
    setForm(EMPTY);
    setIcon(null);
    setCurrentIcon(null);
    setFormError("");
    setShowForm(true);
  }

  function openEdit(c: Category) {
    setEditingId(c.id);
    setForm({
      name: c.name,
      sort_order: String(c.sort_order),
      is_active: c.is_active,
    });
    setIcon(null);
    setCurrentIcon(c.icon);
    setFormError("");
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      const fd = new FormData();
      fd.append("name", form.name);
      fd.append("sort_order", form.sort_order || "0");
      fd.append("is_active", form.is_active ? "true" : "false");
      if (icon) fd.append("icon", icon);
      const cfg = { headers: { "Content-Type": "multipart/form-data" } };
      if (editingId) {
        await api.patch(`/categories/${editingId}/`, fd, cfg);
      } else {
        await api.post("/categories/", fd, cfg);
      }
      setShowForm(false);
      setEditingId(null);
      setForm(EMPTY);
      setIcon(null);
      reload();
    } catch (err: any) {
      setFormError(JSON.stringify(err.response?.data ?? "Error"));
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(c: Category) {
    setBusyId(c.id);
    setActionError("");
    try {
      await api.patch(`/categories/${c.id}/`, { is_active: !c.is_active });
      reload();
    } catch {
      setActionError(`No se pudo cambiar el estado de "${c.name}".`);
    } finally {
      setBusyId(null);
    }
  }

  async function remove(c: Category) {
    if (!window.confirm(`¿Eliminar la categoría "${c.name}"?`)) return;
    setBusyId(c.id);
    setActionError("");
    try {
      await api.delete(`/categories/${c.id}/`);
      reload();
    } catch (err: any) {
      const st = err.response?.status;
      if (st === 400 || st === 409 || st === 500) {
        setActionError(
          `No se puede eliminar "${c.name}" porque tiene productos asociados. Desactívala con el switch en su lugar.`
        );
      } else {
        setActionError(`No se pudo eliminar "${c.name}".`);
      }
    } finally {
      setBusyId(null);
    }
  }

  const preview = icon ? URL.createObjectURL(icon) : iconUrl(currentIcon);

  return (
    <div className="card">
      <div className="section-head">
        <h2>Gestión de Categorías</h2>
        {showForm ? (
          <button className="btn" onClick={() => setShowForm(false)}>
            Cerrar
          </button>
        ) : (
          <button className="btn" onClick={openCreate}>
            + Nueva categoría
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={save} style={{ marginBottom: 24 }}>
          <div className="split-grid">
            <div className="field">
              <label>Nombre</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div className="field">
              <label>
                Orden{" "}
                <span className="muted" style={{ fontWeight: 400 }}>
                  — menor aparece primero
                </span>
              </label>
              <input
                type="number"
                value={form.sort_order}
                onChange={(e) => setForm({ ...form, sort_order: e.target.value })}
              />
            </div>
          </div>

          <label style={{ marginTop: 6 }}>Ícono de la categoría</label>
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
            <label
              style={{
                border: "1px dashed var(--border)",
                borderRadius: 12,
                width: 84,
                height: 84,
                display: "grid",
                placeItems: "center",
                cursor: "pointer",
                overflow: "hidden",
                background: "#faf9ff",
                margin: 0,
                fontWeight: 500,
              }}
            >
              {preview ? (
                <img
                  src={preview}
                  alt=""
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                />
              ) : (
                <span className="muted">+ Ícono</span>
              )}
              <input
                type="file"
                accept="image/*"
                style={{ display: "none" }}
                onChange={(e) => setIcon(e.target.files?.[0] ?? null)}
              />
            </label>
            {editingId && (
              <span className="muted" style={{ fontSize: 13 }}>
                Deja el ícono vacío para conservar el actual.
              </span>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "6px 0 16px" }}>
            <Switch
              checked={form.is_active}
              onChange={() => setForm({ ...form, is_active: !form.is_active })}
            />
            <span style={{ fontWeight: 500 }}>
              {form.is_active ? "Activa" : "Inactiva"}
            </span>
            <span className="muted" style={{ fontSize: 13 }}>
              (las categorías activas se muestran en la app)
            </span>
          </div>

          <button className="btn" disabled={saving}>
            {saving ? "Guardando…" : editingId ? "Guardar cambios" : "Crear categoría"}
          </button>
          {formError && <div className="error-text">{formError}</div>}
        </form>
      )}

      {actionError && <div className="error-text">{actionError}</div>}
      {loading && <div className="loading">Cargando…</div>}
      {error && <div className="error-text">{error}</div>}

      {!loading && !error && (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Ícono</th>
                <th>Nombre</th>
                <th>Orden</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {data
                .slice()
                .sort((a, b) => a.sort_order - b.sort_order)
                .map((c) => (
                  <tr key={c.id} style={{ opacity: c.is_active ? 1 : 0.55 }}>
                    <td>
                      {iconUrl(c.icon) ? (
                        <img
                          src={iconUrl(c.icon)!}
                          alt=""
                          style={{ width: 36, height: 36, objectFit: "cover", borderRadius: 8 }}
                        />
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td style={{ fontWeight: 500 }}>{c.name}</td>
                    <td>{c.sort_order}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <Switch
                          checked={c.is_active}
                          busy={busyId === c.id}
                          onChange={() => toggleActive(c)}
                        />
                        <span className="muted" style={{ fontSize: 12, minWidth: 54 }}>
                          {c.is_active ? "Activa" : "Inactiva"}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 8 }}>
                        <button
                          type="button"
                          onClick={() => openEdit(c)}
                          disabled={busyId === c.id}
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
                          Editar
                        </button>
                        <button
                          type="button"
                          onClick={() => remove(c)}
                          disabled={busyId === c.id}
                          style={{
                            border: "1px solid #fecaca",
                            background: "#fef2f2",
                            color: "#b91c1c",
                            borderRadius: 8,
                            padding: "6px 12px",
                            cursor: "pointer",
                            fontWeight: 500,
                            fontSize: 13,
                          }}
                        >
                          Eliminar
                        </button>
                      </div>
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
