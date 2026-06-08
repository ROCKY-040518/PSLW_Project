from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks
import shutil
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
    # 데이터베이스 연결을 가져옵니다.
    conn = get_conn()
    try:
        # 데이터베이스 커서를 생성하여 쿼리를 실행할 준비를 합니다.
        cursor = conn.cursor()
        # 입력받은 사용자 이름으로 사용자의 API 제공자(provider)와 API 키를 조회합니다.
        cursor.execute("SELECT provider, api_key FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
    except Exception as e:
        # 예외가 발생하면 커넥션을 닫고 500 에러를 반환합니다.
        conn.close()
        raise HTTPException(status_code=500, detail=f"DB 조회 실패: {e}")

    # 조회된 사용자 정보가 없다면 400 에러를 반환합니다.
    if row is None:
        conn.close()
        raise HTTPException(status_code=400, detail="등록되지 않은 사용자입니다.")

    # 조회된 행에서 provider와 api_key를 추출합니다.
    provider = row["provider"]
    api_key = row["api_key"]

    # 사용자가 등록한 API 키가 없다면 요약 작업을 진행할 수 없으므로 에러를 반환합니다.
    if not api_key:
        conn.close()
        raise HTTPException(status_code=400, detail="API 키가 설정되지 않았습니다.")
        
    # 정보 조회가 끝났으므로 DB 커넥션을 닫습니다.
    conn.close()

    # 업로드된 파일의 확장자를 추출합니다. 파일명이 없으면 기본 확장자로 '.tmp'를 사용합니다.
    suffix = os.path.splitext(file.filename or "audio")[1] or ".tmp"
    
    try:
        # 추출한 확장자를 사용하여 삭제되지 않는 임시 파일을 생성합니다.
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            
            # 업로드된 파일의 데이터를 임시 파일로 조금씩 복사(스트리밍)하여 저장합니다.
            shutil.copyfileobj(file.file, tmp)
            
        # 임시 파일이 정상적으로 저장되었는지 확인하기 위해 파일 크기를 검사합니다.
        # 파일 크기가 0바이트라면 파일이 비어있거나 손상된 것이므로 임시 파일을 삭제하고 에러를 반환합니다.
        if os.path.getsize(tmp_path) == 0:
            os.remove(tmp_path)
            raise HTTPException(status_code=400, detail="업로드된 파일이 비어있거나 전송 중 손상되었습니다.")

    except Exception as e:
        # 파일 저장 중 오류가 발생하면 500 에러를 반환합니다.
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {e}")

    # 요약 작업을 추적하기 위해 고유한 UUID를 발급합니다.
    task_id = str(uuid.uuid4())
    
    # 전역 상태 딕셔너리에 작업 상태를 'processing'으로 기록합니다.
    state.task_db[task_id] = {"status": "processing"}

    # 오디오 처리 및 요약 작업을 백그라운드 작업으로 등록하여 메인 쓰레드 대기를 방지합니다.
    background_tasks.add_task(
        process_audio_task,
        task_id,
        username,
        file.filename or "unknown_audio",  # 👈 수정: None일 경우 대체할 문자열 보장
        tmp_path,
        provider,
        api_key
    )

    # 클라이언트에게는 작업 ID와 시작 메시지만 즉시 반환합니다.
    return {"task_id": task_id, "message": "Processing started"}

@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    # 전역 상태 딕셔너리에서 클라이언트가 요청한 작업 ID가 존재하는지 확인합니다.
    if task_id not in state.task_db:
        # 존재하지 않는 작업 ID라면 404 에러를 반환합니다.
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 작업이 존재하면 현재 상태(진행 중, 완료, 실패 등)를 반환합니다.
    return state.task_db[task_id]
