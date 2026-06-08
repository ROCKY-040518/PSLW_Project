from fastapi import APIRouter, HTTPException
from database import get_conn

router = APIRouter()

@router.get("/usage/{username}")
def get_usage(username: str):
    # 사용자의 시스템 이용 통계를 조회하기 위해 DB 커넥션을 가져옵니다.
    conn = get_conn()
    try:
        # 커서를 생성합니다.
        cursor = conn.cursor()
        # users 테이블에서 현재 선택한 제공자, 누적 처리 파일 수, API 호출 수를 가져옵니다.
        cursor.execute("SELECT provider, total_processed_files, total_api_requests FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        
        # 유저가 DB에 없다면 404 에러를 반환합니다.
        if not user_row:
            raise HTTPException(status_code=404, detail="등록되지 않은 사용자입니다.")

        # 조회해 온 통계 데이터를 변수에 각각 할당합니다.
        current_provider = user_row["provider"]
        total_count = user_row["total_processed_files"]
        monthly_count = user_row["total_api_requests"]

        # 기본 월간 할당량(임시값)을 100회로 설정합니다.
        quota_limit = 100
        # 누적 파일 처리 수를 할당량 대비 퍼센트로 계산하되, 최대 100%를 넘지 않도록 제한합니다.
        quota_percent = min(round((total_count / quota_limit) * 100), 100) if quota_limit > 0 else 0

        # 사용량 퍼센트에 따라 사용자에게 보여줄 라벨(문구)을 결정합니다.
        if quota_percent >= 80:
            quota_label = "Limit Approaching"
        elif quota_percent >= 50:
            quota_label = "Moderate Usage"
        else:
            quota_label = "Healthy"

        # 내부적인 provider 코드(openai, gemini)를 화면 표시용 텍스트로 변환하는 딕셔너리입니다.
        provider_display = {
            "openai": "OpenAI GPT-4o-mini",
            "gemini": "Google Gemini",
        }
        # 현재 사용자가 어떤 모델을 주로 사용했는지 나타내는 비율 정보를 생성합니다.
        # 프로토타입 단계이므로 현재 사용 중인 provider가 100%인 것으로 단순화했습니다.
        model_distribution = [
            {
                "name": provider_display.get(current_provider, current_provider),
                "percent": 100 if total_count > 0 else 0,
            }
        ]

        # 지난 7일간의 일일 사용량 추이를 그리기 위한 가상의(Mock) 배열 데이터입니다.
        daily_usage = [
            int(monthly_count * 0.1), int(monthly_count * 0.2), 
            int(monthly_count * 0.15), int(monthly_count * 0.25), 
            int(monthly_count * 0.1), int(monthly_count * 0.15), 
            int(monthly_count * 0.05)
        ]

        # 계산된 모든 통계 데이터를 묶어서 프론트엔드로 반환합니다.
        return {
            "total_processed": total_count,
            "monthly_requests": monthly_count,
            "quota_percent": quota_percent,
            "quota_limit": quota_limit,
            "quota_label": quota_label,
            "model_distribution": model_distribution,
            "daily_usage": daily_usage,
        }
    finally:
        # 조회가 완료되면 DB 커넥션을 닫습니다.
        conn.close()
