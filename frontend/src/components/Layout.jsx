import React from "react";
import Navbar from "./Navbar";
import Footer from "./Footer";
import { FloatingButtons } from "./FloatingButtons";

export default function Layout({ children, hideFooter }) {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navbar />
      <main className="flex-1">{children}</main>
      {!hideFooter && <Footer />}
      <FloatingButtons />
    </div>
  );
}
