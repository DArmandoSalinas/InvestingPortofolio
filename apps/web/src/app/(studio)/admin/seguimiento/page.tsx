import Link from "next/link";
import { redirect } from "next/navigation";
import { addWatch, saveRules, toggleWatch } from "./actions";
import { apiGet } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";
import type { SignalSettings } from "@/lib/types";

function percentField(rate: number) {
  return new Intl.NumberFormat("es-MX", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    useGrouping: false,
  }).format(rate * 100);
}

export default async function TrackingPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
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
  const settings = await apiGet<SignalSettings>("/admin/settings");

  return (
    <div className="mx-auto flex max-w-3xl flex-col">
      <Link href="/admin/acceso" className="text-sm text-muted">
        Acceso
      </Link>
      <h1 className="mt-6 text-5xl font-light tracking-tight">Seguimiento</h1>
      <p className="mt-4 max-w-lg text-sm leading-6 text-muted">
        La comisión y el horizonte aplican a las señales nuevas. Las que ya existen conservan la
        comisión con la que se guardaron. Quitar un activo no borra su señal abierta.
      </p>
      {params.error ? <p className="mt-6 text-sm text-ink">{params.error}</p> : null}

      <form action={saveRules} className="mt-10 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Comisión acciones (%)
          <input
            name="stock_percent"
            type="number"
            min="0"
            max="5"
            step="0.01"
            required
            defaultValue={percentField(settings.stock_commission)}
            className="w-40 rounded-2xl border border-line bg-surface px-4 py-3 text-sm normal-case tracking-normal text-ink"
          />
        </label>
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Comisión crypto (%)
          <input
            name="crypto_percent"
            type="number"
            min="0"
            max="5"
            step="0.01"
            required
            defaultValue={percentField(settings.crypto_commission)}
            className="w-40 rounded-2xl border border-line bg-surface px-4 py-3 text-sm normal-case tracking-normal text-ink"
          />
        </label>
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Sesiones
          <input
            name="horizon_sessions"
            type="number"
            min="1"
            max="30"
            step="1"
            required
            defaultValue={settings.horizon_sessions}
            className="w-28 rounded-2xl border border-line bg-surface px-4 py-3 text-sm normal-case tracking-normal text-ink"
          />
        </label>
        <button type="submit" className="rounded-full bg-ink px-5 py-3 text-sm font-medium text-black">
          Guardar
        </button>
      </form>

      <form action={addWatch} className="mt-12 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Símbolo
          <input
            name="symbol"
            required
            className="w-32 rounded-2xl border border-line bg-surface px-4 py-3 text-sm normal-case tracking-normal text-ink"
          />
        </label>
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Nombre
          <input
            name="name"
            required
            className="w-56 rounded-2xl border border-line bg-surface px-4 py-3 text-sm normal-case tracking-normal text-ink"
          />
        </label>
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Tipo
          <select
            name="asset_class"
            defaultValue="stock"
            className="rounded-2xl border border-line bg-black px-4 py-3 text-sm normal-case tracking-normal"
          >
            <option value="stock">Acción</option>
            <option value="crypto">Crypto</option>
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
              <th className="px-4 py-3 font-medium">Activo</th>
              <th className="px-4 py-3 font-medium">Tipo</th>
              <th className="px-4 py-3 font-medium">Estado</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {settings.watchlist.map((item) => (
              <tr key={item.yahoo_symbol} className="border-b border-line last:border-0">
                <td className="px-4 py-3">
                  <span className="tabular-nums">{item.symbol}</span>
                  <span className="ml-3 text-muted">{item.name}</span>
                </td>
                <td className="px-4 py-3 text-muted">
                  {item.asset_class === "crypto" ? "Crypto" : "Acción"}
                </td>
                <td className="px-4 py-3 text-muted">{item.active ? "Activo" : "Pausado"}</td>
                <td className="px-4 py-3 text-right">
                  <form action={toggleWatch}>
                    <input type="hidden" name="yahoo_symbol" value={item.yahoo_symbol} />
                    <input type="hidden" name="active" value={item.active ? "false" : "true"} />
                    <button type="submit" className="text-sm text-muted hover:text-ink">
                      {item.active ? "Pausar" : "Activar"}
                    </button>
                  </form>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
