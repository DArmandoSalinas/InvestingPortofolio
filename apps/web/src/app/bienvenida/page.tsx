import { redirect } from "next/navigation";
import { Disclaimer } from "@/components/disclaimer";
import { createClient } from "@/lib/supabase/server";
import { setPassword } from "./actions";

const ERRORS: Record<string, string> = {
  session: "No hay una sesión activa.",
  password: "La contraseña debe tener al menos 8 caracteres.",
  match: "Las contraseñas no coinciden.",
  update: "No se pudo actualizar la contraseña.",
};

export default async function WelcomePage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?error=session");
  }

  const params = await searchParams;
  const error = params.error ? ERRORS[params.error] : undefined;

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col px-4 pb-10 pt-28 sm:px-8">
      <p className="text-[11px] uppercase tracking-[0.18em] text-faint">Inversión</p>
      <h1 className="mt-4 text-4xl font-light tracking-tight sm:text-5xl">Establece tu contraseña</h1>
      <p className="mt-4 text-base text-muted">
        Crea una contraseña para acceder a la plataforma.
      </p>

      {error ? <p className="mt-6 text-sm text-ink">{error}</p> : null}

      <form action={setPassword} className="mt-10 flex flex-col gap-6">
        <div className="flex flex-col gap-3">
          <label className="text-xs uppercase tracking-[0.14em] text-faint" htmlFor="password">
            Nueva contraseña
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
        </div>

        <div className="flex flex-col gap-3">
          <label className="text-xs uppercase tracking-[0.14em] text-faint" htmlFor="confirm">
            Confirmar contraseña
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
        </div>

        <div className="rounded-2xl border border-line bg-surface px-4 py-3 text-xs leading-5 text-muted">
          <p className="font-medium text-ink">Requisitos de la contraseña:</p>
          <ul className="mt-2 list-inside list-disc space-y-1">
            <li>Mínimo 8 caracteres</li>
          </ul>
        </div>

        <button
          type="submit"
          className="mt-2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-black"
        >
          Establecer contraseña
        </button>
      </form>

      <div className="mt-auto pt-16">
        <Disclaimer />
      </div>
    </main>
  );
}
