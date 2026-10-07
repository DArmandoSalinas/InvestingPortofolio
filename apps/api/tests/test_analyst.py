from app.analyst import reading_from_text


def test_reading_accepts_json_and_ignores_a_fence():
    text = """```json
{"summary":"La general es 91.","x_sentiment":"No encontré publicaciones útiles.","caution":""}
```"""
    reading = reading_from_text(text)
    assert reading is not None
    assert reading["summary"] == "La general es 91."
    assert reading["x_sentiment"] == "No encontré publicaciones útiles."
    assert reading["caution"] == ""


def test_reading_rejects_prose():
    assert reading_from_text("No hay JSON aquí.") is None


def test_a_report_that_dumps_field_names_is_dropped():
    text = (
        '{"summary":"La general es 91.","x_sentiment":"Nada.",'
        '"report":"revenue_yoy es 0.93 e ingresos 11119777000"}'
    )
    reading = reading_from_text(text)
    assert reading is not None
    assert reading["report"] == ""
