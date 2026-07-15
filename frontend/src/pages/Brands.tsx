import { useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { Brand } from "../api/types";
import { Switch } from "../components/Switch";

const API_ORIGIN = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api")
  .replace(/\/api\/?$/, "");

const EMPTY = { name: "", sort_order: "0", is_active: true };

function logoUrl(logo: string | null): string | null {
  if (!logo) return null;
  return logo.startsWith("http") ? logo : API_ORIGIN + logo;
}

export default function Brands() {
  const { data, loading, error, reload } = useList<Brand>("/brands/");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(EMPTY);
  const [logo, setLogo] = useState<File | null>(null);
  const [currentLogo, setCurrentLogo] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  function openCreate() {
    setEditingId(null);
    setForm(EMPTY);
    setLogo(null);
    setCurrentLogo(null);
    setFormError("");
    setShowForm(true);
  }

  function openEdit(b: Brand) {
    setEditingId(b.id);
    setForm({
      name: b.name,
      sort_order: String(b.sort_order),
      is_active: b.is_active,
    });
    setLogo(null);
    setCurrentLogo(b.logo);
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
      if (logo) fd.append("logo", logo);
      const cfg = { headers: { "Content-Type": "multipart/form-data" } };
      if (editingId) {
        await api.patch(`/brands/${editingId}/`, fd, cfg);
      } else {
        await api.post("/brands/", fd, cfg);
      }
      setShowForm(false);
      setEditingId(null);
      setForm(EMPTY);
      setLogo(null);
      reload();
    } catch (err: any) {
      setFormError(JSON.stringify(err.response?.data ?? "Error"));
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(b: Brand) {
    setBusyId(b.id);
    setActionError("");
    try {
      await api.patch(`/brands/${b.id}/`, { is_active: !b.is_active });
      reload();
    } catch {
      setActionError(`No se pudo cambiar el estado de "${b.name}".`);
    } finally {
      setBusyId(null);
    }
  }

  async function remove(b: Brand) {
    if (!window.confirm(`¿Eliminar la marca "${b.name}"?`)) return;
    setBusyId(b.id);
    setActionError("");
    try {
      await api.delete(`/brands/${b.id}/`);
      reload();
    } catch (err: any) {
      const st = err.response?.status;
      if (st === 400 || st === 409 || st === 500) {
        setActionError(
          `No se puede eliminar "${b.name}" porque tiene productos asociados. Desactívala con el switch en su lugar.`
        );
      } else {
        setActionError(`No se pudo eliminar "${b.name}".`);
      }
    } finally {
      setBusyId(null);
    }
  }

  const preview = logo ? URL.createObjectURL(logo) : logoUrl(currentLogo);

  return (
    <div className="card">
      <div className="section-head">
        <h2>Gestión de Marcas</h2>
        {showForm ? (
          <button className="btn" onClick={() => setShowForm(false)}>
            Cerrar
          </button>
        ) : (
          <button className="btn" onClick={openCreate}>
            + Nueva marca
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

          <label style={{ marginTop: 6 }}>Logo de la marca</label>
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
                <span className="muted">+ Logo</span>
              )}
              <input
                type="file"
                accept="image/*"
                style={{ display: "none" }}
                onChange={(e) => setLogo(e.target.files?.[0] ?? null)}
              />
            </label>
            {editingId && (
              <span className="muted" style={{ fontSize: 13 }}>
                Deja el logo vacío para conservar el actual.
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
              (las marcas activas se muestran en la app)
            </span>
          </div>

          <button className="btn" disabled={saving}>
            {saving ? "Guardando…" : editingId ? "Guardar cambios" : "Crear marca"}
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
                <th>Logo</th>
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
                .map((b) => (
                  <tr key={b.id} style={{ opacity: b.is_active ? 1 : 0.55 }}>
                    <td>
                      {logoUrl(b.logo) ? (
                        <img
                          src={logoUrl(b.logo)!}
                          alt=""
                          style={{ width: 36, height: 36, objectFit: "cover", borderRadius: 8 }}
                        />
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td style={{ fontWeight: 500 }}>{b.name}</td>
                    <td>{b.sort_order}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <Switch
                          checked={b.is_active}
                          busy={busyId === b.id}
                          onChange={() => toggleActive(b)}
                        />
                        <span className="muted" style={{ fontSize: 12, minWidth: 54 }}>
                          {b.is_active ? "Activa" : "Inactiva"}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 8 }}>
                        <button
                          type="button"
                          onClick={() => openEdit(b)}
                          disabled={busyId === b.id}
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
                          onClick={() => remove(b)}
                          disabled={busyId === b.id}
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
