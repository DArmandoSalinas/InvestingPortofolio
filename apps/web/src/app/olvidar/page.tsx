import Link from "next/link";
import { requestReset } from "./actions";

export default async function ForgotPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col px-4 pb-10 pt-16 sm:px-8 sm:pt-28">
      <p className="text-[11px] uppercase tracking-[0.18em] text-faint">Inversión</p>
      <h1 className="mt-4 text-4xl font-light tracking-tight sm:text-5xl">Restablecer contraseña</h1>
      <p className="mt-4 text-base leading-6 text-muted">
        Te mandamos un enlace a tu correo. Al abrirlo podrás elegir una contraseña nueva.
      </p>
      {params.error ? <p className="mt-6 text-sm text-ink">Escribe un correo válido.</p> : null}
      <form action={requestReset} className="mt-10 flex flex-col gap-3">
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
        <button type="submit" className="mt-2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-black">
          Enviar enlace
        </button>
      </form>
      <Link href="/login" className="mt-6 text-sm text-muted hover:text-ink">
        Volver a entrar
      </Link>
    </main>
  );
}
