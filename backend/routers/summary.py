from fastapi import APIRouter, HTTPException
from database import get_conn

router = APIRouter()

@router.get("/summaries/{username}")
def get_summaries(username: str):
    # 지정된 사용자의 모든 요약 내역을 조회하기 위해 DB 커넥션을 가져옵니다.
    conn = get_conn()
    try:
        # DB 쿼리를 실행할 커서를 생성합니다.
        cursor = conn.cursor()
        # summaries 테이블에서 해당 사용자의 데이터를 최신순(id DESC)으로 모두 가져옵니다.
        cursor.execute(
            "SELECT id, filename, created_at, provider, type FROM summaries WHERE username = ? ORDER BY id DESC",
            (username,),
        )
        # 조회된 모든 행을 가져와 rows 변수에 저장합니다.
        rows = cursor.fetchall()
        # 프론트엔드에서 사용하기 쉬운 형태의 딕셔너리 리스트로 가공하여 반환합니다.
        return [{
            "id": row["id"], 
            "filename": row["filename"],
            "date": row["created_at"] or "Recent",
            "provider": row["provider"] or "Unknown",
            "type": row["type"] or "Audio"
        } for row in rows]
    finally:
        # 데이터 조회가 끝나면 안전하게 커넥션을 닫습니다.
        conn.close()

@router.get("/summary/{id}")
def get_summary(id: int):
    # 특정 요약 데이터 1건의 상세 내용을 조회하기 위해 DB 커넥션을 가져옵니다.
    conn = get_conn()
    try:
        # 커서를 생성합니다.
        cursor = conn.cursor()
        # 해당 고유 ID에 일치하는 파일명, 원본 텍스트(STT), 요약문을 조회합니다.
        cursor.execute("SELECT filename, transcript, summary FROM summaries WHERE id = ?", (id,))
        # 하나의 결과만 가져옵니다.
        row = cursor.fetchone()
        # 해당하는 ID의 데이터가 DB에 없다면 404 에러를 반환합니다.
        if row is None:
            raise HTTPException(status_code=404, detail="해당 ID의 데이터가 존재하지 않습니다.")
        # 조회된 데이터를 JSON 형식으로 매핑하여 반환합니다.
        return {
            "filename": row["filename"],
            "transcript": row["transcript"],
            "summaryText": row["summary"],
        }
    finally:
        # DB 커넥션을 닫습니다.
        conn.close()

@router.delete("/summary/{id}")
def delete_summary(id: int):
    # 특정 요약 데이터를 삭제하기 위해 DB 커넥션을 가져옵니다.
    conn = get_conn()
    try:
        # 커서를 생성합니다.
        cursor = conn.cursor()
        # 해당 고유 ID와 일치하는 레코드를 삭제하는 쿼리를 실행합니다.
        cursor.execute("DELETE FROM summaries WHERE id = ?", (id,))
        # 삭제 내용을 DB에 반영(커밋)합니다.
        conn.commit()
        # 삭제된 행이 하나도 없다면(존재하지 않는 ID인 경우) 404 에러를 발생시킵니다.
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="해당 ID의 데이터가 존재하지 않습니다.")
        # 정상적으로 삭제되었음을 클라이언트에 알립니다.
        return {"message": "Deleted successfully"}
    finally:
        # DB 연결을 닫습니다.
        conn.close()
