import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { toMsg } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Calendar, Clock, IndianRupee, Star, TrendingUp, CheckCircle2, Loader2 } from "lucide-react";

const statusColors = {
  pending_payment: "bg-amber-100 text-amber-800",
  confirmed: "bg-blue-100 text-blue-800",
  assigned: "bg-purple-100 text-purple-800",
  accepted: "bg-indigo-100 text-indigo-800",
  in_progress: "bg-orange-100 text-orange-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
  rejected: "bg-red-100 text-red-800",
};
export function StatusBadge({ status }) {
  return <Badge className={`${statusColors[status] || "bg-slate-100 text-slate-700"} font-medium capitalize`}>{status?.replace(/_/g, " ")}</Badge>;
}

/* ========== CUSTOMER ========== */
export function CustomerOverview() {
  const { user } = useAuth();
  const [d, setD] = useState(null);
  const [recent, setRecent] = useState([]);
  useEffect(() => {
    Promise.all([api.get("/dashboard/customer"), api.get("/bookings/mine")]).then(([a, b]) => {
      setD(a.data); setRecent(b.data.slice(0, 5));
    });
  }, []);
  if (!d) return <Skeleton className="h-64 rounded-2xl" />;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display font-extrabold text-3xl">Welcome, {user.name?.split(" ")[0]}!</h1>
        <p className="text-slate-500">Here's your service activity overview.</p>
      </div>
      <div className="grid sm:grid-cols-4 gap-4">
        {[{ l: "Total bookings", v: d.total, i: Calendar }, { l: "Completed", v: d.completed, i: CheckCircle2 }, { l: "Active", v: d.pending, i: Clock }, { l: "Total spent", v: `₹${d.total_spent}`, i: IndianRupee }].map((k) => (
          <Card key={k.l}><CardContent className="p-5"><div className="flex items-center justify-between"><div><div className="text-xs uppercase text-slate-500 tracking-wider">{k.l}</div><div className="font-display font-bold text-2xl mt-1">{k.v}</div></div><div className="h-10 w-10 rounded-xl bg-brand/10 text-brand grid place-items-center"><k.i className="h-5 w-5" /></div></div></CardContent></Card>
        ))}
      </div>
      <Card>
        <CardHeader><CardTitle>Recent bookings</CardTitle></CardHeader>
        <CardContent>
          {recent.length === 0 ? <div className="text-slate-500 text-sm">No bookings yet. <Link className="text-brand" to="/services">Browse services →</Link></div> :
            <div className="divide-y">
              {recent.map((b) => (
                <Link to={`/bookings/${b.id}`} key={b.id} className="flex items-center justify-between py-3 hover:bg-slate-50 px-2 rounded-lg" data-testid={`recent-booking-${b.id}`}>
                  <div><div className="font-medium">{b.service_name}</div><div className="text-xs text-slate-500">{b.scheduled_date} · {b.scheduled_time}</div></div>
                  <div className="flex items-center gap-3"><StatusBadge status={b.status} /><div className="font-semibold">₹{b.total}</div></div>
                </Link>
              ))}
            </div>}
        </CardContent>
      </Card>
    </div>
  );
}

export function MyBookings() {
  const [items, setItems] = useState(null);
  useEffect(() => { api.get("/bookings/mine").then((r) => setItems(r.data)); }, []);
  if (!items) return <Skeleton className="h-64 rounded-2xl" />;
  return (
    <div>
      <h1 className="font-display font-extrabold text-3xl mb-6">My Bookings</h1>
      {items.length === 0 ? <div className="text-slate-500">No bookings yet.</div> :
        <div className="space-y-3">
          {items.map((b) => (
            <Link to={`/bookings/${b.id}`} key={b.id} className="p-5 border border-slate-200 rounded-xl bg-white flex items-center gap-4 card-lift" data-testid={`booking-${b.id}`}>
              {b.service?.image_url && <img src={b.service.image_url} alt="" className="h-16 w-16 rounded-lg object-cover" />}
              <div className="flex-1"><div className="font-semibold">{b.service_name}</div><div className="text-xs text-slate-500">{b.scheduled_date} · {b.scheduled_time} · {b.city}</div></div>
              <div className="text-right"><StatusBadge status={b.status} /><div className="font-semibold mt-2">₹{b.total}</div></div>
            </Link>
          ))}
        </div>}
    </div>
  );
}

