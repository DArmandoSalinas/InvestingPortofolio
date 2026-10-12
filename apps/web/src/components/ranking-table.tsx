import Link from "next/link";
import { Tooltip } from "@/components/tooltip";
import { companyPath, dataNote, marketLabel, sectorLabel } from "@/lib/labels";
import type { RankingRow } from "@/lib/types";

const COLUMNS = [
  { key: "growth", label: "Crecimiento", style: "growth", short: "C" },
  { key: "value", label: "Valor", style: "value", short: "V" },
  { key: "momentum", label: "Momentum", style: "momentum", short: "M" },
  { key: "composite", label: "General", style: "", short: "G" },
] as const;

function Score({ value }: { value: number | null }) {
  if (value === null) {
    return <span className="text-faint">—</span>;
  }
  return <span className="tabular-nums">{value}</span>;
}

export function RankingTable({ rows, style }: { rows: RankingRow[]; style: string }) {
  const active = style || "composite";
  const comparesWithUs = rows.some((row) => row.value_reference === "sp500_sector");

  return (
    <div className="overflow-x-auto rounded-[28px] border border-line bg-surface">
      <table className="w-full border-collapse text-left text-[13px]">
        <thead className="sticky top-0 bg-surface text-[11px] uppercase tracking-[0.14em] text-faint">
          <tr className="border-b border-line">
            <th className="px-4 py-3 font-medium">Empresa</th>
            <th className="px-3 py-3 font-medium">Mercado</th>
            <th className="px-3 py-3 font-medium">Sector</th>
            {COLUMNS.map((column) => (
              <th
                key={column.key}
                className={`px-3 py-3 text-right font-medium ${
                  active === column.style || (column.key === "composite" && active === "composite")
                    ? "text-ink"
                    : ""
                }`}
              >
                <Tooltip term={column.label}>{column.label}</Tooltip>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={7} className="px-4 py-10 text-sm text-muted">
                Ninguna empresa coincide con estos filtros.
              </td>
            </tr>
          ) : (
            rows.map((row) => {
              const note = dataNote(row.missing_fields, row.na_fields);
              return (
                <tr key={row.id} className="border-b border-line last:border-b-0 hover:bg-white/[0.03]">
                  <td className="px-4 py-2.5">
                    <Link href={companyPath(row.market, row.symbol)} className="block">
                      <span className="flex items-baseline gap-3">
                        <span className="font-medium tracking-wide">{row.symbol}</span>
                        <span className="text-muted">{row.name}</span>
                      </span>
                    </Link>
                    {note ? <p className="mt-1 text-xs text-faint">{note}</p> : null}
                  </td>
                  <td className="px-3 py-2.5 text-muted">{marketLabel(row.market)}</td>
                  <td className="px-3 py-2.5 text-muted">{sectorLabel(row.sector)}</td>
                  <td className="px-3 py-2.5 text-right">
                    <Score value={row.growth} />
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <Score value={row.value} />
                    {row.value_reference === "sp500_sector" ? (
                      <span className="ml-2 text-[10px] tracking-wide text-faint">EE.UU.</span>
                    ) : null}
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <Score value={row.momentum} />
                  </td>
                  <td className="px-4 py-2.5 text-right text-[15px]">
                    {row.composite === null ? (
                      <span className="text-xs font-normal tracking-normal text-faint">Incompleto</span>
                    ) : (
                      <span className="font-medium tabular-nums">{row.composite}</span>
                    )}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
      {comparesWithUs ? (
        <p className="border-t border-line px-4 py-3 text-xs text-faint">
          EE.UU. junto al valor: el sector en México tiene menos de 8 emisoras, así que la
          comparación usa el S&P 500.
        </p>
      ) : null}
      <div className="border-t border-line px-4 py-3 text-xs text-faint">
        <Tooltip term="Crecimiento">Crecimiento</Tooltip>, <Tooltip term="Valor">Valor</Tooltip>,{" "}
        <Tooltip term="Momentum">Momentum</Tooltip> y <Tooltip term="General">General</Tooltip> son
        puntuaciones de 0 a 100. Pasa el cursor sobre cada término para ver su definición.
      </div>
    </div>
  );
}
