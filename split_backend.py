import os

os.makedirs('backend/routers', exist_ok=True)
os.makedirs('backend/services', exist_ok=True)
os.makedirs('backend/core', exist_ok=True)

with open('backend/core/state.py', 'w', encoding='utf-8') as f:
    f.write('''# 전역 상태 관리
task_db = {}
whisper_model = None
''')

with open('backend/database.py', 'w', encoding='utf-8') as f:
    f.write('''import sqlite3
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
''')

with open('backend/schemas.py', 'w', encoding='utf-8') as f:
    f.write('''from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str
    provider: str   # "openai" | "gemini"
    api_key: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UpdateApiKeysRequest(BaseModel):
    username: str
    provider: str   # "openai" | "gemini"
    api_key: str

class UpdateProfileRequest(BaseModel):
    username: str
    current_password: str
    new_password: str
''')

with open('backend/services/ai_service.py', 'w', encoding='utf-8') as f:
    f.write('''from fastapi import HTTPException
import time

SUMMARY_PROMPT = (
    "다음 텍스트는 음성 인식(STT) 변환 결과입니다. "
    "이 텍스트의 전체적인 맥락과 성격을 먼저 분석한 뒤, 가장 적합한 양식을 스스로 선택하여 한국어로 요약해 주세요. "
    "불필요한 인사말이나 잡담은 제외하되, 원본의 정보량에 비례하여 내용이 누락되지 않도록 길이를 유연하게 조절하세요.\\n\\n"
    "먼저 텍스트 상단에 [콘텐츠 유형: 회의 / 강의 및 발표 / 일반 대화 및 영상 중 택 1]을 명시하고, "
    "선택한 유형에 맞춰 아래 구조로 요약해 주세요.\\n\\n"
    "■ 유형 A [회의]를 선택한 경우:\\n"
    "1. [회의 주제 및 핵심 요약]: 회의의 전반적인 목적과 핵심 결론 (2~3문장)\\n"
    "2. [주요 논의 사항]: 제안된 아이디어, 의견 대립 등 세부 논의 내역 (-)\\n"
    "3. [결정 사항 및 향후 계획]: 최종 합의 내용과 향후 할 일(Action Items) (-)\\n\\n"
    "■ 유형 B [강의 및 발표]를 선택한 경우:\\n"
    "1. [핵심 주제]: 강의/발표의 메인 타이틀과 핵심 목표 (2~3문장)\\n"
    "2. [주요 개념 및 상세 내용]: 설명된 핵심 개념, 예시, 중요한 정의 등을 논리적 흐름에 따라 정리 (-)\\n"
    "3. [결론 및 시사점]: 발표자가 강조한 최종 메시지나 요약 내용\\n\\n"
    "■ 유형 C [일반 대화 및 영상]를 선택한 경우:\\n"
    "1. [전체 요약]: 영상/대화의 전반적인 스토리나 맥락 (2~3문장)\\n"
    "2. [주요 흐름]: 시간의 흐름이나 사건의 전개에 따른 주요 포인트 (-)\\n"
    "3. [인상 깊은 점 / 결론]: 텍스트에서 도출할 수 있는 주요 감상이나 최종 결론\\n\\n"
    "텍스트:\\n"
)

def summarize_with_openai(api_key: str, transcript: str) -> str:
    """OpenAI GPT-4o-mini를 사용하여 텍스트를 요약합니다."""
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": SUMMARY_PROMPT + transcript,
                }
            ],
            temperature=0.3,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"OpenAI API 호출 실패: {e}"
        )

def summarize_with_gemini(api_key: str, transcript: str, retries: int = 3) -> str:
    """Google Gemini API를 사용하여 텍스트를 요약합니다. (재시도 로직 추가)"""
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
        client = genai.Client(api_key=api_key)
        
        for attempt in range(retries):
            try:
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite", 
                    contents=SUMMARY_PROMPT + transcript,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                    ),
                )
                return (response.text or "").strip()
            except Exception as e:
                if ("503" in str(e) or "429" in str(e)) and attempt < retries - 1:
                    wait_time = attempt + 2 
                    print(f"⚠️ Gemini 서버 혼잡 감지. {wait_time}초 후 재시도합니다... ({attempt+1}/{retries})")
                    time.sleep(wait_time)
                    continue 
                else:
                    raise e
        return ""
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Gemini API 호출 실패: {e}"
        )
''')

