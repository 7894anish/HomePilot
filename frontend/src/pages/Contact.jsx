import React, { useState } from "react";
import Layout from "@/components/Layout";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import api, { toMsg } from "@/lib/api";
import { Mail, Phone, MapPin, MessageCircle } from "lucide-react";

export default function Contact() {
  const [form, setForm] = useState({ name: "", email: "", phone: "", subject: "", message: "" });
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/contact", form);
      toast.success("Message sent — we'll get back within 24h.");
      setForm({ name: "", email: "", phone: "", subject: "", message: "" });
    } catch (err) {
      toast.error(toMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-6 py-16 grid lg:grid-cols-2 gap-12">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] text-brand font-semibold mb-3">Get in touch</div>
          <h1 className="font-display font-extrabold text-4xl sm:text-5xl">We'd love to hear from you.</h1>
          <p className="mt-3 text-slate-600">Have a question, feedback or partnership idea? Drop us a message.</p>

          <div className="mt-10 space-y-5">
            {[
              { i: Phone, t: "Phone", d: "+91 90000 00000" },
              { i: Mail, t: "Email", d: "hello@homefix.pro" },
              { i: MapPin, t: "Office", d: "3rd Floor, Prestige Tower, Bengaluru" },
              { i: MessageCircle, t: "WhatsApp", d: "+91 90000 00000" },
            ].map(({ i: Icon, t, d }) => (
              <div key={t} className="flex items-start gap-4">
                <div className="h-11 w-11 rounded-xl bg-brand/10 text-brand grid place-items-center"><Icon className="h-5 w-5" /></div>
                <div>
                  <div className="font-semibold">{t}</div>
                  <div className="text-slate-600">{d}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={submit} className="p-8 rounded-2xl border border-slate-200 bg-white shadow-sm space-y-4">
          <div>
            <Label>Full name</Label>
            <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="contact-name" />
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <div><Label>Email</Label><Input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} data-testid="contact-email" /></div>
            <div><Label>Phone</Label><Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} data-testid="contact-phone" /></div>
          </div>
          <div><Label>Subject</Label><Input required value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} data-testid="contact-subject" /></div>
          <div><Label>Message</Label><Textarea required rows={5} value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} data-testid="contact-message" /></div>
          <Button type="submit" disabled={busy} className="bg-brand hover:bg-blue-700 h-11 w-full" data-testid="contact-submit">
            {busy ? "Sending..." : "Send message"}
          </Button>
        </form>
      </div>
    </Layout>
  );
}
