import { FadeIn } from "@/components/fade-in";
import { saveProfile } from "./actions";
import { apiGet } from "@/lib/api";
import { formatAsOf } from "@/lib/labels";
import type { ProfileBoard, SleeveView } from "@/lib/types";

const GOAL = [
  { value: "preservar", label: "Cuidar el monto" },
  { value: "crecer", label: "Hacerlo crecer" },
  { value: "ingreso", label: "Recibir un flujo" },
] as const;

const RISK = [
  { value: "bajo", label: "Baja" },
  { value: "medio", label: "Media" },
  { value: "alto", label: "Alta" },
] as const;

function percent(value: number) {
  return new Intl.NumberFormat("es-MX", {
    style: "percent",
    maximumFractionDigits: 1,
    signDisplay: "exceptZero",
  }).format(value);
}

function money(value: number, currency: string) {
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function Figure({ sleeve }: { sleeve: SleeveView }) {
  if (sleeve.return_value === null || !sleeve.return_start || !sleeve.return_end) {
    return <p className="mt-3 text-sm text-faint">Sin cifra. No se inventa.</p>;
  }
  return (
    <p className="mt-3 text-sm tabular-nums text-ink">
      {percent(sleeve.return_value)}
      <span className="ml-2 font-sans text-faint">
        {formatAsOf(sleeve.return_start)} – {formatAsOf(sleeve.return_end)}
      </span>
    </p>
  );
}

export default async function ProfilePage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  const board = await apiGet<ProfileBoard>("/profile");
  const profile = board.profile;
  const allocation = board.allocation;

  return (
    <div className="flex flex-col gap-12">
      <FadeIn>
        <h1 className="text-5xl font-light tracking-tight">Perfil</h1>
        <p className="mt-3 max-w-xl text-sm leading-6 text-muted">
          El monto, el plazo y la tolerancia arman una mezcla. Las cifras de abajo son lo ya
          ocurrido, o quedan vacías.
        </p>
      </FadeIn>
      {params.error ? <p className="text-sm text-ink">{params.error}</p> : null}
      <div className="grid items-start gap-10 xl:grid-cols-[340px_1fr]">
        <form action={saveProfile} className="flex flex-col gap-4">
          <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
            Moneda
            <select
              name="currency"
              defaultValue={profile?.currency ?? "MXN"}
              className="rounded-2xl border border-line bg-black px-4 py-3 text-sm normal-case tracking-normal"
            >
              <option value="MXN">Pesos</option>
              <option value="USD">Dólares</option>
            </select>
          </label>
          <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
            Monto actual
            <input
              name="amount"
              type="number"
              min="1"
              step="1"
              required
              placeholder="Por ejemplo 100000"
              defaultValue={profile?.amount ?? ""}
              className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm tabular-nums normal-case tracking-normal text-ink"
            />
          </label>
          <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
            Aportación mensual
            <input
              name="monthly_contribution"
              type="number"
              min="0"
              step="1"
              required
              placeholder="Por ejemplo 5000. Puede ser 0."
              defaultValue={profile?.monthly_contribution ?? ""}
              className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm tabular-nums normal-case tracking-normal text-ink"
            />
          </label>
          <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
            Plazo en años
            <input
              name="horizon_years"
              type="number"
              min="1"
              max="40"
              step="1"
              required
              placeholder="Por ejemplo 10"
              defaultValue={profile?.horizon_years ?? ""}
              className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm tabular-nums normal-case tracking-normal text-ink"
            />
          </label>
          <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
            Meta
            <select
              name="goal"
              defaultValue={profile?.goal ?? "crecer"}
              className="rounded-2xl border border-line bg-black px-4 py-3 text-sm normal-case tracking-normal"
            >
              {GOAL.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
            Tolerancia
            <select
              name="risk"
              defaultValue={profile?.risk ?? "medio"}
              className="rounded-2xl border border-line bg-black px-4 py-3 text-sm normal-case tracking-normal"
            >
              {RISK.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="mt-2 w-fit rounded-full bg-ink px-5 py-3 text-sm font-medium text-black">
            Guardar perfil
          </button>
          {profile ? (
            <p className="text-xs text-faint">
              {money(profile.amount, profile.currency)} ahora
              <span className="mx-1.5">·</span>
              {money(profile.monthly_contribution, profile.currency)} al mes
              <span className="mx-1.5">·</span>
              {profile.horizon_years} años
            </p>
          ) : null}
        </form>
        <div className="flex flex-col gap-8">
          <p className="text-sm leading-6 text-muted">
            Los porcentajes de estas tarjetas son historia del mercado, con fechas reales. No son tu
            dinero, aunque el formulario todavía esté vacío.
          </p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-5">
            {board.sleeves.map((sleeve) => (
              <article key={sleeve.id} className="rounded-[28px] border border-line bg-surface px-4 py-4">
                <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">{sleeve.name}</h2>
                <Figure sleeve={sleeve} />
                <p className="mt-3 text-xs leading-5 text-muted">{sleeve.detail}</p>
                {sleeve.fit ? <p className="mt-3 text-xs leading-5 text-faint">{sleeve.fit}</p> : null}
              </article>
            ))}
          </div>
          {allocation ? (
            <section className="flex flex-col gap-4">
              <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">Mezcla</h2>
              <div className="flex h-3 gap-1">
                {allocation.sleeves
                  .filter((sleeve) => sleeve.weight > 0)
                  .map((sleeve) => (
                    <div
                      key={sleeve.id}
                      style={{ flexGrow: sleeve.weight }}
                      className="rounded-full bg-ink"
                    />
                  ))}
              </div>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
                {allocation.sleeves.map((sleeve) => {
                  const label = board.sleeves.find((item) => item.id === sleeve.id)?.name ?? sleeve.id;
                  return (
                    <div key={sleeve.id}>
                      <p className="text-sm">
                        <span className="tabular-nums">{sleeve.weight}%</span>
                        <span className="ml-2 text-muted">{label}</span>
                      </p>
                      {sleeve.reason ? (
                        <p className="mt-2 text-xs leading-5 text-faint">{sleeve.reason}</p>
                      ) : null}
                    </div>
                  );
                })}
              </div>
              {allocation.summary ? (
                <p className="max-w-3xl text-sm leading-6 text-muted">{allocation.summary}</p>
              ) : null}
              {allocation.risk ? (
                <p className="max-w-3xl text-sm leading-6 text-faint">{allocation.risk}</p>
              ) : null}
              <p className="text-xs text-faint">
                Los pesos suman 100. No es una instrucción de compra o venta.
              </p>
            </section>
          ) : (
            <p className="text-sm text-muted">
              {profile
                ? "No hubo una mezcla con pesos enteros que sumen 100. El perfil sí quedó guardado."
                : "La mezcla aparece al guardar el perfil."}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
