import React from "react";
import { MessageCircle, Phone } from "lucide-react";

export function FloatingButtons() {
  return (
    <div className="fixed bottom-6 right-6 z-40 flex flex-col gap-3">
      <a
        href="https://wa.me/919000000000"
        target="_blank"
        rel="noreferrer"
        aria-label="WhatsApp"
        data-testid="floating-whatsapp"
        className="h-13 w-13 h-14 w-14 rounded-full bg-[#25D366] text-white grid place-items-center shadow-lg hover:scale-105 transition-transform"
      >
        <MessageCircle className="h-6 w-6" />
      </a>
      <a
        href="tel:+919000000000"
        aria-label="Call now"
        data-testid="floating-call"
        className="h-14 w-14 rounded-full bg-brand text-white grid place-items-center shadow-lg hover:scale-105 transition-transform"
      >
        <Phone className="h-6 w-6" />
      </a>
    </div>
  );
}
