import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import Layout from "@/components/Layout";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { toast } from "sonner";
import { toMsg } from "@/lib/api";
import { Wrench } from "lucide-react";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "", role: "customer" });
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const u = await register(form);
      toast.success("Account created! Welcome to HomeFix Pro.");
      nav(u.role === "technician" ? "/technician" : "/dashboard");
    } catch (err) {
      toast.error(toMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Layout hideFooter>
      <div className="min-h-[calc(100vh-4rem)] grid lg:grid-cols-2">
        <div className="hidden lg:flex flex-col justify-between p-12 bg-accent-orange text-white relative overflow-hidden">
          <div className="absolute -top-32 -right-32 h-96 w-96 rounded-full bg-white/10 blur-3xl" />
          <Link to="/" className="flex items-center gap-2 relative z-10">
            <div className="h-9 w-9 rounded-xl bg-white/20 grid place-items-center"><Wrench className="h-5 w-5" /></div>
            <div className="font-display font-extrabold text-lg">HomeFix.Pro</div>
          </Link>
          <div className="relative z-10 max-w-md">
            <h2 className="font-display font-extrabold text-4xl leading-tight">Join thousands of homeowners.</h2>
            <p className="mt-4 text-white/90">Get 10% off your first booking with code <b>WELCOME10</b>.</p>
          </div>
          <div className="relative z-10 text-sm text-white/80">
            Are you a pro? Register as a technician and start earning.
          </div>
        </div>

        <div className="flex items-center justify-center p-8">
          <div className="w-full max-w-md">
            <h1 className="font-display font-extrabold text-3xl">Create your account</h1>
            <p className="text-slate-500 mt-1">Takes less than 30 seconds.</p>
            <form onSubmit={submit} className="mt-8 space-y-4">
              <div>
                <Label>Full name</Label>
                <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="register-name" />
              </div>
              <div>
                <Label>Email</Label>
                <Input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} data-testid="register-email" />
              </div>
              <div>
                <Label>Phone</Label>
                <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} data-testid="register-phone" />
              </div>
              <div>
                <Label>Password</Label>
                <Input type="password" required minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} data-testid="register-password" />
              </div>
              <div>
                <Label className="mb-2 block">I am a</Label>
                <RadioGroup value={form.role} onValueChange={(v) => setForm({ ...form, role: v })} className="grid grid-cols-2 gap-3">
                  <label className={`p-3 border rounded-xl cursor-pointer text-sm flex items-center gap-2 ${form.role === "customer" ? "border-brand bg-brand/5" : "border-slate-200"}`}>
                    <RadioGroupItem value="customer" data-testid="role-customer" />
                    <span>Customer</span>
                  </label>
                  <label className={`p-3 border rounded-xl cursor-pointer text-sm flex items-center gap-2 ${form.role === "technician" ? "border-brand bg-brand/5" : "border-slate-200"}`}>
                    <RadioGroupItem value="technician" data-testid="role-technician" />
                    <span>Technician / Pro</span>
                  </label>
                </RadioGroup>
              </div>
              <Button type="submit" disabled={busy} className="w-full bg-brand hover:bg-blue-700 h-11" data-testid="register-submit">
                {busy ? "Creating..." : "Create account"}
              </Button>
            </form>
            <div className="mt-6 text-sm text-slate-600 text-center">
              Already have an account? <Link to="/login" className="text-brand font-medium hover:underline">Sign in</Link>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
