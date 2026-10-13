import { EmptyState } from "@/components/empty-state";
import { FadeIn } from "@/components/fade-in";
import { PageHeader } from "@/components/page-header";
import { apiGet } from "@/lib/api";
import { formatAsOf } from "@/lib/labels";
import { setupPlain, statusPlain } from "@/lib/signal-copy";
import type { SignalBoard, SignalRow } from "@/lib/types";

const SETUP: Record<SignalRow["setup"], string> = {
  impulso: "Impulso",
  retroceso: "Retroceso",
};

const STATUS: Record<SignalRow["status"], string> = {
  open: "Abierta",
  target: "Objetivo",
  stop: "Stop",
  expired: "Plazo",
};

function money(value: number) {
  return new Intl.NumberFormat("es-MX", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function percent(value: number, digits = 1, signed = false) {
  return new Intl.NumberFormat("es-MX", {
    style: "percent",
    maximumFractionDigits: digits,
    signDisplay: signed ? "exceptZero" : "auto",
  }).format(value);
}

function ReturnValue({ value }: { value: number | null }) {
  if (value === null) {
    return <span className="text-faint">—</span>;
  }
  const tone = value > 0 ? "text-up" : value < 0 ? "text-down" : "";
  return <span className={`tabular-nums ${tone}`}>{percent(value, 1, true)}</span>;
}

function SignalCard({ signal }: { signal: SignalRow }) {
  const beatSpy =
    signal.status !== "open" &&
    signal.net_return !== null &&
    signal.spy_return !== null
      ? signal.net_return > signal.spy_return
      : null;

  return (
    <article className="rounded-[24px] border border-line bg-surface px-5 py-5 sm:px-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h2 className="text-xl font-medium tracking-wide">{signal.symbol}</h2>
          <p className="mt-1 text-sm text-muted">{signal.name}</p>
        </div>
        <div className="text-right text-sm">
          <p className="text-muted">{STATUS[signal.status]}</p>
          <p className="mt-1">
            <ReturnValue value={signal.net_return} />
          </p>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-muted">{setupPlain(signal.setup)}</p>
      <p className="mt-2 text-sm leading-6 text-faint">{statusPlain(signal.status)}</p>
      <dl className="mt-5 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-[11px] uppercase tracking-[0.14em] text-faint">Entrada</dt>
          <dd className="mt-1 tabular-nums">{money(signal.entry)}</dd>
        </div>
        <div>
          <dt className="text-[11px] uppercase tracking-[0.14em] text-faint">Stop</dt>
          <dd className="mt-1 tabular-nums">{money(signal.stop)}</dd>
        </div>
        <div>
          <dt className="text-[11px] uppercase tracking-[0.14em] text-faint">Objetivo</dt>
          <dd className="mt-1 tabular-nums">{money(signal.target)}</dd>
        </div>
        <div>
          <dt className="text-[11px] uppercase tracking-[0.14em] text-faint">Confianza</dt>
          <dd className="mt-1 tabular-nums">{signal.confidence}</dd>
        </div>
      </dl>
      <p className="mt-4 text-xs leading-5 text-faint">
        {SETUP[signal.setup]}
        <span className="mx-1.5">·</span>
        {signal.asset_class === "crypto" ? "Crypto" : "Acción"}
        <span className="mx-1.5">·</span>
        {formatAsOf(signal.as_of)}
      </p>
      <ul className="mt-3 list-disc space-y-1 pl-4 text-xs leading-5 text-muted">
        {signal.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
      {signal.risks.length > 0 ? (
        <ul className="mt-3 list-disc space-y-1 pl-4 text-xs leading-5 text-faint">
          {signal.risks.map((risk) => (
            <li key={risk}>{risk}</li>
          ))}
        </ul>
      ) : null}
      {signal.context_note ? (
        <p className="mt-3 text-xs leading-5 text-muted">{signal.context_note}</p>
      ) : null}
      {signal.status !== "open" && (signal.spy_return !== null || signal.btc_return !== null) ? (
        <p className="mt-4 text-xs text-faint">
          En el mismo tramo:{" "}
          {signal.spy_return !== null ? `S&P 500 ${percent(signal.spy_return)}` : ""}
          {signal.spy_return !== null && signal.btc_return !== null ? " · " : ""}
          {signal.btc_return !== null ? `BTC ${percent(signal.btc_return)}` : ""}
          {beatSpy !== null ? (
            <span className="ml-2 text-muted">
              {beatSpy ? "Le ganó al S&P en esta señal." : "No le ganó al S&P en esta señal."}
            </span>
          ) : null}
        </p>
      ) : null}
    </article>
  );
}

export default async function SignalsPage() {
  const board = await apiGet<SignalBoard>("/signals");
  const open = board.signals.filter((signal) => signal.status === "open").length;

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Señales"
        description="Reglas de precio en lenguaje claro. Cada señal explica por qué entró, qué puede salir mal y cómo cerró de verdad — sin maquillar el historial."
        meta={
          <span>
            {board.horizon_sessions} sesiones
            <span className="mx-2 text-faint">·</span>
            <span className="tabular-nums">{open} abiertas</span>
          </span>
        }
      />
      {board.signals.length === 0 ? (
        <EmptyState
          title="Ninguna regla se cumplió"
          body="No se inventa una señal. Cuando el precio cumpla impulso o retroceso, aparece aquí con entrada, stop y objetivo."
        />
      ) : (
        <FadeIn>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {board.signals.map((signal) => (
              <SignalCard key={signal.id} signal={signal} />
            ))}
          </div>
        </FadeIn>
      )}
      <p className="text-xs leading-5 text-faint">
        La comisión de ida y vuelta es {percent(board.stock_commission, 2)} en acciones y{" "}
        {percent(board.crypto_commission, 2)} en crypto. Si el stop y el objetivo caen el mismo día,
        cuenta el stop. El verde y el rojo solo marcan el resultado ya cerrado.
      </p>
    </div>
  );
}
