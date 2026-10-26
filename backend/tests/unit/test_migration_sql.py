from pathlib import Path

SQL = (
    Path(__file__).resolve().parents[2] / "app" / "db" / "migrations" / "0001_init.sql"
).read_text(encoding="utf-8")


def test_migration_covers_data_model_tables() -> None:
    for table in (
        "sellers",
        "products",
        "buyers",
        "orders",
        "payments",
        "payment_evidence",
        "verdicts",
        "fraud_signals",
        "messages",
        "webhook_events",
        "daily_summaries",
    ):
        assert f"create table {table} " in SQL


def test_migration_dedupes_messages_orders_buyers_and_webhooks() -> None:
    assert "external_msg_id text unique" in SQL
    assert "ref text not null unique" in SQL
    assert "unique (channel, external_id)" in SQL
    assert "unique (provider, event_id)" in SQL
    assert "unique (type, source_id)" in SQL


def test_money_columns_are_integer_kobo_and_phones_are_hashed() -> None:
    assert "price_kobo bigint" in SQL
    assert "total_kobo bigint" in SQL
    assert "expected_kobo bigint" in SQL
    assert "paid_kobo bigint" in SQL
    assert "phone_hash text" in SQL
    assert "create table buyers (" in SQL
    buyers = SQL.split("create table buyers (", 1)[1].split("create table orders (", 1)[0]
    assert "\n    phone text" not in buyers


def test_catalog_drafts_allow_one_pending_row() -> None:
    drafts = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "db"
        / "migrations"
        / "0002_catalog_drafts.sql"
    ).read_text(encoding="utf-8")
    assert "create table catalog_drafts" in drafts
    assert "where status = 'pending'" in drafts


def test_traces_migration_adds_speech_columns_and_trace_table() -> None:
    traces = (
        Path(__file__).resolve().parents[2] / "app" / "db" / "migrations" / "0003_traces.sql"
    ).read_text(encoding="utf-8")
    assert "add column if not exists transcript" in traces
    assert "add column if not exists asr_confidence" in traces
    assert "create table if not exists traces" in traces
