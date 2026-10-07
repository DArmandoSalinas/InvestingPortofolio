import { Disclaimer } from "@/components/disclaimer";
import { continueWithGoogle, sendLink } from "./actions";

const ERRORS: Record<string, string> = {
  invitacion: "Este correo no tiene invitación.",
  revocado: "Tu acceso fue revocado.",
  google: "Google todavía no está configurado.",
  envio: "No se pudo enviar el enlace.",
  correo: "Escribe un correo válido.",
  enlace: "El enlace no es válido o ya venció.",
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
    <main className="mx-auto flex min-h-screen max-w-xl flex-col px-8 pb-10 pt-28">
      <p className="text-[11px] uppercase tracking-[0.18em] text-faint">Inversión</p>
      <h1 className="mt-4 text-5xl font-light tracking-tight">Iniciar sesión</h1>
      <p className="mt-4 text-base text-muted">El acceso es por invitación.</p>

      {sent ? (
        <p className="mt-10 text-sm leading-6 text-ink">
          Si ese correo está invitado, el enlace llega en unos minutos.
        </p>
      ) : null}
      {error ? <p className="mt-6 text-sm text-ink">{error}</p> : null}

      <form action={sendLink} className="mt-10 flex flex-col gap-3">
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
        <button
          type="submit"
          className="mt-2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-black"
        >
          Enviar enlace
        </button>
      </form>

      <form action={continueWithGoogle} className="mt-3">
        <button
          type="submit"
          className="w-full rounded-full border border-line px-5 py-3 text-sm text-ink"
        >
          Continuar con Google
        </button>
      </form>

      <div className="mt-auto pt-16">
        <Disclaimer />
      </div>
    </main>
  );
}
