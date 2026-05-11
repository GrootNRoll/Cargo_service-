import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useIsAdmin } from "../auth/AuthContext";
import { apiDelete, apiGet, apiPatchJson, apiPostJson } from "../api/client";
import type { Warehouse } from "../types";

export function WarehousesPage() {
  const isAdmin = useIsAdmin();
  const [items, setItems] = useState<Warehouse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [editing, setEditing] = useState<Warehouse | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await apiGet<Warehouse[]>("/warehouses");
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
      await apiPostJson("/warehouses", {
        name,
        address: address.trim() === "" ? null : address,
      });
      setName("");
      setAddress("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function onUpdate(e: FormEvent) {
    e.preventDefault();
    if (!editing) return;
    setError(null);
    try {
      await apiPatchJson(`/warehouses/${editing.id}`, {
        name: editing.name,
        address: editing.address,
      });
      setEditing(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function onDelete(id: number) {
    if (!confirm("Удалить склад? Связанные остатки будут удалены каскадно.")) return;
    setError(null);
    try {
      await apiDelete(`/warehouses/${id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  return (
    <>
      <h1 className="page-title">Склады</h1>
      <p className="page-sub">
        {isAdmin
          ? "Создание и изменение площадок хранения."
          : "Просмотр справочника. Создание и редактирование складов доступны администратору."}
      </p>
      {error && <div className="alert">{error}</div>}
      {isAdmin && (
        <div className="card">
          <h2>{editing ? "Редактирование" : "Новый склад"}</h2>
          {!editing ? (
            <form onSubmit={onCreate} className="grid2">
              <div className="field">
                <label htmlFor="wh-name">Название</label>
                <input id="wh-name" value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="wh-addr">Адрес (необязательно)</label>
                <input id="wh-addr" value={address} onChange={(e) => setAddress(e.target.value)} />
              </div>
              <div className="field" style={{ display: "flex", alignItems: "flex-end" }}>
                <button type="submit" className="btn">
                  Добавить
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={onUpdate} className="grid2">
              <div className="field">
                <label>Название</label>
                <input
                  value={editing.name}
                  onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                  required
                />
              </div>
              <div className="field">
                <label>Адрес</label>
                <input
                  value={editing.address ?? ""}
                  onChange={(e) =>
                    setEditing({
                      ...editing,
                      address: e.target.value.trim() === "" ? null : e.target.value,
                    })
                  }
                />
              </div>
              <div className="field" style={{ display: "flex", alignItems: "flex-end", gap: "0.5rem" }}>
                <button type="submit" className="btn">
                  Сохранить
                </button>
                <button type="button" className="btn secondary" onClick={() => setEditing(null)}>
                  Отмена
                </button>
              </div>
            </form>
          )}
        </div>
      )}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th>Адрес</th>
              <th>Участники</th>
              {isAdmin && <th />}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={isAdmin ? 5 : 4} className="small">
                  Загрузка…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={isAdmin ? 5 : 4} className="small">
                  Нет записей
                </td>
              </tr>
            ) : (
              items.map((w) => (
                <tr key={w.id}>
                  <td>{w.id}</td>
                  <td>{w.name}</td>
                  <td>{w.address ?? "—"}</td>
                  <td className="small">{w.member_count}</td>
                  {isAdmin && (
                    <td>
                      <div className="row-actions">
                        <Link to={`/warehouses/${w.id}/members`} className="btn ghost">
                          Участники
                        </Link>
                        <button type="button" className="btn ghost" onClick={() => setEditing(w)}>
                          Изменить
                        </button>
                        <button type="button" className="btn ghost danger" onClick={() => void onDelete(w.id)}>
                          Удалить
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
