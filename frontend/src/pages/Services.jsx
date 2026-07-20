import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api from "@/lib/api";
import Layout from "@/components/Layout";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Search, Star, Filter } from "lucide-react";

export default function Services() {
  const [params, setParams] = useSearchParams();
  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const size = 12;
  const q = params.get("q") || "";
  const category = params.get("category") || "";
  const [qLocal, setQLocal] = useState(q);

  useEffect(() => {
    api.get("/categories").then((r) => setCategories(r.data));
  }, []);

  // Debounce local search input to URL
  useEffect(() => {
    const t = setTimeout(() => {
      if (qLocal === q) return;
      const p = new URLSearchParams(params);
      if (qLocal) p.set("q", qLocal); else p.delete("q");
      p.delete("page");
      setParams(p);
      setPage(1);
    }, 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qLocal]);

  useEffect(() => {
    setItems(null);
    const p = new URLSearchParams();
    if (q) p.set("q", q);
    if (category) p.set("category_id", category);
    p.set("page", page);
    p.set("size", size);
    api.get(`/services?${p.toString()}`).then((r) => {
      setItems(r.data.items);
      setTotal(r.data.total);
    });
  }, [q, category, page]);

  const setQ = (val) => setQLocal(val);
  const setCategory = (val) => {
    const p = new URLSearchParams(params);
    if (val) p.set("category", val); else p.delete("category");
    setParams(p);
    setPage(1);
  };

  const pages = Math.ceil(total / size);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <h1 className="font-display font-extrabold text-4xl sm:text-5xl">All services</h1>
        <p className="text-slate-600 mt-2">Choose from {total || "our"} services across {categories.length} categories.</p>

        <div className="mt-8 flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <Input
              value={qLocal}
              onChange={(e) => setQLocal(e.target.value)}
              placeholder="Search services..."
              className="pl-10 h-11"
              data-testid="services-search"
            />
          </div>
        </div>

        <div className="mt-6 grid lg:grid-cols-[240px_1fr] gap-8">
          <aside className="border border-slate-200 rounded-2xl p-5 h-fit sticky top-24">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-4">
              <Filter className="h-4 w-4" /> Categories
            </div>
            <div className="space-y-1">
              <button
                onClick={() => setCategory("")}
                data-testid="filter-all"
                className={`w-full text-left px-3 py-2 rounded-lg text-sm ${!category ? "bg-brand text-white" : "hover:bg-slate-100"}`}
              >
                All categories
              </button>
              {categories.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setCategory(c.id)}
                  data-testid={`filter-cat-${c.slug}`}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm ${category === c.id ? "bg-brand text-white" : "hover:bg-slate-100"}`}
                >
                  {c.name}
                </button>
              ))}
            </div>
          </aside>

          <div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {!items && Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-72 rounded-2xl" />)}
              {items?.map((s) => (
                <Link
                  key={s.id}
                  to={`/services/${s.id}`}
                  data-testid={`service-card-${s.id}`}
                  className="card-lift bg-white border border-slate-200 rounded-2xl overflow-hidden flex flex-col"
                >
                  <div className="aspect-video bg-slate-100 relative overflow-hidden">
                    {s.image_url && <img src={s.image_url} alt={s.name} className="w-full h-full object-cover" />}
                    <Badge className="absolute top-3 left-3 bg-white text-slate-900 border border-slate-200">
                      <Star className="h-3 w-3 text-accent-orange fill-current mr-1" /> {s.rating_avg || 4.6}
                    </Badge>
                  </div>
                  <div className="p-5 flex-1 flex flex-col">
                    <div className="font-semibold">{s.name}</div>
                    <div className="text-sm text-slate-500 mt-1 line-clamp-2 flex-1">{s.description}</div>
                    <div className="flex items-center justify-between mt-3">
                      <div className="font-display font-bold text-lg">₹{s.price}</div>
                      <span className="text-brand text-sm font-medium">Book →</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            {items && items.length === 0 && <div className="text-center py-16 text-slate-500">No services match your filter.</div>}
            {pages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-10">
                <Button variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)} data-testid="pg-prev">Prev</Button>
                <span className="text-sm text-slate-600 px-3">Page {page} of {pages}</span>
                <Button variant="outline" disabled={page === pages} onClick={() => setPage(page + 1)} data-testid="pg-next">Next</Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
