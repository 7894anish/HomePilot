import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import Layout from "@/components/Layout";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { toMsg } from "@/lib/api";
import { Wrench } from "lucide-react";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const nextPath = params.get("next") || null;

  const [form, setForm] = useState({ email: "", password: "" });
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const u = await login(form.email, form.password);
      toast.success(`Welcome back, ${u.name?.split(" ")[0]}!`);
      const dest = nextPath || (u.role === "admin" ? "/admin" : u.role === "technician" ? "/technician" : "/dashboard");
      nav(dest);
    } catch (err) {
      toast.error(toMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Layout hideFooter>
      <div className="min-h-[calc(100vh-4rem)] grid lg:grid-cols-2">
        <div className="hidden lg:flex flex-col justify-between p-12 bg-brand text-white relative overflow-hidden">
          <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-white/10 blur-3xl" />
          <Link to="/" className="flex items-center gap-2 relative z-10">
            <div className="h-9 w-9 rounded-xl bg-white/20 grid place-items-center"><Wrench className="h-5 w-5" /></div>
            <div className="font-display font-extrabold text-lg">HomeFix.Pro</div>
          </Link>
          <div className="relative z-10 max-w-md">
            <h2 className="font-display font-extrabold text-4xl leading-tight">Book trusted pros for every home task.</h2>
            <p className="mt-4 text-blue-100">Cleaning, plumbing, AC, electrical & more — verified, insured, warranty-backed.</p>
          </div>
          <div className="relative z-10 text-sm text-blue-100">
            Demo: admin@homefix.pro / admin123 · customer@homefix.pro / customer123
          </div>
        </div>

        <div className="flex items-center justify-center p-8">
          <div className="w-full max-w-md">
            <h1 className="font-display font-extrabold text-3xl">Welcome back</h1>
            <p className="text-slate-500 mt-1">Sign in to book & manage services.</p>
            <form onSubmit={submit} className="mt-8 space-y-4">
              <div>
                <Label>Email</Label>
                <Input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} data-testid="login-email" />
              </div>
              <div>
                <Label>Password</Label>
                <Input type="password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} data-testid="login-password" />
              </div>
              <div className="flex justify-end">
                <Link to="/forgot-password" className="text-sm text-brand hover:underline">Forgot password?</Link>
              </div>
              <Button type="submit" disabled={busy} className="w-full bg-brand hover:bg-blue-700 h-11" data-testid="login-submit">
                {busy ? "Signing in..." : "Sign in"}
              </Button>
            </form>
            <div className="mt-6 text-sm text-slate-600 text-center">
              New here? <Link to="/register" className="text-brand font-medium hover:underline">Create an account</Link>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
