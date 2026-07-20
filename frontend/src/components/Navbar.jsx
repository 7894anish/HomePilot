import React from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Menu, X, Home, LogOut, User as UserIcon, LayoutDashboard, Wrench } from "lucide-react";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function Navbar() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [open, setOpen] = React.useState(false);

  const dashPath = user
    ? user.role === "admin" ? "/admin"
    : user.role === "technician" ? "/technician"
    : "/dashboard"
    : "/login";

  const link = ({ isActive }) =>
    `text-sm font-medium transition-colors ${isActive ? "text-brand" : "text-slate-700 hover:text-brand"}`;

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2" data-testid="brand-logo">
          <div className="h-9 w-9 rounded-xl bg-brand text-white grid place-items-center">
            <Wrench className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <div className="font-display font-extrabold text-lg">HomeFix<span className="text-accent-orange">.</span>Pro</div>
            <div className="text-[10px] tracking-widest text-slate-500 uppercase">Home services, on demand</div>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          <NavLink to="/" className={link} data-testid="nav-home">Home</NavLink>
          <NavLink to="/services" className={link} data-testid="nav-services">Services</NavLink>
          <NavLink to="/about" className={link} data-testid="nav-about">About</NavLink>
          <NavLink to="/contact" className={link} data-testid="nav-contact">Contact</NavLink>
        </nav>

        <div className="hidden md:flex items-center gap-3">
          {!user ? (
            <>
              <Link to="/login"><Button variant="ghost" data-testid="nav-login-btn">Login</Button></Link>
              <Link to="/register">
                <Button className="bg-brand hover:bg-blue-700" data-testid="nav-register-btn">Get Started</Button>
              </Link>
            </>
          ) : (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" data-testid="user-menu-trigger" className="gap-2">
                  <UserIcon className="h-4 w-4" />
                  {user.name?.split(" ")[0] || "Account"}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="font-semibold">{user.name}</div>
                  <div className="text-xs text-slate-500 capitalize">{user.role}</div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => nav(dashPath)} data-testid="user-menu-dashboard">
                  <LayoutDashboard className="h-4 w-4 mr-2" /> Dashboard
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => nav("/profile")} data-testid="user-menu-profile">
                  <UserIcon className="h-4 w-4 mr-2" /> Profile
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={async () => { await logout(); nav("/"); }} data-testid="user-menu-logout">
                  <LogOut className="h-4 w-4 mr-2" /> Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        <button className="md:hidden" onClick={() => setOpen(!open)} data-testid="mobile-menu-toggle">
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-slate-200 bg-white px-6 py-4 space-y-3">
          <Link to="/" onClick={() => setOpen(false)} className="block py-1">Home</Link>
          <Link to="/services" onClick={() => setOpen(false)} className="block py-1">Services</Link>
          <Link to="/about" onClick={() => setOpen(false)} className="block py-1">About</Link>
          <Link to="/contact" onClick={() => setOpen(false)} className="block py-1">Contact</Link>
          {!user ? (
            <div className="pt-2 flex gap-2">
              <Link to="/login" className="flex-1"><Button variant="outline" className="w-full">Login</Button></Link>
              <Link to="/register" className="flex-1"><Button className="w-full bg-brand">Sign up</Button></Link>
            </div>
          ) : (
            <>
              <Link to={dashPath} onClick={() => setOpen(false)} className="block py-1">Dashboard</Link>
              <button onClick={async () => { await logout(); setOpen(false); nav("/"); }} className="text-red-600 py-1">Logout</button>
            </>
          )}
        </div>
      )}
    </header>
  );
}
