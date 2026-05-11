import { FormEvent, useCallback, useEffect, useState } from "react";
import { apiDelete, apiGet, apiPostEmpty, apiPostForJson, apiPostJson } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { UserAdminRow, UserRole } from "../types";

export function UsersAdminPage() {
  const { user: currentUser } = useAuth();
  const [items, setItems] = useState<UserAdminRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("worker");

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await apiGet<UserAdminRow[]>("/admin/users");
      setItems(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await apiPostJson<UserAdminRow>("/admin/users", {
        username: username.trim(),
        password,
        role,
      });
      setUsername("");
      setPassword("");
      setRole("worker");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function onDeactivate(userId: number) {
    if (!confirm("Отключить пользователя? Вход будет невозможен, участие на складах снимется.")) return;
    setError(null);
    try {
      await apiPostEmpty(`/admin/users/${userId}/deactivate`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function onActivate(userId: number) {
    setError(null);
    try {
      await apiPostForJson<UserAdminRow>(`/admin/users/${userId}/activate`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function onDeletePermanent(userId: number, login: string) {
    if (
      !confirm(
        `Полностью удалить пользователя «${login}» из базы? Действие необратимо (история аудита сохранит действия без привязки к учётке).`,
      )
    ) {
      return;
    }
    setError(null);
    try {
      await apiDelete(`/admin/users/${userId}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  return (
    <>
      <h1 className="page-title">Пользователи</h1>
      <p className="page-sub">
        Создание учётных записей, отключение и повторное включение входа, полное удаление записи. Нельзя удалить или
        отключить последнего администратора и свою учётку (отключение / удаление).
      </p>
      {error && <div className="alert">{error}</div>}

      <div className="card" style={{ marginBottom: "1rem" }}>
        <h2>Новый пользователь</h2>
        <form onSubmit={onCreate} className="grid2">
          <div className="field">
            <label htmlFor="nu-login">Логин</label>
            <input
              id="nu-login"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="off"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="nu-pass">Пароль</label>
            <input
              id="nu-pass"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              minLength={6}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="nu-role">Роль</label>
            <select id="nu-role" value={role} onChange={(e) => setRole(e.target.value as UserRole)}>
              <option value="worker">Рабочий</option>
              <option value="admin">Администратор</option>
            </select>
          </div>
          <div className="field" style={{ display: "flex", alignItems: "flex-end" }}>
            <button type="submit" className="btn">
              Создать
            </button>
          </div>
        </form>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Логин</th>
              <th>Роль</th>
              <th>Статус</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="small">
                  Загрузка…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={5} className="small">
                  Нет записей
                </td>
              </tr>
            ) : (
              items.map((u) => (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td>{u.username}</td>
                  <td>{u.role === "admin" ? "Администратор" : "Рабочий"}</td>
                  <td>{u.is_active ? "Активен" : "Отключён"}</td>
                  <td>
                    {u.id === currentUser?.id ? (
                      <span className="small">Это вы</span>
                    ) : (
                      <div className="row-actions">
                        {u.is_active ? (
                          <button
                            type="button"
                            className="btn ghost danger"
                            onClick={() => void onDeactivate(u.id)}
                          >
                            Отключить
                          </button>
                        ) : (
                          <button type="button" className="btn ghost" onClick={() => void onActivate(u.id)}>
                            Включить
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn ghost danger"
                          onClick={() => void onDeletePermanent(u.id, u.username)}
                        >
                          Удалить
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
