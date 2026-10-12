import { Disclaimer } from "@/components/disclaimer";
import { signInWithPassword, resetPassword, sendLink } from "./actions";

const ERRORS: Record<string, string> = {
  invitacion: "Este correo no tiene invitación.",
  revocado: "Tu acceso fue revocado.",
  credentials: "Correo o contraseña incorrectos.",
  correo: "Escribe un correo válido.",
  enlace: "El enlace no es válido o ya venció.",
  session: "Tu sesión expiró. Inicia sesión de nuevo.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; sent?: string }>;
}) {
  const params = await searchParams;
  const error = params.error ? ERRORS[params.error] : undefined;
  const sent = params.sent === "1";

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col px-4 pb-10 pt-28 sm:px-8">
      <p className="text-[11px] uppercase tracking-[0.18em] text-faint">Inversión</p>
      <h1 className="mt-4 text-4xl font-light tracking-tight sm:text-5xl">Iniciar sesión</h1>
      <p className="mt-4 text-base text-muted">El acceso es por invitación.</p>

      {sent ? (
        <p className="mt-10 text-sm leading-6 text-ink">
          Revisa tu correo. El enlace para restablecer tu contraseña llega en unos minutos.
        </p>
      ) : null}
      {error ? <p className="mt-6 text-sm text-ink">{error}</p> : null}

      <form action={signInWithPassword} className="mt-10 flex flex-col gap-6">
        <div className="flex flex-col gap-3">
          <label className="text-xs uppercase tracking-[0.14em] text-faint" htmlFor="email">
            Correo
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            autoComplete="email"
            className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm text-ink outline-none"
          />
        </div>

        <div className="flex flex-col gap-3">
          <label className="text-xs uppercase tracking-[0.14em] text-faint" htmlFor="password">
            Contraseña
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            autoComplete="current-password"
            className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm text-ink outline-none"
          />
        </div>

        <button
          type="submit"
          className="mt-2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-black"
        >
          Iniciar sesión
        </button>
      </form>

      <form action={resetPassword} className="mt-4">
        <button type="submit" className="text-sm text-muted hover:text-ink">
          ¿Olvidaste tu contraseña?
        </button>
      </form>

      <details className="mt-8">
        <summary className="cursor-pointer text-sm text-muted hover:text-ink">
          Otras opciones de inicio de sesión
        </summary>
        <form action={sendLink} className="mt-4 flex flex-col gap-3">
          <label className="text-xs uppercase tracking-[0.14em] text-faint" htmlFor="magic-email">
            Correo
          </label>
          <input
            id="magic-email"
            name="email"
            type="email"
            required
            autoComplete="email"
            className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm text-ink outline-none"
          />
          <button
            type="submit"
            className="rounded-full border border-line px-5 py-3 text-sm text-ink"
          >
            Enviar enlace mágico
          </button>
        </form>
      </details>

      <div className="mt-auto pt-16">
        <Disclaimer />
      </div>
    </main>
  );
}
