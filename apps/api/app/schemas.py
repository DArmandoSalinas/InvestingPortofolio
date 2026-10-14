from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

Role = Literal["admin", "member"]
Market = Literal["us", "mx"]
Style = Literal["growth", "value", "momentum"]


class RankingRow(BaseModel):
    id: str
    market: Market
    symbol: str
    name: str
    sector: str
    currency: Literal["USD", "MXN"]
    growth: int | None
    value: int | None
    momentum: int | None
    composite: int | None
    quality: int | None = None
    value_reference: Literal["local", "sp500_sector"] | None
    missing_fields: list[str]
    na_fields: list[str]


class RankingResponse(BaseModel):
    as_of: date | None
    highlight_min: int
    example: bool
    rows: list[RankingRow]


class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float


class CompanyDetail(BaseModel):
    market: Market
    symbol: str
    name: str
    sector: str
    currency: Literal["USD", "MXN"]
    as_of: date | None
    example: bool
    growth: int | None
    value: int | None
    momentum: int | None
    composite: int | None
    quality: int | None = None
    value_reference: Literal["local", "sp500_sector"] | None
    missing_fields: list[str]
    na_fields: list[str]
    growth_note: str
    value_note: str
    momentum_note: str
    quality_note: str = ""
    reading_summary: str = ""
    reading_sentiment: str = ""
    reading_caution: str = ""
    reading_report: str = ""
    report_period: date | None = None
    report_revenue: float | None = None
    report_earnings: float | None = None
    report_prior_period: date | None = None
    report_revenue_yoy: float | None = None
    report_earnings_yoy: float | None = None
    candles: list[Candle]


class SignalRow(BaseModel):
    id: str
    as_of: date
    asset_class: Literal["stock", "crypto"]
    symbol: str
    name: str
    setup: Literal["impulso", "retroceso"]
    entry: float
    stop: float
    target: float
    confidence: int
    reasons: list[str]
    risks: list[str]
    status: Literal["open", "target", "stop", "expired"]
    net_return: float | None = None
    spy_return: float | None = None
    btc_return: float | None = None
    context_note: str = ""


class SignalBoard(BaseModel):
    horizon_sessions: int
    stock_commission: float
    crypto_commission: float
    signals: list[SignalRow]


class SignalRecord(BaseModel):
    open: int
    closed: int
    targets: int
    stops: int
    expired: int
    hit_rate: float | None = None
    net_return: float | None = None
    spy_return: float | None = None
    btc_return: float | None = None
    net_count: int
    spy_count: int
    btc_count: int
    beat_spy_rate: float | None = None
    beat_spy_count: int = 0
    beat_spy_compared: int = 0


class WatchItem(BaseModel):
    yahoo_symbol: str
    symbol: str
    name: str
    asset_class: Literal["stock", "crypto"]
    active: bool


class SignalSettings(BaseModel):
    stock_commission: float
    crypto_commission: float
    horizon_sessions: int
    watchlist: list[WatchItem]


class SignalSettingsPatch(BaseModel):
    stock_commission: float
    crypto_commission: float
    horizon_sessions: int

    @model_validator(mode="after")
    def bounds(self) -> "SignalSettingsPatch":
        if not 0 <= self.stock_commission <= 0.05 or not 0 <= self.crypto_commission <= 0.05:
            raise ValueError("La comisión tiene que estar entre 0% y 5%")
        if not 1 <= self.horizon_sessions <= 30:
            raise ValueError("El horizonte va de 1 a 30 sesiones")
        return self


class WatchIn(BaseModel):
    symbol: str
    name: str
    asset_class: Literal["stock", "crypto"]


class WatchPatch(BaseModel):
    yahoo_symbol: str
    active: bool


class BriefName(BaseModel):
    market: Literal["us", "mx"]
    symbol: str
    name: str
    composite: int | None = None


class BriefMover(BriefName):
    before: int
    after: int
    delta: int


class BriefSignal(BaseModel):
    symbol: str
    name: str
    setup: Literal["impulso", "retroceso"]
    as_of: date
    confidence: int
    asset_class: Literal["stock", "crypto"]


class MorningBrief(BaseModel):
    as_of: date
    headline: str
    ranking_as_of: date | None = None
    previous_as_of: date | None = None
    compared: bool
    highlights: list[BriefName]
    entered: list[BriefName]
    left: list[BriefName]
    movers: list[BriefMover]
    signals: list[BriefSignal]
    reading_ranking: str = ""
    reading_signals: str = ""
    reading_events: str = ""


