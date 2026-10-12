import { FadeIn } from "@/components/fade-in";
import { apiGet } from "@/lib/api";
import type { SignalRecord, SignalPerformance } from "@/lib/types";

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
  const tone = value > 0 ? "text-[#3d9a6a]" : value < 0 ? "text-[#c45c5c]" : "";
  return <span className={tone}>{percent(value)}</span>;
}

function Figure({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.14em] text-faint">{label}</p>
      <p className="mt-2 text-4xl font-light tabular-nums tracking-tight">{value}</p>
    </div>
  );
}

export default async function HistoryPage() {
  const [record, performance] = await Promise.all([
    apiGet<SignalRecord>("/signals/record"),
    apiGet<SignalPerformance>("/signals/performance"),
  ]);

  return (
    <div className="flex min-w-0 flex-col gap-10">
      <FadeIn>
        <h1 className="text-4xl font-light tracking-tight sm:text-5xl">Historial</h1>
        <p className="mt-4 max-w-xl text-sm leading-6 text-muted">
          Solo cuentan las señales que ya tocaron el stop, el objetivo o cumplieron su plazo.
          El rendimiento es neto de la comisión guardada en cada señal.
        </p>
      </FadeIn>
      {record.closed === 0 ? (
        <p className="text-sm text-muted">
          Ninguna señal ha cerrado. Hay {record.open} abiertas. El marcador aparece cuando una
          termine.
        </p>
      ) : (
        <>
          <section className="grid grid-cols-2 gap-6 rounded-[28px] border border-line bg-surface px-5 py-6 sm:gap-8 sm:px-8 sm:py-7 md:grid-cols-4">
            <Figure label="Cerradas" value={String(record.closed)} />
            <Figure
              label="Aciertos"
              value={record.hit_rate === null ? "—" : percent(record.hit_rate)}
            />
            <Figure label="Objetivo" value={String(record.targets)} />
            <Figure label="Stop" value={String(record.stops)} />
          </section>
          <section className="grid grid-cols-1 gap-4 sm:grid-cols-3 sm:gap-8">
            <div className="rounded-[28px] border border-line bg-surface px-6 py-6">
              <p className="text-[11px] uppercase tracking-[0.14em] text-faint">
                Neto de las señales
              </p>
              <p className="mt-3 text-3xl font-light tabular-nums">
                <ReturnFigure value={record.net_return} />
              </p>
              <p className="mt-3 text-xs text-faint">{record.net_count} con cifra</p>
            </div>
            <div className="rounded-[28px] border border-line bg-surface px-6 py-6">
              <p className="text-[11px] uppercase tracking-[0.14em] text-faint">
                Comprar y mantener el S&amp;P 500
              </p>
              <p className="mt-3 text-3xl font-light tabular-nums">
                <ReturnFigure value={record.spy_return} />
              </p>
              <p className="mt-3 text-xs text-faint">{record.spy_count} con cifra</p>
            </div>
            <div className="rounded-[28px] border border-line bg-surface px-6 py-6">
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
            {record.expired} cerraron por plazo, sin tocar stop ni objetivo.
          </p>
          
          {(performance.impulso || performance.retroceso) && (
            <section className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="text-xs uppercase tracking-[0.16em] text-muted mb-4">
                Desempeño histórico por tipo (últimos 5 años, backtest)
              </h2>
              <div className="grid gap-6">
                {performance.impulso && (
                  <div>
                    <h3 className="text-sm font-medium mb-2">Señales de Impulso</h3>
                    <p className="text-sm text-muted leading-relaxed">
                      De {performance.impulso.total_signals} señales históricas, esta regla alcanzó
                      el objetivo en {performance.impulso.targets} casos (
                      {performance.impulso.hit_rate
                        ? `${(performance.impulso.hit_rate * 100).toFixed(1)}%`
                        : "sin cifra"}
                      ). Rendimiento neto promedio:{" "}
                      {performance.impulso.avg_net_return !== null
                        ? `${(performance.impulso.avg_net_return * 100).toFixed(2)}%`
                        : "sin cifra"}
                      . Esta regla no superó de forma consistente al S&P 500 durante el período de
                      prueba.
                    </p>
                  </div>
                )}
                {performance.retroceso && (
                  <div>
                    <h3 className="text-sm font-medium mb-2">Señales de Retroceso</h3>
                    <p className="text-sm text-muted leading-relaxed">
                      De {performance.retroceso.total_signals} señales históricas, esta regla
                      alcanzó el objetivo en {performance.retroceso.targets} casos (
                      {performance.retroceso.hit_rate
                        ? `${(performance.retroceso.hit_rate * 100).toFixed(1)}%`
                        : "sin cifra"}
                      ). Rendimiento neto promedio:{" "}
                      {performance.retroceso.avg_net_return !== null
                        ? `${(performance.retroceso.avg_net_return * 100).toFixed(2)}%`
                        : "sin cifra"}
                      . Esta regla no superó de forma consistente al S&P 500 durante el período de
                      prueba.
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
