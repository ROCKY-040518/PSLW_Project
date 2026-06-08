from pydantic import BaseModel

# 클라이언트가 회원가입을 요청할 때 전송하는 데이터의 구조(스키마)를 정의합니다.
class RegisterRequest(BaseModel):
    username: str
    password: str
    provider: str   # 사용자가 선택한 AI 제공자 ("openai" 또는 "gemini")
    api_key: str    # 사용자가 입력한 API 키 값

# 클라이언트가 로그인을 요청할 때 전송하는 데이터 구조를 정의합니다.
class LoginRequest(BaseModel):
    username: str
    password: str

# 사용자가 마이페이지 등에서 API 설정(제공자 및 키)을 변경할 때 사용하는 데이터 구조입니다.
class UpdateApiKeysRequest(BaseModel):
    username: str
    provider: str   # 변경할 AI 제공자 ("openai" 또는 "gemini")
    api_key: str    # 변경할 API 키 값

# 사용자가 본인의 비밀번호를 변경하고자 할 때 전송하는 데이터 구조입니다.
class UpdateProfileRequest(BaseModel):
    username: str
    current_password: str # 현재 사용 중인 기존 비밀번호
    new_password: str     # 새롭게 설정할 비밀번호