export function BookingDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [b, setB] = useState(null);
  const [busy, setBusy] = useState(false);
  const [review, setReview] = useState({ rating: 5, comment: "" });
  const [existingReview, setExistingReview] = useState(false);

  const load = () => api.get(`/bookings/${id}`).then((r) => setB(r.data));
  useEffect(() => { load(); }, [id]);

  const act = async (status, note) => {
    setBusy(true);
    try { await api.post(`/bookings/${id}/status`, { status, note }); toast.success(`Booking ${status}`); await load(); }
    catch (e) { toast.error(toMsg(e)); } finally { setBusy(false); }
  };
  const pay = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/payments/checkout", { booking_id: id, origin_url: window.location.origin });
      window.location.href = data.checkout_url;
    } catch (e) { toast.error(toMsg(e)); setBusy(false); }
  };
  const submitReview = async () => {
    setBusy(true);
    try { await api.post("/reviews", { booking_id: id, rating: review.rating, comment: review.comment }); toast.success("Thanks for your review!"); setExistingReview(true); }
    catch (e) { toast.error(toMsg(e)); } finally { setBusy(false); }
  };

  if (!b) return <Skeleton className="h-96 rounded-2xl" />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="font-display font-extrabold text-2xl">{b.service_name}</h1><div className="text-slate-500 text-sm">Booking #{b.id.slice(0, 8)}</div></div>
        <StatusBadge status={b.status} />
      </div>
      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Service details</CardTitle></CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div><div className="text-slate-500">Date</div><div className="font-medium">{b.scheduled_date}</div></div>
              <div><div className="text-slate-500">Time</div><div className="font-medium">{b.scheduled_time}</div></div>
              <div><div className="text-slate-500">City</div><div className="font-medium">{b.city}</div></div>
              <div><div className="text-slate-500">Payment</div><div className="font-medium capitalize">{b.payment_method} · {b.payment_status}</div></div>
            </div>
            <div><div className="text-slate-500">Address</div><div>{b.address}</div></div>
            <div><div className="text-slate-500">Problem</div><div>{b.problem_description}</div></div>
            {b.technician && <div><div className="text-slate-500">Technician</div><div className="font-medium">{b.technician.name} ({b.technician.phone})</div></div>}
            {b.work_images?.length > 0 && <div><div className="text-slate-500 mb-2">Work photos</div><div className="flex gap-2 flex-wrap">{b.work_images.map((u, i) => <img key={i} src={u} className="h-20 w-20 object-cover rounded-lg" alt="" />)}</div></div>}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Total</CardTitle></CardHeader>
            <CardContent className="text-sm space-y-2">
              <div className="flex justify-between"><span className="text-slate-500">Subtotal</span><span>₹{b.amount}</span></div>
              {b.discount > 0 && <div className="flex justify-between text-green-600"><span>Discount</span><span>-₹{b.discount}</span></div>}
              <div className="flex justify-between font-bold text-base border-t pt-2"><span>Total</span><span>₹{b.total}</span></div>
              {user.role === "customer" && b.status === "pending_payment" && <Button className="w-full bg-brand mt-3" onClick={pay} disabled={busy} data-testid="retry-pay-btn">Pay now</Button>}
              {user.role === "customer" && !["completed", "cancelled", "rejected"].includes(b.status) && <Button variant="outline" className="w-full" onClick={() => act("cancelled", "Cancelled by customer")} disabled={busy} data-testid="cancel-btn">Cancel booking</Button>}
              {user.role === "technician" && b.status === "assigned" && (<>
                <Button className="w-full bg-brand" onClick={() => act("accepted")} disabled={busy} data-testid="accept-btn">Accept job</Button>
                <Button variant="outline" className="w-full text-red-600" onClick={() => act("rejected", "Rejected")} disabled={busy} data-testid="reject-btn">Reject</Button>
              </>)}
              {user.role === "technician" && b.status === "accepted" && <Button className="w-full bg-brand" onClick={() => act("in_progress")} disabled={busy} data-testid="start-btn">Start work</Button>}
              {user.role === "technician" && b.status === "in_progress" && <Button className="w-full bg-green-600" onClick={() => act("completed")} disabled={busy} data-testid="complete-btn">Mark complete</Button>}
            </CardContent>
          </Card>
          {user.role === "customer" && b.status === "completed" && !existingReview && (
            <Card><CardHeader><CardTitle>Leave a review</CardTitle></CardHeader><CardContent className="space-y-3">
              <div className="flex gap-1">{[1,2,3,4,5].map((r) => <button key={r} onClick={() => setReview({ ...review, rating: r })} data-testid={`star-${r}`}><Star className={`h-6 w-6 ${r <= review.rating ? "text-accent-orange fill-current" : "text-slate-300"}`} /></button>)}</div>
              <Textarea placeholder="Share your experience..." value={review.comment} onChange={(e) => setReview({ ...review, comment: e.target.value })} data-testid="review-comment" />
              <Button onClick={submitReview} className="w-full bg-brand" disabled={busy} data-testid="submit-review-btn">Submit review</Button>
            </CardContent></Card>
          )}
        </div>
      </div>
    </div>
  );
}

