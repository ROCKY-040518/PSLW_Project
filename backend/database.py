import sqlite3
from fastapi import HTTPException

DB_PATH = "audio_summaries.db"

def init_db() -> None:
    """앱 시작 시 필요한 테이블을 생성합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                username      TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                provider      TEXT NOT NULL,
                api_key       TEXT NOT NULL,
                total_processed_files INTEGER DEFAULT 0,
                total_api_requests INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS summaries (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT    NOT NULL,
                filename   TEXT    NOT NULL,
                transcript TEXT    NOT NULL,
                summary    TEXT    NOT NULL
            );
            """
        )
        conn.commit()

        try: cursor.execute("ALTER TABLE summaries ADD COLUMN created_at TEXT;")
        except: pass
        try: cursor.execute("ALTER TABLE summaries ADD COLUMN provider TEXT;")
        except: pass
        try: cursor.execute("ALTER TABLE summaries ADD COLUMN type TEXT;")
        except: pass

        try: cursor.execute("ALTER TABLE users ADD COLUMN total_processed_files INTEGER DEFAULT 0;")
        except sqlite3.OperationalError: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN total_api_requests INTEGER DEFAULT 0;")
        except sqlite3.OperationalError: pass
        conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"DB 초기화 실패: {e}") from e
    finally:
        conn.close()

def get_conn() -> sqlite3.Connection:
    """DB 연결을 반환합니다. Row를 dict처럼 접근할 수 있도록 row_factory를 설정합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {e}")
