import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDashboardSummary } from "../../api/dashboard";
import type { DashboardSummary } from "../../api/dashboard";

const statusStyles: Record<string, string> = {
  PENDING: "bg-[var(--color-amber-soft)] text-[var(--color-amber)]",
  CONFIRMED: "bg-[var(--color-slateblue-soft)] text-[var(--color-slateblue)]",
  COMPLETED: "bg-[var(--color-moss-soft)] text-[var(--color-moss)]",
  CANCELLED: "bg-stone-100 text-stone-500",
};

interface CardProps {
  label: string;
  value: number;
  accentColor: string;
}

function Card({ label, value, accentColor }: CardProps) {
  return (
    <div
      className="bg-[var(--color-surface)] rounded-md p-5 border border-[var(--color-line)] border-l-4"
      style={{ borderLeftColor: accentColor }}
    >
      <div className="text-xs text-[var(--color-ink-soft)] mb-1 font-medium">{label}</div>
      <div className="font-display text-3xl text-[var(--color-ink)]">{value}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await getDashboardSummary();
      setSummary(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="p-8">
      <h1 className="font-display text-3xl text-[var(--color-ink)] mb-6">Dashboard</h1>

      {error && (
        <div className="mb-4 text-sm text-[var(--color-rust)] bg-[var(--color-rust-soft)] rounded px-4 py-3">
          {error}
        </div>
      )}

      {loading && (
        <div className="text-center py-16 text-[var(--color-ink-soft)] text-sm">
          Loading dashboard...
        </div>
      )}

      {!loading && summary && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <Card label="Total Products" value={summary.total_products} accentColor="#3E5C76" />
            <Card label="Total Stock" value={summary.total_available_stock} accentColor="#3E5C76" />
            <Card label="Low Stock" value={summary.low_stock_products} accentColor="#C9862F" />
            <Card label="Out of Stock" value={summary.out_of_stock_products} accentColor="#A8432B" />
            <Card label="Total Orders" value={summary.total_orders} accentColor="#B8752F" />
            <Card label="Pending Orders" value={summary.pending_orders} accentColor="#C9862F" />
          </div>

          {(summary.low_stock_products > 0 || summary.out_of_stock_products > 0) && (
            <div className="mb-6 flex items-center justify-between bg-[var(--color-amber-soft)] rounded-md px-4 py-3">
              <span className="text-sm text-[var(--color-ink)]">
                {summary.out_of_stock_products > 0 && (
                  <>
                    <strong>{summary.out_of_stock_products}</strong> product
                    {summary.out_of_stock_products !== 1 ? "s are" : " is"} out of stock.{" "}
                  </>
                )}
                {summary.low_stock_products > 0 && (
                  <>
                    <strong>{summary.low_stock_products}</strong> product
                    {summary.low_stock_products !== 1 ? "s are" : " is"} running low.
                  </>
                )}
              </span>
              <Link
                to="/products"
                className="text-sm font-medium text-[var(--color-teak)] hover:text-[var(--color-teak-dark)] whitespace-nowrap ml-4"
              >
                View Products →
              </Link>
            </div>
          )}

          <div className="bg-[var(--color-surface)] rounded-md border border-[var(--color-line)] overflow-hidden">
            <div className="px-5 py-4 border-b border-[var(--color-line)] flex justify-between items-center">
              <h2 className="text-sm font-semibold text-[var(--color-ink)]">Recent Orders</h2>
              <Link
                to="/orders"
                className="text-xs font-medium text-[var(--color-teak)] hover:text-[var(--color-teak-dark)]"
              >
                View all →
              </Link>
            </div>

            {summary.recent_orders.length === 0 ? (
              <div className="text-center py-10 text-[var(--color-ink-soft)] text-sm">
                No orders yet.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-stone-50 border-b border-[var(--color-line)]">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium text-[var(--color-ink-soft)]">
                      Order #
                    </th>
                    <th className="text-left px-4 py-2 font-medium text-[var(--color-ink-soft)]">
                      Customer
                    </th>
                    <th className="text-right px-4 py-2 font-medium text-[var(--color-ink-soft)]">
                      Qty
                    </th>
                    <th className="text-left px-4 py-2 font-medium text-[var(--color-ink-soft)]">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-line)]">
                  {summary.recent_orders.map((o) => (
                    <tr key={o.id} className="hover:bg-stone-50">
                      <td className="px-4 py-2 font-data text-xs text-[var(--color-ink)]">
                        {o.order_number}
                      </td>
                      <td className="px-4 py-2 text-[var(--color-ink)]">{o.customer_name}</td>
                      <td className="px-4 py-2 text-right font-data text-[var(--color-ink)]">
                        {o.total_quantity}
                      </td>
                      <td className="px-4 py-2">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${statusStyles[o.status]}`}
                        >
                          {o.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}