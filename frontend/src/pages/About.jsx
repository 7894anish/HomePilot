import React from "react";
import Layout from "@/components/Layout";
import { Users, Award, HeartHandshake, TrendingUp } from "lucide-react";

const stats = [
  { n: "250k+", l: "Happy customers" },
  { n: "10k+", l: "Verified pros" },
  { n: "8", l: "Cities live" },
  { n: "4.8", l: "Avg. rating" },
];
const values = [
  { i: Users, t: "Customer first", d: "Every process decision is anchored to homeowner peace of mind." },
  { i: Award, t: "Trained professionals", d: "In-house academy trains every pro on quality, safety and etiquette." },
  { i: HeartHandshake, t: "Fair payouts", d: "70% of every booking goes directly to the pro who did the work." },
  { i: TrendingUp, t: "Data-driven", d: "We measure NPS, on-time & first-visit fix rate for continuous improvement." },
];

export default function About() {
  return (
    <Layout>
      <section className="hero-grad">
        <div className="max-w-4xl mx-auto px-6 py-20 text-center">
          <div className="text-xs uppercase tracking-[0.2em] text-brand font-semibold mb-3">About us</div>
          <h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-6xl leading-tight">
            We're on a mission to make home <span className="text-brand">care effortless.</span>
          </h1>
          <p className="mt-5 text-lg text-slate-600 leading-relaxed">
            HomeFix Pro started in 2022 with a simple idea — homeowners deserve a reliable, delightful way to book any home service.
            Today we serve 250k+ customers across 8 cities with a growing network of trained professionals.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 py-16 grid sm:grid-cols-4 gap-6">
        {stats.map((s) => (
          <div key={s.l} className="p-8 border border-slate-200 rounded-2xl text-center bg-white">
            <div className="font-display font-extrabold text-4xl text-brand">{s.n}</div>
            <div className="text-slate-500 text-sm mt-2">{s.l}</div>
          </div>
        ))}
      </section>

      <section className="max-w-7xl mx-auto px-6 py-20">
        <h2 className="font-display font-bold text-3xl sm:text-4xl mb-10">What drives us</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {values.map(({ i: Icon, t, d }) => (
            <div key={t} className="p-8 border border-slate-200 rounded-2xl card-lift bg-white">
              <div className="h-12 w-12 rounded-xl bg-brand/10 text-brand grid place-items-center mb-4">
                <Icon className="h-6 w-6" />
              </div>
              <div className="font-semibold text-xl">{t}</div>
              <div className="text-slate-600 mt-2">{d}</div>
            </div>
          ))}
        </div>
      </section>
    </Layout>
  );
}
