import type { ReactNode } from "react";
import "./financeiro.css";

export default function FinanceiroLayout({ children }: { children: ReactNode }) {
  return <section className="financeiro-shell">{children}</section>;
}
