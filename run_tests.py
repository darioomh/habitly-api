import os
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_KEY", "")
import sys
from fastapi.testclient import TestClient
import app.database as database
import main
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
        tbl = self.fake._data.setdefault(self.name, [])
        if self._select_cols is not None and self._insert_payload is None and self._update_payload is None:
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
        if self._insert_payload is not None:
            new = self._insert_payload.copy()
            if "id" not in new:
                new["id"] = f"fake-{self.name}-{len(tbl)+1}"
            tbl.append(new)
            print(f"[FakeTable] INSERT into {self.name}: {new}")
            return FakeResp(data=[new])
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


def test_create_habit_log_demo_mode():
    orig = database.supabase
    database.supabase = None
    client = TestClient(main.app)
    resp = client.post("/api/habits/logs", params={"habit_id": "h1", "user_id": "u1", "date": "2020-01-01", "completed": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["habit_id"] == "h1"
    assert data["completed"] is True
    database.supabase = orig
    print("test_create_habit_log_demo_mode: PASSED")


def test_create_habit_log_awards_points():
    fake = FakeSupabase()
    fake._data["habits"] = []
    fake._data["habit_logs"] = []
    fake._data["challenge_habits"] = []
    fake._data["challenge_participants"] = []
    fake._data["users"] = []
    fake._data["user_fcm_tokens"] = []
    fake._data["challenge_points_log"] = []

    orig = database.supabase
    database.supabase = fake
    # also patch the imported supabase in modules that captured it at import time
    import app.api.habits as habits_mod
    import app.api.challenges as challenges_mod
    habits_mod.supabase = fake
    challenges_mod.supabase = fake
    client = TestClient(main.app)

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
    print("response body:", body)
    assert body.get("completed") is True

    try:
        # participant should have been created with total_points == xp_earned (10)
        parts = fake._data["challenge_participants"]
        assert len(parts) == 1
        assert parts[0]["challenge_id"] == "challenge-1"
        assert parts[0]["user_id"] == "user-1"
        assert parts[0]["total_points"] == 10

        # check log
        logs = fake._data["challenge_points_log"]
        assert len(logs) == 1
        assert logs[0]["challenge_id"] == "challenge-1"
        assert logs[0]["user_id"] == "user-1"
        assert logs[0]["points"] == 10

        print("test_create_habit_log_awards_points: PASSED")
    except AssertionError as ae:
        print("--- DEBUG STATE ON FAILURE ---")
        print("challenge_participants:", fake._data.get("challenge_participants"))
        print("challenge_points_log:", fake._data.get("challenge_points_log"))
        raise
    finally:
        database.supabase = orig


def test_increment_existing_participant():
    fake = FakeSupabase()
    fake._data["habits"] = [{"id": "habit-2", "xp_value": 12}]
    fake._data["habit_logs"] = []
    fake._data["challenge_habits"] = [{"id": "map-2", "challenge_id": "challenge-2", "habit_id": "habit-2"}]
    fake._data["challenge_participants"] = [{"id": "p1", "challenge_id": "challenge-2", "user_id": "user-2", "total_points": 5}]
    fake._data["users"] = [{"id": "user-2", "display_name": "User2"}]
    fake._data["user_fcm_tokens"] = []
    fake._data["challenge_points_log"] = []

    orig = database.supabase
    database.supabase = fake
    import app.api.habits as habits_mod
    import app.api.challenges as challenges_mod
    habits_mod.supabase = fake
    challenges_mod.supabase = fake
    client = TestClient(main.app)

    resp = client.post("/api/habits/logs", params={"habit_id": "habit-2", "user_id": "user-2", "date": date.today().isoformat(), "completed": True})
    assert resp.status_code == 200

    parts = fake._data["challenge_participants"]
    assert len(parts) == 1
    assert parts[0]["total_points"] == 15  # 5 + xp_earned (10)

    logs = fake._data["challenge_points_log"]
    assert len(logs) == 1
    assert logs[0]["points"] == 10

    database.supabase = orig
    print("test_increment_existing_participant: PASSED")


def test_fcm_notification_scheduled():
    fake = FakeSupabase()
    fake._data["habits"] = [{"id": "habit-3", "xp_value": 8}]
    fake._data["habit_logs"] = []
    fake._data["challenge_habits"] = [{"id": "map-3", "challenge_id": "challenge-3", "habit_id": "habit-3"}]
    fake._data["challenge_participants"] = []
    fake._data["users"] = [{"id": "user-3", "display_name": "User3"}]
    fake._data["user_fcm_tokens"] = [{"id": "t3", "user_id": "user-3", "fcm_token": "tok3"}]
    fake._data["challenge_points_log"] = []
    fake._data["sent_notifications"] = []

    orig = database.supabase
    database.supabase = fake
    import app.api.habits as habits_mod
    import app.api.challenges as challenges_mod
    habits_mod.supabase = fake
    challenges_mod.supabase = fake

    async def fake_send(tokens, title, body, data=None):
        fake._data["sent_notifications"].append({"tokens": tokens, "title": title, "body": body, "data": data})
        return True

    # monkeypatch the async sender
    habits_mod.send_fcm_notification_async = fake_send

    client = TestClient(main.app)
    resp = client.post("/api/habits/logs", params={"habit_id": "habit-3", "user_id": "user-3", "date": date.today().isoformat(), "completed": True})
    assert resp.status_code == 200

    # BackgroundTasks should have run; check sent_notifications
    sent = fake._data["sent_notifications"]
    assert len(sent) == 1
    assert sent[0]["tokens"] == ["tok3"]

    database.supabase = orig
    print("test_fcm_notification_scheduled: PASSED")


def test_points_log_pagination():
    fake = FakeSupabase()
    fake._data["challenge_points_log"] = []
    # create 60 entries across two challenges and two users
    for i in range(60):
        fake._data["challenge_points_log"].append({"id": f"l{i}", "challenge_id": f"c{(i%2)+1}", "user_id": f"u{(i%3)+1}", "points": i%10, "created_at": f"2026-01-01T00:00:{i:02d}"})

    orig = database.supabase
    database.supabase = fake
    import app.api.challenges as challenges_mod
    challenges_mod.supabase = fake
    client = TestClient(main.app)

    # page 2 with per_page 20 should return items 20-39
    try:
        resp = client.get("/api/challenges/points-log/list", params={"page": 2, "per_page": 20})
        print("resp status:", resp.status_code, "body:", resp.text)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 60
        assert len(data["items"]) == 20

        # filter by challenge_id
        resp2 = client.get("/api/challenges/points-log/list", params={"challenge_id": "c1", "page": 1, "per_page": 100})
        print("resp2 status:", resp2.status_code, "body:", resp2.text)
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert all(i["challenge_id"] == "c1" for i in d2["items"]) 

        print("test_points_log_pagination: PASSED")
    except AssertionError as ae:
        print("--- DEBUG ---")
        try:
            print("resp content:", resp.text)
        except Exception:
            pass
        try:
            print("resp2 content:", resp2.text)
        except Exception:
            pass
        raise
    finally:
        database.supabase = orig


if __name__ == "__main__":
    try:
        test_create_habit_log_demo_mode()
        test_create_habit_log_awards_points()
        test_increment_existing_participant()
        test_fcm_notification_scheduled()
        test_points_log_pagination()
        print("ALL TESTS PASSED")
        sys.exit(0)
    except AssertionError as e:
        print("TEST FAILED:", e)
        sys.exit(1)
    except Exception as ex:
        print("ERROR DURING TESTS:", ex)
        sys.exit(2)