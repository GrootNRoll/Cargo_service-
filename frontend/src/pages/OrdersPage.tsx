import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPostJson, transitionOrder } from "../api/client";
import type { Order, OrderStatus, Product, Warehouse } from "../types";

type LineDraft = { product_id: number; quantity: number; unit_price: string };

function statusClass(s: OrderStatus): string {
  if (s === "fulfilled") return "badge ok";
  if (s === "cancelled") return "badge neutral";
  if (s === "confirmed") return "badge warn";
  return "badge";
}

export function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [warehouseId, setWarehouseId] = useState("");
  const [lines, setLines] = useState<LineDraft[]>([
    { product_id: 0, quantity: 1, unit_price: "0" },
  ]);

  const whName = useMemo(() => {
    const m = new Map(warehouses.map((w) => [w.id, w.name] as const));
    return (id: number) => m.get(id) ?? `#${id}`;
  }, [warehouses]);

  const prodSku = useMemo(() => {
    const m = new Map(products.map((p) => [p.id, p.sku] as const));
    return (id: number) => m.get(id) ?? `#${id}`;
  }, [products]);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [o, w, p] = await Promise.all([
        apiGet<Order[]>("/orders"),
        apiGet<Warehouse[]>("/warehouses"),
        apiGet<Product[]>("/products"),
      ]);
      setOrders(o);
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

  function setLine(i: number, patch: Partial<LineDraft>) {
    setLines((prev) => prev.map((row, idx) => (idx === i ? { ...row, ...patch } : row)));
  }

  function addLine() {
    setLines((prev) => [...prev, { product_id: 0, quantity: 1, unit_price: "0" }]);
  }

  function removeLine(i: number) {
    setLines((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const wid = Number(warehouseId);
    if (!Number.isFinite(wid)) {
      setError("Выберите склад");
      return;
    }
    const cleaned = lines
      .filter((l) => l.product_id > 0 && l.quantity > 0)
      .map((l) => ({
        product_id: l.product_id,
        quantity: l.quantity,
        unit_price: l.unit_price,
      }));
    if (cleaned.length === 0) {
      setError("Добавьте хотя бы одну позицию с товаром");
      return;
    }
    try {
      await apiPostJson("/orders", {
        warehouse_id: wid,
        status: "draft",
        lines: cleaned,
      });
      setWarehouseId("");
      setLines([{ product_id: 0, quantity: 1, unit_price: "0" }]);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function onDelete(id: number) {
    if (!confirm("Удалить черновик заказа?")) return;
    setError(null);
    try {
      await apiDelete(`/orders/${id}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function doTransition(id: number, to: OrderStatus) {
    setError(null);
    try {
      await transitionOrder(id, to);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  return (
    <>
      <h1 className="page-title">Заказы</h1>
      <p className="page-sub">
        Создание заказа, смена статуса и отгрузка со списанием остатков на выбранном складе.
      </p>
      {error && <div className="alert">{error}</div>}
      <div className="card">
        <h2>Новый заказ (черновик)</h2>
        <form onSubmit={onCreate} className="stack">
          <div className="field">
            <label htmlFor="ord-wh">Склад отгрузки</label>
            <select
              id="ord-wh"
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
          <div className="stack">
            {lines.map((line, i) => (
              <div key={i} className="grid2" style={{ alignItems: "end" }}>
                <div className="field">
                  <label>Товар</label>
                  <select
                    value={line.product_id || ""}
                    onChange={(e) => setLine(i, { product_id: Number(e.target.value) })}
                  >
                    <option value={0}>— выберите —</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.sku} — {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Кол-во</label>
                  <input
                    type="number"
                    min={1}
                    value={line.quantity}
                    onChange={(e) => setLine(i, { quantity: Number(e.target.value) })}
                  />
                </div>
                <div className="field">
                  <label>Цена за ед.</label>
                  <input
                    value={line.unit_price}
                    onChange={(e) => setLine(i, { unit_price: e.target.value })}
                  />
                </div>
                <div className="row-actions">
                  <button type="button" className="btn secondary" onClick={() => removeLine(i)}>
                    Строка −
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="row-actions">
            <button type="button" className="btn secondary" onClick={addLine}>
              Добавить строку
            </button>
            <button type="submit" className="btn">
              Создать заказ
            </button>
          </div>
        </form>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Склад</th>
              <th>Статус</th>
              <th>Позиции</th>
              <th>Дата</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="small">
                  Загрузка…
                </td>
              </tr>
            ) : orders.length === 0 ? (
              <tr>
                <td colSpan={6} className="small">
                  Нет заказов
                </td>
              </tr>
            ) : (
              orders.map((o) => (
                <tr key={o.id}>
                  <td>{o.id}</td>
                  <td>{whName(o.warehouse_id)}</td>
                  <td>
                    <span className={statusClass(o.status)}>{o.status}</span>
                  </td>
                  <td className="small">
                    {o.lines.map((l) => (
                      <div key={l.id}>
                        {prodSku(l.product_id)} × {l.quantity} @ {l.unit_price}
                      </div>
                    ))}
                  </td>
                  <td className="small">{new Date(o.created_at).toLocaleString()}</td>
                  <td>
                    <div className="row-actions">
                      {o.status === "draft" && (
                        <>
                          <button
                            type="button"
                            className="btn ghost"
                            onClick={() => void doTransition(o.id, "confirmed")}
                          >
                            Подтвердить
                          </button>
                          <button
                            type="button"
                            className="btn ghost danger"
                            onClick={() => void doTransition(o.id, "cancelled")}
                          >
                            Отменить
                          </button>
                          <button type="button" className="btn ghost danger" onClick={() => void onDelete(o.id)}>
                            Удалить
                          </button>
                        </>
                      )}
                      {o.status === "confirmed" && (
                        <>
                          <button
                            type="button"
                            className="btn ghost"
                            onClick={() => void doTransition(o.id, "fulfilled")}
                          >
                            Отгрузить
                          </button>
                          <button
                            type="button"
                            className="btn ghost danger"
                            onClick={() => void doTransition(o.id, "cancelled")}
                          >
                            Отменить
                          </button>
                        </>
                      )}
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
