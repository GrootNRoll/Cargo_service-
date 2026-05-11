import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth, useIsAdmin } from "../auth/AuthContext";
import { SiteFooter } from "./SiteFooter";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? "active" : undefined;

const roleLabel = (role: string) => (role === "admin" ? "Администратор" : "Рабочий");

export function Layout() {
  const { user, logout } = useAuth();
  const isAdmin = useIsAdmin();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    void navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">Учёт склада</div>
        <nav className="sidebar-nav">
          <NavLink to="/" end className={linkClass}>
            Обзор
          </NavLink>
          <NavLink to="/products" className={linkClass}>
            Товары
          </NavLink>
          <NavLink to="/stock" className={linkClass}>
            Остатки
          </NavLink>
          <NavLink to="/orders" className={linkClass}>
            Заказы
          </NavLink>
          <NavLink to="/warehouses" className={linkClass}>
            Склады
          </NavLink>
          {isAdmin && (
            <NavLink to="/users" className={linkClass}>
              Пользователи
            </NavLink>
          )}
          {isAdmin && (
            <NavLink to="/audit" className={linkClass}>
              Журнал
            </NavLink>
          )}
        </nav>
        <div className="sidebar-footer small">
          {isAdmin ? "Все разделы доступны" : "Редактирование складов — только у администратора"}
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <div className="topbar-user">
            <span className="username">{user?.username}</span>
            <span className={`role-pill ${isAdmin ? "admin" : ""}`}>{user ? roleLabel(user.role) : ""}</span>
            <button type="button" className="btn ghost" onClick={handleLogout}>
              Выйти
            </button>
          </div>
        </header>
        <main className="main-content">
          <Outlet />
        </main>
        <SiteFooter />
      </div>
    </div>
  );
}
