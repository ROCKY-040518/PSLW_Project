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

base_dir = os.path.dirname(__file__)
js_path = os.path.join(base_dir, "..", "frontend", "js")

if os.path.exists(js_path):
    app.mount("/js", StaticFiles(directory=js_path), name="static_js")
else:
    print("⚠️ 경고: frontend/js 폴더를 찾을 수 없습니다!")

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
