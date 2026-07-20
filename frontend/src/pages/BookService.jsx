import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { toMsg } from "@/lib/api";
import Layout from "@/components/Layout";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { toast } from "sonner";
import { format } from "date-fns";
import { CalendarIcon, ChevronLeft, ChevronRight, Check, IndianRupee } from "lucide-react";

const TIMES = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00"];

export default function BookService() {
  const { id } = useParams();
  const nav = useNavigate();
  const [service, setService] = useState(null);
  const [cities, setCities] = useState([]);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [couponBusy, setCouponBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [discount, setDiscount] = useState(0);

  const [f, setF] = useState({
    scheduled_date: null,
    scheduled_time: "",
    city: "",
    address: "",
    problem_description: "",
    images: [],
    coupon_code: "",
    payment_method: "cash",
  });

  useEffect(() => {
    Promise.all([api.get(`/services/${id}`), api.get("/cities")]).then(([s, c]) => {
      setService(s.data.service);
      setCities(c.data);
    });
  }, [id]);

  const applyCoupon = async () => {
    if (!f.coupon_code) return;
    setCouponBusy(true);
    try {
      const { data } = await api.post("/coupons/validate", { code: f.coupon_code, amount: service.price });
      setDiscount(data.discount);
      toast.success(`Coupon applied: ₹${data.discount} off`);
    } catch (err) {
      setDiscount(0);
      toast.error(toMsg(err));
    } finally {
      setCouponBusy(false);
    }
  };

  const handleFiles = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setUploading(true);
    try {
      const uploaded = [];
      for (const file of files) {
        const fd = new FormData();
        fd.append("file", file);
        const { data } = await api.post("/upload", fd, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        uploaded.push(`${process.env.REACT_APP_BACKEND_URL}${data.url}`);
      }
      setF((prev) => ({ ...prev, images: [...prev.images, ...uploaded] }));
      toast.success(`${uploaded.length} image(s) uploaded`);
    } catch (err) {
      toast.error(toMsg(err));
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const total = service ? Math.max(0, service.price - discount) : 0;

  const submit = async () => {
    setBusy(true);
    try {
      const payload = {
        service_id: id,
        scheduled_date: format(f.scheduled_date, "yyyy-MM-dd"),
        scheduled_time: f.scheduled_time,
        address: f.address,
        city: f.city,
        problem_description: f.problem_description,
        images: f.images,
        coupon_code: f.coupon_code || null,
        payment_method: f.payment_method,
      };
      const { data: booking } = await api.post("/bookings", payload);
      if (f.payment_method === "online") {
        const { data } = await api.post("/payments/checkout", {
          booking_id: booking.id,
          origin_url: window.location.origin,
        });
        window.location.href = data.checkout_url;
      } else {
        toast.success("Booking confirmed!");
        nav(`/bookings/${booking.id}`);
      }
    } catch (err) {
      toast.error(toMsg(err));
    } finally {
      setBusy(false);
    }
  };

  const canNext = () => {
    if (step === 0) return f.scheduled_date && f.scheduled_time;
    if (step === 1) return f.city && f.address.trim().length > 5;
    if (step === 2) return f.problem_description.trim().length > 5;
    return true;
  };

  if (!service) {
    return <Layout><div className="max-w-4xl mx-auto px-6 py-10"><Skeleton className="h-96 rounded-2xl" /></div></Layout>;
  }

  const steps = ["Date & time", "Address", "Details", "Payment"];

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
        <h1 className="font-display font-extrabold text-3xl">Book — {service.name}</h1>
        <div className="mt-6 flex items-center justify-between">
          {steps.map((s, i) => (
            <div key={s} className="flex-1 flex items-center">
              <div className={`h-9 w-9 rounded-full grid place-items-center text-sm font-semibold ${i <= step ? "bg-brand text-white" : "bg-slate-100 text-slate-500"}`}>
                {i < step ? <Check className="h-4 w-4" /> : i + 1}
              </div>
              <div className={`ml-3 hidden sm:block text-sm ${i === step ? "text-brand font-semibold" : "text-slate-500"}`}>{s}</div>
              {i < steps.length - 1 && <div className="flex-1 h-px bg-slate-200 mx-3" />}
            </div>
          ))}
        </div>
        <Progress value={((step + 1) / steps.length) * 100} className="mt-4" />

        <div className="mt-8 grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 p-6 sm:p-8 border border-slate-200 rounded-2xl bg-white">
            {step === 0 && (
              <div className="space-y-6">
                <div>
                  <Label>Select date</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="w-full justify-start h-11 mt-1" data-testid="date-picker-btn">
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {f.scheduled_date ? format(f.scheduled_date, "PPP") : "Pick a date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={f.scheduled_date}
                        onSelect={(d) => setF({ ...f, scheduled_date: d })}
                        disabled={(d) => d < new Date(new Date().setHours(0, 0, 0, 0))}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
                <div>
                  <Label className="mb-2 block">Select time slot</Label>
                  <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                    {TIMES.map((t) => (
                      <button
                        key={t}
                        onClick={() => setF({ ...f, scheduled_time: t })}
                        data-testid={`time-${t}`}
                        className={`px-3 py-2 rounded-lg border text-sm ${f.scheduled_time === t ? "bg-brand text-white border-brand" : "border-slate-200 hover:border-brand"}`}
                      >{t}</button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {step === 1 && (
              <div className="space-y-5">
                <div>
                  <Label>City</Label>
                  <Select value={f.city} onValueChange={(v) => setF({ ...f, city: v })}>
                    <SelectTrigger className="h-11 mt-1" data-testid="city-select"><SelectValue placeholder="Select your city" /></SelectTrigger>
                    <SelectContent>
                      {cities.map((c) => <SelectItem key={c.id} value={c.name}>{c.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Full address</Label>
                  <Textarea rows={4} value={f.address} onChange={(e) => setF({ ...f, address: e.target.value })} placeholder="House / flat number, street, area, pincode..." data-testid="address-input" />
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-5">
                <div>
                  <Label>Describe the problem</Label>
                  <Textarea rows={5} value={f.problem_description} onChange={(e) => setF({ ...f, problem_description: e.target.value })} placeholder="Tell us more so we send the right pro..." data-testid="problem-input" />
                </div>
                <div>
                  <Label>Upload images (optional)</Label>
                  <div className="flex items-center gap-3 mt-1">
                    <label className="inline-flex items-center gap-2 px-4 h-10 rounded-lg border border-dashed border-slate-300 hover:border-brand cursor-pointer text-sm" data-testid="images-file-label">
                      <span>{uploading ? "Uploading..." : "Choose files"}</span>
                      <input
                        type="file"
                        accept="image/*"
                        multiple
                        className="hidden"
                        disabled={uploading}
                        onChange={handleFiles}
                        data-testid="images-file-input"
                      />
                    </label>
                    <span className="text-xs text-slate-500">JPG / PNG / WebP · up to 5 MB each</span>
                  </div>
                  {f.images.length > 0 && (
                    <div className="flex gap-2 mt-3 flex-wrap">
                      {f.images.map((u, i) => (
                        <div key={i} className="relative">
                          <img src={u} alt="" className="h-16 w-16 object-cover rounded-lg border" />
                          <button
                            type="button"
                            onClick={() => setF({ ...f, images: f.images.filter((_, j) => j !== i) })}
                            className="absolute -top-1 -right-1 h-5 w-5 grid place-items-center rounded-full bg-slate-900 text-white text-xs"
                            data-testid={`remove-image-${i}`}
                          >×</button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-5">
                <div>
                  <Label>Coupon code</Label>
                  <div className="flex gap-2 mt-1">
                    <Input value={f.coupon_code} onChange={(e) => setF({ ...f, coupon_code: e.target.value.toUpperCase() })} placeholder="WELCOME10" data-testid="coupon-input" />
                    <Button variant="outline" onClick={applyCoupon} disabled={couponBusy} data-testid="apply-coupon-btn">Apply</Button>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">Try WELCOME10, MEGA20 or FIRSTBOOK</div>
                </div>
                <div>
                  <Label className="mb-2 block">Payment method</Label>
                  <RadioGroup value={f.payment_method} onValueChange={(v) => setF({ ...f, payment_method: v })} className="space-y-3">
                    <label className={`flex items-center gap-3 p-4 border rounded-xl cursor-pointer ${f.payment_method === "online" ? "border-brand bg-brand/5" : "border-slate-200"}`}>
                      <RadioGroupItem value="online" data-testid="pay-online" />
                      <div><div className="font-medium">Pay online (Stripe)</div><div className="text-xs text-slate-500">Secure card / UPI checkout, get 90-day warranty active</div></div>
                    </label>
                    <label className={`flex items-center gap-3 p-4 border rounded-xl cursor-pointer ${f.payment_method === "cash" ? "border-brand bg-brand/5" : "border-slate-200"}`}>
                      <RadioGroupItem value="cash" data-testid="pay-cash" />
                      <div><div className="font-medium">Cash on service</div><div className="text-xs text-slate-500">Pay the pro after service completion</div></div>
                    </label>
                  </RadioGroup>
                </div>
              </div>
            )}

            <div className="mt-8 flex justify-between">
              <Button variant="ghost" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0} data-testid="wizard-back">
                <ChevronLeft className="h-4 w-4 mr-1" /> Back
              </Button>
              {step < 3 ? (
                <Button className="bg-brand hover:bg-blue-700" onClick={() => setStep(step + 1)} disabled={!canNext()} data-testid="wizard-next">
                  Continue <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              ) : (
                <Button className="bg-brand hover:bg-blue-700 h-11 px-6" onClick={submit} disabled={busy} data-testid="wizard-submit">
                  {busy ? "Processing..." : f.payment_method === "online" ? "Pay & confirm" : "Confirm booking"}
                </Button>
              )}
            </div>
          </div>

          {/* Summary */}
          <aside className="p-6 border border-slate-200 rounded-2xl bg-white h-fit sticky top-24">
            <div className="flex gap-3">
              <img src={service.image_url} alt="" className="h-16 w-16 rounded-lg object-cover" />
              <div>
                <div className="font-semibold">{service.name}</div>
                <div className="text-xs text-slate-500">~{service.duration_minutes} min</div>
              </div>
            </div>
            <div className="mt-6 space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Subtotal</span><span>₹{service.price}</span></div>
              {discount > 0 && <div className="flex justify-between text-green-600"><span>Coupon</span><span>-₹{discount}</span></div>}
              <div className="border-t pt-2 flex justify-between font-semibold text-base"><span>Total</span><span className="flex items-center"><IndianRupee className="h-4 w-4" />{total}</span></div>
            </div>
          </aside>
        </div>
      </div>
    </Layout>
  );
}
