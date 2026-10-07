import Link from "next/link";
import { BriefAlert } from "@/components/brief-alert";
import { FadeIn } from "@/components/fade-in";
import { apiGet } from "@/lib/api";
import { companyPath, formatAsOf } from "@/lib/labels";
import type { BriefBoard, BriefMover, BriefName } from "@/lib/types";

const SETUP = { impulso: "Impulso", retroceso: "Retroceso" };

function signed(value: number) {
  if (value > 0) return `+${value}`;
  return String(value);
}

function Names({ rows }: { rows: BriefName[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-muted">Ninguna.</p>;
  }
  return (
    <ul className="flex flex-col gap-2">
      {rows.map((row) => (
        <li key={`${row.market}-${row.symbol}`}>
          <Link href={companyPath(row.market, row.symbol)} className="text-sm hover:text-ink">
            <span className="font-medium tracking-wide">{row.symbol}</span>
            <span className="ml-3 text-muted">{row.name}</span>
            {row.composite !== null ? (
              <span className="ml-3 tabular-nums text-faint">{row.composite}</span>
            ) : null}
          </Link>
        </li>
      ))}
    </ul>
  );
}

function Movers({ rows }: { rows: BriefMover[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-muted">Ningún cambio de la general con ambos días completos.</p>;
  }
  return (
    <ul className="flex flex-col gap-2">
      {rows.map((row) => (
        <li key={`${row.market}-${row.symbol}`} className="text-sm">
          <Link href={companyPath(row.market, row.symbol)} className="hover:text-ink">
            <span className="font-medium tracking-wide">{row.symbol}</span>
            <span className="ml-3 text-muted">{row.name}</span>
          </Link>
          <span className="ml-3 tabular-nums text-faint">
            {row.before} → {row.after}
            <span className="ml-2">{signed(row.delta)}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

export default async function BriefPage() {
  const board = await apiGet<BriefBoard>("/brief");
  const brief = board.brief;
  const reading = [brief?.reading_ranking, brief?.reading_signals, brief?.reading_events].filter(Boolean);

  return (
    <div className="flex max-w-3xl flex-col gap-10">
      <FadeIn>
        <div className="flex flex-col gap-3">
          <h1 className="text-5xl font-light tracking-tight">Resumen</h1>
          <p className="text-sm text-muted">
            Media hora antes de que abra Nueva York
            {brief ? (
              <>
                <span className="mx-2 text-faint">·</span>
                <span className="tabular-nums">{formatAsOf(brief.as_of)}</span>
              </>
            ) : null}
          </p>
        </div>
      </FadeIn>
      {brief ? (
        <>
          <p className="text-2xl font-light tracking-tight">{brief.headline}</p>
          <section className="flex flex-col gap-3">
            <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">
              {brief.compared ? "Entraron a las altas" : "Altas en los tres"}
            </h2>
            <Names rows={brief.compared ? brief.entered : brief.highlights} />
            {brief.compared ? (
              <>
                <h2 className="mt-4 text-[11px] uppercase tracking-[0.14em] text-faint">Salieron</h2>
                <Names rows={brief.left} />
                <h2 className="mt-4 text-[11px] uppercase tracking-[0.14em] text-faint">
                  Cambios de la general
                </h2>
                <Movers rows={brief.movers} />
              </>
            ) : (
              <p className="text-sm text-muted">
                Todavía no hay un día calculado anterior. No se inventan cambios.
              </p>
            )}
          </section>
          <section className="flex flex-col gap-3">
            <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">Señales abiertas</h2>
            {brief.signals.length === 0 ? (
              <p className="text-sm text-muted">Ninguna regla se cumplió.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {brief.signals.map((signal) => (
                  <li key={`${signal.symbol}-${signal.as_of}`} className="text-sm">
                    <Link href="/senales" className="hover:text-ink">
                      <span className="font-medium tracking-wide">{signal.symbol}</span>
                      <span className="ml-3 text-muted">{signal.name}</span>
                    </Link>
                    <span className="ml-3 text-faint">
                      {SETUP[signal.setup]}
                      <span className="mx-1.5">·</span>
                      {formatAsOf(signal.as_of)}
                      <span className="mx-1.5">·</span>
                      <span className="tabular-nums">{signal.confidence}</span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
          {reading.length > 0 ? (
            <section className="flex flex-col gap-3">
              <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">Lectura</h2>
              {reading.map((paragraph) => (
                <p key={paragraph} className="text-sm leading-6 text-muted">
                  {paragraph}
                </p>
              ))}
            </section>
          ) : null}
        </>
      ) : (
        <p className="text-sm leading-6 text-muted">
          El resumen se publica todos los días a las 9:00 de Nueva York. Si la API estaba apagada a
          esa hora, sale en el siguiente ciclo del mismo día.
        </p>
      )}
      <BriefAlert publicKey={board.vapid_public_key} />
    </div>
  );
}