with open('backend/services/audio_service.py', 'w', encoding='utf-8') as f:
    f.write('''import os
from database import get_conn
from services.ai_service import summarize_with_openai, summarize_with_gemini
import core.state as state

async def process_audio_task(task_id: str, username: str, filename: str, tmp_path: str, provider: str, api_key: str):
    try:
        if state.whisper_model is None:
            raise Exception("Whisper 모델이 초기화되지 않았습니다.")

        import imageio_ffmpeg
        _ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

        result = state.whisper_model.transcribe(tmp_path)
        transcript = str(result["text"]).strip()

        if provider == "openai":
            summary = summarize_with_openai(api_key, transcript)
        elif provider == "gemini":
            summary = summarize_with_gemini(api_key, transcript)
        else:
            raise Exception(f"지원하지 않는 provider: {provider}")

        conn = get_conn()
        try:
            cursor = conn.cursor()
            import datetime
            now = datetime.datetime.now().strftime("%b %d, %Y")
            
            ext = os.path.splitext(filename or "audio")[1].lower()
            if ext in ['.mp3', '.wav', '.m4a', '.flac']:
                file_type = "Audio"
            elif ext in ['.mp4', '.avi', '.mov']:
                file_type = "Video"
            else:
                file_type = "Document"
                
            cursor.execute(
                "INSERT INTO summaries (username, filename, transcript, summary, created_at, provider, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, filename or "unknown", transcript, summary, now, provider, file_type),
            )
            cursor.execute(
                "UPDATE users SET total_processed_files = total_processed_files + 1, total_api_requests = total_api_requests + 1 WHERE username = ?",
                (username,)
            )
            conn.commit()
            new_id = cursor.lastrowid
            
            state.task_db[task_id] = {
                "status": "completed",
                "result": {"id": new_id, "filename": filename, "message": "Success"}
            }
        except Exception as e:
            state.task_db[task_id] = {"status": "failed", "error": f"DB 저장 실패: {e}"}
        finally:
            conn.close()

    except Exception as e:
        state.task_db[task_id] = {"status": "failed", "error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
''')

with open('backend/routers/auth.py', 'w', encoding='utf-8') as f:
    f.write('''from fastapi import APIRouter, HTTPException
from database import get_conn
from schemas import RegisterRequest, LoginRequest, UpdateApiKeysRequest, UpdateProfileRequest
import hashlib

router = APIRouter()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@router.post("/register")
def register(req: RegisterRequest):
    if req.provider not in ("openai", "gemini"):
        raise HTTPException(status_code=400, detail="provider는 'openai' 또는 'gemini'만 허용됩니다.")
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (req.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다.")
        pw_hash = hash_password(req.password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, provider, api_key) VALUES (?, ?, ?, ?)",
            (req.username, pw_hash, req.provider, req.api_key),
        )
        conn.commit()
        return {"message": "User registered successfully"}
    finally:
        conn.close()

@router.post("/login")
def login(req: LoginRequest):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, password_hash, provider, api_key FROM users WHERE username = ?",
            (req.username,),
        )
        row = cursor.fetchone()
        if row is None or row["password_hash"] != hash_password(req.password):
            raise HTTPException(status_code=401, detail="사용자명 또는 비밀번호가 올바르지 않습니다.")
        return {
            "message": "Login successful",
            "username": row["username"],
            "provider": row["provider"],
            "api_key": row["api_key"],
        }
    finally:
        conn.close()

@router.put("/user/api-keys")
def update_api_keys(req: UpdateApiKeysRequest):
    if req.provider not in ("openai", "gemini"):
        raise HTTPException(status_code=400, detail="provider는 'openai' 또는 'gemini'만 허용됩니다.")
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (req.username,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")
        cursor.execute(
            "UPDATE users SET provider = ?, api_key = ? WHERE username = ?",
            (req.provider, req.api_key, req.username),
        )
        conn.commit()
        return {"message": "Settings updated successfully", "provider": req.provider}
    finally:
        conn.close()

@router.put("/user/profile")
def update_user_profile(req: UpdateProfileRequest):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (req.username,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")
        if row["password_hash"] != hash_password(req.current_password):
            raise HTTPException(status_code=401, detail="현재 비밀번호가 일치하지 않습니다.")
        new_pw_hash = hash_password(req.new_password)
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (new_pw_hash, req.username)
        )
        conn.commit()
        return {"message": "비밀번호가 성공적으로 변경되었습니다."}
    finally:
        conn.close()

@router.delete("/user/{username}")
def delete_user_account(username: str):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")
        cursor.execute("DELETE FROM summaries WHERE username = ?", (username,))
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        return {"message": "계정이 영구적으로 삭제되었습니다."}
    finally:
        conn.close()
''')

with open('backend/routers/upload.py', 'w', encoding='utf-8') as f:
    f.write('''from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks
import os
import tempfile
import uuid
from database import get_conn
import core.state as state
from services.audio_service import process_audio_task

router = APIRouter()

@router.post("/upload")
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    username: str = Form(...),
):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT provider, api_key FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"DB 조회 실패: {e}")

    if row is None:
        conn.close()
        raise HTTPException(status_code=400, detail="등록되지 않은 사용자입니다.")

    provider = row["provider"]
    api_key = row["api_key"]

    if not api_key:
        conn.close()
        raise HTTPException(status_code=400, detail="API 키가 설정되지 않았습니다.")
        
    conn.close()

    suffix = os.path.splitext(file.filename or "audio")[1] or ".tmp"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            content = await file.read()
            tmp.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임시 파일 저장 실패: {e}")

    task_id = str(uuid.uuid4())
    state.task_db[task_id] = {"status": "processing"}

    background_tasks.add_task(
        process_audio_task,
        task_id,
        username,
        file.filename,
        tmp_path,
        provider,
        api_key
    )

    return {"task_id": task_id, "message": "Processing started"}

@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    if task_id not in state.task_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return state.task_db[task_id]
''')

