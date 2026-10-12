import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { invite, resendLink, updateAccess } from "./actions";
import { apiGet } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";

type AccessList = {
  entries: {
    email: string;
    role: "admin" | "member";
    active: boolean;
    protected: boolean;
  }[];
};

export default async function AccessPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; enviado?: string }>;
}) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const { data: profile } = user
    ? await supabase.from("profiles").select("role").eq("user_id", user.id).maybeSingle()
    : { data: null };

  if (profile?.role !== "admin") {
    redirect("/");
  }

  const params = await searchParams;
  const list = await apiGet<AccessList>("/admin/access");
  const flashRaw = (await cookies()).get("invite_flash")?.value;
  let flash: { email?: string; password?: string } | null = null;
  if (flashRaw) {
    try {
      flash = JSON.parse(flashRaw) as { email?: string; password?: string };
    } catch {
      flash = null;
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col">
      <div className="flex gap-4 text-sm text-muted">
        <span className="text-ink">Acceso</span>
        <Link href="/admin/seguimiento" className="hover:text-ink">
          Seguimiento
        </Link>
      </div>
      <h1 className="mt-6 text-4xl font-light tracking-tight sm:text-5xl">Acceso</h1>
      <p className="mt-4 max-w-lg text-sm leading-6 text-muted">
        Al agregar un correo se crea la cuenta y se manda una contraseña temporal. Quien la recibe
        tiene que cambiarla en el primer inicio de sesión. Solo esta lista puede entrar.
      </p>
      {params.error ? <p className="mt-6 text-sm text-ink">{params.error}</p> : null}
      {params.enviado === "correo" ? (
        <p className="mt-6 text-sm text-muted">La invitación ya salió hacia ese correo.</p>
      ) : null}
      {params.enviado === "local" ? (
        <p className="mt-6 text-sm text-muted">
          La invitación se generó en la bandeja local. Hasta que SMTP esté configurado no llega a la
          bandeja real.
        </p>
      ) : null}
      {params.enviado === "error" ? (
        <p className="mt-6 text-sm text-ink">No se pudo enviar el correo. Usa la contraseña de abajo.</p>
      ) : null}
      {flash?.password ? (
        <p className="mt-6 text-sm leading-6 text-ink">
          Contraseña temporal de {flash.email}:{" "}
          <span className="font-medium tracking-wide">{flash.password}</span>
          . Cópiala si el correo no llega. Desaparece de esta pantalla en unos minutos.
        </p>
      ) : null}

      <form action={invite} className="mt-10 grid grid-cols-1 items-end gap-3 sm:flex sm:flex-wrap">
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Correo
          <input
            name="email"
            type="email"
            required
            className="w-full rounded-2xl border border-line bg-surface px-4 py-3 text-sm normal-case tracking-normal text-ink sm:w-72"
          />
        </label>
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Rol
          <select
            name="role"
            defaultValue="member"
            className="rounded-2xl border border-line bg-black px-4 py-3 text-sm normal-case tracking-normal"
          >
            <option value="member">Miembro</option>
            <option value="admin">Administrador</option>
          </select>
        </label>
        <button type="submit" className="rounded-full bg-ink px-5 py-3 text-sm font-medium text-black">
          Agregar
        </button>
      </form>

      <div className="mt-8 overflow-hidden rounded-[28px] border border-line bg-surface">
        <table className="w-full text-left text-sm">
          <thead className="text-[11px] uppercase tracking-[0.14em] text-faint">
            <tr className="border-b border-line">
              <th className="px-4 py-3 font-medium">Correo</th>
              <th className="px-4 py-3 font-medium">Rol</th>
              <th className="px-4 py-3 font-medium">Estado</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {list.entries.map((entry) => (
              <tr key={entry.email} className="border-b border-line last:border-b-0">
                <td className="px-4 py-3">{entry.email}</td>
                <td className="px-4 py-3 text-muted">
                  {entry.protected ? (
                    "Administrador de arranque"
                  ) : (
                    <form action={updateAccess} className="flex items-center gap-2">
                      <input type="hidden" name="email" value={entry.email} />
                      <select
                        name="role"
                        defaultValue={entry.role}
                        className="rounded-full border border-line bg-black px-3 py-1.5 text-sm"
                      >
                        <option value="member">Miembro</option>
                        <option value="admin">Administrador</option>
                      </select>
                      <button type="submit" className="text-xs text-muted hover:text-ink">
                        Guardar rol
                      </button>
                    </form>
                  )}
                </td>
                <td className="px-4 py-3 text-muted">{entry.active ? "Activo" : "Revocado"}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-4">
                    {entry.active ? (
                      <form action={resendLink}>
                        <input type="hidden" name="email" value={entry.email} />
                        <button type="submit" className="text-sm text-muted hover:text-ink">
                          Reenviar invitación
                        </button>
                      </form>
                    ) : null}
                    {entry.protected ? null : (
                      <form action={updateAccess}>
                        <input type="hidden" name="email" value={entry.email} />
                        <input type="hidden" name="active" value={entry.active ? "false" : "true"} />
                        <button type="submit" className="text-sm text-muted hover:text-ink">
                          {entry.active ? "Revocar" : "Reactivar"}
                        </button>
                      </form>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
