import os
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_KEY", "")
import sys
from fastapi.testclient import TestClient
import app.database as database
import main
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
            print(f"[FakeTable] INSERT into {self.name}: {new}")
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


def patch_supabase(fake):
    orig = database.supabase
    database.supabase = fake
    import app.api.habits as habits_mod
    import app.api.challenges as challenges_mod
    habits_mod.supabase = fake
    challenges_mod.supabase = fake
    return orig


def test_create_habit_log_demo_mode():
    import app.api.habits as habits_mod

    orig = habits_mod.supabase
    habits_mod.supabase = None
    database.supabase = None
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
    habits_mod.supabase = orig
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

    orig = patch_supabase(fake)
    client = TestClient(main.app)

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
    print("response body:", body)
    assert body.get("completed") is True

    try:
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

        print("test_create_habit_log_awards_points: PASSED")
    except AssertionError as ae:
        print("--- DEBUG STATE ON FAILURE ---")
        print("challenge_participants:", fake._data.get("challenge_participants"))
        print("challenge_points_log:", fake._data.get("challenge_points_log"))
        raise
    finally:
        database.supabase = orig
        import app.api.habits as habits_mod
        import app.api.challenges as challenges_mod
        habits_mod.supabase = orig
        challenges_mod.supabase = orig


def test_increment_existing_participant():
    fake = FakeSupabase()
    fake._data["habits"] = [{"id": "habit-2", "xp_value": 12, "user_id": "user-2"}]
    fake._data["habit_logs"] = []
    fake._data["challenge_habits"] = [{"id": "map-2", "challenge_id": "challenge-2", "habit_id": "habit-2"}]
    fake._data["challenge_participants"] = [{"id": "p1", "challenge_id": "challenge-2", "user_id": "user-2", "total_points": 5}]
    fake._data["users"] = [{"id": "user-2", "display_name": "User2"}]
    fake._data["user_fcm_tokens"] = []
    fake._data["challenge_points_log"] = []

    orig = patch_supabase(fake)
    client = TestClient(main.app)

    resp = client.post(
        "/api/habits/logs",
        params={"habit_id": "habit-2", "user_id": "user-2", "date": date.today().isoformat(), "completed": True},
        headers=auth_headers("user-2"),
    )
    assert resp.status_code == 200

    parts = fake._data["challenge_participants"]
    assert len(parts) == 1
    assert parts[0]["total_points"] == 15  # 5 + xp_earned (10)

    logs = fake._data["challenge_points_log"]
    assert len(logs) == 1
    assert logs[0]["points"] == 10

    database.supabase = orig
    import app.api.habits as habits_mod
    import app.api.challenges as challenges_mod
    habits_mod.supabase = orig
    challenges_mod.supabase = orig
    print("test_increment_existing_participant: PASSED")


def test_fcm_notification_scheduled():
    fake = FakeSupabase()
    fake._data["habits"] = [{"id": "habit-3", "xp_value": 8, "user_id": "user-3"}]
    fake._data["habit_logs"] = []
    fake._data["challenge_habits"] = [{"id": "map-3", "challenge_id": "challenge-3", "habit_id": "habit-3"}]
    fake._data["challenge_participants"] = []
    fake._data["users"] = [{"id": "user-3", "display_name": "User3"}]
    fake._data["user_fcm_tokens"] = [{"id": "t3", "user_id": "user-3", "fcm_token": "tok3"}]
    fake._data["challenge_points_log"] = []
    fake._data["sent_notifications"] = []

    orig = patch_supabase(fake)

    import app.api.habits as habits_mod

    async def fake_send(tokens, title, body, data=None):
        fake._data["sent_notifications"].append({"tokens": tokens, "title": title, "body": body, "data": data})
        return True

    habits_mod.send_fcm_notification_async = fake_send

    client = TestClient(main.app)
    resp = client.post(
        "/api/habits/logs",
        params={"habit_id": "habit-3", "user_id": "user-3", "date": date.today().isoformat(), "completed": True},
        headers=auth_headers("user-3"),
    )
    assert resp.status_code == 200

    sent = fake._data["sent_notifications"]
    assert len(sent) == 1
    assert sent[0]["tokens"] == ["tok3"]

    database.supabase = orig
    import app.api.challenges as challenges_mod
    habits_mod.supabase = orig
    challenges_mod.supabase = orig
    print("test_fcm_notification_scheduled: PASSED")


def test_points_log_pagination():
    fake = FakeSupabase()
    fake._data["challenge_points_log"] = []
    # 60 entries across two challenges for the SAME user (u1)
    for i in range(60):
        fake._data["challenge_points_log"].append(
            {"id": f"l{i}", "challenge_id": f"c{(i % 2) + 1}", "user_id": "u1", "points": i % 10, "created_at": f"2026-01-01T00:00:{i:02d}"}
        )
    # plus entries from other users that must NOT be returned
    fake._data["challenge_points_log"].append({"id": "other", "challenge_id": "c1", "user_id": "u9", "points": 5, "created_at": "2026-01-02T00:00:00"})

    orig = database.supabase
    database.supabase = fake
    import app.api.challenges as challenges_mod
    challenges_mod.supabase = fake
    client = TestClient(main.app)

    try:
        resp = client.get("/api/challenges/points-log/list", params={"page": 2, "per_page": 20}, headers=auth_headers("u1"))
        print("resp status:", resp.status_code, "body:", resp.text)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 60
        assert len(data["items"]) == 20

        resp2 = client.get("/api/challenges/points-log/list", params={"challenge_id": "c1", "page": 1, "per_page": 100}, headers=auth_headers("u1"))
        print("resp2 status:", resp2.status_code, "body:", resp2.text)
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert d2["total"] == 30
        assert all(i["challenge_id"] == "c1" for i in d2["items"])

        resp3 = client.get("/api/challenges/points-log/list", params={"page": 1, "per_page": 10}, headers=auth_headers("u9"))
        assert resp3.status_code == 200
        d3 = resp3.json()
        assert d3["total"] == 1

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
        challenges_mod.supabase = orig


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
