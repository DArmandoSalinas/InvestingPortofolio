import uuid

from app.fixture_data import AS_OF, COMPANIES, RAW_FIELDS
from app.paths import repo_root, seed_sql_path
from app.scoring import composite_of

NAMESPACE = uuid.UUID("6f0c1a2e-9b3d-4e5f-8a71-0c2d4e6f8a10")


def company_id(market: str, symbol: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"{market}:{symbol}")


def sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_num(value: float | int | None) -> str:
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    text = format(value, "f").rstrip("0").rstrip(".")
    return text or "0"


def sql_array(values: list[str]) -> str:
    if not values:
        return "'{}'::text[]"
    inner = ", ".join(sql_text(item) for item in values)
    return f"array[{inner}]::text[]"


def render_seed() -> str:
    company_rows: list[str] = []
    score_rows: list[str] = []
    for company in COMPANIES:
        expected = composite_of(company["growth"], company["value"], company["momentum"])
        if company["composite"] != expected:
            raise SystemExit(
                f"{company['symbol']}: general {company['composite']} no coincide con {expected}"
            )
        identifier = company_id(company["market"], company["symbol"])
        company_rows.append(
            "("
            + ", ".join(
                [
                    sql_text(str(identifier)) + "::uuid",
                    sql_text(company["market"]),
                    sql_text(company["symbol"]),
                    sql_text(company["yahoo_symbol"]),
                    sql_text(company["name"]),
                    sql_text(company["sector"]),
                    sql_text(company["currency"]),
                    sql_text(company["universe_source"]),
                ]
            )
            + ")"
        )
        score_rows.append(
            "("
            + ", ".join(
                [
                    sql_text(str(identifier)) + "::uuid",
                    sql_text(AS_OF.isoformat()) + "::date",
                    sql_num(company["growth"]),
                    sql_num(company["value"]),
                    sql_num(company["momentum"]),
                    sql_num(company["composite"]),
                    "null" if company["value_reference"] is None else sql_text(company["value_reference"]),
                    *[sql_num(company[field]) for field in RAW_FIELDS],
                    sql_array(company["missing_fields"]),
                    sql_array(company["na_fields"]),
                ]
            )
            + ")"
        )

    return f"""-- Generado por `python -m app.render_seed` desde apps/api.
-- Puntajes de ejemplo del {AS_OF.isoformat()}. No son cálculos de mercado.

insert into public.companies (
  id, market, symbol, yahoo_symbol, name, sector, currency, universe_source
) values
{",\n".join(company_rows)};

insert into public.score_snapshots (
  company_id,
  as_of,
  growth,
  value,
  momentum,
  composite,
  value_reference,
  revenue_growth_yoy,
  earnings_growth_yoy,
  pe,
  ps,
  ev_ebitda,
  return_3m,
  return_6m,
  return_12m,
  price_to_sma200,
  missing_fields,
  na_fields
) values
{",\n".join(score_rows)};
"""


def main() -> None:
    path = seed_sql_path(repo_root())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_seed())
    print(path)


if __name__ == "__main__":
    main()
