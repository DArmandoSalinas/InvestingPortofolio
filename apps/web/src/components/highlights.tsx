"use client";

import { motion, useReducedMotion } from "framer-motion";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Tooltip } from "@/components/tooltip";
import { companyPath } from "@/lib/labels";
import type { RankingRow } from "@/lib/types";

function CountUp({ value }: { value: number }) {
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(reduce ? value : 0);

  useEffect(() => {
    if (reduce) {
      return;
    }
    const start = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / 700);
      const eased = 1 - (1 - progress) ** 3;
      setShown(Math.round(value * eased));
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [reduce, value]);

  return <span className="tabular-nums">{shown}</span>;
}

export function Highlights({ rows, minimum }: { rows: RankingRow[]; minimum: number }) {
  const reduce = useReducedMotion();

  return (
    <section className="overflow-hidden rounded-[28px] border border-line bg-surface">
      <div className="flex flex-col gap-1 px-6 pt-5 sm:flex-row sm:items-baseline sm:justify-between sm:gap-0">
        <h2 className="text-[11px] uppercase tracking-[0.16em] text-muted">
          <Tooltip term="Altas en los tres">Altas en los tres</Tooltip>
        </h2>
        <p className="text-xs text-faint">{minimum} puntos o más en cada una</p>
      </div>
      {rows.length === 0 ? (
        <p className="px-6 py-8 text-sm text-muted">
          Ninguna empresa de este corte llega a {minimum} puntos en Crecimiento, Valor y Momentum al
          mismo tiempo.
        </p>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-px border-t border-line bg-line sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {rows.map((row, index) => (
            <motion.article
              key={row.id}
              className="bg-surface px-6 py-5"
              initial={reduce ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: index * 0.05, ease: [0.22, 1, 0.36, 1] }}
            >
              <Link
                href={companyPath(row.market, row.symbol)}
                className="text-xs tracking-[0.08em] text-muted"
              >
                {row.symbol}
              </Link>
              <p className="mt-2 text-[44px] font-light leading-none tracking-tight">
                <CountUp value={row.composite ?? 0} />
              </p>
              <p className="mt-3 text-xs tabular-nums text-faint">
                Crecimiento {row.growth} · Valor {row.value} · Momentum {row.momentum}
              </p>
            </motion.article>
          ))}
        </div>
      )}
    </section>
  );
}
