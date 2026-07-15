import { LogOut } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import logoSupli from "../assets/logo-supli-web.png";
import { useAuth } from "../auth/AuthContext";
import { NAV_ITEMS, canSee } from "./nav";

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const items = NAV_ITEMS.filter((i) => user && canSee(i, user.role));
  const current =
    items.find((i) => i.to === location.pathname)?.label ?? "Back Office";
  const initials = (user?.first_name || user?.username || "S")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-panel">
          <img src={logoSupli} alt="Supli" className="brand-logo" />
          <span>Back Office Toka</span>
        </div>

        <nav className="side-nav" aria-label="Modulos">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  "nav-link" + (isActive ? " active" : "")
                }
              >
                <span className="nav-icon">
                  <Icon size={18} strokeWidth={2.2} />
                </span>
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="user-avatar">{initials}</div>
          <div className="user-copy">
            <div className="user-name">{user?.first_name || user?.username}</div>
            <div>{user?.role_display}</div>
          </div>
          <button className="logout-btn" onClick={logout} aria-label="Cerrar sesion">
            <LogOut size={17} />
          </button>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div>
            <span className="eyebrow">Modulo actual</span>
            <h1>{current}</h1>
          </div>
          <div className="topbar-actions">
            <span className="role-chip">{user?.role_display}</span>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
