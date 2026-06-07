from fastapi import APIRouter, HTTPException
from database import get_conn

router = APIRouter()

@router.get("/summaries/{username}")
def get_summaries(username: str):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, filename, created_at, provider, type FROM summaries WHERE username = ? ORDER BY id DESC",
            (username,),
        )
        rows = cursor.fetchall()
        return [{
            "id": row["id"], 
            "filename": row["filename"],
            "date": row["created_at"] or "Recent",
            "provider": row["provider"] or "Unknown",
            "type": row["type"] or "Audio"
        } for row in rows]
    finally:
        conn.close()

@router.get("/summary/{id}")
def get_summary(id: int):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, transcript, summary FROM summaries WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="해당 ID의 데이터가 존재하지 않습니다.")
        return {
            "filename": row["filename"],
            "transcript": row["transcript"],
            "summaryText": row["summary"],
        }
    finally:
        conn.close()

@router.delete("/summary/{id}")
def delete_summary(id: int):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM summaries WHERE id = ?", (id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="해당 ID의 데이터가 존재하지 않습니다.")
        return {"message": "Deleted successfully"}
    finally:
        conn.close()
