"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Ranking", match: (path: string) => path === "/" },
  { href: "/senales", label: "Señales", match: (path: string) => path.startsWith("/senales") },
  { href: "/historial", label: "Historial", match: (path: string) => path.startsWith("/historial") },
  { href: "/resumen", label: "Qué ver hoy", match: (path: string) => path.startsWith("/resumen") },
  { href: "/perfil", label: "Perfil", match: (path: string) => path.startsWith("/perfil") },
  { href: "/portafolio", label: "Portafolio", match: (path: string) => path.startsWith("/portafolio") },
] as const;

export function NavLinks({ role }: { role: string }) {
  const pathname = usePathname();

  return (
    <nav
      className="-mx-1 flex max-w-full items-center gap-1 overflow-x-auto px-1 pb-1 text-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      aria-label="Principal"
    >
      {LINKS.map((link) => {
        const active = link.match(pathname);
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`whitespace-nowrap rounded-full px-3 py-1.5 transition-colors ${
              active ? "bg-raised text-ink" : "text-muted hover:text-ink"
            }`}
          >
            {link.label}
          </Link>
        );
      })}
      {role === "admin" ? (
        <Link
          href="/admin/acceso"
          className={`whitespace-nowrap rounded-full px-3 py-1.5 transition-colors ${
            pathname.startsWith("/admin") ? "bg-raised text-ink" : "text-muted hover:text-ink"
          }`}
        >
          Acceso
        </Link>
      ) : null}
    </nav>
  );
}