/* ========== TECHNICIAN ========== */
export function TechnicianOverview() {
  const [d, setD] = useState(null);
  const [jobs, setJobs] = useState([]);
  useEffect(() => {
    Promise.all([api.get("/dashboard/technician"), api.get("/bookings/mine")]).then(([a, b]) => { setD(a.data); setJobs(b.data.slice(0, 5)); });
  }, []);
  if (!d) return <Skeleton className="h-64 rounded-2xl" />;
  return (
    <div className="space-y-6">
      <h1 className="font-display font-extrabold text-3xl">Technician Dashboard</h1>
      <div className="grid sm:grid-cols-4 gap-4">
        {[{ l: "Assigned", v: d.assigned, i: Calendar }, { l: "Active", v: d.active, i: Loader2 }, { l: "Completed", v: d.completed, i: CheckCircle2 }, { l: "Earnings", v: `₹${d.earnings}`, i: IndianRupee }].map((k) => (
          <Card key={k.l}><CardContent className="p-5"><div className="text-xs uppercase text-slate-500 tracking-wider">{k.l}</div><div className="font-display font-bold text-2xl mt-1">{k.v}</div></CardContent></Card>
        ))}
      </div>
      <Card><CardHeader><CardTitle>Recent jobs</CardTitle></CardHeader><CardContent>
        {jobs.length === 0 ? <div className="text-slate-500 text-sm">No jobs yet.</div> :
        <div className="divide-y">{jobs.map((j) => (
          <Link to={`/bookings/${j.id}`} key={j.id} className="flex items-center justify-between py-3 hover:bg-slate-50 rounded px-2">
            <div><div className="font-medium">{j.service_name}</div><div className="text-xs text-slate-500">{j.scheduled_date} · {j.scheduled_time}</div></div>
            <StatusBadge status={j.status} />
          </Link>))}</div>}
      </CardContent></Card>
    </div>
  );
}

export function TechnicianJobs() {
  const [items, setItems] = useState(null);
  useEffect(() => { api.get("/bookings/mine").then((r) => setItems(r.data)); }, []);
  if (!items) return <Skeleton className="h-64 rounded-2xl" />;
  return (
    <div>
      <h1 className="font-display font-extrabold text-3xl mb-6">Assigned Jobs</h1>
      {items.length === 0 ? <div className="text-slate-500">No assigned jobs.</div> :
        <div className="space-y-3">{items.map((b) => (
          <Link to={`/bookings/${b.id}`} key={b.id} className="p-5 border border-slate-200 rounded-xl bg-white flex items-center justify-between card-lift">
            <div><div className="font-semibold">{b.service_name}</div><div className="text-xs text-slate-500">{b.scheduled_date} · {b.city}</div></div>
            <StatusBadge status={b.status} />
          </Link>))}</div>}
    </div>
  );
}

