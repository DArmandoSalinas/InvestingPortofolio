import { FadeIn } from "@/components/fade-in";
import { apiGet } from "@/lib/api";
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
  const record = await apiGet<SignalRecord>("/signals/record");

  return (
    <div className="flex flex-col gap-10">
      <FadeIn>
        <h1 className="text-5xl font-light tracking-tight">Historial</h1>
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
          <section className="grid grid-cols-4 gap-8 rounded-[28px] border border-line bg-surface px-8 py-7">
            <Figure label="Cerradas" value={String(record.closed)} />
            <Figure
              label="Aciertos"
              value={record.hit_rate === null ? "—" : percent(record.hit_rate)}
            />
            <Figure label="Objetivo" value={String(record.targets)} />
            <Figure label="Stop" value={String(record.stops)} />
          </section>
          <section className="grid grid-cols-3 gap-8">
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
        </>
      )}
    </div>
  );
}
