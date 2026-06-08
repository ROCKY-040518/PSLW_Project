# 전역 상태 관리

# 생성된 작업(task)들의 현재 진행 상태를 저장하는 딕셔너리입니다.
task_db = {}
# STT 변환을 수행할 Whisper 모델 객체를 메모리에 보관하기 위한 변수입니다.
whisper_model = None
