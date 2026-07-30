import { useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { User } from "../api/types";
import { Pagination, usePagination } from "../components/Pagination";
import { Switch } from "../components/Switch";

const ROLES = [
  { value: "ADMINISTRADOR", label: "Administrador" },
  { value: "PROCUREMENT", label: "Procurement" },
  { value: "LOGISTIC", label: "Logistic" },
  { value: "SALES", label: "Sales" },
];

const EMPTY = {
  username: "",
  email: "",
  first_name: "",
  last_name: "",
  phone: "",
  role: "SALES",
  password: "",
  is_active: true,
};

export default function Users() {
  const { data, loading, error, reload } = useList<User>("/users/");
  const pg = usePagination(data);
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [showForm, setShowForm] = useState(false);

  function openCreate() {
    setEditingId(null);
    setForm(EMPTY);
    setFormError("");
    setShowForm(true);
  }

  function openEdit(u: User) {
    setEditingId(u.id);
    setForm({
      username: u.username,
      email: u.email,
      first_name: u.first_name,
      last_name: u.last_name,
      phone: u.phone ?? "",
      role: u.role,
      password: "",
      is_active: u.is_active,
    });
    setFormError("");
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      if (editingId) {
        // El username no se edita (es el identificador). La contraseña solo se
        // envía si se escribió una nueva; vacía = conservar la actual.
        const { username: _u, password, ...rest } = form;
        const body = password ? { ...rest, password } : rest;
        await api.patch(`/users/${editingId}/`, body);
      } else {
        await api.post("/users/", form);
      }
      setForm(EMPTY);
      setEditingId(null);
      setShowForm(false);
      reload();
    } catch (err: any) {
      setFormError(
        JSON.stringify(err.response?.data ?? "Error al guardar el usuario")
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card">
      <div className="section-head">
        <h2>Administrador de Usuarios y Roles</h2>
        {showForm ? (
          <button className="btn secondary" onClick={() => setShowForm(false)}>
            Cerrar
          </button>
        ) : (
          <button className="btn" onClick={openCreate}>
            + Nuevo usuario
          </button>
        )}
      </div>

      {showForm && (
        <form
          onSubmit={save}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 14,
            marginBottom: 24,
          }}
        >
          <div className="field">
            <label>
              Usuario{" "}
              {editingId && (
                <span className="muted" style={{ fontWeight: 400 }}>
                  — no editable
                </span>
              )}
            </label>
            <input
              value={form.username}
              disabled={!!editingId}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              style={editingId ? { background: "#f3f4f6" } : undefined}
            />
          </div>
          <Input label="Correo" v={form.email} on={(v) => setForm({ ...form, email: v })} />
          <Input label="Nombre" v={form.first_name} on={(v) => setForm({ ...form, first_name: v })} />
          <Input label="Apellido" v={form.last_name} on={(v) => setForm({ ...form, last_name: v })} />
          <Input label="Teléfono" v={form.phone} on={(v) => setForm({ ...form, phone: v })} />
          <div className="field">
            <label>Rol</label>
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
            >
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          <Input
            label={editingId ? "Contraseña (dejar vacío para conservar)" : "Contraseña"}
            type="password"
            v={form.password}
            on={(v) => setForm({ ...form, password: v })}
          />
          <div className="field">
            <label>Estado</label>
            <div style={{ display: "flex", alignItems: "center", gap: 10, height: 38 }}>
              <Switch
                checked={form.is_active}
                onChange={() => setForm({ ...form, is_active: !form.is_active })}
              />
              <span style={{ fontWeight: 500 }}>
                {form.is_active ? "Activo" : "Inactivo"}
              </span>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <button className="btn" disabled={saving}>
              {saving
                ? "Guardando…"
                : editingId
                ? "Guardar cambios"
                : "Crear usuario"}
            </button>
          </div>
          {formError && (
            <div className="error-text" style={{ gridColumn: "1 / -1" }}>
              {formError}
            </div>
          )}
        </form>
      )}

      {loading && <div className="loading">Cargando…</div>}
      {error && <div className="error-text">{error}</div>}

      {!loading && !error && (
        <>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {pg.pageItems.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>
                    {u.first_name} {u.last_name}
                  </td>
                  <td>{u.email}</td>
                  <td>
                    <span className="badge blue">{u.role_display}</span>
                  </td>
                  <td>
                    <span className={"badge " + (u.is_active ? "green" : "gray")}>
                      {u.is_active ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td>
                    <button
                      type="button"
                      onClick={() => openEdit(u)}
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pagination pg={pg} />
        </>
      )}
    </div>
  );
}

function Input({
  label,
  v,
  on,
  type = "text",
}: {
  label: string;
  v: string;
  on: (v: string) => void;
  type?: string;
}) {
  return (
    <div className="field">
      <label>{label}</label>
      <input type={type} value={v} onChange={(e) => on(e.target.value)} />
    </div>
  );
}
