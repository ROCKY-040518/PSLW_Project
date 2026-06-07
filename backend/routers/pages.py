from fastapi import APIRouter, HTTPException
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
