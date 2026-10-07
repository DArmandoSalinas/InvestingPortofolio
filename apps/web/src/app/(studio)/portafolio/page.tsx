import { FadeIn } from "@/components/fade-in";
import { HoldingForm } from "./holding-form";
import { removeHolding } from "./actions";
import { apiGet } from "@/lib/api";
import { formatAsOf } from "@/lib/labels";
import type { HoldingView, PortfolioBoard } from "@/lib/types";

const KIND: Record<HoldingView["asset_class"], string> = {
  stock: "Acción",
  etf: "ETF",
  crypto: "Crypto",
  cetes: "CETES",
  ahorro: "Ahorro",
};

function money(value: number, currency: string) {
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

function percent(value: number) {
  return new Intl.NumberFormat("es-MX", {
    style: "percent",
    maximumFractionDigits: 1,
    signDisplay: "exceptZero",
  }).format(value);
}

function Result({ holding }: { holding: HoldingView }) {
  if (holding.price_state === "carried") {
    return <span className="text-faint">Sin precio de mercado</span>;
  }
  if (holding.pnl === null) {
    return <span className="text-faint">Sin precio</span>;
  }
  const tone = holding.pnl > 0 ? "text-[#3d9a6a]" : holding.pnl < 0 ? "text-[#c45c5c]" : "";
  return <span className={`tabular-nums ${tone}`}>{percent(holding.pnl)}</span>;
}

export default async function PortfolioPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  const board = await apiGet<PortfolioBoard>("/portfolio");

  return (
    <div className="flex flex-col gap-8">
      <FadeIn>
        <h1 className="text-5xl font-light tracking-tight">Portafolio</h1>
        <p className="mt-3 text-sm text-muted">Lo que registras, con el último cierre cuando existe.</p>
      </FadeIn>
      {params.error ? <p className="text-sm text-ink">{params.error}</p> : null}
      <HoldingForm />
      <div className="overflow-hidden rounded-[28px] border border-line bg-surface">
        <table className="w-full border-collapse text-left text-[13px]">
          <thead className="text-[11px] uppercase tracking-[0.14em] text-faint">
            <tr className="border-b border-line">
              <th className="px-4 py-3 font-medium">Posición</th>
              <th className="px-3 py-3 text-right font-medium">Cantidad</th>
              <th className="px-3 py-3 text-right font-medium">Costo</th>
              <th className="px-3 py-3 text-right font-medium">Precio</th>
              <th className="px-3 py-3 text-right font-medium">Valor</th>
              <th className="px-3 py-3 text-right font-medium">Resultado</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {board.positions.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-sm text-muted">
                  Todavía no hay posiciones.
                </td>
              </tr>
            ) : (
              board.positions.map((holding) => (
                <tr key={holding.id} className="border-b border-line last:border-b-0">
                  <td className="px-4 py-3">
                    <div className="flex items-baseline gap-3">
                      <span className="font-medium tracking-wide">{holding.symbol}</span>
                      <span className="text-muted">{holding.name === holding.symbol ? KIND[holding.asset_class] : holding.name}</span>
                    </div>
                    <p className="mt-1 text-xs text-faint">{formatAsOf(holding.opened_on)}</p>
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums">{holding.quantity}</td>
                  <td className="px-3 py-3 text-right tabular-nums">{money(holding.cost, holding.currency)}</td>
                  <td className="px-3 py-3 text-right tabular-nums">
                    {holding.price === null ? (
                      <span className="text-faint">—</span>
                    ) : (
                      money(holding.price, holding.currency)
                    )}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums">
                    {holding.market_value === null ? (
                      <span className="text-faint">—</span>
                    ) : (
                      money(holding.market_value, holding.currency)
                    )}
                  </td>
                  <td className="px-3 py-3 text-right">
                    <Result holding={holding} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <form action={removeHolding}>
                      <input type="hidden" name="id" value={holding.id} />
                      <button type="submit" className="text-xs text-muted hover:text-ink">
                        Quitar
                      </button>
                    </form>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {board.totals.length > 0 ? (
        <div className="flex flex-col gap-2">
          {board.totals.map((total) => {
            const rows = board.positions.filter((holding) => holding.currency === total.currency);
            const registeredOnly = rows.length > 0 && rows.every((holding) => holding.price_state === "carried");
            const value =
              total.market_value === null
                ? `Falta el precio de ${total.missing}. No se calcula el valor.`
                : registeredOnly
                  ? `Monto registrado ${money(total.market_value, total.currency)}`
                  : `Valor ${money(total.market_value, total.currency)}`;
            return (
              <p key={total.currency} className="text-sm text-muted">
                <span className="text-ink">{total.currency}</span>
                <span className="mx-2 text-faint">·</span>
                Costo {money(total.cost, total.currency)}
                <span className="mx-2 text-faint">·</span>
                {value}
              </p>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
