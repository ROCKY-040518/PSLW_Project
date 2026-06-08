// 프론트엔드 애플리케이션에서 백엔드 API를 호출할 때 사용할 기본 주소(Base URL)를 설정합니다.
// 향후 Nginx 배포 등에서 상대 경로 매핑을 사용할 것을 대비하여 기본값을 빈 문자열로 둡니다.
const BASE_URL = ''; 

// 현재 브라우저가 로컬 개발 환경(localhost 또는 127.0.0.1)에서 실행 중인지 확인합니다.
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // 로컬 환경일 경우 백엔드 서버(포트 8000)를 명시적으로 지정할 수 있는 공간입니다. 
    // 필요 시 주석을 해제하여 사용합니다.
    // BASE_URL = 'http://localhost:8000';
}
