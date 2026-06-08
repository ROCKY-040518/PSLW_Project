from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

# 브라우저에서 루트 경로('/')나 '/login.html'로 접속하면 로그인 화면을 반환합니다.
@router.get("/")
@router.get("/login.html")
def serve_login():
    # 현재 파일의 위치를 기준으로 프론트엔드 폴더 안의 login.html 경로를 절대 경로로 계산합니다.
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "..", "..", "frontend", "login.html")
    path = os.path.normpath(path)
    # 해당 파일이 디스크에 존재하지 않으면 404 에러를 반환합니다.
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="login.html을 찾을 수 없습니다.")
    # 파일이 정상적으로 존재하면 HTML 형식으로 브라우저에 전송합니다.
    return FileResponse(path, media_type="text/html")

# 사용자가 '/home'이나 '/home.html'로 접속하면 메인 대시보드 화면을 반환합니다.
@router.get("/home")
@router.get("/home.html")
def serve_home():
    # 프론트엔드의 home.html 위치를 계산합니다.
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "..", "..", "frontend", "home.html")
    path = os.path.normpath(path)
    # 파일이 존재하는지 검사합니다.
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="home.html을 찾을 수 없습니다.")
    # 파일 내용을 HTML 문서로 응답합니다.
    return FileResponse(path, media_type="text/html")

# 사용자가 요약본 상세 조회 페이지('/summary' 또는 '/summary.html')로 접속할 때 처리합니다.
@router.get("/summary")
@router.get("/summary.html")
def serve_summary():
    # 프론트엔드의 summary.html 경로를 조립합니다.
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "..", "..", "frontend", "summary.html")
    path = os.path.normpath(path)
    # 파일의 존재 여부를 확인합니다.
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="summary.html을 찾을 수 없습니다.")
    # 해당 HTML 파일을 브라우저로 렌더링합니다.
    return FileResponse(path, media_type="text/html")
