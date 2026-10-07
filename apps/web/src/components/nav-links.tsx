"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function NavLinks({ role }: { role: string }) {
  const pathname = usePathname();
  const ranking = pathname === "/";
  const signals = pathname.startsWith("/senales");
  const history = pathname.startsWith("/historial");
  const brief = pathname.startsWith("/resumen");
  const profile = pathname.startsWith("/perfil");
  const portfolio = pathname.startsWith("/portafolio");
  const access = pathname.startsWith("/admin");

  return (
    <nav className="flex items-center gap-5 text-sm">
      <Link href="/" className={ranking ? "text-ink" : "text-muted hover:text-ink"}>
        Ranking
      </Link>
      <Link href="/senales" className={signals ? "text-ink" : "text-muted hover:text-ink"}>
        Señales
      </Link>
      <Link href="/historial" className={history ? "text-ink" : "text-muted hover:text-ink"}>
        Historial
      </Link>
      <Link href="/resumen" className={brief ? "text-ink" : "text-muted hover:text-ink"}>
        Resumen
      </Link>
      <Link href="/perfil" className={profile ? "text-ink" : "text-muted hover:text-ink"}>
        Perfil
      </Link>
      <Link href="/portafolio" className={portfolio ? "text-ink" : "text-muted hover:text-ink"}>
        Portafolio
      </Link>
      {role === "admin" ? (
        <Link href="/admin/acceso" className={access ? "text-ink" : "text-muted hover:text-ink"}>
          Acceso
        </Link>
      ) : null}
    </nav>
  );
}
