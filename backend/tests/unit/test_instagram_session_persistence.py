"""Instagram sessions must survive an app restart (Render sleep/deploy).

Regression: sessions lived only in process memory (plus a local .tmp file),
so a Render restart wiped the connected shop and DM auto-replies silently
stopped. With a Supabase client injected, a new store instance (simulating
a restarted process) must reload the session by account id.
"""

from app.db.instagram_session_store import InstagramSessionStore


class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._filters: dict = {}

    def select(self, *_args: object) -> "_FakeQuery":
        return self

    def upsert(self, row: dict) -> "_FakeQuery":
        self._table.rows[row["session_id"]] = dict(row)
        return self

    def delete(self) -> "_FakeQuery":
        return self

    def eq(self, key: str, value: object) -> "_FakeQuery":
        self._filters[key] = value
        return self

    def execute(self) -> object:
        if self._filters:
            for sid, row in list(self._table.rows.items()):
                if all(row.get(k) == v for k, v in self._filters.items()):
                    self._table.rows.pop(sid, None)
            return type("R", (), {"data": []})()
        return type("R", (), {"data": list(self._table.rows.values())})()


class _FakeTable:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def select(self, *args: object) -> _FakeQuery:
        return _FakeQuery(self).select(*args)

    def upsert(self, row: dict) -> _FakeQuery:
        return _FakeQuery(self).upsert(row)

    def delete(self) -> _FakeQuery:
        return _FakeQuery(self).delete()


class _FakeSupabase:
    def __init__(self) -> None:
        self._table = _FakeTable()

    def table(self, _name: str) -> _FakeTable:
        return self._table


def test_session_survives_store_recreation_with_supabase() -> None:
    client = _FakeSupabase()
    store = InstagramSessionStore(supabase_client=client)
    session_id = store.create_session(
        access_token="tok-123",
        account_id="acc-1",
        username="sellsafe.testshop.ng",
        expires_in=3600,
        alias_ids=["me-1"],
    )

    # New instance == restarted process. Webhook lookup must find the token.
    restarted = InstagramSessionStore(supabase_client=client)
    found = restarted.find_by_account_id("acc-1")
    assert found is not None
    assert found.access_token == "tok-123"
    assert found.username == "sellsafe.testshop.ng"
    assert restarted.find_by_account_id("me-1") is not None
    assert restarted.get(session_id) is not None

    restarted.delete(session_id)
    assert InstagramSessionStore(supabase_client=client).get(session_id) is None


def test_store_without_supabase_still_works() -> None:
    store = InstagramSessionStore()
    session_id = store.create_session(access_token="t", account_id="a", username="u")
    assert store.get(session_id) is not None
