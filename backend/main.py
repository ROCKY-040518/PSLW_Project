"""
PSLW Project - FastAPI Backend
-------------------------------
단일 파일 구성: 인증, 음성 업로드(Whisper STT), AI 요약(OpenAI/Gemini), 조회/삭제 API
"""

import hashlib
import os
import sqlite3
import tempfile
from contextlib import asynccontextmanager

import imageio_ffmpeg

import whisper
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────
DB_PATH = "audio_summaries.db"

SUMMARY_PROMPT = (
    "다음 텍스트는 음성 인식(STT) 변환 결과입니다. "
    "이 텍스트의 전체적인 맥락과 성격을 먼저 분석한 뒤, 가장 적합한 양식을 스스로 선택하여 한국어로 요약해 주세요. "
    "불필요한 인사말이나 잡담은 제외하되, 원본의 정보량에 비례하여 내용이 누락되지 않도록 길이를 유연하게 조절하세요.\n\n"
    "먼저 텍스트 상단에 [콘텐츠 유형: 회의 / 강의 및 발표 / 일반 대화 및 영상 중 택 1]을 명시하고, "
    "선택한 유형에 맞춰 아래 구조로 요약해 주세요.\n\n"
    "■ 유형 A [회의]를 선택한 경우:\n"
    "1. [회의 주제 및 핵심 요약]: 회의의 전반적인 목적과 핵심 결론 (2~3문장)\n"
    "2. [주요 논의 사항]: 제안된 아이디어, 의견 대립 등 세부 논의 내역 (-)\n"
    "3. [결정 사항 및 향후 계획]: 최종 합의 내용과 향후 할 일(Action Items) (-)\n\n"
    "■ 유형 B [강의 및 발표]를 선택한 경우:\n"
    "1. [핵심 주제]: 강의/발표의 메인 타이틀과 핵심 목표 (2~3문장)\n"
    "2. [주요 개념 및 상세 내용]: 설명된 핵심 개념, 예시, 중요한 정의 등을 논리적 흐름에 따라 정리 (-)\n"
    "3. [결론 및 시사점]: 발표자가 강조한 최종 메시지나 요약 내용\n\n"
    "■ 유형 C [일반 대화 및 영상]을 선택한 경우:\n"
    "1. [전체 요약]: 영상/대화의 전반적인 스토리나 맥락 (2~3문장)\n"
    "2. [주요 흐름]: 시간의 흐름이나 사건의 전개에 따른 주요 포인트 (-)\n"
    "3. [인상 깊은 점 / 결론]: 텍스트에서 도출할 수 있는 주요 감상이나 최종 결론\n\n"
    "텍스트:\n"
)


# ─────────────────────────────────────────────
# DB 초기화
# ─────────────────────────────────────────────
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
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN total_processed_files INTEGER DEFAULT 0;")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN total_api_requests INTEGER DEFAULT 0;")
        except sqlite3.OperationalError:
            pass
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


# 전역 모델 변수
whisper_model = None

# ─────────────────────────────────────────────
# Lifespan (앱 시작/종료 이벤트)
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global whisper_model
    # imageio-ffmpeg에 번들된 ffmpeg 바이너리를 PATH에 추가
    ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    
    init_db()
    
    # 앱 시작 시 Whisper 모델 1회 로드
    print("Loading Whisper model...")
    whisper_model = whisper.load_model("base")
    print("Whisper model loaded successfully.")
    
    yield


# ─────────────────────────────────────────────
# FastAPI 앱 생성
# ─────────────────────────────────────────────
app = FastAPI(
    title="PSLW Audio Summary API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Pydantic 요청 모델
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# 유틸 함수
# ─────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


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


def summarize_with_gemini(api_key: str, transcript: str) -> str:
    """Google Gemini API를 사용하여 텍스트를 요약합니다."""
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=SUMMARY_PROMPT + transcript,
            config=types.GenerateContentConfig(
                temperature=0.3,
            ),
        )
        return (response.text or "").strip()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Gemini API 호출 실패: {e}"
        )


# ─────────────────────────────────────────────
# 1. Auth API
# ─────────────────────────────────────────────
@app.post("/api/register")
def register(req: RegisterRequest):
    """신규 사용자를 등록합니다."""
    if req.provider not in ("openai", "gemini"):
        raise HTTPException(
            status_code=400, detail="provider는 'openai' 또는 'gemini'만 허용됩니다."
        )

    conn = get_conn()
    try:
        cursor = conn.cursor()
        # 중복 확인
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회원가입 처리 중 오류 발생: {e}")
    finally:
        conn.close()


@app.post("/api/login")
def login(req: LoginRequest):
    """사용자를 인증하고 정보를 반환합니다."""
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
            "username": row["username"],
            "provider": row["provider"],
            "api_key": row["api_key"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그인 처리 중 오류 발생: {e}")
    finally:
        conn.close()


@app.put("/api/user/api-keys")
def update_user_settings(req: UpdateApiKeysRequest):
    """사용자의 provider와 api_key를 업데이트합니다."""
    if req.provider not in ("openai", "gemini"):
        raise HTTPException(
            status_code=400, detail="provider는 'openai' 또는 'gemini'만 허용됩니다."
        )

    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username FROM users WHERE username = ?", (req.username,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")

        cursor.execute(
            "UPDATE users SET provider = ?, api_key = ? WHERE username = ?",
            (req.provider, req.api_key, req.username),
        )
        conn.commit()
        return {"message": "Settings updated successfully", "provider": req.provider}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설정 업데이트 실패: {e}")
    finally:
        conn.close()


