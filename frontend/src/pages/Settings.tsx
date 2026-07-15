import { Moon, Sun, User as UserIcon, KeyRound, Palette } from "lucide-react";
import { useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { User } from "../api/types";
import { getStoredTheme, setTheme, type Theme } from "../lib/theme";

type Tab = "perfil" | "password" | "apariencia";

const TABS: { id: Tab; label: string; icon: typeof UserIcon }[] = [
  { id: "perfil", label: "Perfil", icon: UserIcon },
  { id: "password", label: "Contraseña", icon: KeyRound },
  { id: "apariencia", label: "Apariencia", icon: Palette },
];

export default function Settings() {
  const [tab, setTab] = useState<Tab>("perfil");

  return (
    <div className="split-grid" style={{ alignItems: "start" }}>
      <div className="card" style={{ maxWidth: 260 }}>
        <div className="section-head" style={{ marginBottom: 12 }}>
          <h2 style={{ fontSize: 17 }}>Configuración</h2>
        </div>
        <nav className="side-nav" style={{ overflow: "visible" }}>
          {TABS.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                type="button"
                className={"nav-link" + (tab === t.id ? " active" : "")}
                onClick={() => setTab(t.id)}
                style={{ width: "100%", background: "none" }}
              >
                <span className="nav-icon">
                  <Icon size={18} strokeWidth={2.2} />
                </span>
                <span>{t.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div style={{ display: "grid", gap: 20 }}>
        {tab === "perfil" && <ProfileSection />}
        {tab === "password" && <PasswordSection />}
        {tab === "apariencia" && <AppearanceSection />}
      </div>
    </div>
  );
}

function ProfileSection() {
  const { user, updateUser } = useAuth();
  const [form, setForm] = useState({
    first_name: user?.first_name ?? "",
    last_name: user?.last_name ?? "",
    email: user?.email ?? "",
    phone: user?.phone ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [ok, setOk] = useState("");
  const [error, setError] = useState("");

  function set(k: keyof typeof form, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
    setOk("");
    setError("");
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setOk("");
    setError("");
    try {
      const { data } = await api.patch<User>("/users/me/profile/", form);
      updateUser(data);
      setOk("Perfil actualizado correctamente.");
    } catch (err: any) {
      setError(readError(err, "No se pudo actualizar el perfil."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <div className="section-head">
        <div>
          <span className="eyebrow">Cuenta</span>
          <h2 style={{ fontSize: 18 }}>Datos del perfil</h2>
        </div>
      </div>

      <div className="split-grid">
        <div className="field">
          <label>Nombre</label>
          <input
            value={form.first_name}
            onChange={(e) => set("first_name", e.target.value)}
          />
        </div>
        <div className="field">
          <label>Apellido</label>
          <input
            value={form.last_name}
            onChange={(e) => set("last_name", e.target.value)}
          />
        </div>
        <div className="field">
          <label>Correo electrónico</label>
          <input
            type="email"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
          />
        </div>
        <div className="field">
          <label>Teléfono</label>
          <input
            value={form.phone}
            onChange={(e) => set("phone", e.target.value)}
          />
        </div>
      </div>

      <div className="field">
        <label>Usuario</label>
        <input value={user?.username ?? ""} disabled />
        <p className="muted" style={{ fontSize: 12, marginTop: 6 }}>
          El nombre de usuario y el rol solo puede cambiarlos un administrador.
        </p>
      </div>

      {ok && <div style={{ color: "var(--success)", fontWeight: 700, fontSize: 13 }}>{ok}</div>}
      {error && <div className="error-text">{error}</div>}

      <div style={{ marginTop: 16 }}>
        <button className="btn" disabled={saving}>
          {saving ? "Guardando…" : "Guardar cambios"}
        </button>
      </div>
    </form>
  );
}

function PasswordSection() {
  const [form, setForm] = useState({
    current_password: "",
    new_password: "",
    confirm: "",
  });
  const [saving, setSaving] = useState(false);
  const [ok, setOk] = useState("");
  const [error, setError] = useState("");

  function set(k: keyof typeof form, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
    setOk("");
    setError("");
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setOk("");
    setError("");
    if (form.new_password.length < 8) {
      setError("La nueva contraseña debe tener al menos 8 caracteres.");
      return;
    }
    if (form.new_password !== form.confirm) {
      setError("La confirmación no coincide con la nueva contraseña.");
      return;
    }
    setSaving(true);
    try {
      await api.post("/users/me/change-password/", {
        current_password: form.current_password,
        new_password: form.new_password,
      });
      setForm({ current_password: "", new_password: "", confirm: "" });
      setOk("Contraseña actualizada correctamente.");
    } catch (err: any) {
      setError(readError(err, "No se pudo cambiar la contraseña."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card" onSubmit={submit} style={{ maxWidth: 460 }}>
      <div className="section-head">
        <div>
          <span className="eyebrow">Seguridad</span>
          <h2 style={{ fontSize: 18 }}>Cambiar contraseña</h2>
        </div>
      </div>

      <div className="field">
        <label>Contraseña actual</label>
        <input
          type="password"
          value={form.current_password}
          onChange={(e) => set("current_password", e.target.value)}
          autoComplete="current-password"
        />
      </div>
      <div className="field">
        <label>Nueva contraseña</label>
        <input
          type="password"
          value={form.new_password}
          onChange={(e) => set("new_password", e.target.value)}
          autoComplete="new-password"
        />
      </div>
      <div className="field">
        <label>Confirmar nueva contraseña</label>
        <input
          type="password"
          value={form.confirm}
          onChange={(e) => set("confirm", e.target.value)}
          autoComplete="new-password"
        />
      </div>

      {ok && <div style={{ color: "var(--success)", fontWeight: 700, fontSize: 13 }}>{ok}</div>}
      {error && <div className="error-text">{error}</div>}

      <div style={{ marginTop: 16 }}>
        <button className="btn" disabled={saving}>
          {saving ? "Actualizando…" : "Actualizar contraseña"}
        </button>
      </div>
    </form>
  );
}

function AppearanceSection() {
  const [theme, setThemeState] = useState<Theme>(getStoredTheme());

  function choose(next: Theme) {
    setTheme(next);
    setThemeState(next);
  }

  const options: { id: Theme; label: string; hint: string; icon: typeof Sun }[] = [
    { id: "light", label: "Claro", hint: "Fondo claro, ideal de día", icon: Sun },
    { id: "dark", label: "Oscuro", hint: "Menos brillo, ideal de noche", icon: Moon },
  ];

  return (
    <div className="card">
      <div className="section-head">
        <div>
          <span className="eyebrow">Apariencia</span>
          <h2 style={{ fontSize: 18 }}>Tema de la interfaz</h2>
        </div>
      </div>

      <div className="split-grid">
        {options.map((o) => {
          const Icon = o.icon;
          const active = theme === o.id;
          return (
            <button
              key={o.id}
              type="button"
              onClick={() => choose(o.id)}
              className="card"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                textAlign: "left",
                cursor: "pointer",
                borderColor: active ? "var(--supli-blue)" : "var(--border)",
                boxShadow: active
                  ? "0 0 0 3px rgba(41, 168, 242, 0.18)"
                  : "var(--shadow-soft)",
              }}
            >
              <span className="kpi-icon" style={{ margin: 0 }}>
                <Icon size={20} />
              </span>
              <span style={{ display: "grid", gap: 2 }}>
                <span style={{ fontWeight: 800, color: "var(--text)" }}>
                  {o.label}
                </span>
                <span className="muted" style={{ fontSize: 12 }}>
                  {o.hint}
                </span>
              </span>
            </button>
          );
        })}
      </div>

      <p className="muted" style={{ fontSize: 13, marginTop: 14 }}>
        La preferencia se guarda en este navegador y se aplica automáticamente la
        próxima vez que ingreses.
      </p>
    </div>
  );
}

function readError(err: any, fallback: string): string {
  const data = err?.response?.data;
  if (!data) return fallback;
  if (typeof data === "string") return data;
  if (data.detail) return String(data.detail);
  // Toma el primer error de campo devuelto por DRF.
  const first = Object.values(data)[0];
  if (Array.isArray(first)) return String(first[0]);
  if (typeof first === "string") return first;
  return fallback;
}
