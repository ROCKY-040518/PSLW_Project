import os
from database import get_conn
from services.ai_service import summarize_with_openai, summarize_with_gemini
import core.state as state

async def process_audio_task(task_id: str, username: str, filename: str, tmp_path: str, provider: str, api_key: str):
    try:
        if state.whisper_model is None:
            raise Exception("Whisper 모델이 초기화되지 않았습니다.")

        import imageio_ffmpeg
        _ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

        result = state.whisper_model.transcribe(tmp_path)
        transcript = str(result["text"]).strip()

        if provider == "openai":
            summary = summarize_with_openai(api_key, transcript)
        elif provider == "gemini":
            summary = summarize_with_gemini(api_key, transcript)
        else:
            raise Exception(f"지원하지 않는 provider: {provider}")

        conn = get_conn()
        try:
            cursor = conn.cursor()
            import datetime
            now = datetime.datetime.now().strftime("%b %d, %Y")
            
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
            
            state.task_db[task_id] = {
                "status": "completed",
                "result": {"id": new_id, "filename": filename, "message": "Success"}
            }
        except Exception as e:
            state.task_db[task_id] = {"status": "failed", "error": f"DB 저장 실패: {e}"}
        finally:
            conn.close()

    except Exception as e:
        state.task_db[task_id] = {"status": "failed", "error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