@app.put("/api/user/profile")
def update_user_profile(req: UpdateProfileRequest):
    """사용자의 비밀번호를 업데이트합니다."""
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 업데이트 실패: {e}")
    finally:
        conn.close()


@app.delete("/api/user/{username}")
def delete_user_account(username: str):
    """사용자 계정과 관련 데이터(summaries)를 영구 삭제합니다."""
    conn = get_conn()
    try:
        cursor = conn.cursor()
        # 먼저 사용자가 존재하는지 확인
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")
            
        # 외래 키 또는 연관된 데이터(summaries) 삭제
        cursor.execute("DELETE FROM summaries WHERE username = ?", (username,))
        # 사용자 레코드 삭제
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        return {"message": "계정이 영구적으로 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"계정 삭제 실패: {e}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# 2. Core Processing API
# ─────────────────────────────────────────────
@app.post("/api/upload")
async def upload_audio(
    file: UploadFile = File(...),
    username: str = Form(...),
):
    """오디오 파일을 업로드받아 Whisper STT 후 AI 요약을 생성하고 DB에 저장합니다."""

    # ── 사용자 정보 조회 ──────────────────────
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT provider, api_key FROM users WHERE username = ?", (username,)
        )
        row = cursor.fetchone()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"DB 조회 실패: {e}")

    if row is None:
        conn.close()
        raise HTTPException(status_code=400, detail="등록되지 않은 사용자입니다.")

    provider: str = row["provider"]
    api_key: str = row["api_key"]

    if not api_key:
        conn.close()
        raise HTTPException(status_code=400, detail="API 키가 설정되지 않았습니다.")

    # ── 임시 파일 저장 ────────────────────────
    suffix = os.path.splitext(file.filename or "audio")[1] or ".tmp"
    tmp_path: str = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            content = await file.read()
            tmp.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임시 파일 저장 실패: {e}")

    # ── Whisper STT ───────────────────────────
    try:
        if whisper_model is None:
            raise HTTPException(status_code=500, detail="Whisper 모델이 초기화되지 않았습니다.")

        # imageio-ffmpeg 번들 바이너리를 PATH에 동적 추가
        _ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

        result = whisper_model.transcribe(tmp_path)
        transcript: str = str(result["text"]).strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whisper 음성 인식 실패: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass  # 삭제 실패해도 계속 진행

    # ── AI 요약 생성 ──────────────────────────
    if provider == "openai":
        summary = summarize_with_openai(api_key, transcript)
    elif provider == "gemini":
        summary = summarize_with_gemini(api_key, transcript)
    else:
        conn.close()
        raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")

    # ── DB 저장 ───────────────────────────────
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO summaries (username, filename, transcript, summary) VALUES (?, ?, ?, ?)",
            (username, file.filename or "unknown", transcript, summary),
        )
        cursor.execute(
            "UPDATE users SET total_processed_files = total_processed_files + 1, total_api_requests = total_api_requests + 1 WHERE username = ?",
            (username,)
        )
        conn.commit()
        new_id = cursor.lastrowid
        return {"id": new_id, "filename": file.filename, "message": "Success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 저장 실패: {e}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# 3. Data Retrieval API
# ─────────────────────────────────────────────
@app.get("/api/summaries/{username}")
def get_summaries(username: str):
    """사용자의 요약 목록을 ID 역순으로 반환합니다. (transcript, summary 제외)"""
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, filename FROM summaries WHERE username = ? ORDER BY id DESC",
            (username,),
        )
        rows = cursor.fetchall()
        return [{"id": row["id"], "filename": row["filename"]} for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"목록 조회 실패: {e}")
    finally:
        conn.close()


@app.get("/api/summary/{id}")
def get_summary(id: int):
    """특정 ID의 상세 정보를 반환합니다."""
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filename, transcript, summary FROM summaries WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="해당 ID의 데이터가 존재하지 않습니다.")
        return {
            "filename": row["filename"],
            "transcript": row["transcript"],
            "summaryText": row["summary"],  # 프론트엔드 키 이름에 맞춤
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상세 조회 실패: {e}")
    finally:
        conn.close()


@app.delete("/api/summary/{id}")
def delete_summary(id: int):
    """특정 ID의 요약 레코드를 삭제합니다."""
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM summaries WHERE id = ?", (id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="해당 ID의 데이터가 존재하지 않습니다.")
        return {"message": "Deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 처리 실패: {e}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# 4. Usage & Analytics API
# ─────────────────────────────────────────────
@app.get("/api/usage/{username}")
def get_usage(username: str):
    """사용자의 사용량 통계를 반환합니다."""
    conn = get_conn()
    try:
        cursor = conn.cursor()

        # 사용자 존재 여부 및 provider 확인
        cursor.execute("SELECT provider, total_processed_files, total_api_requests FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")

        current_provider = user_row["provider"]
        total_count = user_row["total_processed_files"]
        monthly_count = user_row["total_api_requests"]

        # 할당량 계산 (100건 기준)
        quota_limit = 100
        quota_percent = min(round((total_count / quota_limit) * 100), 100) if quota_limit > 0 else 0

        if quota_percent >= 80:
            quota_label = "Limit Approaching"
        elif quota_percent >= 50:
            quota_label = "Moderate Usage"
        else:
            quota_label = "Healthy"

        # provider별 분포 (현재 사용자의 provider 기준으로 표시)
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

        # 모의 일별 사용량 (총 월별 사용량을 임의로 분배)
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용량 조회 실패: {e}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# 실행 진입점
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
