import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api/client";
import type { Summary } from "../types";

export function Home() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const s = await apiGet<Summary>("/summary");
      setSummary(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить сводку");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <>
      <h1 className="page-title">Обзор</h1>
      <p className="page-sub">
        Быстрая сводка по справочникам и документам. Переходите в разделы слева для работы с данными.
      </p>
      {error && <div className="alert">{error}</div>}
      {summary && (
        <div className="stat-grid">
          <Link to="/products" className="stat-card">
            <span className="stat-value">{summary.products}</span>
            <span className="stat-label">Товары</span>
          </Link>
          <Link to="/warehouses" className="stat-card">
            <span className="stat-value">{summary.warehouses}</span>
            <span className="stat-label">Склады</span>
          </Link>
          <Link to="/stock" className="stat-card">
            <span className="stat-value">{summary.stock_rows}</span>
            <span className="stat-label">Записей об остатках</span>
          </Link>
          <Link to="/orders" className="stat-card">
            <span className="stat-value">{summary.orders}</span>
            <span className="stat-label">Заказы</span>
          </Link>
        </div>
      )}
      <div className="card">
        <h2>Жизненный цикл заказа</h2>
        <p className="small" style={{ marginTop: 0 }}>
          Черновик → подтверждён → отгружен (остатки списываются по выбранному складу). До отгрузки заказ
          можно отменить.
        </p>
        <p className="small">
          Статусы в списке заказов: <span className="badge neutral">draft</span>,{" "}
          <span className="badge warn">confirmed</span>, <span className="badge ok">fulfilled</span>,{" "}
          <span className="badge">cancelled</span>.
        </p>
      </div>
    </>
  );
}
