from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks
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
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT provider, api_key FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"DB 조회 실패: {e}")

    if row is None:
        conn.close()
        raise HTTPException(status_code=400, detail="등록되지 않은 사용자입니다.")

    provider = row["provider"]
    api_key = row["api_key"]

    if not api_key:
        conn.close()
        raise HTTPException(status_code=400, detail="API 키가 설정되지 않았습니다.")
        
    conn.close()

    suffix = os.path.splitext(file.filename or "audio")[1] or ".tmp"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            content = await file.read()
            tmp.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임시 파일 저장 실패: {e}")

    task_id = str(uuid.uuid4())
    state.task_db[task_id] = {"status": "processing"}

    background_tasks.add_task(
        process_audio_task,
        task_id,
        username,
        file.filename,
        tmp_path,
        provider,
        api_key
    )

    return {"task_id": task_id, "message": "Processing started"}

@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    if task_id not in state.task_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return state.task_db[task_id]
