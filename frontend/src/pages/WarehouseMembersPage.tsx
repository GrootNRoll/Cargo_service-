import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiDelete, apiGet, apiPostJson } from "../api/client";
import type { UserPublic } from "../types";

export function WarehouseMembersPage() {
  const { warehouseId } = useParams<{ warehouseId: string }>();
  const wid = warehouseId ? Number.parseInt(warehouseId, 10) : NaN;
  const [members, setMembers] = useState<UserPublic[]>([]);
  const [users, setUsers] = useState<UserPublic[]>([]);
  const [addUserId, setAddUserId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!Number.isFinite(wid)) {
      setError("Некорректный id склада");
      setLoading(false);
      return;
    }
    setError(null);
    try {
      const [m, u] = await Promise.all([
        apiGet<UserPublic[]>(`/warehouses/${wid}/members`),
        apiGet<UserPublic[]>("/admin/users?active_only=true"),
      ]);
      setMembers(m);
      setUsers(u);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [wid]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onAdd(e: FormEvent) {
    e.preventDefault();
    if (!Number.isFinite(wid) || addUserId === "") return;
    setError(null);
    try {
      await apiPostJson(`/warehouses/${wid}/members`, { user_id: Number.parseInt(addUserId, 10) });
      setAddUserId("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function onRemove(userId: number) {
    if (!Number.isFinite(wid) || !confirm("Убрать участника со склада?")) return;
    setError(null);
    try {
      await apiDelete(`/warehouses/${wid}/members/${userId}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  const memberIds = new Set(members.map((m) => m.id));
  const candidates = users.filter((u) => !memberIds.has(u.id));

  if (!Number.isFinite(wid)) {
    return <p className="page-sub">Некорректная ссылка.</p>;
  }

  return (
    <>
      <p className="small" style={{ marginBottom: "0.5rem" }}>
        <Link to="/warehouses">← Склады</Link>
      </p>
      <h1 className="page-title">Участники склада #{wid}</h1>
      <p className="page-sub">Назначение пользователей на площадку. Список и изменения доступны администратору.</p>
      {error && <div className="alert">{error}</div>}

      <div className="card" style={{ marginBottom: "1rem" }}>
        <h2>Добавить участника</h2>
        <form onSubmit={onAdd} className="grid2">
          <div className="field">
            <label htmlFor="add-user">Пользователь</label>
            <select
              id="add-user"
              value={addUserId}
              onChange={(e) => setAddUserId(e.target.value)}
              required
            >
              <option value="">— выберите —</option>
              {candidates.map((u) => (
                <option key={u.id} value={String(u.id)}>
                  {u.username} ({u.role})
                </option>
              ))}
            </select>
          </div>
          <div className="field" style={{ display: "flex", alignItems: "flex-end" }}>
            <button type="submit" className="btn" disabled={candidates.length === 0}>
              Добавить
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
              <th />
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="small">
                  Загрузка…
                </td>
              </tr>
            ) : members.length === 0 ? (
              <tr>
                <td colSpan={4} className="small">
                  Участников пока нет
                </td>
              </tr>
            ) : (
              members.map((m) => (
                <tr key={m.id}>
                  <td>{m.id}</td>
                  <td>{m.username}</td>
                  <td>{m.role}</td>
                  <td>
                    <button type="button" className="btn ghost danger" onClick={() => void onRemove(m.id)}>
                      Убрать
                    </button>
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
