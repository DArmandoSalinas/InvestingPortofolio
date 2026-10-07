import { FadeIn } from "@/components/fade-in";
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

function ReturnValue({ value }: { value: number | null }) {
  if (value === null) {
    return <span className="text-faint">—</span>;
  }
  const tone = value > 0 ? "text-[#3d9a6a]" : value < 0 ? "text-[#c45c5c]" : "";
  return <span className={`tabular-nums ${tone}`}>{percent(value, 1, true)}</span>;
}

export default async function SignalsPage() {
  const board = await apiGet<SignalBoard>("/signals");
  const open = board.signals.filter((signal) => signal.status === "open").length;

  return (
    <div className="flex flex-col gap-8">
      <FadeIn>
        <div>
          <h1 className="text-5xl font-light tracking-tight">Señales</h1>
          <p className="mt-3 text-sm text-muted">
            Reglas de precio · {board.horizon_sessions} sesiones
            <span className="mx-2 text-faint">·</span>
            <span className="tabular-nums">{open} abiertas</span>
          </p>
        </div>
      </FadeIn>
      <div className="overflow-hidden rounded-[28px] border border-line bg-surface">
        <table className="w-full border-collapse text-left text-[13px]">
          <thead className="text-[11px] uppercase tracking-[0.14em] text-faint">
            <tr className="border-b border-line">
              <th className="px-4 py-3 font-medium">Activo</th>
              <th className="px-3 py-3 font-medium">Regla</th>
              <th className="px-3 py-3 text-right font-medium">Entrada</th>
              <th className="px-3 py-3 text-right font-medium">Stop</th>
              <th className="px-3 py-3 text-right font-medium">Objetivo</th>
              <th className="px-3 py-3 text-right font-medium">Confianza</th>
              <th className="px-3 py-3 font-medium">Estado</th>
              <th className="px-4 py-3 text-right font-medium">Neto</th>
            </tr>
          </thead>
          <tbody>
            {board.signals.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-sm text-muted">
                  Ninguna regla se cumplió. No se inventa una señal.
                </td>
              </tr>
            ) : (
              board.signals.map((signal) => (
                <tr key={signal.id} className="border-b border-line align-top last:border-b-0">
                  <td className="px-4 py-3">
                    <div className="flex items-baseline gap-3">
                      <span className="font-medium tracking-wide">{signal.symbol}</span>
                      <span className="text-muted">{signal.name}</span>
                    </div>
                    <p className="mt-1 text-xs text-faint">
                      {signal.asset_class === "crypto" ? "Crypto" : "Acción"}
                      <span className="mx-1.5">·</span>
                      {formatAsOf(signal.as_of)}
                    </p>
                    <p className="mt-2 max-w-md text-xs leading-5 text-faint">
                      {signal.reasons.join(" ")}
                    </p>
                    {signal.context_note ? (
                      <p className="mt-2 max-w-md text-xs leading-5 text-muted">{signal.context_note}</p>
                    ) : null}
                  </td>
                  <td className="px-3 py-3 text-muted">{SETUP[signal.setup]}</td>
                  <td className="px-3 py-3 text-right tabular-nums">{money(signal.entry)}</td>
                  <td className="px-3 py-3 text-right tabular-nums">{money(signal.stop)}</td>
                  <td className="px-3 py-3 text-right tabular-nums">{money(signal.target)}</td>
                  <td className="px-3 py-3 text-right tabular-nums">{signal.confidence}</td>
                  <td className="px-3 py-3 text-muted">{STATUS[signal.status]}</td>
                  <td className="px-4 py-3 text-right">
                    <ReturnValue value={signal.net_return} />
                    {signal.status !== "open" && (signal.spy_return !== null || signal.btc_return !== null) ? (
                      <p className="mt-1 text-[11px] text-faint">
                        {signal.spy_return !== null ? `S&P 500 ${percent(signal.spy_return)}` : ""}
                        {signal.spy_return !== null && signal.btc_return !== null ? " · " : ""}
                        {signal.btc_return !== null ? `BTC ${percent(signal.btc_return)}` : ""}
                      </p>
                    ) : null}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs leading-5 text-faint">
        La comisión de ida y vuelta es {percent(board.stock_commission, 2)} en acciones y{" "}
        {percent(board.crypto_commission, 2)} en crypto. Si el stop y el objetivo caen el mismo día,
        cuenta el stop. El verde y el rojo solo marcan el resultado ya cerrado.
      </p>
    </div>
  );
}
