import json
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

XAI_URL = "https://api.x.ai/v1/responses"
MODEL = "grok-4.6"
_CACHE: dict[tuple[str, str, str], dict[str, str]] = {}

INSTRUCTIONS = """Eres el analista de una plataforma privada de estudio. Escribes en español de México.
Solo puedes usar los datos calculados de este mensaje y publicaciones recientes de X que encuentres con la herramienta.
No inventes cifras, precios, porcentajes ni fechas. Si un número no está en los datos o en una publicación, no lo escribas.
No recomiendes comprar ni vender. "Sin operación" es una respuesta válida.
Responde solo con JSON, sin markdown:
{"summary":"2 o 3 frases sobre las puntuaciones ya calculadas","x_sentiment":"qué se dice en X, o No encontré publicaciones útiles.","caution":"un riesgo concreto o vacío","report":"una frase en español sobre el trimestre, sin nombres de campos ni cifras crudas, o vacío"}"""


def reading_from_text(text: str) -> dict[str, str] | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    summary = str(data.get("summary") or "").strip()
    sentiment = str(data.get("x_sentiment") or "").strip()
    caution = str(data.get("caution") or "").strip()
    if not summary and not sentiment:
        return None
    report = str(data.get("report") or "").strip()
    if re.search(r"\b[a-z]+_[a-z]+\b", report) or re.search(r"\d{8,}", report):
        report = ""
    return {
        "summary": summary,
        "x_sentiment": sentiment,
        "caution": caution,
        "report": report,
    }


def _output_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for block in item.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "output_text" and isinstance(block.get("text"), str):
                chunks.append(block["text"])
    if chunks:
        return "\n".join(chunks)
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    return ""


def read_company(api_key: str, company: dict[str, Any], as_of: date) -> dict[str, str] | None:
    if not api_key:
        return None
    symbol = str(company.get("symbol") or "")
    market = str(company.get("market") or "")
    cache_key = (market, symbol, f"{as_of.isoformat()}:r3")
    cached = _CACHE.get(cache_key)
    if cached:
        return cached
    start = (as_of - timedelta(days=21)).isoformat()
    facts = {
        "empresa": company.get("name"),
        "simbolo": symbol,
        "mercado": market,
        "sector": company.get("sector"),
        "fecha": as_of.isoformat(),
        "crecimiento": company.get("growth"),
        "valor": company.get("value"),
        "momentum": company.get("momentum"),
        "general": company.get("composite"),
        "notas": {
            "crecimiento": company.get("growth_note"),
            "valor": company.get("value_note"),
            "momentum": company.get("momentum_note"),
        },
        "reporte": company.get("report"),
    }
    body = {
        "model": MODEL,
        "instructions": INSTRUCTIONS,
        "input": json.dumps(facts, ensure_ascii=False),
        "tools": [{"type": "x_search", "from_date": start, "to_date": as_of.isoformat()}],
        "reasoning": {"effort": "low"},
    }
    try:
        response = httpx.post(
            XAI_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=90,
        )
    except httpx.HTTPError:
        return None
    if response.status_code >= 400:
        return None
    reading = reading_from_text(_output_text(response.json()))
    if reading:
        _CACHE[cache_key] = reading
    return reading


SIGNAL_INSTRUCTIONS = """Eres el analista de una plataforma privada de estudio. Escribes en español de México.
La señal ya fue decidida por una regla de precio. Tú solo aportas contexto de publicaciones recientes en X.
No inventes cifras. No recomiendes comprar ni vender. "Sin operación" es válido.
Responde solo con JSON, sin markdown:
{"context":"una o dos frases, o vacío","risk":"un riesgo visto en X, o vacío"}"""


BRIEF_INSTRUCTIONS = """Eres el analista de una plataforma privada de estudio. Escribes en español de México.
Redactas el resumen de antes de la apertura. Solo puedes usar los hechos de este mensaje y publicaciones recientes de X.
No inventes cifras, precios, porcentajes ni fechas. Si no hay un día anterior, no hables de cambios.
No recomiendes comprar ni vender.
Responde solo con JSON, sin markdown:
{"headline":"una frase","ranking":"2 frases sobre altas y cambios, o vacío","signals":"1 o 2 frases sobre las señales abiertas, o vacío","events":"qué se dice en X, o No encontré publicaciones útiles."}"""


