import { FormEvent, useCallback, useEffect, useState } from "react";
import { apiDelete, apiGet, apiPatchJson, apiPostJson } from "../api/client";
import type { Product } from "../types";

export function ProductsPage() {
  const [items, setItems] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [unit, setUnit] = useState("шт");
  const [editing, setEditing] = useState<Product | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await apiGet<Product[]>("/products");
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
      await apiPostJson("/products", { sku, name, unit });
      setSku("");
      setName("");
      setUnit("шт");
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
      await apiPatchJson(`/products/${editing.id}`, { sku: editing.sku, name: editing.name, unit: editing.unit });
      setEditing(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function onDelete(id: number) {
    if (!confirm("Удалить товар?")) return;
    setError(null);
    try {
      await apiDelete(`/products/${id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  return (
    <>
      <h1 className="page-title">Товары</h1>
      <p className="page-sub">Справочник номенклатуры. Код SKU должен быть уникальным.</p>
      {error && <div className="alert">{error}</div>}
      <div className="card">
        <h2>{editing ? "Редактирование" : "Новый товар"}</h2>
        {!editing ? (
          <form onSubmit={onCreate} className="grid2">
            <div className="field">
              <label htmlFor="sku">SKU</label>
              <input id="sku" value={sku} onChange={(e) => setSku(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="name">Наименование</label>
              <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="unit">Ед. учёта</label>
              <input id="unit" value={unit} onChange={(e) => setUnit(e.target.value)} />
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
              <label>SKU</label>
              <input
                value={editing.sku}
                onChange={(e) => setEditing({ ...editing, sku: e.target.value })}
                required
              />
            </div>
            <div className="field">
              <label>Наименование</label>
              <input
                value={editing.name}
                onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                required
              />
            </div>
            <div className="field">
              <label>Ед. учёта</label>
              <input
                value={editing.unit}
                onChange={(e) => setEditing({ ...editing, unit: e.target.value })}
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
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>SKU</th>
              <th>Наименование</th>
              <th>Ед.</th>
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
              items.map((p) => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{p.sku}</td>
                  <td>{p.name}</td>
                  <td>{p.unit}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="btn ghost" onClick={() => setEditing(p)}>
                        Изменить
                      </button>
                      <button type="button" className="btn ghost danger" onClick={() => void onDelete(p.id)}>
                        Удалить
                      </button>
                    </div>
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
