import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../features/auth/AuthContext";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/products", label: "Products" },
  { to: "/orders", label: "Orders" },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen flex bg-[var(--color-canvas)]">
      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-[var(--color-ink)] text-white flex items-center justify-between px-4 z-40">
        <span className="font-display text-lg tracking-tight">Timberline</span>
        <button onClick={() => setMobileOpen(!mobileOpen)} className="text-2xl leading-none">
          {mobileOpen ? "✕" : "☰"}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`w-60 bg-[var(--color-ink)] text-stone-300 flex flex-col shrink-0 fixed md:static top-0 left-0 h-full z-30 transition-transform duration-200 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0`}
      >
        <div className="px-6 py-6 border-b border-white/10 hidden md:block">
          <h1 className="font-display text-2xl text-white tracking-tight">Timberline</h1>
          <p className="text-xs text-stone-500 mt-0.5 tracking-wide">WPC Dealership</p>
        </div>
        <div className="h-14 md:hidden" />
        <nav className="flex-1 px-3 py-5 space-y-0.5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `block px-3 py-2.5 rounded text-sm font-medium transition border-l-2 ${
                  isActive
                    ? "bg-white/5 text-white border-[var(--color-teak)]"
                    : "text-stone-400 hover:text-white hover:bg-white/5 border-transparent"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-5 border-t border-white/10">
          <div className="text-sm text-stone-200 font-medium">{user?.name}</div>
          <div className="text-xs text-stone-500 mb-3 tracking-wide">{user?.role}</div>
          <button
            onClick={logout}
            className="w-full text-left text-sm text-stone-400 hover:text-white font-medium transition"
          >
            Sign out
          </button>
        </div>
      </aside>

      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <main className="flex-1 min-w-0 pt-14 md:pt-0">
        <Outlet />
      </main>
    </div>
  );
}