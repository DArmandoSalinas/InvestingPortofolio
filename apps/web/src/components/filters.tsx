import Link from "next/link";
import { SECTORS } from "@/lib/labels";
import { one, type SearchParams } from "@/lib/types";

const MARKETS = [
  { value: "", label: "Todos" },
  { value: "us", label: "EE. UU." },
  { value: "mx", label: "México" },
] as const;

const STYLES = [
  { value: "", label: "General" },
  { value: "growth", label: "Crecimiento" },
  { value: "value", label: "Valor" },
  { value: "momentum", label: "Momentum" },
] as const;

function hrefFor(current: URLSearchParams, patch: Record<string, string | null>) {
  const next = new URLSearchParams(current);
  for (const [key, value] of Object.entries(patch)) {
    if (value === null || value === "") {
      next.delete(key);
    } else {
      next.set(key, value);
    }
  }
  const query = next.toString();
  return query ? `/?${query}` : "/";
}

export function Filters({ searchParams }: { searchParams: SearchParams }) {
  const market = one(searchParams.market) ?? "";
  const sector = one(searchParams.sector) ?? "";
  const style = one(searchParams.style) ?? "";
  const minScore = one(searchParams.min_score) ?? "";
  const current = new URLSearchParams();
  if (market) current.set("market", market);
  if (sector) current.set("sector", sector);
  if (style) current.set("style", style);
  if (minScore) current.set("min_score", minScore);
  const filtered = current.toString().length > 0;

  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="inline-flex rounded-full border border-line p-1">
        {MARKETS.map((option) => (
          <Link
            key={option.label}
            href={hrefFor(current, { market: option.value })}
            className={`rounded-full px-4 py-1.5 text-sm ${
              market === option.value ? "bg-ink text-black" : "text-muted"
            }`}
            aria-current={market === option.value ? "true" : undefined}
          >
            {option.label}
          </Link>
        ))}
      </div>
      <div className="inline-flex rounded-full border border-line p-1">
        {STYLES.map((option) => (
          <Link
            key={option.value || "general"}
            href={hrefFor(current, { style: option.value })}
            className={`rounded-full px-4 py-1.5 text-sm ${
              style === option.value ? "bg-ink text-black" : "text-muted"
            }`}
            aria-current={style === option.value ? "true" : undefined}
          >
            {option.label}
          </Link>
        ))}
      </div>
      <form action="/" className="flex items-center gap-2">
        {market ? <input type="hidden" name="market" value={market} /> : null}
        {style ? <input type="hidden" name="style" value={style} /> : null}
        {minScore ? <input type="hidden" name="min_score" value={minScore} /> : null}
        <label className="text-xs uppercase tracking-[0.14em] text-faint" htmlFor="sector">
          Sector
        </label>
        <select
          id="sector"
          name="sector"
          defaultValue={sector}
          className="rounded-full border border-line bg-black px-4 py-2 text-sm"
        >
          <option value="">Todos</option>
          {SECTORS.map((item) => (
            <option key={item.code} value={item.code}>
              {item.label}
            </option>
          ))}
        </select>
        <button type="submit" className="text-sm text-muted hover:text-ink">
          Aplicar
        </button>
      </form>
      <form action="/" className="flex items-center gap-2">
        {market ? <input type="hidden" name="market" value={market} /> : null}
        {sector ? <input type="hidden" name="sector" value={sector} /> : null}
        {style ? <input type="hidden" name="style" value={style} /> : null}
        <label className="text-xs uppercase tracking-[0.14em] text-faint" htmlFor="min_score">
          Mínimo
        </label>
        <input
          id="min_score"
          name="min_score"
          type="number"
          min={0}
          max={100}
          defaultValue={minScore}
          className="w-20 rounded-full border border-line bg-black px-3 py-2 text-sm tabular-nums"
        />
        <button type="submit" className="text-sm text-muted hover:text-ink">
          Aplicar
        </button>
      </form>
      {filtered ? (
        <Link href="/" className="text-sm text-faint hover:text-ink">
          Limpiar
        </Link>
      ) : null}
    </div>
  );
}
