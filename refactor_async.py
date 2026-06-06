import os
import re

# ------------- UPDATE main.py -------------
with open('backend/main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

# 1. Update imports and add task_db
main_code = main_code.replace(
    "from fastapi import FastAPI, File, Form, HTTPException, UploadFile",
    "import uuid\nfrom fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks"
)
if "task_db = {}" not in main_code:
    main_code = main_code.replace(
        "DB_PATH = \"audio_summaries.db\"",
        "DB_PATH = \"audio_summaries.db\"\ntask_db = {}"
    )

# 2. Replace upload_audio
upload_start = main_code.find('@app.post("/api/upload")')
next_section = main_code.find('# ─────────────────────────────────────────────\n# 3. Data Retrieval API')

new_upload_code = """async def process_audio_task(task_id: str, username: str, filename: str, tmp_path: str, provider: str, api_key: str):
    try:
        # ── Whisper STT ───────────────────────────
        if whisper_model is None:
            raise Exception("Whisper 모델이 초기화되지 않았습니다.")

        import imageio_ffmpeg
        _ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

        result = whisper_model.transcribe(tmp_path)
        transcript = str(result["text"]).strip()

        # ── AI 요약 생성 ──────────────────────────
        if provider == "openai":
            summary = summarize_with_openai(api_key, transcript)
        elif provider == "gemini":
            summary = summarize_with_gemini(api_key, transcript)
        else:
            raise Exception(f"지원하지 않는 provider: {provider}")

        # ── DB 저장 ───────────────────────────────
        conn = get_conn()
        try:
            cursor = conn.cursor()
            import datetime
            now = datetime.datetime.now().strftime("%b %d, %Y")
            
            import os
            ext = os.path.splitext(filename or "audio")[1].lower()
            if ext in ['.mp3', '.wav', '.m4a', '.flac']:
                file_type = "Audio"
            elif ext in ['.mp4', '.avi', '.mov']:
                file_type = "Video"
            else:
                file_type = "Document"
                
            cursor.execute(
                "INSERT INTO summaries (username, filename, transcript, summary, created_at, provider, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, filename or "unknown", transcript, summary, now, provider, file_type),
            )
            cursor.execute(
                "UPDATE users SET total_processed_files = total_processed_files + 1, total_api_requests = total_api_requests + 1 WHERE username = ?",
                (username,)
            )
            conn.commit()
            new_id = cursor.lastrowid
            
            task_db[task_id] = {
                "status": "completed",
                "result": {"id": new_id, "filename": filename, "message": "Success"}
            }
        except Exception as e:
            task_db[task_id] = {"status": "failed", "error": f"DB 저장 실패: {e}"}
        finally:
            conn.close()

    except Exception as e:
        task_db[task_id] = {"status": "failed", "error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@app.post("/api/upload")
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    username: str = Form(...),
):
    \"\"\"오디오 파일을 업로드받아 백그라운드에서 처리합니다.\"\"\"
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

    import os
    suffix = os.path.splitext(file.filename or "audio")[1] or ".tmp"
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            content = await file.read()
            tmp.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임시 파일 저장 실패: {e}")

    task_id = str(uuid.uuid4())
    task_db[task_id] = {"status": "processing"}

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


@app.get("/api/status/{task_id}")
def get_task_status(task_id: str):
    if task_id not in task_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_db[task_id]

"""
main_code = main_code[:upload_start] + new_upload_code + "\n\n" + main_code[next_section:]

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)


# ------------- UPDATE home.html -------------
with open('frontend/home.html', 'r', encoding='utf-8') as f:
    home_code = f.read()

upload_start = home_code.find('    // --- File Upload ---')
upload_end = home_code.find('    // --- API Settings ---')

new_frontend_code = """    // --- File Upload ---
    async function uploadFile(file) {
        const defaultState = document.getElementById('upload-default-state');
        const loadingState = document.getElementById('upload-loading-state');
        const dropZone = document.getElementById('drop-zone');
        if(!defaultState || !loadingState) return;

        defaultState.classList.add('hidden');
        loadingState.classList.remove('hidden');
        loadingState.classList.add('flex');
        dropZone.classList.add('upload-loading');
        
        const loadingText = loadingState.querySelector('h3');
        if(loadingText) loadingText.textContent = "요약 중입니다. 잠시만 기다려주세요...";

        function resetUploadUI() {
            loadingState.classList.add('hidden');
            loadingState.classList.remove('flex');
            defaultState.classList.remove('hidden');
            dropZone.classList.remove('upload-loading');
            document.getElementById('file-input').value = '';
        }

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('username', user.username);
            const res = await fetch(`${BASE_URL}/api/upload`, { method: 'POST', body: formData });
            
            if (!res.ok) { 
                const data = await res.json(); 
                alert(`업로드 실패: ${data.detail}`); 
                resetUploadUI();
                return;
            }
            
            const data = await res.json();
            const taskId = data.task_id;
            
            // Polling
            const pollInterval = setInterval(async () => {
                try {
                    const statusRes = await fetch(`${BASE_URL}/api/status/${taskId}`);
                    if(!statusRes.ok) throw new Error("Status check failed");
                    const statusData = await statusRes.json();
                    
                    if (statusData.status === "completed") {
                        clearInterval(pollInterval);
                        await loadSummaries();
                        switchView('view-history');
                        resetUploadUI();
                    } else if (statusData.status === "failed") {
                        clearInterval(pollInterval);
                        alert(`요약 실패: ${statusData.error}`);
                        resetUploadUI();
                    }
                } catch(e) {
                    clearInterval(pollInterval);
                    alert("상태 확인 중 오류가 발생했습니다.");
                    resetUploadUI();
                }
            }, 5000);

        } catch (err) { 
            alert('업로드 중 오류가 발생했습니다.'); 
            resetUploadUI();
        }
    }

"""

home_code = home_code[:upload_start] + new_frontend_code + home_code[upload_end:]

with open('frontend/home.html', 'w', encoding='utf-8') as f:
    f.write(home_code)

print("Files updated successfully.")
