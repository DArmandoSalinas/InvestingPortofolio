import Link from "next/link";
import { CandleChart } from "@/components/candle-chart";
import { ScoreChart } from "@/components/score-chart";
import { FadeIn } from "@/components/fade-in";
import { apiGetResult } from "@/lib/api";
import { formatAsOf, marketLabel, sectorLabel } from "@/lib/labels";
import type { CompanyDetail } from "@/lib/types";

function money(value: number | null, currency: string) {
  if (value === null) return "Sin cifra";
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function change(value: number | null) {
  if (value === null) return "sin cifra";
  return new Intl.NumberFormat("es-MX", {
    style: "percent",
    maximumFractionDigits: 1,
    signDisplay: "exceptZero",
  }).format(value);
}

function Score({ label, value }: { label: string; value: number | null }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.14em] text-faint">{label}</p>
      <p className="mt-2 text-4xl font-light tabular-nums tracking-tight">
        {value === null ? <span className="text-xl text-faint">—</span> : value}
      </p>
    </div>
  );
}

export default async function CompanyPage({
  params,
}: {
  params: Promise<{ market: string; symbol: string }>;
}) {
  const { market, symbol } = await params;
  const decoded = decodeURIComponent(symbol);
  const result = await apiGetResult<CompanyDetail>(
    `/companies/${market}/${encodeURIComponent(decoded)}`,
  );

  if (!result.ok || !result.data) {
    return (
      <div className="flex flex-col gap-6">
        <Link href="/" className="text-sm text-muted">
          Ranking
        </Link>
        <h1 className="text-5xl font-light tracking-tight">No está en el universo</h1>
        <p className="text-sm text-muted">{result.detail}</p>
      </div>
    );
  }

  const company = result.data;
  const asOf = company.as_of ? formatAsOf(company.as_of) : "sin fecha";

  return (
    <div className="flex min-w-0 flex-col gap-10">
      <FadeIn>
        <Link href="/" className="text-sm text-muted">
          Ranking
        </Link>
        <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between sm:gap-8">
          <div>
            <h1 className="text-4xl font-light tracking-tight sm:text-5xl">{company.symbol}</h1>
            <p className="mt-3 text-sm text-muted">
              {company.name}
              <span className="mx-2 text-faint">·</span>
              {marketLabel(company.market)}
              <span className="mx-2 text-faint">·</span>
              {sectorLabel(company.sector)}
              <span className="mx-2 text-faint">·</span>
              {company.currency}
            </p>
          </div>
          <p className="text-sm text-muted">
            {company.example ? "Datos de ejemplo" : "Calculado"}
            <span className="mx-2 text-faint">·</span>
            {asOf}
          </p>
        </div>
      </FadeIn>
      <section className="grid grid-cols-2 gap-6 rounded-[28px] border border-line bg-surface px-5 py-6 sm:gap-8 sm:px-8 sm:py-7 md:grid-cols-4">
        <Score label="Crecimiento" value={company.growth} />
        <Score label="Valor" value={company.value} />
        <Score label="Momentum" value={company.momentum} />
        <Score label="General" value={company.composite} />
      </section>
      {company.quality !== null && company.quality !== undefined && (
        <section className="rounded-[28px] border border-line bg-surface px-8 py-7">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-baseline sm:gap-8">
            <div>
              <p className="text-[11px] uppercase tracking-[0.14em] text-faint">Calidad</p>
              <p className="mt-2 text-4xl font-light tabular-nums tracking-tight">
                {company.quality}
              </p>
            </div>
            <p className="text-sm text-muted max-w-2xl">{company.quality_note}</p>
          </div>
        </section>
      )}
      <ScoreChart
        title="Puntuaciones"
        rows={[
          { key: "growth", label: "Crecimiento", value: company.growth },
          { key: "value", label: "Valor", value: company.value },
          { key: "momentum", label: "Momentum", value: company.momentum },
          { key: "composite", label: "General", value: company.composite },
        ]}
      />
      <section className="overflow-hidden rounded-[28px] border border-line bg-surface">
        <h2 className="px-6 pt-6 text-[11px] uppercase tracking-[0.14em] text-faint">Precio</h2>
        <CandleChart bars={company.candles} />
      </section>
      {company.reading_summary || company.reading_sentiment ? (
        <section className="max-w-3xl">
          <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">Lectura</h2>
          {company.reading_summary ? (
            <p className="mt-3 text-lg font-light leading-8">{company.reading_summary}</p>
          ) : null}
          {company.reading_sentiment ? (
            <p className="mt-4 text-sm leading-6 text-muted">{company.reading_sentiment}</p>
          ) : null}
          {company.reading_caution ? (
            <p className="mt-4 text-sm leading-6 text-muted">{company.reading_caution}</p>
          ) : null}
        </section>
      ) : null}
      <section className="max-w-3xl">
        <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">Reporte</h2>
        {company.report_period ? (
          <>
            <p className="mt-3 text-sm text-muted">
              Trimestre al {formatAsOf(company.report_period)}
            </p>
            <div className="mt-6 grid grid-cols-2 gap-8">
              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-faint">Ingresos</p>
                <p className="mt-2 text-3xl font-light tabular-nums">
                  {money(company.report_revenue, company.currency)}
                </p>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.14em] text-faint">Utilidad neta</p>
                <p className="mt-2 text-3xl font-light tabular-nums">
                  {money(company.report_earnings, company.currency)}
                </p>
              </div>
            </div>
            <p className="mt-6 text-sm leading-6 text-muted">
              {company.report_prior_period
                ? `Contra el trimestre al ${formatAsOf(company.report_prior_period)}, los ingresos cambiaron ${change(company.report_revenue_yoy)} y la utilidad ${change(company.report_earnings_yoy)}.`
                : "No hay un trimestre comparable de hace un año. No se inventa la variación."}
            </p>
            {company.reading_report ? (
              <p className="mt-4 text-sm leading-6 text-muted">{company.reading_report}</p>
            ) : null}
          </>
        ) : (
          <p className="mt-3 text-sm leading-6 text-muted">
            No hay un reporte trimestral en la fuente. No se inventa.
          </p>
        )}
      </section>
      <section className="grid grid-cols-1 gap-8 md:grid-cols-3 md:gap-10">
        <div>
          <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">Crecimiento</h2>
          <p className="mt-3 text-sm leading-6 text-muted">{company.growth_note}</p>
        </div>
        <div>
          <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">Valor</h2>
          <p className="mt-3 text-sm leading-6 text-muted">{company.value_note}</p>
        </div>
        <div>
          <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">Momentum</h2>
          <p className="mt-3 text-sm leading-6 text-muted">{company.momentum_note}</p>
        </div>
      </section>
    </div>
  );
}
