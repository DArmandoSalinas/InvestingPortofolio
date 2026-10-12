import { FadeIn } from "@/components/fade-in";
import { Filters } from "@/components/filters";
import { Highlights } from "@/components/highlights";
import { RankingTable } from "@/components/ranking-table";
import { ScoreChart } from "@/components/score-chart";
import { companyPath } from "@/lib/labels";
import { apiGet } from "@/lib/api";
import { formatAsOf } from "@/lib/labels";
import { one, type RankingResponse, type SearchParams } from "@/lib/types";

function queryString(params: Record<string, string>) {
  const search = new URLSearchParams(params);
  const text = search.toString();
  return text ? `?${text}` : "";
}

export default async function RankingPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const market = one(params.market);
  const sector = one(params.sector);
  const style = one(params.style);
  const minScore = one(params.min_score);

  const rankingParams: Record<string, string> = {};
  const highlightParams: Record<string, string> = {};
  if (market === "us" || market === "mx") {
    rankingParams.market = market;
    highlightParams.market = market;
  }
  if (sector) {
    rankingParams.sector = sector;
    highlightParams.sector = sector;
  }
  if (style === "growth" || style === "value" || style === "momentum") {
    rankingParams.style = style;
  }
  if (minScore && Number.isFinite(Number(minScore))) {
    rankingParams.min_score = minScore;
  }

  const [ranking, highlighted] = await Promise.all([
    apiGet<RankingResponse>(`/ranking${queryString(rankingParams)}`),
    apiGet<RankingResponse>(`/ranking/highlights${queryString(highlightParams)}`),
  ]);

  const asOf = ranking.as_of ? formatAsOf(ranking.as_of) : "sin fecha";

  return (
    <div className="flex flex-col gap-8">
      <FadeIn>
        <div>
          <h1 className="text-4xl font-light tracking-tight sm:text-5xl">Ranking</h1>
          <p className="mt-2 text-sm leading-6 text-muted">
            Encuentra empresas de EE.UU. y México ordenadas por sus puntuaciones de Crecimiento,
            Valor y Momentum. Cada empresa tiene una puntuación General (promedio de las tres).
          </p>
          <p className="mt-3 text-sm text-faint">
            {ranking.example ? "Datos de ejemplo" : "Calculado"} · {asOf}
            <span className="mx-2">·</span>
            <span className="tabular-nums">{ranking.rows.length} empresas</span>
          </p>
        </div>
      </FadeIn>
      <Highlights rows={highlighted.rows} minimum={highlighted.highlight_min} />
      <ScoreChart
        title={
          rankingParams.style === "growth"
            ? "Crecimiento"
            : rankingParams.style === "value"
              ? "Valor"
              : rankingParams.style === "momentum"
                ? "Momentum"
                : "General"
        }
        rows={ranking.rows.slice(0, 12).map((row) => ({
          key: row.id,
          label: row.symbol,
          href: companyPath(row.market, row.symbol),
          value:
            rankingParams.style === "growth"
              ? row.growth
              : rankingParams.style === "value"
                ? row.value
                : rankingParams.style === "momentum"
                  ? row.momentum
                  : row.composite,
        }))}
      />
      <Filters searchParams={params} />
      <RankingTable rows={ranking.rows} style={rankingParams.style ?? ""} />
    </div>
  );
}
