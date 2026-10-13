import { EmptyState } from "@/components/empty-state";
import { FadeIn } from "@/components/fade-in";
import { PageHeader } from "@/components/page-header";
import { apiGet } from "@/lib/api";
import { beatSpyLabel } from "@/lib/signal-copy";
import type { SignalRecord } from "@/lib/types";

function percent(value: number | null) {
  if (value === null) return "Sin cifra";
  return new Intl.NumberFormat("es-MX", {
    style: "percent",
    maximumFractionDigits: 1,
    signDisplay: "exceptZero",
  }).format(value);
}

function ReturnFigure({ value }: { value: number | null }) {
  if (value === null) return <span className="text-faint">Sin cifra</span>;
  const tone = value > 0 ? "text-up" : value < 0 ? "text-down" : "";
  return <span className={tone}>{percent(value)}</span>;
}

function Figure({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.14em] text-faint">{label}</p>
      <p className="mt-2 text-3xl font-light tabular-nums tracking-tight sm:text-4xl">{value}</p>
      {hint ? <p className="mt-2 text-xs text-faint">{hint}</p> : null}
    </div>
  );
}

export default async function HistoryPage() {
  const record = await apiGet<SignalRecord>("/signals/record");
  const beatRate = record.beat_spy_rate ?? null;
  const beatPct = beatRate === null ? null : Math.round(beatRate * 100);

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Historial"
        description="Solo cuentan las señales que ya tocaron el stop, el objetivo o cumplieron su plazo. El rendimiento es neto de la comisión guardada en cada señal."
      />
      {record.closed === 0 ? (
        <EmptyState
          title="Ninguna señal ha cerrado"
          body={`Hay ${record.open} abiertas. El marcador aparece cuando una termine — no se inventa un porcentaje.`}
        />
      ) : (
        <>
          <FadeIn>
            <section className="rounded-[24px] border border-accent/40 bg-surface px-5 py-7 sm:px-8">
              <p className="text-[11px] uppercase tracking-[0.14em] text-accent">Cara a cara con el S&P 500</p>
              <p className="mt-4 text-4xl font-light tracking-tight sm:text-5xl">
                {beatPct === null ? "—" : (
                  <span className="tabular-nums">
                    {beatPct}
                    <span className="text-2xl text-muted">%</span>
                  </span>
                )}
              </p>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">
                {beatSpyLabel(beatRate, record.beat_spy_compared)}
              </p>
              {beatRate !== null && record.beat_spy_compared > 0 ? (
                <div className="mt-6 h-2 overflow-hidden rounded-full bg-raised">
                  <div
                    className="h-full rounded-full bg-accent transition-[width]"
                    style={{ width: `${Math.min(100, Math.max(0, beatPct ?? 0))}%` }}
                  />
                </div>
              ) : null}
              <p className="mt-3 text-xs text-faint">
                {record.beat_spy_count} de {record.beat_spy_compared} señales con cifra del S&P le
                ganaron en el mismo tramo. Un acierto al objetivo no es lo mismo que batir al índice.
              </p>
            </section>
          </FadeIn>
          <section className="grid grid-cols-2 gap-6 rounded-[24px] border border-line bg-surface px-5 py-7 sm:grid-cols-4 sm:gap-8 sm:px-8">
            <Figure label="Cerradas" value={String(record.closed)} />
            <Figure
              label="Al objetivo"
              value={record.hit_rate === null ? "—" : percent(record.hit_rate)}
              hint="No es “éxito total”: solo toques de objetivo"
            />
            <Figure label="Objetivo" value={String(record.targets)} />
            <Figure label="Stop" value={String(record.stops)} />
          </section>
          <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-[24px] border border-line bg-surface px-6 py-6">
              <p className="text-[11px] uppercase tracking-[0.14em] text-faint">Neto de las señales</p>
              <p className="mt-3 text-3xl font-light tabular-nums">
                <ReturnFigure value={record.net_return} />
              </p>
              <p className="mt-3 text-xs text-faint">{record.net_count} con cifra</p>
            </div>
            <div className="rounded-[24px] border border-line bg-surface px-6 py-6">
              <p className="text-[11px] uppercase tracking-[0.14em] text-faint">
                Comprar y mantener el S&amp;P 500
              </p>
              <p className="mt-3 text-3xl font-light tabular-nums">
                <ReturnFigure value={record.spy_return} />
              </p>
              <p className="mt-3 text-xs text-faint">{record.spy_count} con cifra</p>
            </div>
            <div className="rounded-[24px] border border-line bg-surface px-6 py-6">
              <p className="text-[11px] uppercase tracking-[0.14em] text-faint">
                Comprar y mantener Bitcoin
              </p>
              <p className="mt-3 text-3xl font-light tabular-nums">
                <ReturnFigure value={record.btc_return} />
              </p>
              <p className="mt-3 text-xs text-faint">{record.btc_count} con cifra</p>
            </div>
          </section>
          <p className="text-sm text-muted">
            {record.expired} cerraron por plazo, sin tocar stop ni objetivo. Los promedios de S&P y BTC
            solo usan filas con cifra; no se rellenan con cero.
          </p>
        </>
      )}
    </div>
  );
}
