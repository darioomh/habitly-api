import os
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_KEY", "")
from fastapi.testclient import TestClient
import pytest
import main
import app.database as database
from app.auth import create_access_token
from datetime import date


def auth_headers(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


class FakeResp:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class FakeTable:
    def __init__(self, fake, name):
        self.fake = fake
        self.name = name
        self._select_cols = None
        self._filters = []
        self._update_payload = None
        self._insert_payload = None

    def select(self, *cols):
        self._select_cols = cols
        return self

    def eq(self, key, value):
        self._filters.append((key, value))
        return self

    def in_(self, key, values):
        self._filters.append((key, list(values)))
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, n):
        return self

    def insert(self, payload):
        self._insert_payload = payload
        return self

    def update(self, payload):
        self._update_payload = payload
        return self

    def delete(self):
        return self

    def execute(self):
        tbl = self.fake._data.setdefault(self.name, [])
        if self._select_cols is not None and self._insert_payload is None and self._update_payload is None:
            results = []
            for row in tbl:
                ok = True
                for k, v in self._filters:
                    if isinstance(v, list):
                        if str(row.get(k)) not in [str(x) for x in v]:
                            ok = False
                            break
                    elif str(row.get(k)) != str(v):
                        ok = False
                        break
                if ok:
                    results.append(row.copy())
            return FakeResp(data=results)
        if self._insert_payload is not None:
            new = self._insert_payload.copy()
            if "id" not in new:
                new["id"] = f"fake-{self.name}-{len(tbl)+1}"
            tbl.append(new)
            return FakeResp(data=[new])
        if self._update_payload is not None:
            updated = []
            for row in tbl:
                ok = True
                for k, v in self._filters:
                    if isinstance(v, list):
                        if str(row.get(k)) not in [str(x) for x in v]:
                            ok = False
                            break
                    elif str(row.get(k)) != str(v):
                        ok = False
                        break
                if ok:
                    row.update(self._update_payload)
                    updated.append(row.copy())
            return FakeResp(data=updated)
        return FakeResp(data=None)


class FakeSupabase:
    def __init__(self):
        self._data = {}

    def table(self, name):
        return FakeTable(self, name)


@pytest.fixture(autouse=True)
def client_and_fake_supabase(monkeypatch):
    client = TestClient(main.app)
    fake = FakeSupabase()
    fake._data["habits"] = []
    fake._data["habit_logs"] = []
    fake._data["challenge_habits"] = []
    fake._data["challenge_participants"] = []
    fake._data["users"] = []
    fake._data["user_fcm_tokens"] = []
    fake._data["challenge_points_log"] = []

    import app.api.habits as habits_mod
    import app.api.challenges as challenges_mod

    origs = {
        "database": database.supabase,
        "habits": habits_mod.supabase,
        "challenges": challenges_mod.supabase,
    }
    monkeypatch.setattr(database, "supabase", fake)
    monkeypatch.setattr(habits_mod, "supabase", fake)
    monkeypatch.setattr(challenges_mod, "supabase", fake)
    yield client, fake
    monkeypatch.setattr(database, "supabase", origs["database"])
    monkeypatch.setattr(habits_mod, "supabase", origs["habits"])
    monkeypatch.setattr(challenges_mod, "supabase", origs["challenges"])


def test_create_habit_log_demo_mode(monkeypatch):
    import app.api.habits as habits_mod

    orig = habits_mod.supabase
    monkeypatch.setattr(habits_mod, "supabase", None)
    monkeypatch.setattr(database, "supabase", None)
    client = TestClient(main.app)
    resp = client.post(
        "/api/habits/logs",
        params={"habit_id": "h1", "user_id": "u1", "date": "2020-01-01", "completed": True},
        headers=auth_headers("u1"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["habit_id"] == "h1"
    assert data["completed"] is True
    monkeypatch.setattr(habits_mod, "supabase", orig)
    monkeypatch.setattr(database, "supabase", orig)


def test_create_habit_log_requires_auth(client_and_fake_supabase):
    client, fake = client_and_fake_supabase
    fake._data["habits"].append({"id": "habit-1", "xp_value": 15, "user_id": "user-1"})
    resp = client.post(
        "/api/habits/logs",
        params={"habit_id": "habit-1", "user_id": "user-1", "date": date.today().isoformat(), "completed": True},
    )
    assert resp.status_code == 401


def test_create_habit_log_requires_ownership(client_and_fake_supabase):
    client, fake = client_and_fake_supabase
    fake._data["habits"].append({"id": "habit-1", "xp_value": 15, "user_id": "user-other"})
    resp = client.post(
        "/api/habits/logs",
        params={"habit_id": "habit-1", "user_id": "user-1", "date": date.today().isoformat(), "completed": True},
        headers=auth_headers("user-1"),
    )
    assert resp.status_code == 403


def test_create_habit_log_awards_points(client_and_fake_supabase):
    client, fake = client_and_fake_supabase

    habit = {"id": "habit-1", "xp_value": 15, "user_id": "user-1"}
    fake._data["habits"].append(habit)

    fake._data["challenge_habits"].append({"id": "map-1", "challenge_id": "challenge-1", "habit_id": "habit-1"})

    fake._data["users"].append({"id": "user-1", "display_name": "Test User"})

    fake._data["user_fcm_tokens"].append({"id": "t1", "user_id": "user-1", "fcm_token": "token-abc"})

    assert not fake._data["challenge_participants"]

    resp = client.post(
        "/api/habits/logs",
        params={"habit_id": "habit-1", "user_id": "user-1", "date": date.today().isoformat(), "completed": True},
        headers=auth_headers("user-1"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("completed") is True

    parts = fake._data["challenge_participants"]
    assert len(parts) == 1
    assert parts[0]["challenge_id"] == "challenge-1"
    assert parts[0]["user_id"] == "user-1"
    assert parts[0]["total_points"] == 10

    logs = fake._data["challenge_points_log"]
    assert len(logs) == 1
    assert logs[0]["challenge_id"] == "challenge-1"
    assert logs[0]["user_id"] == "user-1"
    assert logs[0]["points"] == 10


def test_habit_get_requires_auth(client_and_fake_supabase):
    client, fake = client_and_fake_supabase
    fake._data["habits"].append({"id": "habit-1", "user_id": "user-1"})
    resp = client.get("/api/habits/habit-1")
    assert resp.status_code == 401


def test_habit_get_ownership(client_and_fake_supabase):
    client, fake = client_and_fake_supabase
    fake._data["habits"].append({"id": "habit-1", "user_id": "user-other"})
    resp = client.get("/api/habits/habit-1", headers=auth_headers("user-1"))
    assert resp.status_code == 403
