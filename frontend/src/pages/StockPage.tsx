import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPatchJson, apiPostJson } from "../api/client";
import type { Product, StockItem, Warehouse } from "../types";

export function StockPage() {
  const [stock, setStock] = useState<StockItem[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [warehouseId, setWarehouseId] = useState("");
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState("0");
  const [editing, setEditing] = useState<StockItem | null>(null);

  const whName = useMemo(() => {
    const m = new Map(warehouses.map((w) => [w.id, w.name] as const));
    return (id: number) => m.get(id) ?? `#${id}`;
  }, [warehouses]);

  const prodName = useMemo(() => {
    const m = new Map(products.map((p) => [p.id, `${p.sku} — ${p.name}`] as const));
    return (id: number) => m.get(id) ?? `#${id}`;
  }, [products]);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [s, w, p] = await Promise.all([
        apiGet<StockItem[]>("/stock"),
        apiGet<Warehouse[]>("/warehouses"),
        apiGet<Product[]>("/products"),
      ]);
      setStock(s);
      setWarehouses(w);
      setProducts(p);
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
    const wid = Number(warehouseId);
    const pid = Number(productId);
    const qty = Number(quantity);
    if (!Number.isFinite(wid) || !Number.isFinite(pid) || !Number.isFinite(qty)) {
      setError("Проверьте числовые поля");
      return;
    }
    try {
      await apiPostJson("/stock", { warehouse_id: wid, product_id: pid, quantity: qty });
      setWarehouseId("");
      setProductId("");
      setQuantity("0");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function onUpdate(e: FormEvent) {
    e.preventDefault();
    if (!editing) return;
    setError(null);
    const qty = Number(editing.quantity);
    if (!Number.isFinite(qty) || qty < 0) {
      setError("Некорректное количество");
      return;
    }
    try {
      await apiPatchJson(`/stock/${editing.id}`, { quantity: qty });
      setEditing(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function onDelete(id: number) {
    if (!confirm("Удалить запись об остатке?")) return;
    setError(null);
    try {
      await apiDelete(`/stock/${id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  return (
    <>
      <h1 className="page-title">Остатки</h1>
      <p className="page-sub">Остатки в разрезе склада и товара (уникальная пара).</p>
      {error && <div className="alert">{error}</div>}
      <div className="card">
        <h2>{editing ? "Изменить количество" : "Новая запись"}</h2>
        {!editing ? (
          <form onSubmit={onCreate} className="grid2">
            <div className="field">
              <label htmlFor="st-wh">Склад</label>
              <select
                id="st-wh"
                value={warehouseId}
                onChange={(e) => setWarehouseId(e.target.value)}
                required
              >
                <option value="">— выберите —</option>
                {warehouses.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="st-pr">Товар</label>
              <select
                id="st-pr"
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                required
              >
                <option value="">— выберите —</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.sku} — {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="st-qty">Количество</label>
              <input
                id="st-qty"
                type="number"
                min={0}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
              />
            </div>
            <div className="field" style={{ display: "flex", alignItems: "flex-end" }}>
              <button type="submit" className="btn">
                Добавить
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={onUpdate} className="grid2">
            <div className="field small">
              {whName(editing.warehouse_id)} · {prodName(editing.product_id)}
            </div>
            <div className="field">
              <label>Количество</label>
              <input
                type="number"
                min={0}
                value={editing.quantity}
                onChange={(e) =>
                  setEditing({ ...editing, quantity: Number(e.target.value) })
                }
                required
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
              <th>Склад</th>
              <th>Товар</th>
              <th>Кол-во</th>
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
            ) : stock.length === 0 ? (
              <tr>
                <td colSpan={5} className="small">
                  Нет записей
                </td>
              </tr>
            ) : (
              stock.map((row) => (
                <tr key={row.id}>
                  <td>{row.id}</td>
                  <td>{whName(row.warehouse_id)}</td>
                  <td className="small">{prodName(row.product_id)}</td>
                  <td>{row.quantity}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="btn ghost" onClick={() => setEditing(row)}>
                        Изменить
                      </button>
                      <button type="button" className="btn ghost danger" onClick={() => void onDelete(row.id)}>
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
