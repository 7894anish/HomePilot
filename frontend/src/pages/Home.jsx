import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Search, Star, ShieldCheck, Clock, BadgeCheck, Sparkles, Wrench, Zap, Wind,
  Refrigerator, Hammer, Paintbrush, Tv, Droplet, Camera, ArrowRight, CheckCircle2,
} from "lucide-react";
import { motion } from "framer-motion";

const ICONS = { Sparkles, Wrench, Zap, Wind, Refrigerator, Hammer, Paintbrush, Tv, Droplet, Camera };

const HERO_IMG = "https://images.pexels.com/photos/6196694/pexels-photo-6196694.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940";

const TESTIMONIALS = [
  { n: "Meera J.", c: "Bengaluru", t: "Booked a deep-clean at 9 AM, team arrived by 11. My kitchen looks brand new!", r: 5 },
  { n: "Arjun P.", c: "Mumbai", t: "AC gas refill was done in 45 minutes. Transparent pricing, no upsell.", r: 5 },
  { n: "Sneha R.", c: "Delhi", t: "Painting job finished in 2 days. Zero mess, great finish.", r: 4 },
];

const FAQ = [
  { q: "How do I book a service?", a: "Pick a service, choose date/time, add address & description, then pay online or select cash on service." },
  { q: "Are professionals verified?", a: "Yes — every professional passes ID verification, background check and skill training before joining." },
  { q: "What if I need to reschedule?", a: "You can reschedule or cancel free of charge from your dashboard up to 2 hours before the slot." },
  { q: "Is there a service warranty?", a: "All services include a 90-day service warranty against workmanship defects." },
  { q: "Which cities do you serve?", a: "We're live in 8 major Indian cities, with more launching every month." },
];

