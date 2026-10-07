export const SECTORS: { code: string; label: string }[] = [
  { code: "energy", label: "Energía" },
  { code: "materials", label: "Materiales" },
  { code: "industrials", label: "Industria" },
  { code: "consumer_discretionary", label: "Consumo discrecional" },
  { code: "consumer_staples", label: "Consumo básico" },
  { code: "health_care", label: "Salud" },
  { code: "financials", label: "Finanzas" },
  { code: "information_technology", label: "Tecnología" },
  { code: "communication_services", label: "Comunicación" },
  { code: "utilities", label: "Servicios públicos" },
  { code: "real_estate", label: "Bienes raíces" },
];

const FIELD_LABELS: Record<string, string> = {
  revenue_growth_yoy: "crecimiento de ingresos",
  earnings_growth_yoy: "crecimiento de utilidades",
  pe: "P/E",
  ps: "P/S",
  ev_ebitda: "EV/EBITDA",
  return_3m: "rendimiento a 3 meses",
  return_6m: "rendimiento a 6 meses",
  return_12m: "rendimiento a 12 meses",
  price_to_sma200: "precio contra la media de 200 días",
};

export function sectorLabel(code: string) {
  if (code === "unknown") return "Sin sector";
  return SECTORS.find((sector) => sector.code === code)?.label ?? code;
}

export function companyPath(market: string, symbol: string) {
  return `/empresa/${market}/${encodeURIComponent(symbol)}`;
}

export function marketLabel(market: "us" | "mx") {
  return market === "us" ? "EE. UU." : "México";
}

export function dataNote(missing: string[], notApplicable: string[]) {
  const parts = [
    ...missing.map((field) => `Falta ${FIELD_LABELS[field] ?? field}`),
    ...notApplicable.map((field) => `${FIELD_LABELS[field] ?? field} no aplica`),
  ];
  return parts.join(" · ");
}

export function formatAsOf(asOf: string) {
  return new Intl.DateTimeFormat("es-MX", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "America/Monterrey",
  }).format(new Date(`${asOf}T12:00:00`));
}
