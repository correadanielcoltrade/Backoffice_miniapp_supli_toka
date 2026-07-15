import { Eye, EyeOff, Lock, ShieldCheck, UserRound } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import logoSupli from "../assets/logo-supli-web.png";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch {
      setError("Usuario o contraseña incorrectos.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-wrap">
      <span className="login-blob one" aria-hidden="true" />
      <span className="login-blob two" aria-hidden="true" />
      <span className="login-blob three" aria-hidden="true" />

      <header className="login-topbar">
        <span className="login-badge">
          <ShieldCheck size={15} />
          Plataforma de control
        </span>
      </header>

      <div className="login-content">
        <form className="login-card" onSubmit={onSubmit}>
          <div className="login-avatar">
            <img src={logoSupli} alt="Supli" />
          </div>
          <h2>Iniciar sesión</h2>
          <p className="login-sub">
            Ingresa para gestionar los pedidos de la Mini App
          </p>

          <div className="input-with-icon">
            <UserRound size={17} />
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Usuario"
              aria-label="Usuario"
              autoComplete="username"
              autoFocus
            />
          </div>

          <div className="input-with-icon">
            <Lock size={17} />
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Contraseña"
              aria-label="Contraseña"
              autoComplete="current-password"
            />
            <button
              type="button"
              className="input-eye"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={
                showPassword ? "Ocultar contraseña" : "Mostrar contraseña"
              }
            >
              {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
            </button>
          </div>

          {error && <div className="error-text">{error}</div>}

          <button className="btn login-submit" disabled={loading}>
            {loading ? "Ingresando…" : "Iniciar sesión"}
          </button>

          <p className="login-foot">
            <Lock size={13} />
            Conexión segura · Acceso restringido
          </p>
        </form>

        <div className="login-welcome">
          <h1>
            Back Office
            <br />
            MiniApp Supli-Toka
          </h1>
          <p>
            La herramienta donde llegan y se gestionan los pedidos de la Mini
            App: catálogo, inventario, pagos, logística inversa y reportes, todo
            desde un solo lugar.
          </p>
        </div>
      </div>
    </div>
  );
}
