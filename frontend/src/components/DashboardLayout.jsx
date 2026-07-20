import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import Layout from "@/components/Layout";
import { useAuth } from "@/context/AuthContext";
import { LayoutDashboard, User, Calendar, Bell, Star, CreditCard, Lock, LogOut, Briefcase, ClipboardList, Wallet, Users, Grid2x2, Sparkles, Tag, MapPin, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";

const menus = {
  customer: [
    { to: "/dashboard", label: "Overview", icon: LayoutDashboard, end: true },
    { to: "/dashboard/bookings", label: "My Bookings", icon: Calendar },
    { to: "/dashboard/payments", label: "Payments", icon: CreditCard },
    { to: "/dashboard/reviews", label: "Reviews", icon: Star },
    { to: "/dashboard/notifications", label: "Notifications", icon: Bell },
    { to: "/profile", label: "Profile", icon: User },
    { to: "/change-password", label: "Password", icon: Lock },
  ],
  technician: [
    { to: "/technician", label: "Overview", icon: LayoutDashboard, end: true },
    { to: "/technician/jobs", label: "Assigned Jobs", icon: ClipboardList },
    { to: "/technician/earnings", label: "Earnings", icon: Wallet },
    { to: "/technician/reviews", label: "Reviews", icon: Star },
    { to: "/technician/notifications", label: "Notifications", icon: Bell },
    { to: "/profile", label: "Profile", icon: User },
    { to: "/change-password", label: "Password", icon: Lock },
  ],
  admin: [
    { to: "/admin", label: "Overview", icon: LayoutDashboard, end: true },
    { to: "/admin/bookings", label: "Bookings", icon: Calendar },
    { to: "/admin/users", label: "Customers", icon: Users },
    { to: "/admin/technicians", label: "Technicians", icon: Briefcase },
    { to: "/admin/services", label: "Services", icon: Sparkles },
    { to: "/admin/categories", label: "Categories", icon: Grid2x2 },
    { to: "/admin/coupons", label: "Coupons", icon: Tag },
    { to: "/admin/cities", label: "Cities", icon: MapPin },
    { to: "/admin/reviews", label: "Reviews", icon: Star },
    { to: "/admin/contact", label: "Contact requests", icon: MessageSquare },
  ],
};

export default function DashboardLayout({ role }) {
  const { user, logout } = useAuth();
  const items = menus[role || user?.role] || [];

  return (
    <Layout hideFooter>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 grid lg:grid-cols-[240px_1fr] gap-6">
        <aside className="lg:sticky lg:top-24 h-fit border border-slate-200 rounded-2xl bg-white p-4">
          <div className="px-3 py-3 border-b border-slate-100 mb-3">
            <div className="text-xs text-slate-500 uppercase tracking-wider">Signed in as</div>
            <div className="font-semibold mt-1">{user?.name}</div>
            <div className="text-xs text-slate-500 capitalize">{user?.role}</div>
          </div>
          <nav className="space-y-1">
            {items.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                data-testid={`nav-${label.toLowerCase().replace(/\s+/g, "-")}`}
                className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${isActive ? "bg-brand text-white" : "hover:bg-slate-100 text-slate-700"}`}
              >
                <Icon className="h-4 w-4" /> {label}
              </NavLink>
            ))}
          </nav>
          <Button variant="ghost" onClick={logout} className="w-full mt-3 text-red-600 justify-start" data-testid="sidebar-logout">
            <LogOut className="h-4 w-4 mr-2" /> Logout
          </Button>
        </aside>
        <div className="min-w-0"><Outlet /></div>
      </div>
    </Layout>
  );
}