export default function Home() {
  const [categories, setCategories] = useState(null);
  const [services, setServices] = useState(null);
  const [q, setQ] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    (async () => {
      const [c, s] = await Promise.all([
        api.get("/categories"),
        api.get("/services?size=8"),
      ]);
      setCategories(c.data);
      setServices(s.data.items);
    })();
  }, []);

  const search = (e) => {
    e.preventDefault();
    nav(`/services${q ? `?q=${encodeURIComponent(q)}` : ""}`);
  };

  return (
    <Layout>
      {/* HERO */}
      <section className="hero-grad">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-14 pb-20 lg:pt-20 lg:pb-28 grid lg:grid-cols-2 gap-12 items-center">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Badge className="bg-accent text-accent-foreground rounded-full px-3 py-1 mb-6" data-testid="hero-badge">
              <BadgeCheck className="h-3.5 w-3.5 mr-1" /> Trusted by 250,000+ homes
            </Badge>
            <h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-6xl leading-tight tracking-tight text-slate-900">
              Home services, <span className="text-brand">on demand.</span>
              <br />
              <span className="text-accent-orange">Booked in 60 seconds.</span>
            </h1>
            <p className="mt-5 text-slate-600 text-lg leading-relaxed max-w-xl">
              From deep cleaning to AC repair — 10,000+ background-checked pros ready for your home.
              90-day warranty on every service.
            </p>

            <form onSubmit={search} className="mt-8 flex gap-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-2 max-w-xl">
              <div className="flex-1 flex items-center gap-2 px-3">
                <Search className="h-5 w-5 text-slate-400" />
                <Input
                  data-testid="hero-search-input"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search for AC repair, cleaning, plumber..."
                  className="border-0 focus-visible:ring-0 shadow-none text-base"
                />
              </div>
              <Button type="submit" className="bg-brand hover:bg-blue-700 h-11 px-6" data-testid="hero-search-btn">
                Search
              </Button>
            </form>

            <div className="mt-8 flex flex-wrap items-center gap-5 text-sm text-slate-600">
              <div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-brand" /> Verified pros</div>
              <div className="flex items-center gap-2"><Clock className="h-4 w-4 text-brand" /> On-time or free</div>
              <div className="flex items-center gap-2"><Star className="h-4 w-4 text-accent-orange fill-current" /> 4.8 avg rating</div>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6 }} className="relative">
            <div className="relative rounded-3xl overflow-hidden border border-slate-200 shadow-xl shadow-blue-500/10">
              <img src={HERO_IMG} alt="Home cleaning pro" className="w-full h-[420px] lg:h-[520px] object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900/40 via-transparent to-transparent" />
            </div>
            <Card className="absolute -bottom-6 -left-6 p-4 shadow-xl border-slate-200 hidden md:block max-w-[260px]">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-xl bg-brand/10 text-brand grid place-items-center"><ShieldCheck /></div>
                <div>
                  <div className="font-semibold text-sm">90-day warranty</div>
                  <div className="text-xs text-slate-500">on every service booked</div>
                </div>
              </div>
            </Card>
            <Card className="absolute -top-4 -right-4 p-4 shadow-xl border-slate-200 hidden md:block max-w-[220px]">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-xl bg-accent-orange/10 text-accent-orange grid place-items-center"><Star className="fill-current" /></div>
                <div>
                  <div className="font-semibold text-sm">4.8/5</div>
                  <div className="text-xs text-slate-500">by 42,000+ customers</div>
                </div>
              </div>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* CATEGORIES */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-16">
        <div className="flex items-end justify-between mb-10">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-brand font-semibold mb-2">What we offer</div>
            <h2 className="font-display font-bold text-3xl sm:text-4xl">Explore by category</h2>
          </div>
          <Link to="/services" className="hidden sm:flex items-center gap-1 text-brand font-medium hover:underline" data-testid="view-all-services">
            View all <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {!categories && Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-2xl" />)}
          {categories?.map((c) => {
            const Icon = ICONS[c.icon] || Wrench;
            return (
              <Link
                key={c.id}
                to={`/services?category=${c.id}`}
                data-testid={`category-${c.slug}`}
                className="group card-lift bg-white border border-slate-200 rounded-2xl p-5 flex flex-col gap-3"
              >
                <div className="h-11 w-11 rounded-xl bg-brand/10 text-brand grid place-items-center group-hover:bg-brand group-hover:text-white transition-colors">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">{c.name}</div>
                  <div className="text-xs text-slate-500 line-clamp-2 mt-0.5">{c.description}</div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* POPULAR SERVICES */}
      <section className="bg-slate-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-end justify-between mb-10">
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-accent-orange font-semibold mb-2">Most booked</div>
              <h2 className="font-display font-bold text-3xl sm:text-4xl">Popular services this week</h2>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {!services && Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-72 rounded-2xl" />)}
            {services?.map((s) => (
              <Link
                key={s.id}
                to={`/services/${s.id}`}
                data-testid={`popular-service-${s.id}`}
                className="card-lift bg-white rounded-2xl border border-slate-200 overflow-hidden flex flex-col"
              >
                <div className="aspect-video bg-slate-100 relative overflow-hidden">
                  {s.image_url && <img src={s.image_url} alt={s.name} className="w-full h-full object-cover" />}
                  <Badge className="absolute top-3 left-3 bg-white text-slate-900 border border-slate-200">
                    <Star className="h-3 w-3 text-accent-orange fill-current mr-1" /> {s.rating_avg || 4.6}
                  </Badge>
                </div>
                <div className="p-5 flex flex-col gap-2 flex-1">
                  <div className="font-semibold line-clamp-1">{s.name}</div>
                  <div className="text-sm text-slate-500 line-clamp-2 flex-1">{s.description}</div>
                  <div className="flex items-center justify-between mt-2">
                    <div className="font-display font-bold text-lg">₹{s.price}</div>
                    <span className="text-brand text-sm font-medium">Book now →</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* WHY US */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-20">
        <div className="text-center max-w-2xl mx-auto mb-14">
          <div className="text-xs uppercase tracking-[0.2em] text-brand font-semibold mb-2">Why HomeFix Pro</div>
          <h2 className="font-display font-bold text-3xl sm:text-4xl">Built for stress-free home services</h2>
        </div>
        <div className="grid md:grid-cols-4 gap-6">
          {[
            { i: ShieldCheck, t: "Verified experts", d: "ID + background verified, trained in our academy." },
            { i: Clock, t: "On-time or free", d: "If a pro is late, your booking is on us." },
            { i: BadgeCheck, t: "Upfront pricing", d: "Transparent quotes — no hidden charges." },
            { i: CheckCircle2, t: "90-day warranty", d: "Free re-service if issue recurs in 90 days." },
          ].map(({ i: Icon, t, d }) => (
            <div key={t} className="p-6 rounded-2xl border border-slate-200 bg-white card-lift">
              <div className="h-11 w-11 rounded-xl bg-brand/10 text-brand grid place-items-center mb-4">
                <Icon className="h-5 w-5" />
              </div>
              <div className="font-semibold text-lg">{t}</div>
              <div className="text-sm text-slate-500 mt-1">{d}</div>
            </div>
          ))}
        </div>
      </section>

      {/* PROCESS */}
      <section className="bg-slate-950 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="max-w-2xl mb-14">
            <div className="text-xs uppercase tracking-[0.2em] text-accent-orange font-semibold mb-2">How it works</div>
            <h2 className="font-display font-bold text-3xl sm:text-4xl">Book a pro in 3 quick steps</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { n: "01", t: "Pick a service", d: "Browse categories or search — we've got 10+ verticals." },
              { n: "02", t: "Choose a slot", d: "Same-day slots available. Book up to 30 days in advance." },
              { n: "03", t: "Sit back & relax", d: "Pro shows up. Quick job. Pay online or on-service." },
            ].map((s) => (
              <div key={s.n} className="border border-slate-800 rounded-2xl p-8 hover:border-brand transition-colors">
                <div className="font-display font-black text-5xl text-brand mb-4">{s.n}</div>
                <div className="font-semibold text-xl">{s.t}</div>
                <div className="text-slate-400 mt-2">{s.d}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-20">
        <div className="text-center max-w-2xl mx-auto mb-14">
          <div className="text-xs uppercase tracking-[0.2em] text-brand font-semibold mb-2">Loved by 250k homes</div>
          <h2 className="font-display font-bold text-3xl sm:text-4xl">What our customers say</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((r, i) => (
            <div key={i} className="p-6 rounded-2xl bg-white border border-slate-200 card-lift">
              <div className="flex items-center gap-1 mb-3 text-accent-orange">
                {Array.from({ length: r.r }).map((_, j) => <Star key={j} className="h-4 w-4 fill-current" />)}
              </div>
              <p className="text-slate-700 leading-relaxed">"{r.t}"</p>
              <div className="mt-4 pt-4 border-t border-slate-100">
                <div className="font-semibold">{r.n}</div>
                <div className="text-xs text-slate-500">{r.c}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="bg-slate-50 py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-10">
            <div className="text-xs uppercase tracking-[0.2em] text-brand font-semibold mb-2">Questions</div>
            <h2 className="font-display font-bold text-3xl sm:text-4xl">Frequently asked</h2>
          </div>
          <Accordion type="single" collapsible className="bg-white rounded-2xl border border-slate-200 divide-y">
            {FAQ.map((f, i) => (
              <AccordionItem key={i} value={`item-${i}`} className="border-b-0 px-6">
                <AccordionTrigger className="text-left font-medium py-5" data-testid={`faq-${i}`}>{f.q}</AccordionTrigger>
                <AccordionContent className="text-slate-600 pb-5">{f.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-20">
        <div className="rounded-3xl bg-brand text-white p-10 md:p-16 flex flex-col md:flex-row items-center justify-between gap-6 relative overflow-hidden">
          <div className="absolute -top-10 -right-10 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
          <div className="relative z-10 max-w-xl">
            <h3 className="font-display font-extrabold text-3xl sm:text-4xl">Ready for hassle-free home services?</h3>
            <p className="mt-3 text-blue-100">Join 250,000+ happy customers. Get 10% off your first booking with code <b>WELCOME10</b>.</p>
          </div>
          <Link to="/services">
            <Button size="lg" className="bg-white text-brand hover:bg-slate-100 h-12 px-8" data-testid="cta-book-btn">
              Book a service
            </Button>
          </Link>
        </div>
      </section>
    </Layout>
  );
}
