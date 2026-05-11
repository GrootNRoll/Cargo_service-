import { Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { AdminOnly } from "./components/AdminOnly";
import { RequireAuth } from "./components/RequireAuth";
import { AuditLogPage } from "./pages/AuditLogPage";
import { UsersAdminPage } from "./pages/UsersAdminPage";
import { WarehouseMembersPage } from "./pages/WarehouseMembersPage";
import { Home } from "./pages/Home";
import { LoginPage } from "./pages/LoginPage";
import { OrdersPage } from "./pages/OrdersPage";
import { ProductsPage } from "./pages/ProductsPage";
import { StockPage } from "./pages/StockPage";
import { WarehousesPage } from "./pages/WarehousesPage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireAuth />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route
              path="/warehouses/:warehouseId/members"
              element={
                <AdminOnly>
                  <WarehouseMembersPage />
                </AdminOnly>
              }
            />
            <Route path="/warehouses" element={<WarehousesPage />} />
            <Route path="/stock" element={<StockPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route
              path="/users"
              element={
                <AdminOnly>
                  <UsersAdminPage />
                </AdminOnly>
              }
            />
            <Route
              path="/audit"
              element={
                <AdminOnly>
                  <AuditLogPage />
                </AdminOnly>
              }
            />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  );
}
