import os
from fastapi.testclient import TestClient
import pytest
from app import main
import app.database as database
from datetime import date


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
        # Simple behavior per table
        tbl = self.fake._data.setdefault(self.name, [])
        # SELECT
        if self._select_cols is not None and self._insert_payload is None and self._update_payload is None:
            # apply filters
            results = []
            for row in tbl:
                ok = True
                for k, v in self._filters:
                    if str(row.get(k)) != str(v):
                        ok = False
                        break
                if ok:
                    results.append(row.copy())
            return FakeResp(data=results)
        # INSERT
        if self._insert_payload is not None:
            # emulate adding id
            new = self._insert_payload.copy()
            if "id" not in new:
                new["id"] = f"fake-{self.name}-{len(tbl)+1}"
            tbl.append(new)
            return FakeResp(data=[new])
        # UPDATE
        if self._update_payload is not None:
            updated = []
            for row in tbl:
                ok = True
                for k, v in self._filters:
                    if str(row.get(k)) != str(v):
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
    # start with app main TestClient
    client = TestClient(main.app)
    fake = FakeSupabase()
    # provide some base data
    fake._data["habits"] = []
    fake._data["habit_logs"] = []
    fake._data["challenge_habits"] = []
    fake._data["challenge_participants"] = []
    fake._data["users"] = []
    fake._data["user_fcm_tokens"] = []
    fake._data["challenge_points_log"] = []

    # patch database.supabase
    orig = database.supabase
    monkeypatch.setattr(database, "supabase", fake)
    yield client, fake
    # restore
    monkeypatch.setattr(database, "supabase", orig)


def test_create_habit_log_demo_mode(monkeypatch):
    # set supabase to None to trigger demo path
    orig = database.supabase
    monkeypatch.setattr(database, "supabase", None)
    client = TestClient(main.app)
    resp = client.post("/api/habits/logs", params={"habit_id": "h1", "user_id": "u1", "date": "2020-01-01", "completed": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["habit_id"] == "h1"
    assert data["completed"] is True
    monkeypatch.setattr(database, "supabase", orig)


def test_create_habit_log_awards_points(client_and_fake_supabase):
    client, fake = client_and_fake_supabase

    # create habit with xp_value 15
    habit = {"id": "habit-1", "xp_value": 15}
    fake._data["habits"].append(habit)

    # map habit to challenge
    fake._data["challenge_habits"].append({"id": "map-1", "challenge_id": "challenge-1", "habit_id": "habit-1"})

    # add user display name
    fake._data["users"].append({"id": "user-1", "display_name": "Test User"})

    # add a dummy fcm token
    fake._data["user_fcm_tokens"].append({"id": "t1", "user_id": "user-1", "fcm_token": "token-abc"})

    # ensure no participant exists initially
    assert not fake._data["challenge_participants"]

    # call API to create habit log
    resp = client.post("/api/habits/logs", params={"habit_id": "habit-1", "user_id": "user-1", "date": date.today().isoformat(), "completed": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("completed") is True

    # participant should have been created with total_points == 15
    parts = fake._data["challenge_participants"]
    assert len(parts) == 1
    assert parts[0]["challenge_id"] == "challenge-1"
    assert parts[0]["user_id"] == "user-1"
    assert parts[0]["total_points"] == 15

    # check log
    logs = fake._data["challenge_points_log"]
    assert len(logs) == 1
    assert logs[0]["challenge_id"] == "challenge-1"
    assert logs[0]["user_id"] == "user-1"
    assert logs[0]["points"] == 15
