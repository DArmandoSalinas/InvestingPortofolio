import Link from "next/link";
import { BriefAlert } from "@/components/brief-alert";
import { EmptyState } from "@/components/empty-state";
import { FadeIn } from "@/components/fade-in";
import { PageHeader } from "@/components/page-header";
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
          <Link href={companyPath(row.market, row.symbol)} className="text-sm hover:text-accent">
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
          <Link href={companyPath(row.market, row.symbol)} className="hover:text-accent">
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

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[24px] border border-line bg-surface px-5 py-6 sm:px-7">
      <h2 className="text-[11px] uppercase tracking-[0.14em] text-faint">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export default async function BriefPage() {
  const board = await apiGet<BriefBoard>("/brief");
  const brief = board.brief;
  const reading = [brief?.reading_ranking, brief?.reading_signals, brief?.reading_events].filter(Boolean);

  return (
    <div className="flex max-w-3xl flex-col gap-8">
      <PageHeader
        eyebrow="Resumen"
        title="Qué ver hoy"
        description="Media hora antes de que abra Nueva York: cambios del ranking, señales abiertas y una lectura breve. Sin ruido."
        meta={brief ? <span className="tabular-nums">{formatAsOf(brief.as_of)}</span> : null}
      />
      {brief ? (
        <>
          <FadeIn>
            <p className="text-2xl font-light leading-snug tracking-tight sm:text-3xl">{brief.headline}</p>
          </FadeIn>
          <div className="grid grid-cols-1 gap-4">
            <Panel title={brief.compared ? "Entraron a las altas" : "Altas en los tres"}>
              <Names rows={brief.compared ? brief.entered : brief.highlights} />
              {brief.compared ? (
                <div className="mt-6 flex flex-col gap-6">
                  <div>
                    <h3 className="text-[11px] uppercase tracking-[0.14em] text-faint">Salieron</h3>
                    <div className="mt-3">
                      <Names rows={brief.left} />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-[11px] uppercase tracking-[0.14em] text-faint">
                      Cambios de la general
                    </h3>
                    <div className="mt-3">
                      <Movers rows={brief.movers} />
                    </div>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-muted">
                  Todavía no hay un día calculado anterior. No se inventan cambios.
                </p>
              )}
            </Panel>
            <Panel title="Señales abiertas">
              {brief.signals.length === 0 ? (
                <p className="text-sm text-muted">Ninguna regla se cumplió.</p>
              ) : (
                <ul className="flex flex-col gap-3">
                  {brief.signals.map((signal) => (
                    <li key={`${signal.symbol}-${signal.as_of}`} className="text-sm">
                      <Link href="/senales" className="hover:text-accent">
                        <span className="font-medium tracking-wide">{signal.symbol}</span>
                        <span className="ml-3 text-muted">{signal.name}</span>
                      </Link>
                      <span className="mt-1 block text-faint sm:ml-0 sm:mt-0 sm:inline sm:before:mx-3 sm:before:content-['·']">
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
            </Panel>
            {reading.length > 0 ? (
              <Panel title="Lectura">
                <div className="flex flex-col gap-3">
                  {reading.map((paragraph) => (
                    <p key={paragraph} className="text-sm leading-6 text-muted">
                      {paragraph}
                    </p>
                  ))}
                </div>
              </Panel>
            ) : null}
          </div>
        </>
      ) : (
        <EmptyState
          title="Aún no hay resumen de hoy"
          body="Se publica todos los días a las 9:00 de Nueva York. Si la API estaba apagada a esa hora, sale en el siguiente ciclo del mismo día."
        />
      )}
      <BriefAlert publicKey={board.vapid_public_key} />
    </div>
  );
}
