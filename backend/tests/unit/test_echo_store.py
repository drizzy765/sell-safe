from uuid import uuid4

from app.db.echo_store import SupabaseEchoStore


class _Result:
    def __init__(self, data: list[dict]) -> None:
        self.data = data


class _Duplicate(Exception):
    def __init__(self) -> None:
        super().__init__("duplicate key value violates unique constraint 23505")
        self.code = "23505"


class _Query:
    def __init__(self, db: dict[str, list[dict]], name: str) -> None:
        self._db = db
        self._name = name
        self._op = ""
        self._payload: dict | None = None
        self._filters: list[tuple[str, str, object]] = []
        self._limit: int | None = None

    def select(self, *_args: object, **_kwargs: object) -> "_Query":
        self._op = "select"
        return self

    def insert(self, payload: dict) -> "_Query":
        self._op = "insert"
        self._payload = payload
        return self

    def contains(self, column: str, value: object) -> "_Query":
        self._filters.append(("contains", column, value))
        return self

    def eq(self, column: str, value: object) -> "_Query":
        self._filters.append(("eq", column, value))
        return self

    def limit(self, count: int) -> "_Query":
        self._limit = count
        return self

    def execute(self) -> _Result:
        table = self._db.setdefault(self._name, [])
        if self._op == "select":
            rows = list(table)
            for kind, column, value in self._filters:
                if kind == "eq":
                    rows = [row for row in rows if row.get(column) == value]
                else:
                    assert isinstance(value, dict)
                    rows = [
                        row
                        for row in rows
                        if isinstance(row.get(column), dict)
                        and all(row[column].get(key) == item for key, item in value.items())
                    ]
            if self._limit is not None:
                rows = rows[: self._limit]
            return _Result(rows)
        assert self._payload is not None
        row = dict(self._payload)
        row.setdefault("id", str(uuid4()))
        if self._name == "messages":
            existing = {item.get("external_msg_id") for item in table}
            if row.get("external_msg_id") in existing:
                raise _Duplicate()
        table.append(row)
        return _Result([row])


class _Client:
    def __init__(self) -> None:
        self.db: dict[str, list[dict]] = {}

    def table(self, name: str) -> _Query:
        return _Query(self.db, name)


def test_supabase_store_creates_seller_and_buyer_once() -> None:
    client = _Client()
    store = SupabaseEchoStore(client)

    seller_a = store.ensure_seller("1234567890")
    seller_b = store.ensure_seller("1234567890")
    buyer_a = store.ensure_buyer("whatsapp", "15550000001", "Ada")
    buyer_b = store.ensure_buyer("whatsapp", "15550000001", "Ada")

    assert seller_a == seller_b
    assert buyer_a == buyer_b
    assert len(client.db["sellers"]) == 1
    assert client.db["sellers"][0]["channel_ids"] == {"whatsapp": "1234567890"}
    assert len(client.db["buyers"]) == 1


def test_supabase_store_rejects_duplicate_message_id() -> None:
    client = _Client()
    store = SupabaseEchoStore(client)
    seller_id = store.ensure_seller("1234567890")
    buyer_id = store.ensure_buyer("whatsapp", "15550000001")
    kwargs = {
        "seller_id": seller_id,
        "buyer_id": buyer_id,
        "channel": "whatsapp",
        "external_msg_id": "wamid.test-text-1",
        "message_type": "text",
        "text": "hello",
    }

    assert store.save_inbound(**kwargs) is True
    assert store.save_inbound(**kwargs) is False
    assert len(client.db["messages"]) == 1
