 import { useEffect, useState } from "react";
import { getOrders, createOrder, updateOrderStatus, downloadInvoice } from "../../api/orders";
import type { Order, OrderItemInput } from "../../api/orders";
import { getProducts } from "../../api/products";
import type { Product } from "../../api/products";
import { useToast } from "../../components/ui/Toast";

const statusStyles: Record<string, string> = {
  PENDING: "bg-amber-100 text-amber-700",
  CONFIRMED: "bg-blue-100 text-blue-700",
  COMPLETED: "bg-green-100 text-green-700",
  CANCELLED: "bg-slate-200 text-slate-600",
};

const ALLOWED_NEXT: Record<string, string[]> = {
  PENDING: ["CONFIRMED", "CANCELLED"],
  CONFIRMED: ["COMPLETED", "CANCELLED"],
  COMPLETED: [],
  CANCELLED: [],
};

export default function OrdersPage() {
  const { showToast } = useToast();
  const [orders, setOrders] = useState<Order[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [statusFilter, setStatusFilter] = useState("ALL");

  const [createOpen, setCreateOpen] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<OrderItemInput[]>([{ product_id: "", quantity: 1 }]);
  const [createError, setCreateError] = useState("");
  const [creating, setCreating] = useState(false);

  const [detailOrder, setDetailOrder] = useState<Order | null>(null);
  const [statusActionError, setStatusActionError] = useState("");
  const [statusActionLoading, setStatusActionLoading] = useState(false);

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [ordersData, productsData] = await Promise.all([getOrders(), getProducts()]);
      setOrders(ordersData);
      setProducts(productsData);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load orders.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  const filtered = orders.filter((o) => statusFilter === "ALL" || o.status === statusFilter);

  function openCreateModal() {
    setCustomerName("");
    setCustomerPhone("");
    setNotes("");
    setItems([{ product_id: "", quantity: 1 }]);
    setCreateError("");
    setCreateOpen(true);
  }

  function addItemRow() {
    setItems([...items, { product_id: "", quantity: 1 }]);
  }

  function removeItemRow(index: number) {
    setItems(items.filter((_, i) => i !== index));
  }

  function updateItemRow(index: number, field: keyof OrderItemInput, value: string | number) {
    const next = [...items];
    next[index] = { ...next[index], [field]: value };
    setItems(next);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreateError("");

    const validItems = items.filter((i) => i.product_id && i.quantity > 0);
    if (validItems.length === 0) {
      setCreateError("Add at least one product with a valid quantity.");
      return;
    }

    setCreating(true);
    try {
      const created = await createOrder({
        customer_name: customerName,
        customer_phone: customerPhone,
        notes: notes || null,
        items: validItems,
      });
      setCreateOpen(false);
      if (created.status === "CONFIRMED") {
        showToast("Order created and confirmed automatically");
      } else {
        showToast("Order created - pending review (insufficient stock)");
      }
      await loadAll();
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || "Failed to create order.");
    } finally {
      setCreating(false);
    }
  }

  async function handleStatusChange(order: Order, newStatus: string) {
    setStatusActionError("");
    setStatusActionLoading(true);
    try {
      const updated = await updateOrderStatus(order.id, newStatus);
      setDetailOrder(updated);
      showToast(`Order ${newStatus.toLowerCase()}`);
      await loadAll();
    } catch (err: any) {
      setStatusActionError(err.response?.data?.detail || "Failed to update order status.");
    } finally {
      setStatusActionLoading(false);
    }
  }

  async function handleDownloadInvoice(order: Order) {
    try {
      await downloadInvoice(order.id, order.order_number);
    } catch (err: any) {
      setStatusActionError("Failed to download invoice.");
    }
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-slate-800">Orders</h1>
        <button
          onClick={openCreateModal}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-md transition"
        >
          + Create Order
        </button>
      </div>

      <div className="flex gap-3 mb-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="ALL">All Statuses</option>
          <option value="PENDING">Pending</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="COMPLETED">Completed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      {error && (
        <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-4 py-3">
          {error}
        </div>
      )}

      {loading && (
        <div className="text-center py-16 text-slate-400 text-sm">Loading orders...</div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-16 text-slate-400 text-sm">
          No orders found. {statusFilter !== "ALL" ? "Try a different filter." : "Create your first order to get started."}
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Order #</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Customer</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Phone</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">Total Qty</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Status</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Created</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((o) => (
                <tr key={o.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">{o.order_number}</td>
                  <td className="px-4 py-3 text-slate-800 font-medium">{o.customer_name}</td>
                  <td className="px-4 py-3 text-slate-600">{o.customer_phone}</td>
                  <td className="px-4 py-3 text-right text-slate-800">{o.total_quantity}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusStyles[o.status]}`}>
                      {o.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-xs">
                    {new Date(o.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right space-x-3">
                    <button
                      onClick={() => {
                        setStatusActionError("");
                        setDetailOrder(o);
                      }}
                      className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                    >
                      View Details
                    </button>
                    {(o.status === "CONFIRMED" || o.status === "COMPLETED") && (
                      <button
                        onClick={() => handleDownloadInvoice(o)}
                        className="text-slate-600 hover:text-slate-800 text-xs font-medium"
                      >
                        Invoice
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Order Modal */}
      {createOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-xl p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">Create Order</h2>
            <p className="text-xs text-slate-500 mb-4">
              If enough stock is available, this order will be confirmed automatically and stock deducted right away.
            </p>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Customer Name</label>
                  <input
                    required
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Customer Phone</label>
                  <input
                    required
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Notes (optional)</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-2">Products</label>
                <div className="space-y-2">
                  {items.map((item, index) => (
                    <div key={index} className="flex gap-2 items-center">
                      <select
                        required
                        value={item.product_id}
                        onChange={(e) => updateItemRow(index, "product_id", e.target.value)}
                        className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
                      >
                        <option value="">Select product...</option>
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.product_code} - {p.name} ({p.available_quantity} {p.unit} avail.)
                          </option>
                        ))}
                      </select>
                      <input
                        required
                        type="number"
                        min={1}
                        value={item.quantity}
                        onChange={(e) => updateItemRow(index, "quantity", Number(e.target.value))}
                        className="w-24 rounded-md border border-slate-300 px-3 py-2 text-sm"
                      />
                      {items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeItemRow(index)}
                          className="text-red-500 hover:text-red-700 text-xs px-2"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={addItemRow}
                  className="mt-2 text-blue-600 hover:text-blue-800 text-xs font-medium"
                >
                  + Add another product
                </button>
              </div>

              {createError && (
                <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                  {createError}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setCreateOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-md transition"
                >
                  {creating ? "Creating..." : "Create Order"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Order Detail Modal */}
      {detailOrder && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-800">{detailOrder.order_number}</h2>
                <span className={`inline-block mt-1 px-2 py-1 rounded-full text-xs font-medium ${statusStyles[detailOrder.status]}`}>
                  {detailOrder.status}
                </span>
              </div>
              <button
                onClick={() => setDetailOrder(null)}
                className="text-slate-400 hover:text-slate-600 text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <span className="text-slate-500">Customer:</span>{" "}
                <span className="text-slate-800 font-medium">{detailOrder.customer_name}</span>
              </div>
              <div>
                <span className="text-slate-500">Phone:</span>{" "}
                <span className="text-slate-800">{detailOrder.customer_phone}</span>
              </div>
              {detailOrder.notes && (
                <div>
                  <span className="text-slate-500">Notes:</span>{" "}
                  <span className="text-slate-800">{detailOrder.notes}</span>
                </div>
              )}
              <div>
                <span className="text-slate-500">Created:</span>{" "}
                <span className="text-slate-800">{new Date(detailOrder.created_at).toLocaleString()}</span>
              </div>
              <div>
                <span className="text-slate-500">Last updated:</span>{" "}
                <span className="text-slate-800">{new Date(detailOrder.updated_at).toLocaleString()}</span>
              </div>

              <div>
                <div className="text-slate-500 mb-2">Products ordered:</div>
                <div className="border border-slate-200 rounded-md overflow-hidden">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="text-left px-3 py-2 font-medium text-slate-600">Product</th>
                        <th className="text-left px-3 py-2 font-medium text-slate-600">Code</th>
                        <th className="text-right px-3 py-2 font-medium text-slate-600">Qty</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {detailOrder.items.map((item) => (
                        <tr key={item.id}>
                          <td className="px-3 py-2 text-slate-800">{item.product_name}</td>
                          <td className="px-3 py-2 text-slate-500 font-mono">{item.product_code}</td>
                          <td className="px-3 py-2 text-right text-slate-800">{item.quantity}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="text-right text-slate-600 text-xs mt-1">
                  Total quantity: <strong>{detailOrder.total_quantity}</strong>
                </div>
              </div>
            </div>

            {statusActionError && (
              <div className="mt-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                {statusActionError}
              </div>
            )}

            {(detailOrder.status === "CONFIRMED" ||
              detailOrder.status === "COMPLETED" ||
              ALLOWED_NEXT[detailOrder.status].length > 0) && (
              <div className="flex justify-end gap-2 mt-5 pt-4 border-t border-slate-100">
                {(detailOrder.status === "CONFIRMED" || detailOrder.status === "COMPLETED") && (
                  <button
                    onClick={() => handleDownloadInvoice(detailOrder)}
                    className="px-4 py-2 text-sm font-medium text-slate-700 border border-slate-300 rounded-md hover:bg-slate-50"
                  >
                    Download Invoice
                  </button>
                )}
                {ALLOWED_NEXT[detailOrder.status].includes("CANCELLED") && (
                  <button
                    onClick={() => handleStatusChange(detailOrder, "CANCELLED")}
                    disabled={statusActionLoading}
                    className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-800 disabled:opacity-50"
                  >
                    Cancel Order
                  </button>
                )}
                {ALLOWED_NEXT[detailOrder.status].includes("CONFIRMED") && (
                  <button
                    onClick={() => handleStatusChange(detailOrder, "CONFIRMED")}
                    disabled={statusActionLoading}
                    className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-md transition"
                  >
                    {statusActionLoading ? "Confirming..." : "Confirm Order"}
                  </button>
                )}
                {ALLOWED_NEXT[detailOrder.status].includes("COMPLETED") && (
                  <button
                    onClick={() => handleStatusChange(detailOrder, "COMPLETED")}
                    disabled={statusActionLoading}
                    className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-md transition"
                  >
                    {statusActionLoading ? "Completing..." : "Mark Completed"}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}