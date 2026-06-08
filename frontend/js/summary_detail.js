        // 1. 다크모드 상태 동기화
        // 사용자가 이전에 설정해 둔 테마(다크/라이트)를 로컬 스토리지에서 읽어와 페이지 색상을 변경합니다.
        if (localStorage.getItem('theme') === 'dark' || document.documentElement.classList.contains('dark')) {
            document.documentElement.classList.add('dark');
        }

        // 2. 인증 및 파라미터 확인
        // 브라우저 저장소에 사용자 세션이 없다면 권한 없음으로 판단하고 로그인 페이지로 쫓아냅니다.
        if (!localStorage.getItem('pslw_user')) { window.location.href = 'login.html'; }
        
        // 현재 브라우저 URL 주소에서 ?id=숫자 형태의 파라미터를 파싱합니다.
        const params = new URLSearchParams(window.location.search);
        const summaryId = params.get('id');
        
        // 만약 접속 주소에 ID가 없다면 보여줄 내용이 없으므로 홈으로 돌려보냅니다.
        if (!summaryId) { window.location.href = 'home.html'; }

        // 3. 데이터 로드 및 렌더링
        // 백엔드에 요약 데이터의 상세 정보를 요청하는 함수입니다.
        async function loadSummary() {
            try {
                // 추출한 ID 값으로 GET 요청을 날립니다.
                const res = await fetch(`${BASE_URL}/api/summary/${summaryId}`);
                // 서버가 404(Not found) 등을 반환하면 에러를 던집니다.
                if (!res.ok) throw new Error('Not found');
                const data = await res.json();

                // 화면 상단의 배지 텍스트를 현재 조회 중인 고유 ID로 업데이트합니다.
                document.getElementById('summary-id-badge').textContent = `ID: ${summaryId}`;
                // 브라우저 탭의 제목(title)을 해당 오디오 파일명으로 설정합니다.
                document.title = `${data.filename} - PSLW`;
                // 메인 타이틀 텍스트를 파일명으로 교체합니다.
                document.getElementById('summary-title').textContent = data.filename;

                // 서버에서 가져온 STT(음성 인식 원본 텍스트)를 화면 왼쪽 박스에 채워 넣습니다.
                document.getElementById('transcript-container').textContent = data.transcript || '(내용 없음)';

                // AI가 생성한 요약본 데이터를 변수에 담습니다.
                const summaryRawText = data.summaryText || data.summary || '(요약 없음)';
                
                // 요약 내용이 존재한다면 마크다운(Markdown) 문법을 해석하여 화면 오른쪽 박스에 예쁘게 HTML로 렌더링합니다.
                if(summaryRawText !== '(요약 없음)') {
                    document.getElementById('summary-content').innerHTML = marked.parse(summaryRawText);
                // 내용이 없다면 마크다운 파싱을 생략하고 그냥 텍스트로 표기합니다.
                } else {
                    document.getElementById('summary-content').textContent = summaryRawText;
                }

            } catch (error) {
                // 데이터를 가져오지 못한 경우 에러를 콘솔에 찍고 알림을 띄운 뒤 홈으로 보냅니다.
                console.error(error);
                alert('데이터를 불러오는 데 실패했습니다.');
                window.location.href = 'home.html';
            }
        }

        // 4. 삭제 기능
        // 현재 보고 있는 요약 내역을 지우는 함수입니다.
        async function deleteSummary() {
            // 실수로 삭제하는 것을 방지하기 위해 팝업으로 재확인합니다.
            if (!confirm('정말 이 요약 데이터를 영구 삭제하시겠습니까?')) return;
            try {
                // DELETE 메서드로 해당 ID 삭제 API를 호출합니다.
                const res = await fetch(`${BASE_URL}/api/summary/${summaryId}`, { method: 'DELETE' });
                // 삭제가 무사히 완료되면 대시보드(홈) 화면으로 되돌아갑니다.
                if (res.ok) { window.location.href = 'home.html'; }
                // 삭제에 실패했다면 실패 메시지를 띄웁니다.
                else { alert('삭제에 실패했습니다.'); }
            } catch { 
                // 통신 자체에 오류가 났을 때의 처리입니다.
                alert('서버 연결 오류가 발생했습니다.'); 
            }
        }

        // HTML 문서를 모두 읽어 들인 직후, loadSummary 함수를 실행하여 첫 화면을 그립니다.
        document.addEventListener('DOMContentLoaded', loadSummary);