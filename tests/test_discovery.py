import pytest

def test_weather_and_events_and_translate(client):
    # 1. Weather
    weather_res = client.get("/api/v1/discovery/weather?destination=Tokyo&start_date=2026-09-01&end_date=2026-09-03")
    assert weather_res.status_code == 200
    forecast = weather_res.json()
    assert len(forecast) == 3
    assert "temp_high" in forecast[0]

    # 2. Events
    events_res = client.get("/api/v1/discovery/events?destination=Tokyo&start_date=2026-09-01&end_date=2026-09-03")
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 1
    assert "Tokyo" in events[0]["name"]

    # 3. Translation
    trans_res = client.post("/api/v1/discovery/translate", json={"text": "thank you", "target_language": "ja"})
    assert trans_res.status_code == 200
    data = trans_res.json()
    assert data["translated_text"] == "Arigatou"

def test_cities_autocomplete_and_currency(client):
    # 1. Autocomplete with 't'
    res_t = client.get("/api/v1/places/cities/autocomplete?q=t")
    assert res_t.status_code == 200
    cities_t = res_t.json()
    city_names = [c["city"] for c in cities_t]
    assert "Tokyo" in city_names or "Toronto" in city_names
    
    # 2. Autocomplete with 'to'
    res_to = client.get("/api/v1/places/cities/autocomplete?q=to")
    assert res_to.status_code == 200
    cities_to = res_to.json()
    assert any(c["city"] == "Tokyo" for c in cities_to)
    assert any(c["city"] == "Toronto" for c in cities_to)

    # 3. Check Tokyo has JPY and exchange rate
    tokyo = next(c for c in cities_to if c["city"] == "Tokyo")
    assert tokyo["currency_code"] == "JPY"
    assert tokyo["currency_symbol"] == "¥"
    assert tokyo["exchange_rate_to_usd"] > 100

    # 4. Currency conversion
    conv_res = client.get("/api/v1/discovery/currency/convert?amount=100&from_currency=USD&to_currency=JPY")
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    assert conv_data["converted_amount"] > 10000
    assert "JPY" in conv_data["formatted"]

def test_places_search(client):
    res = client.get("/api/v1/places/search?q=Museum&destination=Paris")
    assert res.status_code == 200
    places = res.json()
    assert len(places) > 0
    assert "name" in places[0]
