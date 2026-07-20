import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Star, Clock, ShieldCheck, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function ServiceDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const { user } = useAuth();
  const nav = useNavigate();

  useEffect(() => {
    api.get(`/services/${id}`).then((r) => setData(r.data));
  }, [id]);

  if (!data) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 grid lg:grid-cols-3 gap-8">
          <Skeleton className="h-96 rounded-2xl lg:col-span-2" />
          <Skeleton className="h-96 rounded-2xl" />
        </div>
      </Layout>
    );
  }
  const s = data.service;

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <div className="text-sm text-slate-500 mb-4">
          <Link to="/" className="hover:text-brand">Home</Link> / <Link to="/services" className="hover:text-brand">Services</Link> / <span className="text-slate-900">{s.name}</span>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="aspect-[16/9] rounded-2xl overflow-hidden border border-slate-200">
              {s.image_url && <img src={s.image_url} alt={s.name} className="w-full h-full object-cover" />}
            </div>
            <div>
              <div className="flex items-center gap-3 text-sm text-slate-500 mb-3">
                {data.category && <Badge variant="outline">{data.category.name}</Badge>}
                <span className="flex items-center gap-1"><Star className="h-4 w-4 text-accent-orange fill-current" /> {s.rating_avg || 4.6} ({s.rating_count || 0})</span>
                <span className="flex items-center gap-1"><Clock className="h-4 w-4" /> ~{s.duration_minutes} min</span>
              </div>
              <h1 className="font-display font-extrabold text-4xl">{s.name}</h1>
              <p className="mt-4 text-slate-700 leading-relaxed">{s.description}</p>
            </div>

            <div className="border-t border-slate-200 pt-6">
              <h2 className="font-display font-bold text-2xl mb-4">What's included</h2>
              <ul className="grid sm:grid-cols-2 gap-3">
                {(s.features || []).map((f, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle2 className="h-5 w-5 text-brand mt-0.5" />
                    <span className="text-slate-700">{f}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="border-t border-slate-200 pt-6">
              <h2 className="font-display font-bold text-2xl mb-4">Customer reviews</h2>
              {data.reviews?.length === 0 && <div className="text-slate-500">No reviews yet — be the first!</div>}
              <div className="space-y-4">
                {data.reviews?.map((r) => (
                  <div key={r.id} className="p-5 rounded-xl border border-slate-200">
                    <div className="flex items-center justify-between mb-1">
                      <div className="font-semibold">{r.customer_name}</div>
                      <div className="flex items-center gap-1 text-accent-orange">
                        {Array.from({ length: r.rating }).map((_, j) => <Star key={j} className="h-4 w-4 fill-current" />)}
                      </div>
                    </div>
                    <div className="text-slate-600 text-sm">{r.comment}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <aside className="space-y-4">
            <div className="rounded-2xl border border-slate-200 p-6 sticky top-24 bg-white shadow-sm">
              <div className="text-slate-500 text-sm">Starting at</div>
              <div className="font-display font-extrabold text-4xl mt-1">₹{s.price}</div>
              <div className="text-xs text-slate-500 mt-1">Incl. all taxes</div>
              <Button
                data-testid="book-service-btn"
                className="w-full bg-brand hover:bg-blue-700 h-12 mt-5"
                onClick={() => nav(user ? `/book/${s.id}` : `/login?next=/book/${s.id}`)}
              >
                Book service
              </Button>
              <div className="mt-5 space-y-3 text-sm">
                <div className="flex items-center gap-2 text-slate-700"><ShieldCheck className="h-4 w-4 text-brand" /> 90-day service warranty</div>
                <div className="flex items-center gap-2 text-slate-700"><Clock className="h-4 w-4 text-brand" /> On-time or free</div>
                <div className="flex items-center gap-2 text-slate-700"><CheckCircle2 className="h-4 w-4 text-brand" /> Verified professionals</div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </Layout>
  );
}