def brief_reading(api_key: str, facts: dict[str, Any]) -> dict[str, str]:
    empty = {"headline": "", "ranking": "", "signals": "", "events": ""}
    if not api_key:
        return empty
    as_of = str(facts.get("sesion") or "")[:10]
    if len(as_of) != 10:
        return empty
    start = (date.fromisoformat(as_of) - timedelta(days=3)).isoformat()
    body = {
        "model": MODEL,
        "instructions": BRIEF_INSTRUCTIONS,
        "input": json.dumps(facts, ensure_ascii=False),
        "tools": [{"type": "x_search", "from_date": start, "to_date": as_of}],
        "reasoning": {"effort": "low"},
    }
    try:
        response = httpx.post(
            XAI_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=90,
        )
    except httpx.HTTPError:
        return empty
    if response.status_code >= 400:
        return empty
    parsed = _brief_from_text(_output_text(response.json()))
    return parsed or empty


def _brief_from_text(text: str) -> dict[str, str] | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return {
        "headline": str(data.get("headline") or "").strip(),
        "ranking": str(data.get("ranking") or "").strip(),
        "signals": str(data.get("signals") or "").strip(),
        "events": str(data.get("events") or "").strip(),
    }


def signal_context(api_key: str, signal: dict[str, Any]) -> str:
    if not api_key:
        return ""
    as_of = str(signal.get("as_of") or "")[:10]
    if len(as_of) != 10:
        return ""
    start = (date.fromisoformat(as_of) - timedelta(days=21)).isoformat()
    facts = {
        "empresa": signal.get("name"),
        "simbolo": signal.get("symbol"),
        "regla": signal.get("setup"),
        "fecha": as_of,
        "razones": signal.get("reasons"),
        "riesgos": signal.get("risks"),
    }
    body = {
        "model": MODEL,
        "instructions": SIGNAL_INSTRUCTIONS,
        "input": json.dumps(facts, ensure_ascii=False),
        "tools": [{"type": "x_search", "from_date": start, "to_date": as_of}],
        "reasoning": {"effort": "low"},
    }
    try:
        response = httpx.post(
            XAI_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=90,
        )
    except httpx.HTTPError:
        return ""
    if response.status_code >= 400:
        return ""
    note = reading_from_text(
        _output_text(response.json()).replace('"context"', '"summary"').replace('"risk"', '"caution"')
    )
    if note is None:
        return ""
    return " ".join(part for part in (note["summary"], note["caution"]) if part).strip()


ALLOCATION_INSTRUCTIONS = """Eres el analista de una plataforma privada de estudio. Escribes en español de México.
Propones una mezcla entre cinco casilleros: cetes, ahorro, etf, acciones y crypto.
Solo puedes usar los hechos de este mensaje. Si una tasa o un rendimiento es null, no inventes el número ni lo menciones.
Los weight son enteros, cada uno entre 0 y 100, y tienen que sumar exactamente 100. No son una instrucción de compra o venta.
"Sin operación" cabe como más peso en cetes o ahorro.
Responde solo con JSON, sin markdown:
{"summary":"dos frases","risk":"un riesgo concreto","sleeves":[{"id":"cetes","weight":0,"reason":"una frase"},{"id":"ahorro","weight":0,"reason":""},{"id":"etf","weight":0,"reason":""},{"id":"acciones","weight":0,"reason":""},{"id":"crypto","weight":0,"reason":""}]}"""


def allocation_proposal(api_key: str, facts: dict[str, Any]) -> dict[str, Any] | None:
    from app.investor import parse_allocation

    if not api_key:
        return None
    as_of = datetime.now(timezone.utc).date()
    start = (as_of - timedelta(days=7)).isoformat()
    body = {
        "model": MODEL,
        "instructions": ALLOCATION_INSTRUCTIONS,
        "input": json.dumps(facts, ensure_ascii=False),
        "tools": [{"type": "x_search", "from_date": start, "to_date": as_of.isoformat()}],
        "reasoning": {"effort": "low"},
    }
    try:
        response = httpx.post(
            XAI_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=60,
        )
    except httpx.HTTPError:
        return None
    if response.status_code >= 400:
        return None
    parsed = _json_object(_output_text(response.json()))
    return parse_allocation(parsed)


def _json_object(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
