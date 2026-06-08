import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import whisper
import imageio_ffmpeg

from database import init_db
import core.state as state
from routers import auth, upload, summary, usage, pages

# 애플리케이션 시작과 종료 시 실행할 동작을 정의합니다.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # FFmpeg 실행 파일의 디렉토리를 찾습니다.
    ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    # 시스템 PATH 환경 변수에 FFmpeg 경로를 주입하여 프로세스 내에서 사용 가능하게 만듭니다.
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    
    # 애플리케이션에 필요한 데이터베이스 테이블을 초기화합니다.
    init_db()
    
    print("Loading Whisper model...")
    # 전역 상태 관리를 통해 Whisper AI 모델을 메모리에 1회 적재합니다.
    state.whisper_model = whisper.load_model("base")
    print("Whisper model loaded successfully.")
    
    # 모델 적재 등 준비가 완료되었음을 알리고 API 요청 처리를 시작합니다.
    yield

# FastAPI 인스턴스를 생성하며 앱 제목과 버전을 지정하고 lifespan 이벤트를 연결합니다.
app = FastAPI(
    title="PSLW Audio Summary API",
    version="1.0.0",
    lifespan=lifespan,
)

# 현재 파일 위치를 기준으로 기본 디렉토리 경로를 설정합니다.
base_dir = os.path.dirname(__file__)
# 프론트엔드의 JS 정적 파일들이 모여있는 경로를 정의합니다.
js_path = os.path.join(base_dir, "..", "frontend", "js")

# JS 정적 폴더가 존재하는지 확인합니다.
if os.path.exists(js_path):
    # 폴더가 존재하면 /js 경로로 정적 파일을 서비스할 수 있도록 마운트합니다.
    app.mount("/js", StaticFiles(directory=js_path), name="static_js")
else:
    # 폴더가 없으면 경고 메시지를 출력합니다.
    print("⚠️ 경고: frontend/js 폴더를 찾을 수 없습니다!")

# 다른 출처(도메인/포트)에서 API를 호출할 수 있도록 CORS 미들웨어를 추가합니다.
# 추후 보안을 위해 실제 도메인으로 변경하세요
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 관심사별로 분리된 각각의 라우터들을 애플리케이션에 등록합니다.
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(summary.router, prefix="/api", tags=["Summary"])
app.include_router(usage.router, prefix="/api", tags=["Usage"])
app.include_router(pages.router, tags=["Pages"])

# 이 파일이 직접 실행될 경우, uvicorn 서버를 구동시킵니다.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
