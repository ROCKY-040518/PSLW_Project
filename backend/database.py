import sqlite3
from fastapi import HTTPException

# 로컬 환경에서 사용할 SQLite 데이터베이스 파일의 경로를 선언합니다.
DB_PATH = "audio_summaries.db"

def init_db() -> None:
    """앱 시작 시 필요한 테이블을 생성합니다."""
    try:
        # 설정한 파일 경로로 데이터베이스 연결을 엽니다.
        conn = sqlite3.connect(DB_PATH)
        # 데이터베이스 명령을 실행할 커서 객체를 생성합니다.
        cursor = conn.cursor()
        # 다중 쿼리 실행(executescript)을 통해 필요한 테이블 구조를 한 번에 생성합니다.
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
        # 지금까지 생성된 테이블 구조를 실제 DB 파일에 반영(커밋)합니다.
        conn.commit()

        # 기존 테이블에 없는 새로운 열(컬럼)들을 순차적으로 추가 시도합니다.
        # 이미 열이 존재하면 에러가 나므로 예외 처리를 통해 무시(pass)합니다.
        try: cursor.execute("ALTER TABLE summaries ADD COLUMN created_at TEXT;")
        except: pass
        try: cursor.execute("ALTER TABLE summaries ADD COLUMN provider TEXT;")
        except: pass
        try: cursor.execute("ALTER TABLE summaries ADD COLUMN type TEXT;")
        except: pass

        # users 테이블에도 누적 사용량을 위한 새 열을 추가 시도합니다.
        try: cursor.execute("ALTER TABLE users ADD COLUMN total_processed_files INTEGER DEFAULT 0;")
        except sqlite3.OperationalError: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN total_api_requests INTEGER DEFAULT 0;")
        except sqlite3.OperationalError: pass
        
        # 새롭게 추가된 열 정보들을 DB에 반영(커밋)합니다.
        conn.commit()
    except sqlite3.Error as e:
        # 초기화 중 DB 오류가 발생하면 런타임 에러를 던져 애플리케이션 시작을 막습니다.
        raise RuntimeError(f"DB 초기화 실패: {e}") from e
    finally:
        # 데이터베이스 초기화가 성공했든 실패했든 무조건 연결을 닫습니다.
        conn.close()

def get_conn() -> sqlite3.Connection:
    """DB 연결을 반환합니다. Row를 dict처럼 접근할 수 있도록 row_factory를 설정합니다."""
    try:
        # 새로운 DB 커넥션 인스턴스를 생성합니다.
        conn = sqlite3.connect(DB_PATH)
        # 조회된 데이터(Row)의 컬럼명으로 값에 접근할 수 있게 팩토리를 설정합니다.
        conn.row_factory = sqlite3.Row
        # 설정이 끝난 DB 커넥션을 반환합니다.
        return conn
    except sqlite3.Error as e:
        # 커넥션 생성 과정에서 에러가 나면 500 에러를 반환합니다.
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {e}")

# -------------------------------------------------------------------
# [마감 전 방어적 리팩토링] FastAPI 의존성 주입(DI)을 위한 함수 추가
# -------------------------------------------------------------------
def get_db():
    """
    FastAPI Depends를 위한 DB 커넥션 제너레이터.
    - check_same_thread=False: FastAPI의 멀티 스레드 환경에서 SQLite Thread 에러를 방지합니다.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()