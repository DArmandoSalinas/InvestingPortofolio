"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

export function NavLinks({ role }: { role: string }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = [
    { href: "/", label: "Ranking", active: pathname === "/" },
    { href: "/senales", label: "Señales", active: pathname.startsWith("/senales") },
    { href: "/historial", label: "Historial", active: pathname.startsWith("/historial") },
    { href: "/resumen", label: "Resumen", active: pathname.startsWith("/resumen") },
    { href: "/perfil", label: "Perfil", active: pathname.startsWith("/perfil") },
    { href: "/portafolio", label: "Portafolio", active: pathname.startsWith("/portafolio") },
  ];

  const adminItems = role === "admin" 
    ? [
        { href: "/admin/acceso", label: "Acceso", active: pathname.startsWith("/admin/acceso") },
        { href: "/admin/seguimiento", label: "Seguimiento", active: pathname.startsWith("/admin/seguimiento") },
      ]
    : [];

  const allItems = [...navItems, ...adminItems];

  return (
    <>
      {/* Desktop navigation */}
      <nav className="hidden items-center gap-5 text-sm md:flex">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={item.active ? "text-ink" : "text-muted hover:text-ink"}
          >
            {item.label}
          </Link>
        ))}
        {role === "admin" && (
          <>
            <span className="mx-2 h-4 w-px bg-line" />
            {adminItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={item.active ? "text-ink" : "text-muted hover:text-ink"}
              >
                {item.label}
              </Link>
            ))}
          </>
        )}
      </nav>

      {/* Mobile menu button */}
      <button
        type="button"
        onClick={() => setMobileOpen(!mobileOpen)}
        className="md:hidden text-muted hover:text-ink p-2 -m-2"
        aria-label="Menú"
      >
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d={mobileOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"}
          />
        </svg>
      </button>

      {/* Mobile menu overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/80 md:hidden"
          onClick={() => setMobileOpen(false)}
        >
          <div
            className="absolute right-0 top-0 h-full w-64 bg-[#0a0a0a] border-l border-line"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-line">
              <span className="text-xs uppercase tracking-[0.18em] text-faint">Menú</span>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="text-muted hover:text-ink p-2"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <nav className="flex flex-col p-2">
              {allItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`rounded-lg px-4 py-3 text-sm transition-colors ${
                    item.active
                      ? "bg-white/[0.08] text-ink"
                      : "text-muted hover:text-ink"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </div>
      )}
    </>
  );
}