/* ========== ADMIN ========== */
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from "recharts";
const CHART_COLORS = ["#0d6efd", "#fd7e14", "#10b981", "#8b5cf6", "#ef4444", "#f59e0b"];

export function AdminOverview() {
  const [d, setD] = useState(null);
  useEffect(() => { api.get("/dashboard/admin").then((r) => setD(r.data)); }, []);
  if (!d) return <Skeleton className="h-64 rounded-2xl" />;
  return (
    <div className="space-y-6">
      <h1 className="font-display font-extrabold text-3xl">Admin Dashboard</h1>
      <div className="grid sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {[{ l: "Bookings", v: d.kpi.total_bookings }, { l: "Completed", v: d.kpi.completed }, { l: "Pending", v: d.kpi.pending }, { l: "Customers", v: d.kpi.customers }, { l: "Technicians", v: d.kpi.technicians }, { l: "Revenue", v: `₹${d.kpi.revenue}` }].map((k) => (
          <Card key={k.l}><CardContent className="p-4"><div className="text-xs uppercase text-slate-500 tracking-wider">{k.l}</div><div className="font-display font-bold text-xl mt-1">{k.v}</div></CardContent></Card>
        ))}
      </div>
      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2"><CardHeader><CardTitle>Weekly bookings & revenue</CardTitle></CardHeader><CardContent style={{ height: 280 }}>
          <ResponsiveContainer><LineChart data={d.weekly.map((w) => ({ date: w._id.slice(5), count: w.count, revenue: w.revenue }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="date" /><YAxis /><Tooltip />
            <Line type="monotone" dataKey="count" stroke="#0d6efd" strokeWidth={2} name="Bookings" />
            <Line type="monotone" dataKey="revenue" stroke="#fd7e14" strokeWidth={2} name="Revenue" />
          </LineChart></ResponsiveContainer>
        </CardContent></Card>
        <Card><CardHeader><CardTitle>Bookings by status</CardTitle></CardHeader><CardContent style={{ height: 280 }}>
          <ResponsiveContainer><PieChart>
            <Pie data={d.by_status.map((s) => ({ name: s._id, value: s.count }))} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
              {d.by_status.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
            </Pie><Tooltip />
          </PieChart></ResponsiveContainer>
        </CardContent></Card>
      </div>
      <Card><CardHeader><CardTitle>Top services</CardTitle></CardHeader><CardContent style={{ height: 280 }}>
        <ResponsiveContainer><BarChart data={d.top_services.map((t) => ({ name: t._id, count: t.count }))}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="name" /><YAxis /><Tooltip />
          <Bar dataKey="count" fill="#0d6efd" radius={[8, 8, 0, 0]} />
        </BarChart></ResponsiveContainer>
      </CardContent></Card>
    </div>
  );
}

export function AdminBookings() {
  const [items, setItems] = useState(null);
  const [techs, setTechs] = useState([]);
  const load = () => api.get("/admin/bookings").then((r) => setItems(r.data));
  useEffect(() => { load(); api.get("/technicians").then((r) => setTechs(r.data)); }, []);
  const assign = async (id, techId) => {
    try { await api.post(`/admin/bookings/${id}/assign`, { technician_id: techId }); toast.success("Assigned"); load(); }
    catch (e) { toast.error(toMsg(e)); }
  };
  if (!items) return <Skeleton className="h-64 rounded-2xl" />;
  return (<div>
    <h1 className="font-display font-extrabold text-3xl mb-6">All Bookings</h1>
    <div className="space-y-3">{items.map((b) => (
      <div key={b.id} className="p-5 border border-slate-200 rounded-xl bg-white flex items-center gap-4">
        <div className="flex-1"><Link to={`/bookings/${b.id}`} className="font-semibold hover:text-brand">{b.service_name}</Link><div className="text-xs text-slate-500">{b.customer?.name} · {b.scheduled_date} · {b.city}</div></div>
        <StatusBadge status={b.status} />
        <div className="font-semibold w-20 text-right">₹{b.total}</div>
        {["confirmed", "pending_payment"].includes(b.status) && !b.technician_id && (
          <Select onValueChange={(v) => assign(b.id, v)}>
            <SelectTrigger className="w-40" data-testid={`assign-${b.id}`}><SelectValue placeholder="Assign pro" /></SelectTrigger>
            <SelectContent>{techs.map((t) => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
          </Select>)}
      </div>))}</div></div>);
}

export function AdminList({ endpoint, title, columns, canDelete = true, extraActions }) {
  const [items, setItems] = useState(null);
  const load = () => api.get(endpoint).then((r) => setItems(r.data));
  useEffect(() => { load(); }, [endpoint]);
  const del = async (id, delEndpoint) => { if (!window.confirm("Delete?")) return; try { await api.delete(delEndpoint); toast.success("Deleted"); load(); } catch (e) { toast.error(toMsg(e)); } };
  if (!items) return <Skeleton className="h-64 rounded-2xl" />;
  return (<div>
    <div className="flex items-center justify-between mb-6"><h1 className="font-display font-extrabold text-3xl">{title}</h1>{extraActions?.(load)}</div>
    {items.length === 0 ? <div className="text-slate-500">No records.</div> :
    <div className="border border-slate-200 rounded-2xl bg-white overflow-hidden">
      <table className="w-full text-sm"><thead className="bg-slate-50"><tr>{columns.map((c) => <th key={c.key} className="text-left px-4 py-3 font-semibold">{c.label}</th>)}{canDelete && <th className="px-4 py-3" />}</tr></thead>
      <tbody className="divide-y">{items.map((it) => (<tr key={it.id} className="hover:bg-slate-50">
        {columns.map((c) => <td key={c.key} className="px-4 py-3">{c.render ? c.render(it) : it[c.key]}</td>)}
        {canDelete && <td className="px-4 py-3 text-right"><Button size="sm" variant="ghost" className="text-red-600" onClick={() => del(it.id, `${endpoint.replace("/admin","")}/${it.id}`)} data-testid={`delete-${it.id}`}>Delete</Button></td>}
      </tr>))}</tbody></table></div>}
  </div>);
}

/* ========== SHARED ========== */
export function Profile() {
  const { user, refresh } = useAuth();
  const [f, setF] = useState({ name: user?.name || "", phone: user?.phone || "", address: user?.address || "", city: user?.city || "", bio: user?.bio || "" });
  const [busy, setBusy] = useState(false);
  const save = async () => { setBusy(true); try { await api.put("/users/me", f); await refresh(); toast.success("Profile updated"); } catch (e) { toast.error(toMsg(e)); } finally { setBusy(false); } };
  return (<div className="max-w-2xl">
    <h1 className="font-display font-extrabold text-3xl mb-6">Profile</h1>
    <div className="space-y-4 p-6 border border-slate-200 rounded-2xl bg-white">
      <div><Label>Full name</Label><Input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} data-testid="profile-name" /></div>
      <div><Label>Phone</Label><Input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} data-testid="profile-phone" /></div>
      <div><Label>City</Label><Input value={f.city} onChange={(e) => setF({ ...f, city: e.target.value })} data-testid="profile-city" /></div>
      <div><Label>Address</Label><Input value={f.address} onChange={(e) => setF({ ...f, address: e.target.value })} data-testid="profile-address" /></div>
      <div><Label>Bio</Label><Textarea value={f.bio} onChange={(e) => setF({ ...f, bio: e.target.value })} data-testid="profile-bio" /></div>
      <Button onClick={save} disabled={busy} className="bg-brand" data-testid="profile-save">{busy ? "Saving..." : "Save changes"}</Button>
    </div>
  </div>);
}

export function ChangePassword() {
  const [f, setF] = useState({ current_password: "", new_password: "" });
  const [busy, setBusy] = useState(false);
  const save = async (e) => { e.preventDefault(); setBusy(true); try { await api.post("/auth/change-password", f); toast.success("Password updated"); setF({ current_password: "", new_password: "" }); } catch (er) { toast.error(toMsg(er)); } finally { setBusy(false); } };
  return (<form onSubmit={save} className="max-w-md space-y-4">
    <h1 className="font-display font-extrabold text-3xl mb-4">Change password</h1>
    <div><Label>Current password</Label><Input type="password" required value={f.current_password} onChange={(e) => setF({ ...f, current_password: e.target.value })} data-testid="cur-pw" /></div>
    <div><Label>New password</Label><Input type="password" required minLength={6} value={f.new_password} onChange={(e) => setF({ ...f, new_password: e.target.value })} data-testid="new-pw" /></div>
    <Button type="submit" disabled={busy} className="bg-brand" data-testid="save-pw">{busy ? "Saving..." : "Update password"}</Button>
  </form>);
}

export function Notifications() {
  const [items, setItems] = useState(null);
  useEffect(() => { api.get("/notifications").then((r) => setItems(r.data)); }, []);
  if (!items) return <Skeleton className="h-64 rounded-2xl" />;
  return (<div>
    <h1 className="font-display font-extrabold text-3xl mb-6">Notifications</h1>
    {items.length === 0 ? <div className="text-slate-500">No notifications.</div> :
    <div className="space-y-2">{items.map((n) => (
      <div key={n.id} className={`p-4 border rounded-xl ${n.read ? "border-slate-200 bg-white" : "border-brand/30 bg-brand/5"}`}>
        <div className="font-semibold">{n.title}</div><div className="text-sm text-slate-600">{n.message}</div>
        <div className="text-xs text-slate-400 mt-1">{new Date(n.created_at).toLocaleString()}</div>
      </div>))}</div>}
  </div>);
}

export function MyReviews() {
  const [items, setItems] = useState(null);
  useEffect(() => { api.get("/reviews/mine").then((r) => setItems(r.data)); }, []);
  if (!items) return <Skeleton className="h-64 rounded-2xl" />;
  return (<div>
    <h1 className="font-display font-extrabold text-3xl mb-6">Reviews</h1>
    {items.length === 0 ? <div className="text-slate-500">No reviews yet.</div> :
    <div className="space-y-3">{items.map((r) => (
      <div key={r.id} className="p-5 border border-slate-200 rounded-xl bg-white">
        <div className="flex items-center gap-1 mb-2 text-accent-orange">{Array.from({ length: r.rating }).map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
        <div className="text-sm">{r.comment}</div><div className="text-xs text-slate-400 mt-2">{new Date(r.created_at).toLocaleDateString()}</div>
      </div>))}</div>}
  </div>);
}

export function MyPayments() {
  const [items, setItems] = useState(null);
  useEffect(() => { api.get("/payments/mine").then((r) => setItems(r.data)); }, []);
  if (!items) return <Skeleton className="h-64 rounded-2xl" />;
  return (<div>
    <h1 className="font-display font-extrabold text-3xl mb-6">Payment history</h1>
    {items.length === 0 ? <div className="text-slate-500">No payments yet.</div> :
    <div className="border border-slate-200 rounded-2xl bg-white overflow-hidden"><table className="w-full text-sm">
      <thead className="bg-slate-50"><tr><th className="text-left px-4 py-3">Date</th><th className="text-left px-4 py-3">Amount</th><th className="text-left px-4 py-3">Status</th><th className="text-left px-4 py-3">Session</th></tr></thead>
      <tbody className="divide-y">{items.map((p) => (<tr key={p.session_id}>
        <td className="px-4 py-3">{new Date(p.created_at).toLocaleDateString()}</td>
        <td className="px-4 py-3">₹{p.amount}</td>
        <td className="px-4 py-3"><Badge className={p.payment_status === "paid" ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"}>{p.payment_status}</Badge></td>
        <td className="px-4 py-3 text-xs text-slate-500">{p.session_id.slice(0, 20)}...</td>
      </tr>))}</tbody></table></div>}
  </div>);
}
