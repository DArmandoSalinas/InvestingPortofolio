import asyncio
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.analyst import allocation_proposal, read_company
from app.brief_job import brief_payload
from app.config import Settings, get_settings
from app.db import DatabaseUnavailable, SupabaseRest
from app.deps import close_db, get_db, require_admin, require_user
from app.explain import growth_note, momentum_note, value_note
from app.investor import allocation_facts, market_sleeves, normalize_holding, parse_allocation, priced_positions, rollup
from app.market_data import daily_bars, quarterly_report
from app.schedule import refresh_loop
from app.schemas import (
    AccessCreate,
    AccessEntry,
    AccessLink,
    AccessList,
    ForgotPassword,
    PasswordChange,
    AccessPatch,
    Candle,
    CompanyDetail,
    MeResponse,
    Allocation,
    BriefBoard,
    HoldingIn,
    HoldingView,
    InvestorProfile,
    MorningBrief,
    PortfolioBoard,
    PortfolioTotal,
    ProfileBoard,
    ProfileIn,
    PushSubscriptionIn,
    SleeveView,
    RankingResponse,
    RankingRow,
    SignalBoard,
    SignalRecord,
    SignalRow,
    SignalSettings,
    SignalSettingsPatch,
    WatchIn,
    WatchItem,
    WatchPatch,
    UserContext,
)
from app.scoring import apply_min, highlights, sort_rows
from app.signals import CRYPTO_COMMISSION, HORIZON_SESSIONS, STOCK_COMMISSION, scoreboard

