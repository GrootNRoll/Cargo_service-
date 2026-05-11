import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useIsAdmin } from "../auth/AuthContext";

export function AdminOnly({ children }: { children: ReactNode }) {
  const isAdmin = useIsAdmin();
  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
