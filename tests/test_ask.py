"""Q&A section: question parsing, offline answers, book search, and the optional AI path (mocked)."""
import json

import httpx
from fastapi.testclient import TestClient

from vedic_engine import ask, books
from vedic_engine.api import app

C = TestClient(app)
B = {"datetime_local": "1980-12-27T22:46:00", "tz": "Asia/Kolkata", "lat": 31.708, "lon": 76.932,
     "at": "2026-11-18T12:00:00"}


def test_parse():
    p = ask.parse("What does Saturn in my 2nd house mean?")
    assert p["planets"] == ["Saturn"] and p["houses"] == [2] and p["areas"] == []
    p = ask.parse("मेरी शादी कब होगी?")
    assert p["areas"] == ["marriage"] and "when" in p["intents"]
    p = ask.parse("सातवें भाव में शुक्र")
    assert p["houses"] == [7] and p["planets"] == ["Venus"]
    assert ask.parse("remedy for kaal sarp dosha")["doshas"] == ["kaal_sarp"]


def test_books_index_and_search():
    st = books.status()
    assert all(st[b] > 100 for b in st), st
    hits = books.search("marriage", lang="en")
    assert hits and all(h["snippet"] for h in hits)
    assert books.page_label("lalkitab", 5) == "PDF p. 5"


def test_offline_answers(monkeypatch, tmp_path):
    monkeypatch.setattr(ask, "CONFIG", tmp_path / "ai.json")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = C.post("/ask", json={**B, "lang": "en", "question": "When will I get a promotion?"}).json()
    assert r["mode"] == "offline" and r["sections"][0]["kind"] == "area"
    assert "Periods that activate it" in " ".join(r["sections"][0]["paras"])
    assert any(x["book"] == "bhrigu" and x.get("why") for x in r["refs"])
    r = C.post("/ask", json={**B, "lang": "hi", "question": "कालसर्प दोष का उपाय क्या है?"}).json()
    assert r["remedies"] and "कालसर्प" in str(r["sections"])
    r = C.post("/ask", json={**B, "lang": "en", "question": "hello"}).json()
    assert r["sections"][0]["kind"] == "now"


def test_ai_path_mocked(monkeypatch, tmp_path):
    monkeypatch.setattr(ask, "CONFIG", tmp_path / "ai.json")
    assert C.post("/ask/key", json={"api_key": "sk-ant-test-1234"}).json()["ai"] is True
    sent = {}

    def fake_post(url, **kw):
        sent.update(kw["json"])
        return httpx.Response(200, json={"content": [{"type": "text", "text": "Answer [Lal Kitab, p. 207]"}]},
                              request=httpx.Request("POST", url))
    monkeypatch.setattr(ask.httpx, "post", fake_post)
    r = C.post("/ask", json={**B, "lang": "en", "question": "What about Saturn in my 2nd house?"}).json()
    assert r["mode"] == "ai" and r["ai_text"].startswith("Answer")
    assert "Saturn: Virgo" in sent["messages"][0]["content"] and "<page" in sent["messages"][0]["content"]

    def fail_post(url, **kw):
        return httpx.Response(401, json={"error": {"message": "invalid x-api-key"}}, request=httpx.Request("POST", url))
    monkeypatch.setattr(ask.httpx, "post", fail_post)
    r = C.post("/ask", json={**B, "lang": "en", "question": "career"}).json()
    assert r["mode"] == "offline" and "invalid x-api-key" in r["ai_error"]
    assert C.post("/ask/key", json={"api_key": ""}).json()["ai"] is False
    assert json.loads((tmp_path / "ai.json").read_text())["api_key"] == ""
