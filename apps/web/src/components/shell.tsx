import { Disclaimer } from "@/components/disclaimer";
import { NavLinks } from "@/components/nav-links";
import { ThemeToggle } from "@/components/theme-toggle";
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
    <div className="mx-auto flex min-h-screen max-w-[1520px] flex-col px-4 sm:px-6 lg:px-12">
      <header className="flex flex-col gap-4 border-b border-line py-5 sm:py-6">
        <div className="flex items-center gap-4">
          <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-accent">Inversión</p>
          <div className="ml-auto flex items-center gap-3">
            <ThemeToggle />
            <p className="hidden max-w-[14rem] truncate text-xs text-faint sm:block">{email}</p>
            <form action={signOut}>
              <button type="submit" className="text-sm text-muted hover:text-ink">
                Salir
              </button>
            </form>
          </div>
        </div>
        <NavLinks role={role} />
      </header>
      <main className="flex-1 py-8 sm:py-10">{children}</main>
      <footer className="border-t border-line py-6">
        <Disclaimer />
      </footer>
    </div>
  );
}
