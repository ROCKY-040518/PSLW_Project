import os
from database import get_conn
from services.ai_service import summarize_with_openai, summarize_with_gemini
import core.state as state

def process_audio_task(task_id: str, username: str, filename: str, tmp_path: str, provider: str, api_key: str):
    try:
        # 전역 상태에 Whisper 모델이 적재되어 있는지 확인합니다.
        if state.whisper_model is None:
            # 적재되지 않았다면 예외를 발생시킵니다.
            raise Exception("Whisper 모델이 초기화되지 않았습니다.")

        # 동적 주입 방식으로 FFmpeg 패키지를 로드합니다.
        import imageio_ffmpeg
        _ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        # 시스템 PATH 환경 변수에 FFmpeg 실행 파일 경로를 추가합니다.
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

        # Whisper 모델을 사용하여 임시 오디오 파일에서 텍스트(STT)를 추출합니다.
        result = state.whisper_model.transcribe(tmp_path)
        # 추출된 텍스트의 앞뒤 공백을 제거합니다.
        transcript = str(result["text"]).strip()

        # 사용자가 선택한 provider에 따라 분기하여 텍스트 요약을 요청합니다.
        if provider == "openai":
            # OpenAI API를 호출하여 요약문을 생성합니다.
            summary = summarize_with_openai(api_key, transcript)
        elif provider == "gemini":
            # Gemini API를 호출하여 요약문을 생성합니다.
            summary = summarize_with_gemini(api_key, transcript)
        else:
            # 지원하지 않는 제공자인 경우 예외를 발생시킵니다.
            raise Exception(f"지원하지 않는 provider: {provider}")

        # 처리된 결과를 저장하기 위해 DB 커넥션을 가져옵니다.
        conn = get_conn()
        try:
            # DB 작업을 위한 커서를 생성합니다.
            cursor = conn.cursor()
            
            # 현재 시간을 생성일자로 지정하기 위해 포맷팅합니다.
            import datetime
            now = datetime.datetime.now().strftime("%b %d, %Y")
            
            # 원본 파일명에서 확장자를 추출하고 소문자로 변환합니다.
            ext = os.path.splitext(filename or "audio")[1].lower()
            
            # 확장자에 따라 파일 유형을 오디오, 비디오, 또는 문서로 분류합니다.
            if ext in ['.mp3', '.wav', '.m4a', '.flac']:
                file_type = "Audio"
            elif ext in ['.mp4', '.avi', '.mov']:
                file_type = "Video"
            else:
                file_type = "Document"
                
            # 분류된 정보와 추출된 텍스트, 요약 결과를 summaries 테이블에 삽입합니다.
            cursor.execute(
                "INSERT INTO summaries (username, filename, transcript, summary, created_at, provider, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, filename or "unknown", transcript, summary, now, provider, file_type),
            )
            
            # 작업을 완료한 사용자의 누적 파일 처리 수와 API 요청 수를 증가시킵니다.
            cursor.execute(
                "UPDATE users SET total_processed_files = total_processed_files + 1, total_api_requests = total_api_requests + 1 WHERE username = ?",
                (username,)
            )
            # 변경된 사항을 DB에 최종 반영(커밋)합니다.
            conn.commit()
            
            # 방금 삽입된 요약 데이터의 ID를 가져옵니다.
            new_id = cursor.lastrowid
            
            # 작업이 정상적으로 끝났으므로, 전역 상태 DB에 완료 상태와 결과를 업데이트합니다.
            state.task_db[task_id] = {
                "status": "completed",
                "result": {"id": new_id, "filename": filename, "message": "Success"}
            }
        except Exception as e:
            # DB 저장 과정에서 에러가 나면 작업 상태를 실패로 변경합니다.
            state.task_db[task_id] = {"status": "failed", "error": f"DB 저장 실패: {e}"}
        finally:
            # 작업 성공/실패 여부에 상관없이 DB 커넥션을 안전하게 닫습니다.
            conn.close()

    except Exception as e:
        # 요약 처리 과정 전반에서 에러가 발생한 경우 작업 상태를 실패로 기록합니다.
        state.task_db[task_id] = {"status": "failed", "error": str(e)}
    finally:
        # 모든 작업이 종료된 후 임시 파일 경로가 존재한다면 디스크에서 완전 삭제합니다.
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
