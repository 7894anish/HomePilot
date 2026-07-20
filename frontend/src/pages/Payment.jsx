import React, { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import api from "@/lib/api";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";

export function PaymentSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [status, setStatus] = useState("polling");
  const [bookingId, setBookingId] = useState(null);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    let tries = 0;
    const poll = async () => {
      try {
        const { data } = await api.get(`/payments/status/${sessionId}`);
        if (cancelled) return;
        setBookingId(data.booking_id);
        if (data.payment_status === "paid") { setStatus("paid"); return; }
        if (data.payment_status === "failed" || data.payment_status === "expired") { setStatus("failed"); return; }
        if (++tries < 20) setTimeout(poll, 2000);
        else setStatus("timeout");
      } catch { setStatus("failed"); }
    };
    poll();
    return () => { cancelled = true; };
  }, [sessionId]);

  return (
    <Layout>
      <div className="max-w-xl mx-auto px-6 py-24 text-center">
        {status === "polling" && (<>
          <Loader2 className="h-16 w-16 animate-spin text-brand mx-auto" />
          <h1 className="mt-6 font-display font-bold text-2xl">Confirming your payment...</h1>
          <p className="text-slate-500 mt-2">Please wait, this takes a few seconds.</p>
        </>)}
        {status === "paid" && (<>
          <CheckCircle2 className="h-20 w-20 text-green-500 mx-auto" />
          <h1 className="mt-6 font-display font-extrabold text-3xl">Payment successful!</h1>
          <p className="text-slate-500 mt-2">Your booking is confirmed. A pro will be assigned shortly.</p>
          <div className="mt-8 flex gap-3 justify-center">
            {bookingId && <Link to={`/bookings/${bookingId}`}><Button className="bg-brand" data-testid="view-booking-btn">View booking</Button></Link>}
            <Link to="/dashboard"><Button variant="outline">Go to dashboard</Button></Link>
          </div>
        </>)}
        {(status === "failed" || status === "timeout") && (<>
          <XCircle className="h-20 w-20 text-red-500 mx-auto" />
          <h1 className="mt-6 font-display font-bold text-2xl">Payment not confirmed</h1>
          <p className="text-slate-500 mt-2">Please check your bookings dashboard or retry.</p>
          <Link to="/dashboard"><Button className="mt-6">Go to dashboard</Button></Link>
        </>)}
      </div>
    </Layout>
  );
}

export function PaymentCancel() {
  const [params] = useSearchParams();
  const bookingId = params.get("booking_id");
  return (
    <Layout>
      <div className="max-w-xl mx-auto px-6 py-24 text-center">
        <XCircle className="h-20 w-20 text-slate-400 mx-auto" />
        <h1 className="mt-6 font-display font-bold text-2xl">Payment cancelled</h1>
        <p className="text-slate-500 mt-2">Your booking is saved but unpaid. You can retry payment from your dashboard.</p>
        <div className="mt-6 flex gap-3 justify-center">
          {bookingId && <Link to={`/bookings/${bookingId}`}><Button className="bg-brand">View booking</Button></Link>}
          <Link to="/services"><Button variant="outline">Browse services</Button></Link>
        </div>
      </div>
    </Layout>
  );
}
