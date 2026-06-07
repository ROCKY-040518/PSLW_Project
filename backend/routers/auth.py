from fastapi import APIRouter, HTTPException
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