Style = Literal["growth", "value", "momentum"]
Market = Literal["us", "mx"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.admin_email:
        db = SupabaseRest(settings)
        try:
            db.ensure_admin(settings.admin_email)
        except DatabaseUnavailable as exc:
            db.close()
            raise RuntimeError("No se pudo preparar el administrador de arranque") from exc
        db.close()
    stop = asyncio.Event()
    task = asyncio.create_task(refresh_loop(stop))
    yield
    stop.set()
    task.cancel()
    close_db()


app = FastAPI(title="Plataforma de inversión", lifespan=lifespan)
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _rows_for(
    db: SupabaseRest,
    as_of: date | None,
    market: Market | None,
    sector: str | None,
) -> tuple[date | None, list[dict]]:
    try:
        resolved = as_of or db.latest_as_of()
        if resolved is None:
            return None, []
        return resolved, db.fetch_snapshots(resolved, market, sector)
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/digest")
def digest_api(
    token: Annotated[str, Query()],
    db: Annotated[SupabaseRest, Depends(get_db)],
) -> dict:
    """
    Read-only digest endpoint for external consumption.
    Returns daily summary: ranking top, changes, signals, hit rate.
    Protected by token authentication.
    """
    if not db.verify_digest_token(token):
        raise HTTPException(status_code=401, detail="Token inválido o inactivo")
    
    try:
        latest_as_of = db.calculated_as_of()
        if not latest_as_of:
            raise HTTPException(status_code=404, detail="No hay ranking calculado todavía")
        
        current = db.fetch_snapshots(latest_as_of, None, None)
        previous_as_of = db.calculated_as_of(latest_as_of)
        previous = db.fetch_snapshots(previous_as_of, None, None) if previous_as_of else []
        
        from app.scoring import highlights, sort_rows
        from app.brief import ranking_brief
        from app.signals import scoreboard
        
        settings = get_settings()
        top = sort_rows(current, None)[:20]
        highlighted = highlights(current, settings.rank_highlight_min)
        changes = ranking_brief(current, previous, settings.rank_highlight_min)
        
        signals = db.list_signals()
        open_signals = [s for s in signals if s.get("status") == "open"]
        closed_signals = [s for s in signals if s.get("status") != "open"]
        record = scoreboard(signals)
        
        latest_brief = db.latest_brief()
        brief_data = brief_payload(latest_brief) if latest_brief else None
        
        return {
            "as_of": latest_as_of.isoformat(),
            "previous_as_of": previous_as_of.isoformat() if previous_as_of else None,
            "ranking": {
                "top_20": [
                    {
                        "symbol": row["symbol"],
                        "name": row["name"],
                        "market": row["market"],
                        "sector": row["sector"],
                        "composite": row.get("composite"),
                        "growth": row.get("growth"),
                        "value": row.get("value"),
                        "momentum": row.get("momentum"),
                    }
                    for row in top
                ],
                "highlights": [
                    {
                        "symbol": row["symbol"],
                        "name": row["name"],
                        "market": row["market"],
                        "composite": row.get("composite"),
                    }
                    for row in highlighted
                ],
                "changes": {
                    "compared": changes["compared"],
                    "entered": len(changes["entered"]),
                    "left": len(changes["left"]),
                    "movers": len(changes["movers"]),
                },
            },
            "signals": {
                "open": len(open_signals),
                "open_list": [
                    {
                        "symbol": s["symbol"],
                        "name": s["name"],
                        "as_of": str(s["as_of"]),
                        "setup": s.get("setup"),
                        "confidence": s.get("confidence"),
                    }
                    for s in open_signals[:10]
                ],
                "new_today": len([s for s in open_signals if str(s.get("as_of")) == latest_as_of.isoformat()]),
            },
            "track_record": {
                "total_closed": record.get("total", 0),
                "hits": record.get("hits", 0),
                "hit_rate": record.get("hit_rate"),
                "average_return": record.get("average_return"),
                "vs_spy": record.get("vs_spy"),
                "vs_btc": record.get("vs_btc"),
            },
            "brief": brief_data,
        }
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None


@app.get("/me", response_model=MeResponse)
def me(user: Annotated[UserContext, Depends(require_user)]) -> MeResponse:
    return MeResponse(email=user.email, role=user.role, display_name=user.display_name)


def _latest_snapshot(snapshots: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not snapshots:
        return None
    return max(snapshots, key=lambda row: row["as_of"])


@app.get("/companies/{market}/{symbol}", response_model=CompanyDetail)
def company_detail(
    market: str,
    symbol: str,
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> CompanyDetail:
    del user
    if market not in ("us", "mx"):
        raise HTTPException(status_code=404, detail="No está en el universo")
    try:
        company = db.fetch_company(market, symbol)
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    if company is None:
        raise HTTPException(status_code=404, detail="No está en el universo")
    snapshot = _latest_snapshot(company.get("score_snapshots") or []) or {}
    notes = snapshot or {
        "missing_fields": [],
        "na_fields": [],
    }
    as_of = snapshot.get("as_of")
    report = quarterly_report(company["yahoo_symbol"]) or {}
    reading = None
    if as_of:
        reading = read_company(
            get_settings().xai_api_key,
            {
                "name": company["name"],
                "symbol": company["symbol"],
                "market": company["market"],
                "sector": company["sector"],
                "growth": snapshot.get("growth"),
                "value": snapshot.get("value"),
                "momentum": snapshot.get("momentum"),
                "composite": snapshot.get("composite"),
                "growth_note": growth_note(notes),
                "value_note": value_note(notes),
                "momentum_note": momentum_note(notes),
                "report": report or None,
            },
            as_of if isinstance(as_of, date) else date.fromisoformat(str(as_of)),
        )
    
    # Generar quality_note si hay quality
    quality_note_text = ""
    if snapshot.get("quality") is not None:
        from app.quality import quality_note as generate_quality_note
        # Reconstruir detail desde el snapshot
        quality_detail = {}
        if snapshot.get("operating_margin") is not None:
            quality_detail["operating_margin_score"] = snapshot.get("operating_margin")
        if snapshot.get("net_margin") is not None:
            quality_detail["net_margin_score"] = snapshot.get("net_margin")
        if snapshot.get("roe") is not None:
            quality_detail["roe_score"] = snapshot.get("roe")
        if snapshot.get("debt_to_equity") is not None:
            quality_detail["debt_score"] = snapshot.get("debt_to_equity")
        if snapshot.get("fcf_yield") is not None:
            quality_detail["fcf_score"] = snapshot.get("fcf_yield")
        
        quality_note_text = generate_quality_note(quality_detail)
    
    return CompanyDetail(
        market=company["market"],
        symbol=company["symbol"],
        name=company["name"],
        sector=company["sector"],
        currency=company["currency"],
        as_of=snapshot.get("as_of"),
        example=not bool(snapshot.get("calculated")),
        growth=snapshot.get("growth"),
        value=snapshot.get("value"),
        momentum=snapshot.get("momentum"),
        composite=snapshot.get("composite"),
        quality=snapshot.get("quality"),
        value_reference=snapshot.get("value_reference"),
        missing_fields=snapshot.get("missing_fields") or [],
        na_fields=snapshot.get("na_fields") or [],
        growth_note=growth_note(notes),
        value_note=value_note(notes),
        momentum_note=momentum_note(notes),
        quality_note=quality_note_text,
        reading_summary=(reading or {}).get("summary", ""),
        reading_sentiment=(reading or {}).get("x_sentiment", ""),
        reading_caution=(reading or {}).get("caution", ""),
        reading_report=(reading or {}).get("report", ""),
        report_period=report.get("period"),
        report_revenue=report.get("revenue"),
        report_earnings=report.get("earnings"),
        report_prior_period=report.get("prior_period"),
        report_revenue_yoy=report.get("revenue_yoy"),
        report_earnings_yoy=report.get("earnings_yoy"),
        candles=[Candle.model_validate(bar) for bar in daily_bars(company["yahoo_symbol"])],
    )


def _rules(db: SupabaseRest) -> tuple[float, float, int]:
    try:
        row = db.get_signal_config()
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    if not row:
        return STOCK_COMMISSION, CRYPTO_COMMISSION, HORIZON_SESSIONS
    return float(row["stock_commission"]), float(row["crypto_commission"]), int(row["horizon_sessions"])


@app.get("/signals", response_model=SignalBoard)
def signals(
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> SignalBoard:
    del user
    try:
        rows = db.list_signals()
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    opens = [row for row in rows if row.get("status") == "open"]
    closed = [row for row in rows if row.get("status") != "open"]
    opens.sort(key=lambda row: str(row.get("as_of")), reverse=True)
    closed.sort(key=lambda row: str(row.get("as_of")), reverse=True)
    stock_commission, crypto_commission, horizon = _rules(db)
    return SignalBoard(
        horizon_sessions=horizon,
        stock_commission=stock_commission,
        crypto_commission=crypto_commission,
        signals=[SignalRow.model_validate(row) for row in [*opens, *closed]],
    )


@app.get("/signals/record", response_model=SignalRecord)
def signal_record(
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> SignalRecord:
    del user
    try:
        rows = db.list_signals()
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    return SignalRecord.model_validate(scoreboard(rows))


@app.get("/signals/performance")
def signals_performance(
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> dict[str, Any]:
    """Obtiene el desempeño histórico por tipo de señal."""
    del user
    try:
        performance = db.get_signal_performance()
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    
    result: dict[str, Any] = {}
    for row in performance:
        setup = row.get("setup")
        if setup:
            result[setup] = {
                "total_signals": row.get("total_signals", 0),
                "targets": row.get("targets", 0),
                "stops": row.get("stops", 0),
                "expired": row.get("expired", 0),
                "hit_rate": row.get("hit_rate"),
                "avg_net_return": row.get("avg_net_return"),
                "avg_gross_return": row.get("avg_gross_return"),
                "avg_winner": row.get("avg_winner"),
                "avg_loser": row.get("avg_loser"),
                "win_loss_ratio": row.get("win_loss_ratio"),
                "last_updated": row.get("last_updated"),
            }
    return result


def _ranking_response(
    resolved: date | None,
    source_rows: list[dict],
    response_rows: list[dict],
    settings: Settings,
) -> RankingResponse:
    example = not source_rows or any(row.get("calculated") is not True for row in source_rows)
    return RankingResponse(
        as_of=resolved,
        highlight_min=settings.rank_highlight_min,
        example=example,
        rows=[RankingRow.model_validate(row) for row in response_rows],
    )


@app.get("/brief", response_model=BriefBoard)
def brief(
    db: Annotated[SupabaseRest, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[UserContext, Depends(require_user)],
) -> BriefBoard:
    del user
    try:
        row = db.latest_brief()
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    payload = brief_payload(row)
    return BriefBoard(
        vapid_public_key=settings.vapid_public_key,
        brief=MorningBrief.model_validate(payload) if payload else None,
    )


@app.get("/dashboard")
def daily_dashboard(
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> dict[str, Any]:
    """Genera el dashboard diario 'Qué ver hoy' con insights accionables."""
    try:
        # Obtener ranking actual
        latest_as_of = db.latest_as_of()
        if not latest_as_of:
            return {"insights": [], "as_of": None, "has_open_signals": False, "top_company": None}
        
        current = db.fetch_snapshots(latest_as_of, None, None)
        
        # Obtener ranking anterior
        previous_as_of = db.calculated_as_of(latest_as_of)
        previous = db.fetch_snapshots(previous_as_of, None, None) if previous_as_of else None
        
        # Obtener señales
        signals = db.list_signals()
        
        # Obtener desempeño de señales
        performance_rows = db.get_signal_performance()
        performance = {row["setup"]: row for row in performance_rows}
        
        # Obtener perfil del usuario (opcional)
        profile_row = db.get_investor_profile(user.id)
        
        # Generar dashboard
        from app.daily_dashboard import generate_daily_dashboard
        
        dashboard = generate_daily_dashboard(
            ranking_current=current,
            ranking_previous=previous,
            signals=signals,
            performance=performance,
            spy_data=None,  # TODO: agregar datos recientes de SPY
            btc_data=None,  # TODO: agregar datos recientes de BTC
            profile=profile_row,
            as_of=latest_as_of,
        )
        
        return dashboard
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None


@app.post("/push/subscriptions", status_code=204, response_model=None)
def save_push_subscription(
    body: PushSubscriptionIn,
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> None:
    try:
        db.upsert_push_subscription(user.id, body.endpoint, body.keys.p256dh, body.keys.auth)
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None


def _profile_board(db: SupabaseRest, user_id: str) -> ProfileBoard:
    try:
        row = db.get_investor_profile(user_id)
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    profile = InvestorProfile.model_validate(row) if row else None
    sleeves = market_sleeves(
        None if profile is None else profile.risk,
        None if profile is None else profile.horizon_years,
    )
    parsed = parse_allocation(None if row is None else row.get("proposal"))
    return ProfileBoard(
        profile=profile,
        sleeves=[SleeveView.model_validate(item) for item in sleeves],
        allocation=Allocation.model_validate(parsed) if parsed else None,
    )


@app.get("/profile", response_model=ProfileBoard)
def profile(
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> ProfileBoard:
    return _profile_board(db, user.id)


@app.put("/profile", response_model=ProfileBoard)
def save_profile(
    body: ProfileIn,
    db: Annotated[SupabaseRest, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[UserContext, Depends(require_user)],
) -> ProfileBoard:
    record = {
        "user_id": user.id,
        "currency": body.currency,
        "amount": body.amount,
        "monthly_contribution": body.monthly_contribution,
        "horizon_years": body.horizon_years,
        "goal": body.goal,
        "risk": body.risk,
        "proposal": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        db.upsert_investor_profile(record)
        sleeves = market_sleeves(body.risk, body.horizon_years)
        proposal = allocation_proposal(
            settings.xai_api_key,
            allocation_facts(record, sleeves),
        )
        if proposal is not None:
            record["proposal"] = proposal
            db.upsert_investor_profile(record)
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    return _profile_board(db, user.id)


def _portfolio_board(db: SupabaseRest, user_id: str) -> PortfolioBoard:
    try:
        stored = db.list_holdings(user_id)
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    positions = priced_positions(stored)
    return PortfolioBoard(
        positions=[HoldingView.model_validate(row) for row in positions],
        totals=[PortfolioTotal.model_validate(row) for row in rollup(positions)],
    )


@app.get("/portfolio", response_model=PortfolioBoard)
def portfolio(
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> PortfolioBoard:
    return _portfolio_board(db, user.id)


@app.post("/portfolio", status_code=204, response_model=None)
def add_holding(
    body: HoldingIn,
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> None:
    try:
        holding = normalize_holding(
            body.asset_class,
            body.symbol,
            body.market,
            body.quantity,
            body.unit_cost,
            body.currency,
            body.opened_on,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    if holding["asset_class"] in ("stock", "etf") and body.market:
        try:
            company = db.fetch_company(body.market, holding["symbol"])
        except DatabaseUnavailable:
            raise HTTPException(status_code=503, detail="La base de datos no responde") from None
        if company and company.get("name"):
            holding["name"] = company["name"]
            if company.get("yahoo_symbol"):
                holding["yahoo_symbol"] = company["yahoo_symbol"]
    holding["user_id"] = user.id
    try:
        db.insert_holding(holding)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None


@app.delete("/portfolio/{holding_id}", status_code=204, response_model=None)
def remove_holding(
    holding_id: str,
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> None:
    try:
        deleted = db.delete_holding(user.id, holding_id)
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    if not deleted:
        raise HTTPException(status_code=404, detail="Esa posición no está en el portafolio")


@app.get("/ranking", response_model=RankingResponse)
def ranking(
    db: Annotated[SupabaseRest, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[UserContext, Depends(require_user)],
    market: Annotated[Market | None, Query()] = None,
    sector: Annotated[str | None, Query()] = None,
    style: Annotated[Style | None, Query()] = None,
    min_score: Annotated[int | None, Query(ge=0, le=100)] = None,
    as_of: Annotated[date | None, Query()] = None,
) -> RankingResponse:
    del user
    resolved, rows = _rows_for(db, as_of, market, sector)
    visible = sort_rows(apply_min(rows, style, min_score), style)
    return _ranking_response(resolved, rows, visible, settings)


@app.get("/ranking/highlights", response_model=RankingResponse)
def ranking_highlights(
    db: Annotated[SupabaseRest, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[UserContext, Depends(require_user)],
    market: Annotated[Market | None, Query()] = None,
    sector: Annotated[str | None, Query()] = None,
    as_of: Annotated[date | None, Query()] = None,
) -> RankingResponse:
    del user
    resolved, rows = _rows_for(db, as_of, market, sector)
    picked = highlights(rows, settings.rank_highlight_min)
    return _ranking_response(resolved, rows, picked, settings)


@app.get("/admin/access", response_model=AccessList)
def list_access(
    db: Annotated[SupabaseRest, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    admin: Annotated[UserContext, Depends(require_admin)],
) -> AccessList:
    del admin
    try:
        entries = db.list_allowed()
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    return AccessList(
        entries=[
            AccessEntry(
                email=entry["email"],
                role=entry["role"],
                active=entry["active"],
                protected=entry["email"] == settings.admin_email,
            )
            for entry in entries
        ]
    )


def _watch_row(body: WatchIn) -> dict[str, str]:
    symbol = body.symbol.strip().upper().replace(" ", "")
    name = body.name.strip()
    if not symbol or not name or len(symbol) > 12:
        raise HTTPException(status_code=400, detail="Escribe el símbolo y el nombre")
    if body.asset_class == "crypto":
        symbol = symbol.removesuffix("-USD")
        yahoo = f"{symbol}-USD"
    else:
        symbol = symbol.replace("-", ".")
        yahoo = symbol.replace(".", "-")
    if not symbol or not all(character.isalnum() or character in ".-" for character in yahoo):
        raise HTTPException(status_code=400, detail="El símbolo no es válido")
    return {
        "yahoo_symbol": yahoo,
        "symbol": symbol,
        "name": name,
        "asset_class": body.asset_class,
        "active": True,
    }


@app.get("/admin/settings", response_model=SignalSettings)
def admin_settings(
    db: Annotated[SupabaseRest, Depends(get_db)],
    admin: Annotated[UserContext, Depends(require_admin)],
) -> SignalSettings:
    del admin
    try:
        config = db.get_signal_config()
        watch = db.list_watchlist()
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    stock, crypto, horizon = _rules(db) if config is None else (
        float(config["stock_commission"]),
        float(config["crypto_commission"]),
        int(config["horizon_sessions"]),
    )
    return SignalSettings(
        stock_commission=stock,
        crypto_commission=crypto,
        horizon_sessions=horizon,
        watchlist=[WatchItem.model_validate(item) for item in watch],
    )


@app.put("/admin/settings", response_model=SignalSettings)
def save_admin_settings(
    body: SignalSettingsPatch,
    db: Annotated[SupabaseRest, Depends(get_db)],
    admin: Annotated[UserContext, Depends(require_admin)],
) -> SignalSettings:
    try:
        db.update_signal_config(
            {
                "stock_commission": body.stock_commission,
                "crypto_commission": body.crypto_commission,
                "horizon_sessions": body.horizon_sessions,
            }
        )
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    return admin_settings(db, admin)


@app.post("/admin/watchlist", status_code=204, response_model=None)
def add_watch(
    body: WatchIn,
    db: Annotated[SupabaseRest, Depends(get_db)],
    admin: Annotated[UserContext, Depends(require_admin)],
) -> None:
    del admin
    try:
        db.upsert_watch_item(_watch_row(body))
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None


@app.patch("/admin/watchlist", status_code=204, response_model=None)
def patch_watch(
    body: WatchPatch,
    db: Annotated[SupabaseRest, Depends(get_db)],
    admin: Annotated[UserContext, Depends(require_admin)],
) -> None:
    del admin
    try:
        updated = db.set_watch_active(body.yahoo_symbol, body.active)
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    if not updated:
        raise HTTPException(status_code=404, detail="Ese activo no está en la lista")


def _issue_access_password(
    db: SupabaseRest,
    settings: Settings,
    email: str,
    invited_by: str,
) -> dict:
    from app.db import EmailAlreadyRegistered
    from app.mailer import send_invitation
    from app.passwords import issue_temporary_password

    try:
        return issue_temporary_password(
            db,
            email=email,
            invited_by=invited_by,
            site_url=settings.site_url,
            send=send_invitation,
        )
    except EmailAlreadyRegistered:
        raise HTTPException(status_code=409, detail="Ese correo ya está registrado y no se pudo actualizar") from None
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None


@app.post("/me/password")
def replace_password(
    body: PasswordChange,
    db: Annotated[SupabaseRest, Depends(get_db)],
    user: Annotated[UserContext, Depends(require_user)],
) -> dict[str, bool]:
    from app.passwords import change_password

    try:
        change_password(db, user_id=user.id, email=user.email, new_password=body.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    return {"ok": True}


@app.post("/auth/forgot-password")
def forgot_password(
    body: ForgotPassword,
    db: Annotated[SupabaseRest, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, bool]:
    """Emite contraseña temporal por SMTP. Respuesta genérica para no filtrar invitados."""
    from app.mailer import send_password_reset
    from app.passwords import issue_temporary_password

    email = body.email
    try:
        allowed = db.get_allowed(email)
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    if not allowed or not allowed.get("active", True):
        return {"ok": True}
    try:
        issue_temporary_password(
            db,
            email=email,
            invited_by="forgot-password",
            site_url=settings.site_url,
            send=send_password_reset,
        )
        role = "admin" if email == settings.admin_email else str(allowed.get("role") or "member")
        db.update_profile(email, {"role": role, "active": True, "must_change_password": True})
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    except Exception:
        # No filtrar si el usuario existe; el cliente siempre ve éxito.
        return {"ok": True}
    return {"ok": True}


@app.post("/admin/access", response_model=AccessEntry)
def create_access(
    body: AccessCreate,
    db: Annotated[SupabaseRest, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    admin: Annotated[UserContext, Depends(require_admin)],
) -> AccessEntry:
    email = body.email.lower()
    role = "admin" if email == settings.admin_email else body.role
    try:
        entry = db.upsert_allowed(email, role, True)
        db.update_profile(email, {"role": role, "active": True})
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    issued = _issue_access_password(db, settings, email, admin.email)
    try:
        db.update_profile(email, {"role": role, "active": True, "must_change_password": True})
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    return AccessEntry(
        email=entry["email"],
        role=entry["role"],
        active=entry["active"],
        protected=email == settings.admin_email,
        mail=str(issued["mail"]),
        temporary_password=str(issued["temp_password"]),
    )


@app.post("/admin/access/link", response_model=AccessEntry)
def resend_access_link(
    body: AccessLink,
    db: Annotated[SupabaseRest, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    admin: Annotated[UserContext, Depends(require_admin)],
) -> AccessEntry:
    email = body.email.lower()
    try:
        current = db.get_allowed(email)
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    if current is None or not current.get("active"):
        raise HTTPException(status_code=400, detail="Ese correo no está activo")
    issued = _issue_access_password(db, settings, email, admin.email)
    return AccessEntry(
        email=current["email"],
        role=current["role"],
        active=bool(current["active"]),
        protected=email == settings.admin_email,
        mail=str(issued["mail"]),
        temporary_password=str(issued["temp_password"]),
    )


@app.patch("/admin/access", response_model=AccessEntry)
def patch_access(
    body: AccessPatch,
    db: Annotated[SupabaseRest, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    admin: Annotated[UserContext, Depends(require_admin)],
) -> AccessEntry:
    email = body.email.lower()
    if email == settings.admin_email and (body.active is False or body.role == "member"):
        raise HTTPException(
            status_code=400,
            detail="Este correo es el administrador de arranque",
        )
    if email == admin.email and (body.active is False or body.role == "member"):
        raise HTTPException(status_code=400, detail="No puedes quitarte el acceso")
    try:
        current = db.get_allowed(email)
        if current is None:
            raise HTTPException(status_code=404, detail="Ese correo no está en la lista")
        role = body.role or current["role"]
        active = current["active"] if body.active is None else body.active
        entry = db.upsert_allowed(email, role, active)
        db.update_profile(email, {"role": role, "active": active})
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    return AccessEntry.model_validate(entry)
