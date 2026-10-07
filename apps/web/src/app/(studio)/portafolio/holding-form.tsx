"use client";

import { useState } from "react";
import { addHolding } from "./actions";

export function HoldingForm() {
  const [kind, setKind] = useState("stock");
  const cash = kind === "cetes" || kind === "ahorro";
  const listed = kind === "stock" || kind === "etf";

  return (
    <form action={addHolding} className="flex flex-wrap items-end gap-3">
      <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
        Tipo
        <select
          name="asset_class"
          value={kind}
          onChange={(event) => setKind(event.target.value)}
          className="rounded-2xl border border-line bg-black px-4 py-3 text-sm normal-case tracking-normal"
        >
          <option value="stock">Acción</option>
          <option value="etf">ETF</option>
          <option value="crypto">Crypto</option>
          <option value="cetes">CETES</option>
          <option value="ahorro">Ahorro</option>
        </select>
      </label>
      {listed ? (
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Mercado
          <select
            name="market"
            defaultValue="us"
            className="rounded-2xl border border-line bg-black px-4 py-3 text-sm normal-case tracking-normal"
          >
            <option value="us">EE. UU.</option>
            <option value="mx">México</option>
          </select>
        </label>
      ) : null}
      {cash ? (
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Moneda
          <select
            name="currency"
            defaultValue="MXN"
            className="rounded-2xl border border-line bg-black px-4 py-3 text-sm normal-case tracking-normal"
          >
            <option value="MXN">Pesos</option>
            <option value="USD">Dólares</option>
          </select>
        </label>
      ) : (
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Símbolo
          <input
            name="symbol"
            required
            className="w-32 rounded-2xl border border-line bg-surface px-4 py-3 text-sm uppercase tracking-normal text-ink"
          />
        </label>
      )}
      <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
        {cash ? "Monto" : "Cantidad"}
        <input
          name="quantity"
          type="number"
          min="0.0001"
          step="any"
          required
          className="w-32 rounded-2xl border border-line bg-surface px-4 py-3 text-sm tabular-nums normal-case tracking-normal text-ink"
        />
      </label>
      {cash ? (
        <input type="hidden" name="unit_cost" value="1" />
      ) : (
        <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
          Costo por unidad
          <input
            name="unit_cost"
            type="number"
            min="0.0001"
            step="any"
            required
            className="w-36 rounded-2xl border border-line bg-surface px-4 py-3 text-sm tabular-nums normal-case tracking-normal text-ink"
          />
        </label>
      )}
      <label className="flex flex-col gap-2 text-xs uppercase tracking-[0.14em] text-faint">
        Fecha
        <input
          name="opened_on"
          type="date"
          required
          className="rounded-2xl border border-line bg-surface px-4 py-3 text-sm tabular-nums normal-case tracking-normal text-ink"
        />
      </label>
      <button type="submit" className="rounded-full bg-ink px-5 py-3 text-sm font-medium text-black">
        Registrar
      </button>
    </form>
  );
}
