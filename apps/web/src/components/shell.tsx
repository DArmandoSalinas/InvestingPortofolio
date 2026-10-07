import { Disclaimer } from "@/components/disclaimer";
import { NavLinks } from "@/components/nav-links";
import { signOut } from "@/app/(studio)/actions";

export function Shell({
  email,
  role,
  children,
}: {
  email: string;
  role: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto flex min-h-screen max-w-[1520px] flex-col px-8 lg:px-12">
      <header className="flex items-center gap-8 py-6">
        <p className="text-[11px] uppercase tracking-[0.18em] text-faint">Inversión</p>
        <NavLinks role={role} />
        <div className="ml-auto flex items-center gap-4">
          <p className="text-xs text-faint">{email}</p>
          <form action={signOut}>
            <button type="submit" className="text-sm text-muted hover:text-ink">
              Salir
            </button>
          </form>
        </div>
      </header>
      <main className="flex-1 pb-12">{children}</main>
      <footer className="border-t border-line py-6">
        <Disclaimer />
      </footer>
    </div>
  );
}
