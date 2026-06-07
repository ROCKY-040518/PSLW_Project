
        // 1. 다크모드 상태 동기화 (home.html과 동일하게)
        if (localStorage.getItem('theme') === 'dark' || document.documentElement.classList.contains('dark')) {
            document.documentElement.classList.add('dark');
        }

        // 2. 인증 및 파라미터 확인
        if (!localStorage.getItem('pslw_user')) { window.location.href = 'login.html'; }
        const params = new URLSearchParams(window.location.search);
        const summaryId = params.get('id');
        if (!summaryId) { window.location.href = 'home.html'; }

        // 3. 데이터 로드 및 렌더링
        async function loadSummary() {
            try {
                const res = await fetch(`${BASE_URL}/api/summary/${summaryId}`);
                if (!res.ok) throw new Error('Not found');
                const data = await res.json();

                // 헤더 업데이트
                document.getElementById('summary-id-badge').textContent = `ID: ${summaryId}`;
                document.title = `${data.filename} - PSLW`;
                document.getElementById('summary-title').textContent = data.filename;

                // STT 원본 텍스트 렌더링
                document.getElementById('transcript-container').textContent = data.transcript || '(내용 없음)';

                // AI 요약본 렌더링 (진짜 핵심!)
                const summaryRawText = data.summaryText || data.summary || '(요약 없음)';
                
                // 마크다운 파싱을 거쳐서 HTML로 삽입
                if(summaryRawText !== '(요약 없음)') {
                    document.getElementById('summary-content').innerHTML = marked.parse(summaryRawText);
                } else {
                    document.getElementById('summary-content').textContent = summaryRawText;
                }

            } catch (error) {
                console.error(error);
                alert('데이터를 불러오는 데 실패했습니다.');
                window.location.href = 'home.html';
            }
        }

        // 4. 삭제 기능
        async function deleteSummary() {
            if (!confirm('정말 이 요약 데이터를 영구 삭제하시겠습니까?')) return;
            try {
                const res = await fetch(`${BASE_URL}/api/summary/${summaryId}`, { method: 'DELETE' });
                if (res.ok) { window.location.href = 'home.html'; }
                else { alert('삭제에 실패했습니다.'); }
            } catch { alert('서버 연결 오류가 발생했습니다.'); }
        }

        document.addEventListener('DOMContentLoaded', loadSummary);