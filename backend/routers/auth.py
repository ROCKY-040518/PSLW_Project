from fastapi import APIRouter, HTTPException
from database import get_conn
from schemas import RegisterRequest, LoginRequest, UpdateApiKeysRequest, UpdateProfileRequest
import hashlib

router = APIRouter()

def hash_password(password: str) -> str:
    # 입력받은 문자열을 UTF-8 바이트로 변환한 뒤, SHA-256 알고리즘을 사용해 해시 값을 생성하여 반환합니다.
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@router.post("/register")
def register(req: RegisterRequest):
    # 가입하려는 사용자의 provider가 openai나 gemini 중 하나인지 유효성 검사를 합니다.
    if req.provider not in ("openai", "gemini"):
        raise HTTPException(status_code=400, detail="provider는 'openai' 또는 'gemini'만 허용됩니다.")
    # 회원가입 처리를 위해 데이터베이스 커넥션을 가져옵니다.
    conn = get_conn()
    try:
        # 쿼리 실행을 위해 커서를 생성합니다.
        cursor = conn.cursor()
        # 입력받은 아이디(username)가 이미 테이블에 존재하는지 조회합니다.
        cursor.execute("SELECT username FROM users WHERE username = ?", (req.username,))
        # 만약 동일한 아이디가 존재한다면 400 에러를 발생시킵니다.
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다.")
        # 사용자가 입력한 비밀번호를 단방향 해시로 변환합니다.
        pw_hash = hash_password(req.password)
        # 아이디, 해시된 비밀번호, 제공자, API 키 정보를 users 테이블에 추가합니다.
        cursor.execute(
            "INSERT INTO users (username, password_hash, provider, api_key) VALUES (?, ?, ?, ?)",
            (req.username, pw_hash, req.provider, req.api_key),
        )
        # 추가한 내용을 데이터베이스에 최종 저장(커밋)합니다.
        conn.commit()
        # 성공 메시지를 클라이언트에게 반환합니다.
        return {"message": "User registered successfully"}
    finally:
        # 성공 여부와 관계없이 DB 연결을 안전하게 닫습니다.
        conn.close()

@router.post("/login")
def login(req: LoginRequest):
    # 로그인 검증을 위해 데이터베이스 커넥션을 가져옵니다.
    conn = get_conn()
    try:
        # 커서를 생성하여 조회를 준비합니다.
        cursor = conn.cursor()
        # 입력받은 아이디(username)를 바탕으로 사용자 정보를 가져옵니다.
        cursor.execute(
            "SELECT username, password_hash, provider, api_key FROM users WHERE username = ?",
            (req.username,),
        )
        # 조회된 행 정보를 변수에 담습니다.
        row = cursor.fetchone()
        # 사용자가 존재하지 않거나, 입력된 비밀번호의 해시값이 DB의 해시값과 다르면 401 에러를 발생시킵니다.
        if row is None or row["password_hash"] != hash_password(req.password):
            raise HTTPException(status_code=401, detail="사용자명 또는 비밀번호가 올바르지 않습니다.")
        # 로그인이 성공했다면 사용자 관련 정보들을 모아서 반환합니다.
        return {
            "message": "Login successful",
            "username": row["username"],
            "provider": row["provider"],
            "api_key": row["api_key"],
        }
    finally:
        # DB 연결을 닫아 자원을 회수합니다.
        conn.close()

@router.put("/user/api-keys")
def update_api_keys(req: UpdateApiKeysRequest):
    # 변경하려는 provider 값이 허용된 옵션인지 검사합니다.
    if req.provider not in ("openai", "gemini"):
        raise HTTPException(status_code=400, detail="provider는 'openai' 또는 'gemini'만 허용됩니다.")
    # 정보 업데이트를 위해 DB 커넥션을 가져옵니다.
    conn = get_conn()
    try:
        # DB 커서를 생성합니다.
        cursor = conn.cursor()
        # 해당 사용자가 테이블에 존재하는지 확인합니다.
        cursor.execute("SELECT username FROM users WHERE username = ?", (req.username,))
        # 사용자가 없다면 404 에러를 발생시킵니다.
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")
        # 사용자가 존재한다면 새로운 제공자 정보와 API 키로 덮어씁니다.
        cursor.execute(
            "UPDATE users SET provider = ?, api_key = ? WHERE username = ?",
            (req.provider, req.api_key, req.username),
        )
        # 변경 사항을 커밋합니다.
        conn.commit()
        # 업데이트 성공 메시지와 변경된 provider를 반환합니다.
        return {"message": "Settings updated successfully", "provider": req.provider}
    finally:
        # 연결을 닫습니다.
        conn.close()

@router.put("/user/profile")
def update_user_profile(req: UpdateProfileRequest):
    # 비밀번호 업데이트를 위해 DB 커넥션을 가져옵니다.
    conn = get_conn()
    try:
        # DB 커서를 생성합니다.
        cursor = conn.cursor()
        # 사용자의 기존 비밀번호 해시값을 가져옵니다.
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (req.username,))
        row = cursor.fetchone()
        # 사용자 데이터가 없다면 404 에러를 반환합니다.
        if not row:
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")
        # 현재 비밀번호가 일치하는지 해시값을 비교하여 검증합니다.
        if row["password_hash"] != hash_password(req.current_password):
            raise HTTPException(status_code=401, detail="현재 비밀번호가 일치하지 않습니다.")
        # 새로운 비밀번호를 해시 암호화합니다.
        new_pw_hash = hash_password(req.new_password)
        # users 테이블에 변경된 새 비밀번호 해시값을 업데이트합니다.
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (new_pw_hash, req.username)
        )
        # 업데이트를 저장(커밋)합니다.
        conn.commit()
        # 성공 메시지를 반환합니다.
        return {"message": "비밀번호가 성공적으로 변경되었습니다."}
    finally:
        # DB 연결을 닫습니다.
        conn.close()

@router.delete("/user/{username}")
def delete_user_account(username: str):
    # 계정 삭제 처리를 위해 DB 커넥션을 엽니다.
    conn = get_conn()
    try:
        # 쿼리를 실행할 커서를 만듭니다.
        cursor = conn.cursor()
        # 삭제하려는 사용자가 실제로 존재하는지 검색합니다.
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        # 사용자가 없다면 404 에러를 발생시킵니다.
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")
        # 해당 사용자가 생성했던 모든 요약 데이터(summaries)를 제거합니다.
        cursor.execute("DELETE FROM summaries WHERE username = ?", (username,))
        # 사용자의 기본 계정 데이터(users)를 제거합니다.
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        # 삭제 내역을 데이터베이스에 커밋합니다.
        conn.commit()
        # 영구 삭제가 완료되었다는 메시지를 반환합니다.
        return {"message": "계정이 영구적으로 삭제되었습니다."}
    finally:
        # 완료 후 커넥션을 닫습니다.
        conn.close()
