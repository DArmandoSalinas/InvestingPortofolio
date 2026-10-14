import Link from "next/link";
import { Disclaimer } from "@/components/disclaimer";
import { continueWithGoogle, signIn } from "./actions";

const ERRORS: Record<string, string> = {
  invitacion: "Este correo no tiene invitación.",
  revocado: "Tu acceso fue revocado.",
  google: "Google todavía no está configurado.",
  correo: "Escribe el correo y la contraseña.",
  credenciales: "Correo o contraseña incorrectos.",
  enlace: "El enlace no es válido o ya venció.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; cambiada?: string; enviado?: string }>;
}) {
  const params = await searchParams;
  const error = params.error ? ERRORS[params.error] : undefined;

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col px-4 pb-10 pt-16 sm:px-8 sm:pt-28">
      <p className="text-[11px] uppercase tracking-[0.18em] text-faint">Inversión</p>
      <h1 className="mt-4 text-4xl font-light tracking-tight sm:text-5xl">Iniciar sesión</h1>
      <p className="mt-4 text-base leading-6 text-muted">
        El acceso es por invitación. Entra con el correo y la contraseña que te enviamos.
      </p>

      {params.cambiada === "1" ? (
        <p className="mt-8 text-sm leading-6 text-ink">Contraseña actualizada. Entra con la nueva.</p>
      ) : null}
      {params.enviado === "1" ? (
        <p className="mt-8 text-sm leading-6 text-ink">
          Si ese correo está invitado, la contraseña temporal llega en unos minutos. Entra con ella y
          cámbiala al iniciar sesión.
        </p>
      ) : null}
      {error ? <p className="mt-6 text-sm text-ink">{error}</p> : null}

      <form action={signIn} className="mt-10 flex flex-col gap-3">
        <label className="text-xs uppercase tracking-[0.14em] text-faint" htmlFor="email">
          Correo
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="username"
          className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm text-ink outline-none"
        />
        <label className="mt-2 text-xs uppercase tracking-[0.14em] text-faint" htmlFor="password">
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
        <button
          type="submit"
          className="mt-2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-black"
        >
          Entrar
        </button>
      </form>

      <Link href="/olvidar" className="mt-4 text-sm text-muted hover:text-ink">
        ¿Olvidaste tu contraseña?
      </Link>

      <form action={continueWithGoogle} className="mt-6">
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