class BriefBoard(BaseModel):
    vapid_public_key: str = ""
    brief: MorningBrief | None = None


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    endpoint: str
    keys: PushKeys

    @model_validator(mode="after")
    def endpoint_is_usable(self) -> "PushSubscriptionIn":
        if not self.endpoint.startswith("https://") or not self.keys.p256dh or not self.keys.auth:
            raise ValueError("La suscripción del aviso no es válida")
        return self


SleeveId = Literal["cetes", "ahorro", "etf", "acciones", "crypto"]
Goal = Literal["preservar", "crecer", "ingreso"]
RiskBand = Literal["bajo", "medio", "alto"]
AssetClass = Literal["stock", "etf", "crypto", "cetes", "ahorro"]


class SleeveView(BaseModel):
    id: SleeveId
    name: str
    detail: str
    fit: str = ""
    return_value: float | None = None
    return_start: date | None = None
    return_end: date | None = None


class AllocationSleeve(BaseModel):
    id: SleeveId
    weight: int
    reason: str = ""


class Allocation(BaseModel):
    summary: str = ""
    risk: str = ""
    sleeves: list[AllocationSleeve]


class InvestorProfile(BaseModel):
    currency: Literal["MXN", "USD"]
    amount: float
    monthly_contribution: float
    horizon_years: int
    goal: Goal
    risk: RiskBand
    updated_at: datetime | None = None


class ProfileIn(BaseModel):
    currency: Literal["MXN", "USD"]
    amount: float
    monthly_contribution: float
    horizon_years: int
    goal: Goal
    risk: RiskBand

    @model_validator(mode="after")
    def amounts_make_sense(self) -> "ProfileIn":
        if self.amount <= 0 or self.monthly_contribution < 0:
            raise ValueError("El monto tiene que ser mayor que cero")
        if not 1 <= self.horizon_years <= 40:
            raise ValueError("El plazo va de 1 a 40 años")
        return self


class ProfileBoard(BaseModel):
    profile: InvestorProfile | None = None
    sleeves: list[SleeveView]
    allocation: Allocation | None = None


class HoldingIn(BaseModel):
    asset_class: AssetClass
    symbol: str = ""
    market: Market | None = None
    quantity: float
    unit_cost: float = 1
    currency: Literal["MXN", "USD"] | None = None
    opened_on: date


class HoldingView(BaseModel):
    id: str
    asset_class: AssetClass
    symbol: str
    name: str
    quantity: float
    unit_cost: float
    currency: Literal["MXN", "USD"]
    opened_on: date
    price: float | None = None
    price_as_of: date | None = None
    cost: float
    market_value: float | None = None
    pnl: float | None = None
    price_state: Literal["market", "carried", "missing"]


class PortfolioTotal(BaseModel):
    currency: Literal["MXN", "USD"]
    cost: float
    market_value: float | None = None
    missing: int


class PortfolioBoard(BaseModel):
    positions: list[HoldingView]
    totals: list[PortfolioTotal]


class MeResponse(BaseModel):
    email: str
    role: Role
    display_name: str | None


class AccessEntry(BaseModel):
    email: str
    role: Role
    active: bool
    protected: bool = False
    mail: str = ""
    temporary_password: str = ""


class PasswordChange(BaseModel):
    password: str


class AccessList(BaseModel):
    entries: list[AccessEntry]


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    local, separator, domain = email.partition("@")
    if not separator or not local or not domain or " " in email:
        raise ValueError("Escribe un correo válido")
    return email


class ForgotPassword(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        return normalize_email(value)


class AccessCreate(BaseModel):
    email: str
    role: Role = "member"

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        return normalize_email(value)


class AccessLink(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        return normalize_email(value)


class AccessPatch(BaseModel):
    email: str
    role: Role | None = None
    active: bool | None = None

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        return normalize_email(value)

    @model_validator(mode="after")
    def something_changes(self) -> "AccessPatch":
        if self.role is None and self.active is None:
            raise ValueError("Indica un rol o si el acceso sigue activo")
        return self


class UserContext(BaseModel):
    id: str
    email: str
    role: Role
    display_name: str | None = None
