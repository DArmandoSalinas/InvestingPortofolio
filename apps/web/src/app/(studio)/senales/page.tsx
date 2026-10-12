import { FadeIn } from "@/components/fade-in";
import { Tooltip } from "@/components/tooltip";
import { apiGet } from "@/lib/api";
import { formatAsOf } from "@/lib/labels";
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

function SignalCard({ signal }: { signal: SignalRow }) {
  const tone =
    signal.net_return === null
      ? ""
      : signal.net_return > 0
        ? "text-[#3d9a6a]"
        : signal.net_return < 0
          ? "text-[#c45c5c]"
          : "";

  return (
    <div className="rounded-2xl border border-line bg-surface p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-baseline gap-3">
            <span className="text-lg font-medium tracking-wide">{signal.symbol}</span>
            <span className="text-sm text-muted">{signal.name}</span>
          </div>
          <p className="mt-1 text-xs text-faint">
            {signal.asset_class === "crypto" ? "Crypto" : "Acción"}
            <span className="mx-1.5">·</span>
            {SETUP[signal.setup]}
            <span className="mx-1.5">·</span>
            {formatAsOf(signal.as_of)}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="text-xs text-muted">{STATUS[signal.status]}</span>
          {signal.net_return !== null && (
            <span className={`text-lg font-medium tabular-nums ${tone}`}>
              {percent(signal.net_return, 1, true)}
            </span>
          )}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-4 gap-4 text-xs">
        <div>
          <div className="text-faint">
            <Tooltip term="Entrada">Entrada</Tooltip>
          </div>
          <div className="mt-1 font-medium tabular-nums">{money(signal.entry)}</div>
        </div>
        <div>
          <div className="text-faint">
            <Tooltip term="Stop">Stop</Tooltip>
          </div>
          <div className="mt-1 font-medium tabular-nums">{money(signal.stop)}</div>
        </div>
        <div>
          <div className="text-faint">
            <Tooltip term="Objetivo">Objetivo</Tooltip>
          </div>
          <div className="mt-1 font-medium tabular-nums">{money(signal.target)}</div>
        </div>
        <div>
          <div className="text-faint">
            <Tooltip term="Confianza">Confianza</Tooltip>
          </div>
          <div className="mt-1 font-medium tabular-nums">{signal.confidence}</div>
        </div>
      </div>

      <details className="mt-4 group">
        <summary className="cursor-pointer text-xs text-muted hover:text-ink list-none flex items-center gap-2">
          <span className="inline-block transition-transform group-open:rotate-90">→</span>
          Razones y contexto
        </summary>
        <div className="mt-3 space-y-2 text-xs leading-5">
          <p className="text-faint">{signal.reasons.join(" ")}</p>
          {signal.context_note && <p className="text-muted">{signal.context_note}</p>}
        </div>
      </details>

      {signal.status !== "open" && (signal.spy_return !== null || signal.btc_return !== null) ? (
        <div className="mt-3 pt-3 border-t border-line text-xs text-faint">
          Comparación:{" "}
          {signal.spy_return !== null && `S&P 500 ${percent(signal.spy_return)}`}
          {signal.spy_return !== null && signal.btc_return !== null && " · "}
          {signal.btc_return !== null && `BTC ${percent(signal.btc_return)}`}
        </div>
      ) : null}
    </div>
  );
}

export default async function SignalsPage() {
  const board = await apiGet<SignalBoard>("/signals");
  const open = board.signals.filter((signal) => signal.status === "open");
  const closed = board.signals.filter((signal) => signal.status !== "open");

  return (
    <div className="flex flex-col gap-8">
      <FadeIn>
        <div>
          <h1 className="text-5xl font-light tracking-tight">Señales</h1>
          <p className="mt-2 text-sm leading-6 text-muted">
            Señales de compra generadas por reglas de precio, con stop-loss y objetivo. Cada señal
            dura hasta <Tooltip term="Sesiones">{board.horizon_sessions} sesiones</Tooltip> o hasta
            que toque el stop o el objetivo.
          </p>
          <p className="mt-3 text-sm text-faint">
            <span className="tabular-nums">{open.length} abiertas</span>
            {closed.length > 0 && (
              <>
                <span className="mx-2">·</span>
                <span className="tabular-nums">{closed.length} cerradas</span>
              </>
            )}
          </p>
        </div>
      </FadeIn>

      {open.length > 0 && (
        <section>
          <h2 className="mb-4 text-xs uppercase tracking-[0.16em] text-muted">Abiertas</h2>
          <div className="grid gap-4">
            {open.map((signal) => (
              <SignalCard key={signal.id} signal={signal} />
            ))}
          </div>
        </section>
      )}

      {closed.length > 0 && (
        <section>
          <h2 className="mb-4 text-xs uppercase tracking-[0.16em] text-muted">Cerradas</h2>
          <div className="grid gap-4">
            {closed.map((signal) => (
              <SignalCard key={signal.id} signal={signal} />
            ))}
          </div>
        </section>
      )}

      {board.signals.length === 0 && (
        <div className="rounded-2xl border border-line bg-surface p-10 text-center text-sm text-muted">
          Ninguna regla se cumplió. No se inventa una señal.
        </div>
      )}

      <p className="text-xs leading-5 text-faint">
        La comisión de ida y vuelta es {percent(board.stock_commission, 2)} en acciones y{" "}
        {percent(board.crypto_commission, 2)} en crypto. Si el stop y el objetivo caen el mismo día,
        cuenta el stop. El <Tooltip term="Neto">resultado neto</Tooltip> ya descuenta comisiones.
      </p>
    </div>
  );
}
