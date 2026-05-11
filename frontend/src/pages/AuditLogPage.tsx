import { FormEvent, useCallback, useEffect, useState } from "react";
import { apiGet } from "../api/client";
import type { AuditLogEntry, Warehouse } from "../types";

export function AuditLogPage() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [warehouseId, setWarehouseId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadWarehouses = useCallback(async () => {
    try {
      const w = await apiGet<Warehouse[]>("/warehouses");
      setWarehouses(w);
    } catch {
      /* optional */
    }
  }, []);

  const loadLog = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const q =
        warehouseId.trim() === ""
          ? "/admin/audit-log?limit=200"
          : `/admin/audit-log?limit=200&warehouse_id=${encodeURIComponent(warehouseId)}`;
      const data = await apiGet<AuditLogEntry[]>(q);
      setEntries(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [warehouseId]);

  useEffect(() => {
    void loadWarehouses();
  }, [loadWarehouses]);

  useEffect(() => {
    void loadLog();
  }, [loadLog]);

  function onFilter(e: FormEvent) {
    e.preventDefault();
    void loadLog();
  }

  return (
    <>
      <h1 className="page-title">Журнал изменений</h1>
      <p className="page-sub">
        События по складам, товарам, остаткам и заказам. Доступно администратору.
      </p>
      {error && <div className="alert">{error}</div>}
      <form onSubmit={onFilter} className="card" style={{ marginBottom: "1rem" }}>
        <div className="grid2">
          <div className="field">
            <label htmlFor="audit-wh">Фильтр по складу</label>
            <select
              id="audit-wh"
              value={warehouseId}
              onChange={(e) => setWarehouseId(e.target.value)}
            >
              <option value="">Все склады</option>
              {warehouses.map((w) => (
                <option key={w.id} value={String(w.id)}>
                  {w.name} (id {w.id})
                </option>
              ))}
            </select>
          </div>
          <div className="field" style={{ display: "flex", alignItems: "flex-end" }}>
            <button type="submit" className="btn">
              Обновить
            </button>
          </div>
        </div>
      </form>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Время (UTC)</th>
              <th>Кто</th>
              <th>Действие</th>
              <th>Сущность</th>
              <th>Склад</th>
              <th>Детали</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="small">
                  Загрузка…
                </td>
              </tr>
            ) : entries.length === 0 ? (
              <tr>
                <td colSpan={6} className="small">
                  Записей нет
                </td>
              </tr>
            ) : (
              entries.map((row) => (
                <tr key={row.id}>
                  <td className="small">{row.created_at}</td>
                  <td>{row.actor_username ?? "—"}</td>
                  <td>
                    <code>{row.action}</code>
                  </td>
                  <td className="small">
                    {row.entity_type}
                    {row.entity_id != null ? ` #${row.entity_id}` : ""}
                  </td>
                  <td>{row.warehouse_id ?? "—"}</td>
                  <td className="small" style={{ maxWidth: "18rem", wordBreak: "break-word" }}>
                    {row.detail ? JSON.stringify(row.detail) : "—"}
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
