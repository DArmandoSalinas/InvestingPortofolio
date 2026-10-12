import { signOut } from "@/app/(studio)/actions";
import { savePassword } from "./actions";

const KNOWN: Record<string, string> = {
  distinta: "Las dos contraseñas no coinciden.",
};

export default async function ChangePasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  const error = params.error ? (KNOWN[params.error] ?? params.error) : undefined;

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col px-4 pb-10 pt-16 sm:px-8 sm:pt-28">
      <p className="text-[11px] uppercase tracking-[0.18em] text-faint">Inversión</p>
      <h1 className="mt-4 text-4xl font-light tracking-tight sm:text-5xl">Nueva contraseña</h1>
      <p className="mt-4 text-base leading-6 text-muted">
        Antes de usar la plataforma elige una contraseña propia. Mínimo 8 caracteres, con mayúscula,
        minúscula y un número.
      </p>
      {error ? <p className="mt-6 text-sm text-ink">{error}</p> : null}
      <form action={savePassword} className="mt-10 flex flex-col gap-3">
        <label className="text-xs uppercase tracking-[0.14em] text-faint" htmlFor="password">
          Contraseña nueva
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm text-ink outline-none"
        />
        <label className="mt-2 text-xs uppercase tracking-[0.14em] text-faint" htmlFor="confirm">
          Repite la contraseña
        </label>
        <input
          id="confirm"
          name="confirm"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm text-ink outline-none"
        />
        <button type="submit" className="mt-2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-black">
          Guardar y entrar de nuevo
        </button>
      </form>
      <form action={signOut} className="mt-6">
        <button type="submit" className="text-sm text-muted hover:text-ink">
          Salir
        </button>
      </form>
    </main>
  );
}
