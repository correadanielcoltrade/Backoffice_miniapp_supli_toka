import { useState } from "react";
import { api } from "../api/client";
import { useList } from "../api/useList";
import type { User } from "../api/types";

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
};

export default function Users() {
  const { data, loading, error, reload } = useList<User>("/users/");
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [showForm, setShowForm] = useState(false);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      await api.post("/users/", form);
      setForm(EMPTY);
      setShowForm(false);
      reload();
    } catch (err: any) {
      setFormError(
        JSON.stringify(err.response?.data ?? "Error al crear el usuario")
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card">
      <div className="section-head">
        <h2>Administrador de Usuarios y Roles</h2>
        <button className="btn" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cerrar" : "+ Nuevo usuario"}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={create}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 14,
            marginBottom: 24,
          }}
        >
          <Input label="Usuario" v={form.username} on={(v) => setForm({ ...form, username: v })} />
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
            label="Contraseña"
            type="password"
            v={form.password}
            on={(v) => setForm({ ...form, password: v })}
          />
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <button className="btn" disabled={saving}>
              {saving ? "Guardando…" : "Crear usuario"}
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
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {data.map((u) => (
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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
