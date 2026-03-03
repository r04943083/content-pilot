"""SQLite database engine with async support."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    username TEXT NOT NULL,
    nickname TEXT DEFAULT '',
    avatar_url TEXT DEFAULT '',
    follower_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    post_count INTEGER DEFAULT 0,
    login_state TEXT DEFAULT 'inactive',  -- active / inactive / expired
    session_path TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, username)
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER REFERENCES accounts(id),
    platform TEXT NOT NULL,
    title TEXT DEFAULT '',
    content TEXT NOT NULL,
    tags TEXT DEFAULT '',          -- JSON array
    images TEXT DEFAULT '',        -- JSON array of paths
    video_path TEXT DEFAULT '',
    style TEXT DEFAULT '',
    status TEXT DEFAULT 'draft',   -- draft / approved / scheduled / publishing / published / failed
    platform_post_id TEXT DEFAULT '',
    platform_url TEXT DEFAULT '',
    error_message TEXT DEFAULT '',
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    platform TEXT NOT NULL,
    topic TEXT DEFAULT '',
    style TEXT DEFAULT 'tutorial',
    cron_expression TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER REFERENCES posts(id),
    platform TEXT NOT NULL,
    platform_post_id TEXT DEFAULT '',
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    favorites INTEGER DEFAULT 0,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS account_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER REFERENCES accounts(id),
    platform TEXT NOT NULL,
    follower_count INTEGER DEFAULT 0,
    follower_delta INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    total_likes INTEGER DEFAULT 0,
    recorded_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, recorded_date)
);

CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
CREATE INDEX IF NOT EXISTS idx_analytics_post ON analytics(post_id);
CREATE INDEX IF NOT EXISTS idx_metrics_account ON account_metrics(account_id);
"""


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.executescript(_SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    async def execute(self, sql: str, params: tuple = ()) -> aiosqlite.Cursor:
        try:
            cursor = await self.conn.execute(sql, params)
            await self.conn.commit()
            return cursor
        except Exception:
            await self.conn.rollback()
            raise

    async def fetch_one(self, sql: str, params: tuple = ()) -> dict | None:
        cursor = await self.conn.execute(sql, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    async def fetch_all(self, sql: str, params: tuple = ()) -> list[dict]:
        cursor = await self.conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # --- Account operations ---

    async def upsert_account(
        self, platform: str, username: str, **kwargs: object
    ) -> int:
        existing = await self.fetch_one(
            "SELECT id FROM accounts WHERE platform = ? AND username = ?",
            (platform, username),
        )
        if existing:
            sets = ", ".join(f"{k} = ?" for k in kwargs)
            if sets:
                await self.execute(
                    f"UPDATE accounts SET {sets}, updated_at = CURRENT_TIMESTAMP "
                    f"WHERE id = ?",
                    (*kwargs.values(), existing["id"]),
                )
            return existing["id"]
        cols = ["platform", "username", *kwargs.keys()]
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        cursor = await self.execute(
            f"INSERT INTO accounts ({col_names}) VALUES ({placeholders})",
            (platform, username, *kwargs.values()),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    async def get_account(self, platform: str) -> dict | None:
        return await self.fetch_one(
            "SELECT * FROM accounts WHERE platform = ? AND login_state = 'active' "
            "ORDER BY updated_at DESC LIMIT 1",
            (platform,),
        )

    async def get_all_accounts(self) -> list[dict]:
        return await self.fetch_all(
            "SELECT * FROM accounts ORDER BY platform, updated_at DESC"
        )

    # --- Post operations ---

    async def create_post(self, **kwargs: object) -> int:
        cols = list(kwargs.keys())
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        cursor = await self.execute(
            f"INSERT INTO posts ({col_names}) VALUES ({placeholders})",
            tuple(kwargs.values()),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    async def update_post(self, post_id: int, **kwargs: object) -> None:
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        await self.execute(
            f"UPDATE posts SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (*kwargs.values(), post_id),
        )

    async def get_post(self, post_id: int) -> dict | None:
        return await self.fetch_one("SELECT * FROM posts WHERE id = ?", (post_id,))

    async def get_posts(
        self, platform: str | None = None, status: str | None = None, limit: int = 50
    ) -> list[dict]:
        sql = "SELECT * FROM posts WHERE 1=1"
        params: list[object] = []
        if platform:
            sql += " AND platform = ?"
            params.append(platform)
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        return await self.fetch_all(sql, tuple(params))

    async def delete_post(self, post_id: int) -> None:
        await self.execute("DELETE FROM posts WHERE id = ?", (post_id,))

    # --- Schedule operations ---

    async def create_schedule(self, **kwargs: object) -> int:
        cols = list(kwargs.keys())
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        cursor = await self.execute(
            f"INSERT INTO schedules ({col_names}) VALUES ({placeholders})",
            tuple(kwargs.values()),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    async def get_schedules(self, enabled_only: bool = False) -> list[dict]:
        sql = "SELECT * FROM schedules"
        if enabled_only:
            sql += " WHERE enabled = 1"
        sql += " ORDER BY created_at DESC"
        return await self.fetch_all(sql)

    async def update_schedule(self, schedule_id: int, **kwargs: object) -> None:
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        await self.execute(
            f"UPDATE schedules SET {sets} WHERE id = ?",
            (*kwargs.values(), schedule_id),
        )

    async def delete_schedule(self, schedule_id: int) -> None:
        await self.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))

    # --- Analytics operations ---

    async def record_analytics(self, **kwargs: object) -> int:
        cols = list(kwargs.keys())
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        cursor = await self.execute(
            f"INSERT INTO analytics ({col_names}) VALUES ({placeholders})",
            tuple(kwargs.values()),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    async def get_post_analytics(self, post_id: int) -> list[dict]:
        return await self.fetch_all(
            "SELECT * FROM analytics WHERE post_id = ? ORDER BY collected_at DESC",
            (post_id,),
        )

    async def record_account_metrics(self, **kwargs: object) -> int:
        cols = list(kwargs.keys())
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        cursor = await self.execute(
            f"INSERT OR REPLACE INTO account_metrics ({col_names}) VALUES ({placeholders})",
            tuple(kwargs.values()),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    async def get_growth_data(
        self, account_id: int, days: int = 30
    ) -> list[dict]:
        return await self.fetch_all(
            "SELECT * FROM account_metrics WHERE account_id = ? "
            "ORDER BY recorded_date DESC LIMIT ?",
            (account_id, days),
        )

    async def count_posts_today(self, platform: str) -> int:
        row = await self.fetch_one(
            "SELECT COUNT(*) as cnt FROM posts "
            "WHERE platform = ? AND status = 'published' "
            "AND DATE(published_at) = DATE('now')",
            (platform,),
        )
        return row["cnt"] if row else 0
