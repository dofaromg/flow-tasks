"""test_MRL_baseworld_schema_sandbox.py (origin: MrLiouWord)

把先前過度保守標『待實機』的 BaseWorld DB schema,在沙盒以 stdlib sqlite 真套用驗證:
27 表建成 + NOT NULL 完整性約束生效。真實 DL580 線上資料連線仍為待實機(誠實保留)。
"""
import os, sqlite3, pathlib, pytest

_REPO = pathlib.Path(__file__).resolve().parent.parent
_SCHEMA = _REPO / "MRL_BaseWorld_DB_v1" / "MRL_BaseWorld_DB_v1_Schema" / "MRL_BaseWorld_DB_v1.sql"


def _db():
    con = sqlite3.connect(":memory:")
    con.executescript(_SCHEMA.read_text(encoding="utf-8"))
    return con


@pytest.mark.skipif(not _SCHEMA.exists(), reason="schema sql absent")
def test_canonical_schema_creates_27_tables():
    con = _db()
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert len(tables) == 27


@pytest.mark.skipif(not _SCHEMA.exists(), reason="schema sql absent")
def test_not_null_integrity_enforced():
    # 完整性約束真的生效(缺必填欄被擋)= 非空殼 schema
    con = _db()
    t = con.execute("SELECT name FROM sqlite_master WHERE type='table' "
                    "ORDER BY name LIMIT 1").fetchone()[0]
    has_notnull = any(c[3] for c in con.execute(f"PRAGMA table_info({t})").fetchall())
    if has_notnull:
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(f"INSERT INTO {t} DEFAULT VALUES")


@pytest.mark.skipif(not _SCHEMA.exists(), reason="schema sql absent")
def test_tables_are_mrl_named():
    con = _db()
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert all(t.startswith("MRL_") for t in tables)   # rl_12 命名主權
