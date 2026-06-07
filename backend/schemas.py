from pydantic import BaseModel

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
