// [DEPLOYMENT SETTING]
// 로컬 개발 시: 'http://localhost:8000'
// 외부 접속 시: 'http://서버공인IP_또는_DDNS주소:8000' (예: 'http://my-project.iptime.org:8000')
const BASE_URL = ''; // Nginx 환경을 고려해 비워둠
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // 로컬 환경 대체
    // BASE_URL = 'http://localhost:8000';
}
