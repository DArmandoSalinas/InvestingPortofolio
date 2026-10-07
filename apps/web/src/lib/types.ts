export type RankingRow = {
  id: string;
  market: "us" | "mx";
  symbol: string;
  name: string;
  sector: string;
  currency: "USD" | "MXN";
  growth: number | null;
  value: number | null;
  momentum: number | null;
  composite: number | null;
  value_reference: "local" | "sp500_sector" | null;
  missing_fields: string[];
  na_fields: string[];
};

export type RankingResponse = {
  as_of: string | null;
  highlight_min: number;
  example: boolean;
  rows: RankingRow[];
};

export type Candle = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
};

export type CompanyDetail = {
  market: "us" | "mx";
  symbol: string;
  name: string;
  sector: string;
  currency: "USD" | "MXN";
  as_of: string | null;
  example: boolean;
  growth: number | null;
  value: number | null;
  momentum: number | null;
  composite: number | null;
  value_reference: "local" | "sp500_sector" | null;
  missing_fields: string[];
  na_fields: string[];
  growth_note: string;
  value_note: string;
  momentum_note: string;
  reading_summary: string;
  reading_sentiment: string;
  reading_caution: string;
  reading_report: string;
  report_period: string | null;
  report_revenue: number | null;
  report_earnings: number | null;
  report_prior_period: string | null;
  report_revenue_yoy: number | null;
  report_earnings_yoy: number | null;
  candles: Candle[];
};

export type SignalRow = {
  id: string;
  as_of: string;
  asset_class: "stock" | "crypto";
  symbol: string;
  name: string;
  setup: "impulso" | "retroceso";
  entry: number;
  stop: number;
  target: number;
  confidence: number;
  reasons: string[];
  risks: string[];
  status: "open" | "target" | "stop" | "expired";
  net_return: number | null;
  spy_return: number | null;
  btc_return: number | null;
  context_note: string;
};

export type SignalBoard = {
  horizon_sessions: number;
  stock_commission: number;
  crypto_commission: number;
  signals: SignalRow[];
};

export type BriefName = {
  market: "us" | "mx";
  symbol: string;
  name: string;
  composite: number | null;
};

export type BriefMover = BriefName & {
  before: number;
  after: number;
  delta: number;
};

export type BriefSignal = {
  symbol: string;
  name: string;
  setup: "impulso" | "retroceso";
  as_of: string;
  confidence: number;
  asset_class: "stock" | "crypto";
};

export type MorningBrief = {
  as_of: string;
  headline: string;
  ranking_as_of: string | null;
  previous_as_of: string | null;
  compared: boolean;
  highlights: BriefName[];
  entered: BriefName[];
  left: BriefName[];
  movers: BriefMover[];
  signals: BriefSignal[];
  reading_ranking: string;
  reading_signals: string;
  reading_events: string;
};

export type BriefBoard = {
  vapid_public_key: string;
  brief: MorningBrief | null;
};

export type SleeveView = {
  id: "cetes" | "ahorro" | "etf" | "acciones" | "crypto";
  name: string;
  detail: string;
  fit: string;
  return_value: number | null;
  return_start: string | null;
  return_end: string | null;
};

export type Allocation = {
  summary: string;
  risk: string;
  sleeves: { id: SleeveView["id"]; weight: number; reason: string }[];
};

export type InvestorProfile = {
  currency: "MXN" | "USD";
  amount: number;
  monthly_contribution: number;
  horizon_years: number;
  goal: "preservar" | "crecer" | "ingreso";
  risk: "bajo" | "medio" | "alto";
  updated_at: string | null;
};

export type ProfileBoard = {
  profile: InvestorProfile | null;
  sleeves: SleeveView[];
  allocation: Allocation | null;
};

export type HoldingView = {
  id: string;
  asset_class: "stock" | "etf" | "crypto" | "cetes" | "ahorro";
  symbol: string;
  name: string;
  quantity: number;
  unit_cost: number;
  currency: "MXN" | "USD";
  opened_on: string;
  price: number | null;
  price_as_of: string | null;
  cost: number;
  market_value: number | null;
  pnl: number | null;
  price_state: "market" | "carried" | "missing";
};

export type PortfolioBoard = {
  positions: HoldingView[];
  totals: {
    currency: "MXN" | "USD";
    cost: number;
    market_value: number | null;
    missing: number;
  }[];
};

export type SignalRecord = {
  open: number;
  closed: number;
  targets: number;
  stops: number;
  expired: number;
  hit_rate: number | null;
  net_return: number | null;
  spy_return: number | null;
  btc_return: number | null;
  net_count: number;
  spy_count: number;
  btc_count: number;
};

export type WatchItem = {
  yahoo_symbol: string;
  symbol: string;
  name: string;
  asset_class: "stock" | "crypto";
  active: boolean;
};

export type SignalSettings = {
  stock_commission: number;
  crypto_commission: number;
  horizon_sessions: number;
  watchlist: WatchItem[];
};

export type AccessEntry = {
  email: string;
  role: "admin" | "member";
  active: boolean;
  protected: boolean;
};

export type SearchParams = Record<string, string | string[] | undefined>;

export function one(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