with open('backend/routers/summary.py', 'w', encoding='utf-8') as f:
    f.write('''from fastapi import APIRouter, HTTPException
from database import get_conn

router = APIRouter()

@router.get("/summaries/{username}")
def get_summaries(username: str):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, filename, created_at, provider, type FROM summaries WHERE username = ? ORDER BY id DESC",
            (username,),
        )
        rows = cursor.fetchall()
        return [{
            "id": row["id"], 
            "filename": row["filename"],
            "date": row["created_at"] or "Recent",
            "provider": row["provider"] or "Unknown",
            "type": row["type"] or "Audio"
        } for row in rows]
    finally:
        conn.close()

@router.get("/summary/{id}")
def get_summary(id: int):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, transcript, summary FROM summaries WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="해당 ID의 데이터가 존재하지 않습니다.")
        return {
            "filename": row["filename"],
            "transcript": row["transcript"],
            "summaryText": row["summary"],
        }
    finally:
        conn.close()

@router.delete("/summary/{id}")
def delete_summary(id: int):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM summaries WHERE id = ?", (id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="해당 ID의 데이터가 존재하지 않습니다.")
        return {"message": "Deleted successfully"}
    finally:
        conn.close()
''')

with open('backend/routers/usage.py', 'w', encoding='utf-8') as f:
    f.write('''from fastapi import APIRouter, HTTPException
from database import get_conn

router = APIRouter()

@router.get("/usage/{username}")
def get_usage(username: str):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT provider, total_processed_files, total_api_requests FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")

        current_provider = user_row["provider"]
        total_count = user_row["total_processed_files"]
        monthly_count = user_row["total_api_requests"]

        quota_limit = 100
        quota_percent = min(round((total_count / quota_limit) * 100), 100) if quota_limit > 0 else 0

        if quota_percent >= 80:
            quota_label = "Limit Approaching"
        elif quota_percent >= 50:
            quota_label = "Moderate Usage"
        else:
            quota_label = "Healthy"

        provider_display = {
            "openai": "OpenAI GPT-4o-mini",
            "gemini": "Google Gemini",
        }
        model_distribution = [
            {
                "name": provider_display.get(current_provider, current_provider),
                "percent": 100 if total_count > 0 else 0,
            }
        ]

        daily_usage = [
            int(monthly_count * 0.1), int(monthly_count * 0.2), 
            int(monthly_count * 0.15), int(monthly_count * 0.25), 
            int(monthly_count * 0.1), int(monthly_count * 0.15), 
            int(monthly_count * 0.05)
        ]

        return {
            "total_processed": total_count,
            "monthly_requests": monthly_count,
            "quota_percent": quota_percent,
            "quota_limit": quota_limit,
            "quota_label": quota_label,
            "model_distribution": model_distribution,
            "daily_usage": daily_usage,
        }
    finally:
        conn.close()
''')

with open('backend/routers/pages.py', 'w', encoding='utf-8') as f:
    f.write('''from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/")
@router.get("/login.html")
def serve_login():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "..", "..", "frontend", "login.html")
    path = os.path.normpath(path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="login.html을 찾을 수 없습니다.")
    return FileResponse(path, media_type="text/html")

@router.get("/home")
@router.get("/home.html")
def serve_home():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "..", "..", "frontend", "home.html")
    path = os.path.normpath(path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="home.html을 찾을 수 없습니다.")
    return FileResponse(path, media_type="text/html")

@router.get("/summary")
@router.get("/summary.html")
def serve_summary():
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "..", "..", "frontend", "summary.html")
    path = os.path.normpath(path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="summary.html을 찾을 수 없습니다.")
    return FileResponse(path, media_type="text/html")
''')

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write('''import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import whisper
import imageio_ffmpeg

from database import init_db
import core.state as state
from routers import auth, upload, summary, usage, pages

@asynccontextmanager
async def lifespan(app: FastAPI):
    ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    
    init_db()
    
    print("Loading Whisper model...")
    state.whisper_model = whisper.load_model("base")
    print("Whisper model loaded successfully.")
    
    yield

app = FastAPI(
    title="PSLW Audio Summary API",
    version="1.0.0",
    lifespan=lifespan,
)

# 추후 보안을 위해 실제 도메인으로 변경하세요
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(summary.router, prefix="/api", tags=["Summary"])
app.include_router(usage.router, prefix="/api", tags=["Usage"])
app.include_router(pages.router, tags=["Pages"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
''')
