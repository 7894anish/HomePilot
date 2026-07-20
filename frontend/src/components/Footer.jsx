import React from "react";
import { Link } from "react-router-dom";
import { Wrench, Phone, Mail, MapPin, Facebook, Twitter, Instagram, Linkedin } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-slate-950 text-slate-300 mt-24">
      <div className="max-w-7xl mx-auto px-6 py-16 grid gap-12 md:grid-cols-4">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="h-9 w-9 rounded-xl bg-brand grid place-items-center">
              <Wrench className="h-5 w-5 text-white" />
            </div>
            <div className="font-display font-extrabold text-xl text-white">HomeFix<span className="text-accent-orange">.</span>Pro</div>
          </div>
          <p className="text-sm text-slate-400 leading-relaxed">
            Verified pros for cleaning, plumbing, electrical, AC, appliances & more — booked in under 60 seconds.
          </p>
          <div className="flex gap-3 mt-5">
            {[Facebook, Twitter, Instagram, Linkedin].map((I, i) => (
              <a key={i} href="#" className="h-9 w-9 grid place-items-center rounded-full border border-slate-700 hover:border-brand hover:text-brand transition-colors">
                <I className="h-4 w-4" />
              </a>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-white font-semibold mb-4">Company</h4>
          <ul className="space-y-2 text-sm">
            <li><Link to="/about" className="hover:text-white">About us</Link></li>
            <li><Link to="/services" className="hover:text-white">All services</Link></li>
            <li><Link to="/contact" className="hover:text-white">Contact</Link></li>
            <li><Link to="/register" className="hover:text-white">Become a pro</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="text-white font-semibold mb-4">Top services</h4>
          <ul className="space-y-2 text-sm">
            <li><Link to="/services" className="hover:text-white">Home cleaning</Link></li>
            <li><Link to="/services" className="hover:text-white">AC repair</Link></li>
            <li><Link to="/services" className="hover:text-white">Plumbing</Link></li>
            <li><Link to="/services" className="hover:text-white">Electrical</Link></li>
            <li><Link to="/services" className="hover:text-white">Painting</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="text-white font-semibold mb-4">Reach us</h4>
          <ul className="space-y-3 text-sm">
            <li className="flex items-start gap-2"><Phone className="h-4 w-4 mt-0.5 text-brand" /> +91 90000 00000</li>
            <li className="flex items-start gap-2"><Mail className="h-4 w-4 mt-0.5 text-brand" /> hello@homefix.pro</li>
            <li className="flex items-start gap-2"><MapPin className="h-4 w-4 mt-0.5 text-brand" /> 3rd Floor, Prestige Tower, Bengaluru</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        © {new Date().getFullYear()} HomeFix Pro. All rights reserved.
      </div>
    </footer>
  );
}
