import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.mark.asyncio
async def test_predict_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        payload = {"product_id": "CP_01", "periods": 4}
        r = await ac.post("/api/v1/forecast/predict", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "forecasts" in body
        assert len(body["forecasts"]) == 4
        assert body["product_id"] == "CP_01"


@pytest.mark.asyncio
async def test_recommend_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        payload = {"product_id": "CP_01", "periods": 4}
        r = await ac.post("/api/v1/forecast/recommend", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "recommendations" in body
        assert body["product_id"] == "CP_01"
