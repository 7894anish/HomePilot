import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "sonner";
import Home from "@/pages/Home";
import Services from "@/pages/Services";
import ServiceDetail from "@/pages/ServiceDetail";
import About from "@/pages/About";
import Contact from "@/pages/Contact";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import BookService from "@/pages/BookService";
import { PaymentSuccess, PaymentCancel } from "@/pages/Payment";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import DashboardLayout from "@/components/DashboardLayout";
import {
  CustomerOverview, MyBookings, BookingDetail, TechnicianOverview, TechnicianJobs,
  AdminOverview, AdminBookings, AdminList, Profile, ChangePassword, Notifications, MyReviews, MyPayments,
} from "@/pages/dashboards";

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Toaster position="top-right" richColors />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/services" element={<Services />} />
            <Route path="/services/:id" element={<ServiceDetail />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/book/:id" element={<ProtectedRoute roles={["customer"]}><BookService /></ProtectedRoute>} />
            <Route path="/payment/success" element={<ProtectedRoute><PaymentSuccess /></ProtectedRoute>} />
            <Route path="/payment/cancel" element={<ProtectedRoute><PaymentCancel /></ProtectedRoute>} />

            {/* Customer dashboard */}
            <Route path="/dashboard" element={<ProtectedRoute roles={["customer"]}><DashboardLayout role="customer" /></ProtectedRoute>}>
              <Route index element={<CustomerOverview />} />
              <Route path="bookings" element={<MyBookings />} />
              <Route path="payments" element={<MyPayments />} />
              <Route path="reviews" element={<MyReviews />} />
              <Route path="notifications" element={<Notifications />} />
            </Route>

            {/* Technician dashboard */}
            <Route path="/technician" element={<ProtectedRoute roles={["technician"]}><DashboardLayout role="technician" /></ProtectedRoute>}>
              <Route index element={<TechnicianOverview />} />
              <Route path="jobs" element={<TechnicianJobs />} />
              <Route path="earnings" element={<MyPayments />} />
              <Route path="reviews" element={<MyReviews />} />
              <Route path="notifications" element={<Notifications />} />
            </Route>

            {/* Admin dashboard */}
            <Route path="/admin" element={<ProtectedRoute roles={["admin"]}><DashboardLayout role="admin" /></ProtectedRoute>}>
              <Route index element={<AdminOverview />} />
              <Route path="bookings" element={<AdminBookings />} />
              <Route path="users" element={
                <AdminList endpoint="/admin/users?role=customer" title="Customers" columns={[
                  { key: "name", label: "Name" }, { key: "email", label: "Email" }, { key: "phone", label: "Phone" }, { key: "city", label: "City" },
                ]} />
              } />
              <Route path="technicians" element={
                <AdminList endpoint="/admin/users?role=technician" title="Technicians" columns={[
                  { key: "name", label: "Name" }, { key: "email", label: "Email" }, { key: "phone", label: "Phone" },
                  { key: "rating_avg", label: "Rating", render: (t) => t.rating_avg || "—" },
                ]} />
              } />
              <Route path="services" element={
                <AdminList endpoint="/services?size=200" title="Services" columns={[
                  { key: "name", label: "Name" }, { key: "price", label: "Price", render: (s) => `₹${s.price}` },
                  { key: "duration_minutes", label: "Duration (min)" },
                ]} />
              } />
              <Route path="categories" element={
                <AdminList endpoint="/categories" title="Categories" columns={[{ key: "name", label: "Name" }, { key: "slug", label: "Slug" }]} />
              } />
              <Route path="coupons" element={
                <AdminList endpoint="/coupons" title="Coupons" columns={[
                  { key: "code", label: "Code" }, { key: "discount_percent", label: "Discount %" }, { key: "min_order", label: "Min order" },
                ]} />
              } />
              <Route path="cities" element={
                <AdminList endpoint="/cities" title="Cities" columns={[{ key: "name", label: "Name" }, { key: "state", label: "State" }]} />
              } />
              <Route path="reviews" element={
                <AdminList endpoint="/admin/reviews" title="Reviews" columns={[
                  { key: "customer_name", label: "Customer" }, { key: "rating", label: "Rating" }, { key: "comment", label: "Comment" },
                ]} />
              } />
              <Route path="contact" element={
                <AdminList endpoint="/admin/contact" title="Contact requests" canDelete={false} columns={[
                  { key: "name", label: "Name" }, { key: "email", label: "Email" }, { key: "subject", label: "Subject" }, { key: "message", label: "Message" },
                ]} />
              } />
            </Route>

            {/* Shared authenticated */}
            <Route path="/bookings/:id" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
              <Route index element={<BookingDetail />} />
            </Route>
            <Route path="/profile" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
              <Route index element={<Profile />} />
            </Route>
            <Route path="/change-password" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
              <Route index element={<ChangePassword />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}
export default App;
