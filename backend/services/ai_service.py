from fastapi import HTTPException
import time

# 요약을 생성할 때 AI에게 전달할 공통 지시문(프롬프트)을 정의합니다.
SUMMARY_PROMPT = (
    "다음 텍스트는 음성 인식(STT) 변환 결과입니다. "
    "이 텍스트의 전체적인 맥락과 성격을 먼저 분석한 뒤, 가장 적합한 양식을 스스로 선택하여 한국어로 요약해 주세요. "
    "불필요한 인사말이나 잡담은 제외하되, 원본의 정보량에 비례하여 내용이 누락되지 않도록 길이를 유연하게 조절하세요.\n\n"
    "먼저 텍스트 상단에 [콘텐츠 유형: 회의 / 강의 및 발표 / 일반 대화 및 영상 중 택 1]을 명시하고, "
    "선택한 유형에 맞춰 아래 구조로 요약해 주세요.\n\n"
    "■ 유형 A [회의]를 선택한 경우:\n"
    "1. [회의 주제 및 핵심 요약]: 회의의 전반적인 목적과 핵심 결론 (2~3문장)\n"
    "2. [주요 논의 사항]: 제안된 아이디어, 의견 대립 등 세부 논의 내역 (-)\n"
    "3. [결정 사항 및 향후 계획]: 최종 합의 내용과 향후 할 일(Action Items) (-)\n\n"
    "■ 유형 B [강의 및 발표]를 선택한 경우:\n"
    "1. [핵심 주제]: 강의/발표의 메인 타이틀과 핵심 목표 (2~3문장)\n"
    "2. [주요 개념 및 상세 내용]: 설명된 핵심 개념, 예시, 중요한 정의 등을 논리적 흐름에 따라 정리 (-)\n"
    "3. [결론 및 시사점]: 발표자가 강조한 최종 메시지나 요약 내용\n\n"
    "■ 유형 C [일반 대화 및 영상]를 선택한 경우:\n"
    "1. [전체 요약]: 영상/대화의 전반적인 스토리나 맥락 (2~3문장)\n"
    "2. [주요 흐름]: 시간의 흐름이나 사건의 전개에 따른 주요 포인트 (-)\n"
    "3. [인상 깊은 점 / 결론]: 텍스트에서 도출할 수 있는 주요 감상이나 최종 결론\n\n"
    "텍스트:\n"
)

def summarize_with_openai(api_key: str, transcript: str) -> str:
    """OpenAI GPT-4o-mini를 사용하여 텍스트를 요약합니다."""
    try:
        # OpenAI 라이브러리를 동적으로 가져옵니다.
        from openai import OpenAI  # type: ignore
        # 사용자의 API 키를 이용해 OpenAI 클라이언트를 초기화합니다.
        client = OpenAI(api_key=api_key)
        # GPT-4o-mini 모델을 사용하여 텍스트 생성을 요청합니다.
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": SUMMARY_PROMPT + transcript,
                }
            ],
            temperature=0.3,
        )
        # 생성된 응답 텍스트를 추출하고 좌우 공백을 제거하여 반환합니다.
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        # 호출 과정에서 에러가 발생하면 500 에러를 던집니다.
        raise HTTPException(
            status_code=500, detail=f"OpenAI API 호출 실패: {e}"
        )

def summarize_with_gemini(api_key: str, transcript: str, retries: int = 3) -> str:
    """Google Gemini API를 사용하여 텍스트를 요약합니다. (재시도 로직 추가)"""
    try:
        # Gemini 라이브러리를 동적으로 가져옵니다.
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
        # 사용자의 API 키를 이용해 Gemini 클라이언트를 초기화합니다.
        client = genai.Client(api_key=api_key)
        
        # 지정된 횟수(retries)만큼 재시도 루프를 돕니다.
        for attempt in range(retries):
            try:
                # Gemini 모델을 호출하여 텍스트 생성을 요청합니다.
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite", 
                    contents=SUMMARY_PROMPT + transcript,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                    ),
                )
                # 생성된 응답 텍스트를 추출하고 좌우 공백을 제거하여 반환합니다.
                return (response.text or "").strip()
            except Exception as e:
                # 에러 메시지 중 503(서버 오류) 또는 429(너무 많은 요청)가 포함되어 있는지 확인합니다.
                # 재시도 기회가 남아있을 경우에만 다시 시도합니다.
                if ("503" in str(e) or "429" in str(e)) and attempt < retries - 1:
                    # 점진적으로 대기 시간을 늘려가며 재시도를 준비합니다.
                    wait_time = attempt + 2 
                    print(f"⚠️ Gemini 서버 혼잡 감지. {wait_time}초 후 재시도합니다... ({attempt+1}/{retries})")
                    time.sleep(wait_time)
                    continue 
                else:
                    # 재시도 횟수를 모두 소진했거나 다른 치명적인 에러인 경우 예외를 발생시킵니다.
                    raise e
        return ""
    except Exception as e:
        # 호출 과정에서 에러가 발생하면 500 에러를 던집니다.
        raise HTTPException(
            status_code=500, detail=f"Gemini API 호출 실패: {e}"
        )
