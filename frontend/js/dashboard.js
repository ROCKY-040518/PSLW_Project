
    // 브라우저의 로컬 스토리지에서 사용자 정보를 가져옵니다.
    const userRaw = localStorage.getItem('pslw_user');
    // 사용자 정보가 없다면 로그인 페이지로 강제 이동시킵니다.
    if (!userRaw) { window.location.href = 'login.html'; }
    // 가져온 문자열 형태의 사용자 정보를 자바스크립트 객체로 변환합니다.
    const user = JSON.parse(userRaw || '{}');

    // XSS(크로스 사이트 스크립팅) 공격을 방지하기 위해 문자열을 안전한 HTML 텍스트로 변환하는 함수입니다.
    function escHtml(str) {
        const d = document.createElement('div');
        d.appendChild(document.createTextNode(str || ''));
        return d.innerHTML;
    }

    // 클릭한 메뉴에 따라 화면(View)을 전환하는 함수입니다.
    function switchView(viewId) {
        // 관리할 모든 화면 섹션의 ID 목록을 정의합니다.
        const sections = ['view-dashboard', 'view-api-settings', 'view-history', 'view-usage', 'view-settings'];
        // 각 섹션을 순회하면서
        sections.forEach((id) => {
            const section = document.getElementById(id);
            if (!section) return;
            // 전달받은 viewId와 일치하는 섹션만 보이게 하고('block'), 나머지는 숨깁니다('hidden').
            section.className = id === viewId ? 'block' : 'hidden';
        });

        // 사이드바의 네비게이션 링크들을 모두 찾습니다.
        const navLinks = document.querySelectorAll('nav a[onclick^="switchView"]');
        navLinks.forEach(link => {
            // 현재 클릭된 링크(viewId 포함)인 경우 활성화 스타일(파란색 배경, 강조 아이콘 등)을 적용합니다.
            if (link.getAttribute('onclick').includes(viewId)) {
                link.className = "flex items-center gap-3 px-4 py-3 text-primary bg-surface-container-highest border-l-4 border-primary font-label-md text-label-md cursor-pointer active:scale-[0.98] transition-transform";
                const icon = link.querySelector('.material-symbols-outlined');
                if(icon) icon.style.fontVariationSettings = "'FILL' 1";
            // 그렇지 않은 나머지 링크들은 기본 스타일로 되돌립니다.
            } else {
                link.className = "flex items-center gap-3 px-4 py-3 text-on-surface-variant dark:text-[#a0a0a0] font-label-md text-label-md hover:bg-surface-container-high transition-colors duration-200 cursor-pointer active:scale-[0.98] rounded-lg";
                const icon = link.querySelector('.material-symbols-outlined');
                if(icon) icon.style.fontVariationSettings = "'FILL' 0";
            }
        });

        // 전환된 화면에 필요한 데이터를 서버에서 즉시 불러옵니다.
        if (viewId === 'view-history' || viewId === 'view-dashboard') loadSummaries();
        if (viewId === 'view-usage') loadUsage();
        if (viewId === 'view-api-settings') prefillApiSettings();
    }

    // --- Dashboard & History ---
    // 전체 요약 내역을 담을 배열과 현재 페이지 상태를 선언합니다.
    let allHistoryItems = [];
    let currentHistoryPage = 1;
    const ITEMS_PER_PAGE = 5;

    // 현재 사용자의 요약 내역을 백엔드에서 불러오는 함수입니다.
    async function loadSummaries() {
        try {
            // 사용자 이름을 포함하여 API 요청을 보냅니다.
            const res = await fetch(`${BASE_URL}/api/summaries/${user.username}`);
            // 응답이 정상(200번대)이 아니면 에러를 발생시킵니다.
            if (!res.ok) throw new Error();
            // 서버에서 받은 JSON 데이터를 전체 내역 배열에 저장합니다.
            allHistoryItems = await res.json();
            // 대시보드의 카드 형태 UI를 업데이트합니다.
            renderCards(allHistoryItems);
            // 히스토리 탭의 테이블 형태 UI를 업데이트합니다.
            renderHistoryTable();
        } catch { 
            // 데이터를 불러오는데 실패하면 콘솔에 에러를 기록합니다.
            console.error('Failed to load summaries'); 
        }
    }

    // 대시보드 화면에 요약 내역을 카드 형태로 그리는 함수입니다.
    function renderCards(items) {
        const grid = document.getElementById('summaries-grid');
        if (!grid) return;
        // 기존에 그려진 내용을 모두 지웁니다.
        grid.innerHTML = '';
        // 요약 내역이 하나도 없는 경우 빈 화면 메시지를 표시하고 함수를 종료합니다.
        if (items.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center text-on-surface-variant dark:text-[#a0a0a0] py-xl">
                    <span class="material-symbols-outlined text-[48px] mb-md block text-outline">inbox</span>
                    <p class="font-body-md text-body-md">No summaries yet. Upload an audio file to get started.</p>
                </div>`;
            return;
        }
        // 최신 내역 최대 6개까지만 순회하면서 카드를 생성합니다.
        items.slice(0, 6).forEach(item => {
            const card = document.createElement('div');
            // 카드의 기본 스타일(배경, 테두리, 그림자 등)을 지정합니다.
            card.className = 'bg-surface-container-lowest dark:bg-[#1e1e1e] border border-outline-variant dark:border-[#333333] rounded-xl p-lg flex flex-col justify-between hover:shadow-[0px_10px_15px_-3px_rgba(15,23,42,0.05)] transition-shadow duration-300';
            // 카드 내부에 들어갈 HTML 내용을 조립합니다.
            card.innerHTML = `
                <div>
                    <div class="flex justify-between items-start mb-md">
                        <div class="flex items-center gap-sm overflow-hidden">
                            <div class="w-10 h-10 shrink-0 rounded-lg bg-surface-container-high flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">mic</span>
                            </div>
                            <div class="overflow-hidden">
                                <p class="font-label-md text-label-md text-on-surface dark:text-[#f8f9fa] truncate" title="${escHtml(item.filename)}">${escHtml(item.filename)}</p>
                                <p class="font-body-sm text-body-sm text-on-surface-variant dark:text-[#a0a0a0]">#${item.id}</p>
                            </div>
                        </div>
                        <span class="ml-sm shrink-0 px-3 py-1 rounded-full bg-surface-container dark:bg-[#2a2a2a] border border-outline-variant dark:border-[#444444] font-label-md text-label-md text-on-surface dark:text-[#f8f9fa] text-[12px]">Completed</span>
                    </div>
                </div>
                <div class="flex items-center gap-sm pt-md border-t border-surface-container-high mt-4">
                    <button onclick="viewSummary(${item.id})" class="flex-1 bg-primary hover:bg-primary-container text-on-primary font-label-md text-label-md py-2 px-4 rounded-lg flex justify-center items-center gap-xs transition-colors">
                        <span class="material-symbols-outlined text-[18px]">visibility</span> View Details
                    </button>
                    <button onclick="deleteSummary(${item.id})" class="w-10 h-10 flex items-center justify-center text-outline hover:text-error hover:bg-error-container rounded-lg transition-colors">
                        <span class="material-symbols-outlined text-[20px]">delete</span>
                    </button>
                </div>`;
            // 완성된 카드를 그리드 컨테이너에 추가합니다.
            grid.appendChild(card);
        });
    }

    // 히스토리 화면에 요약 내역을 표(Table)와 페이지네이션 형태로 그리는 함수입니다.
    function renderHistoryTable() {
        const tbody = document.getElementById('history-tbody');
        if (!tbody) return;
        
        // 검색창에 입력된 텍스트를 소문자로 변환하여 가져옵니다.
        const searchVal = document.getElementById('history-search')?.value.toLowerCase() || '';
        
        // 전체 내역 중 검색어(파일명 또는 ID)와 일치하는 항목만 필터링합니다.
        let filtered = allHistoryItems.filter(item => {
            if (searchVal && !item.filename.toLowerCase().includes(searchVal) && !item.id.toString().includes(searchVal)) return false;
            return true;
        });
        
        // 필터링된 결과의 총 개수를 구합니다.
        const totalItems = filtered.length;
        // 총 개수를 한 페이지당 항목 수(5개)로 나누어 전체 페이지 수를 계산합니다.
        const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE) || 1;
        // 현재 페이지가 전체 페이지 수를 초과하면 보정합니다.
        if (currentHistoryPage > totalPages) currentHistoryPage = totalPages;
        // 현재 페이지가 1보다 작으면 1로 고정합니다.
        if (currentHistoryPage < 1) currentHistoryPage = 1;
        
        // 현재 페이지에 해당하는 데이터의 시작 인덱스를 계산합니다.
        const startIdx = (currentHistoryPage - 1) * ITEMS_PER_PAGE;
        // 필터링된 배열에서 현재 페이지 분량만큼 잘라냅니다.
        const paginated = filtered.slice(startIdx, startIdx + ITEMS_PER_PAGE);
        
        // 표 안의 내용을 초기화합니다.
        tbody.innerHTML = '';
        if (paginated.length === 0) {
            // 보여줄 항목이 없으면 안내 메시지를 출력합니다.
            tbody.innerHTML = `<tr><td colspan="6" class="py-12 text-center text-on-surface-variant dark:text-[#cccccc]">No history available.</td></tr>`;
        } else {
            // 현재 페이지의 항목들을 하나씩 순회하며 행(tr)을 생성합니다.
            paginated.forEach(item => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-surface-bright dark:hover:bg-[#252525] border-b border-surface-container dark:border-gray-800 transition-colors group';
                tr.innerHTML = `
                    <td class="py-4 px-4 font-mono-sm text-mono-sm text-outline dark:text-[#cccccc]">#${item.id}</td>
                    <td class="py-4 px-4 dark:text-[#cccccc]">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded bg-primary-container/20 flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-size: 18px;">description</span>
                            </div>
                            <div>
                                <p class="font-body-md text-body-md font-medium text-on-surface dark:text-[#f8f9fa] group-hover:text-primary transition-colors">${escHtml(item.filename)}</p>
                            </div>
                        </div>
                    </td>
                    <td class="py-4 px-4 font-body-sm text-body-sm text-on-surface-variant dark:text-[#a0a0a0]">${item.date || 'Recent'}</td>
                    <td class="py-4 px-4 dark:text-[#cccccc]">
                        <span class="inline-flex items-center px-2 py-1 rounded-md bg-surface-container dark:bg-gray-800 text-on-surface dark:text-[#f8f9fa] font-label-md text-[12px]">${item.provider || '-'}</span>
                    </td>
                    <td class="py-4 px-4 dark:text-[#cccccc]">
                        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-secondary-container/30 text-secondary border border-secondary/20 font-label-md text-[12px]">
                            <span class="material-symbols-outlined" style="font-size: 14px;">subject</span>
                            ${item.type || 'Summary'}
                        </span>
                    </td>
                    <td class="py-4 px-4 text-right dark:text-[#cccccc]">
                        <div class="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onclick="viewSummary(${item.id})" class="p-1.5 text-on-surface-variant dark:text-[#a0a0a0] hover:text-primary hover:bg-surface-container rounded transition-colors" title="View Details">
                                <span class="material-symbols-outlined" style="font-size: 20px;">visibility</span>
                            </button>
                            <button onclick="deleteSummary(${item.id})" class="p-1.5 text-on-surface-variant dark:text-[#a0a0a0] hover:text-error hover:bg-error-container/20 rounded transition-colors" title="Delete">
                                <span class="material-symbols-outlined" style="font-size: 20px;">delete</span>
                            </button>
                        </div>
                    </td>
                `;
                // 생성된 행을 표에 추가합니다.
                tbody.appendChild(tr);
            });
        }
        
        // 페이지네이션(번호 버튼) 영역을 그립니다.
        const paginationDiv = document.getElementById('history-pagination');
        if (paginationDiv) {
            let buttonsHtml = '';
            // 전체 페이지 수만큼 반복하면서 번호 버튼을 만듭니다.
            for (let i = 1; i <= totalPages; i++) {
                if (i === currentHistoryPage) {
                    // 현재 선택된 페이지는 활성화 스타일을 줍니다.
                    buttonsHtml += `<button class="w-8 h-8 flex items-center justify-center rounded bg-primary text-on-primary font-label-md text-label-md">${i}</button>`;
                } else {
                    // 선택되지 않은 페이지는 클릭 가능하게 만들고 클릭 시 changePage 함수를 호출합니다.
                    buttonsHtml += `<button onclick="changePage(${i})" class="w-8 h-8 flex items-center justify-center rounded text-on-surface-variant dark:text-[#a0a0a0] hover:bg-surface-container font-label-md text-label-md transition-colors">${i}</button>`;
                }
            }
            
            // 페이지 요약 문구와 이전/다음 화살표 버튼을 포함하여 페이지네이션 HTML을 최종 완성합니다.
            paginationDiv.innerHTML = `
                <p class="font-body-sm text-body-sm text-on-surface-variant dark:text-[#a0a0a0]">Showing <span class="font-medium text-on-surface dark:text-[#f8f9fa]">${totalItems === 0 ? 0 : startIdx + 1}</span> to <span class="font-medium text-on-surface dark:text-[#f8f9fa]">${Math.min(startIdx + ITEMS_PER_PAGE, totalItems)}</span> of <span class="font-medium text-on-surface dark:text-[#f8f9fa]">${totalItems}</span> results</p>
                <div class="flex items-center gap-1">
                    <button onclick="changePage(${currentHistoryPage - 1})" class="p-2 text-outline hover:text-on-surface dark:text-[#f8f9fa] hover:bg-surface-container rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" ${currentHistoryPage <= 1 ? 'disabled' : ''}>
                        <span class="material-symbols-outlined" style="font-size: 20px;">chevron_left</span>
                    </button>
                    ${buttonsHtml}
                    <button onclick="changePage(${currentHistoryPage + 1})" class="p-2 text-on-surface-variant dark:text-[#a0a0a0] hover:text-on-surface dark:text-[#f8f9fa] hover:bg-surface-container rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed" ${currentHistoryPage >= totalPages ? 'disabled' : ''}>
                        <span class="material-symbols-outlined" style="font-size: 20px;">chevron_right</span>
                    </button>
                </div>
            `;
        }
    }

    // 페이지 번호를 누를 때 호출되는 함수로, 현재 페이지 변수를 갱신하고 테이블을 다시 그립니다.
    function changePage(p) {
        currentHistoryPage = p;
        renderHistoryTable();
    }

    // 특정 항목의 보기(View) 버튼을 누르면 상세 페이지로 이동합니다.
    function viewSummary(id) { window.location.href = `summary.html?id=${id}`; }

    // 요약 데이터를 삭제하는 함수입니다.
    async function deleteSummary(id) {
        // 사용자에게 먼저 삭제 의사를 묻습니다.
        if (!confirm('이 요약을 삭제하시겠습니까?')) return;
        try {
            // 백엔드의 삭제 API를 호출합니다.
            const res = await fetch(`${BASE_URL}/api/summary/${id}`, { method: 'DELETE' });
            if (res.ok) { 
                // 삭제가 성공하면 요약 목록을 다시 서버에서 불러와 화면을 갱신합니다.
                await loadSummaries(); 
                // 삭제 완료 후 현재 페이지(히스토리 또는 대시보드) 화면 새로고침
            } else { 
                // 에러가 나면 알림을 띄웁니다.
                alert('삭제 실패'); 
            }
        } catch { 
            alert('서버 연결 오류'); 
        }
    }

    // --- File Upload ---
    // 오디오 파일을 서버로 업로드하는 메인 로직입니다.
    async function uploadFile(file) {
        const defaultState = document.getElementById('upload-default-state');
        const loadingState = document.getElementById('upload-loading-state');
        const dropZone = document.getElementById('drop-zone');
        if(!defaultState || !loadingState) return;

        // 업로드 시작 시, 기존의 점선 박스 화면을 숨기고 빙글빙글 도는 로딩 화면을 표시합니다.
        defaultState.classList.add('hidden');
        loadingState.classList.remove('hidden');
        loadingState.classList.add('flex');
        dropZone.classList.add('upload-loading');
        
        // 안내 문구를 업로드 중으로 변경합니다.
        const loadingText = loadingState.querySelector('h3');
        if(loadingText) loadingText.textContent = "요약 중입니다. 잠시만 기다려주세요...";

        // 업로드가 완료되거나 실패했을 때 화면을 다시 원래 점선 박스로 되돌리는 내부 함수입니다.
        function resetUploadUI() {
            loadingState.classList.add('hidden');
            loadingState.classList.remove('flex');
            defaultState.classList.remove('hidden');
            dropZone.classList.remove('upload-loading');
            document.getElementById('file-input').value = '';
        }

        try {
            // 파일을 서버로 전송하기 위해 폼 데이터를 구성합니다.
            const formData = new FormData();
            formData.append('file', file);
            formData.append('username', user.username);
            
            // POST 요청으로 파일을 백엔드에 보냅니다.
            const res = await fetch(`${BASE_URL}/api/upload`, { method: 'POST', body: formData });
            
            // 응답이 정상이 아니라면 에러 메시지를 띄우고 UI를 원상복구합니다.
            if (!res.ok) { 
                const data = await res.json(); 
                alert(`업로드 실패: ${data.detail}`); 
                resetUploadUI();
                return;
            }
            
            // 응답에서 작업 진행을 확인하기 위한 task_id를 받아옵니다.
            const data = await res.json();
            const taskId = data.task_id;
            
            // 5초에 한 번씩 서버에 작업 상태(폴링)를 물어봅니다.
            const pollInterval = setInterval(async () => {
                try {
                    // 발급받은 task_id로 현재 백그라운드 작업 상태를 조회합니다.
                    const statusRes = await fetch(`${BASE_URL}/api/status/${taskId}`);
                    if(!statusRes.ok) throw new Error("Status check failed");
                    const statusData = await statusRes.json();
                    
                    // 작업이 무사히 완료된 경우
                    if (statusData.status === "completed") {
                        // 5초 간격의 반복 조회를 중지합니다.
                        clearInterval(pollInterval);
                        // 새롭게 생성된 요약 데이터가 포함되도록 대시보드 리스트를 다시 불러옵니다.
                        await loadSummaries();
                        // UI를 원래의 점선 박스 형태로 되돌립니다.
                        resetUploadUI();
                    // 작업 중 오류가 발생한 경우
                    } else if (statusData.status === "failed") {
                        // 반복 조회를 중지하고 서버의 에러 메시지를 알림으로 띄웁니다.
                        clearInterval(pollInterval);
                        alert(`요약 실패: ${statusData.error}`);
                        resetUploadUI();
                    }
                } catch(e) {
                    // 폴링 도중 네트워크 오류 등이 나면 중지하고 알림을 띄웁니다.
                    clearInterval(pollInterval);
                    alert("상태 확인 중 오류가 발생했습니다.");
                    resetUploadUI();
                }
            }, 5000); // 5000ms = 5초 주기

        } catch (err) { 
            // 파일 업로드 요청 자체가 실패했을 때의 예외 처리입니다.
            alert('업로드 중 오류가 발생했습니다.'); 
            resetUploadUI();
        }
    }

    // --- API Settings ---
    // API 설정 화면 접속 시 로컬에 저장된 제공자 정보를 셀렉트 박스에 미리 채워놓습니다.
    function prefillApiSettings() {
        const providerSelect = document.getElementById('api-provider');
        if (providerSelect && user.provider) {
            providerSelect.value = user.provider;
        }
    }

    // 사용자가 입력한 API 키와 제공자 정보를 서버에 저장합니다.
    async function saveApiSettings() {
        const provider = document.getElementById('api-provider').value;
        const apiKey = document.getElementById('apiKey').value;
        const statusBadge = document.getElementById('api-status-badge');
        
        // 키가 빈 값이라면 입력하라는 경고를 띄웁니다.
        if (!apiKey.trim()) { alert('API Key를 입력해주세요.'); return; }
        
        try {
            // 변경된 설정을 백엔드로 전송(PUT)합니다.
            const res = await fetch(`${BASE_URL}/api/user/api-keys`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user.username, provider: provider, api_key: apiKey })
            });
            const data = await res.json();
            // 서버 응답이 실패라면 에러를 던집니다.
            if (!res.ok) throw new Error(data.detail);
            
            // 서버 저장이 성공하면 로컬 스토리지 정보도 갱신합니다.
            user.provider = provider;
            user.api_key = apiKey;
            localStorage.setItem('pslw_user', JSON.stringify(user));
            
            // 화면 상단의 연결 상태 뱃지를 녹색 성공 상태로 바꿔줍니다.
            if(statusBadge) {
                statusBadge.innerHTML = `<span class="material-symbols-outlined" style="font-size: 16px;">check_circle</span> Status: Connected (${provider})`;
                statusBadge.className = 'flex items-center gap-2 text-primary font-label-md text-label-md bg-primary-container/20 px-3 py-1.5 rounded-full border border-primary/20';
            }
            alert('API 키가 성공적으로 저장되었습니다.');
        } catch (e) {
            alert(`API 키 저장 실패: ${e.message}`);
        }
    }

    // 연결 테스트 버튼을 누르면 API 키 저장 함수를 재활용하여 확인합니다.
    async function testApiConnection() {
        await saveApiSettings(); // 저장 테스트로 갈음
    }

    // --- Usage ---
    // 사용자의 요약 사용량 통계 데이터를 서버에서 불러와 화면에 그립니다.
    async function loadUsage() {
        try {
            // 사용자 이름으로 사용량 통계 조회 API를 호출합니다.
            const res = await fetch(`${BASE_URL}/api/usage/${user.username}`);
            if (!res.ok) throw new Error();
            const data = await res.json();
            
            // 전체 누적 파일 처리 횟수를 표시합니다.
            const countEl = document.getElementById('usage-total-count');
            if (countEl) countEl.textContent = data.total_processed;
            
            // 이번 달 API 요청 횟수를 표시합니다.
            const monthlyEl = document.getElementById('usage-monthly-count');
            if (monthlyEl) monthlyEl.textContent = data.monthly_requests;
            
            // 이번 달 쿼터(할당량) 대비 사용률(%)을 표시합니다.
            const percentEl = document.getElementById('usage-quota-percent');
            if (percentEl) percentEl.textContent = data.quota_percent + '%';
            
            // 상태 텍스트(예: "Good", "Warning")를 표시합니다.
            const labelEl = document.getElementById('usage-quota-label');
            if (labelEl) labelEl.textContent = data.quota_label;
            
            // 시각적인 프로그레스 바의 너비를 퍼센트만큼 채웁니다.
            const barEl = document.getElementById('usage-quota-bar');
            if (barEl) barEl.style.width = data.quota_percent + '%';

            // 사용량에 따라 프로그레스 바와 카드의 색상을 동적으로 바꿉니다.
            const quotaCard = document.getElementById('usage-quota-card');
            const quotaText = document.getElementById('usage-quota-text');
            const quotaIcon = document.getElementById('usage-quota-icon');
            const quotaBg = document.getElementById('usage-quota-bg');
            if (quotaCard && quotaText && quotaIcon && quotaBg && percentEl && labelEl && barEl) {
                // 사용률이 80% 이상일 때: 에러(빨간색/주황색) 테마로 경고합니다.
                if (data.quota_percent >= 80) {
                    quotaCard.className = 'col-span-4 bg-error-container/20 border border-error rounded-xl p-6 shadow-sm flex flex-col justify-between h-32 relative overflow-hidden';
                    quotaText.className = 'font-label-md text-label-md text-error font-semibold';
                    quotaIcon.className = 'material-symbols-outlined text-error';
                    percentEl.className = 'font-display-lg text-display-lg text-error';
                    labelEl.className = 'font-label-md text-label-md text-error';
                    quotaBg.className = 'w-full bg-error-container rounded-full h-1.5';
                    barEl.className = 'bg-error h-1.5 rounded-full';
                    quotaIcon.textContent = 'warning';
                // 사용률이 안정적일 때: 파란색 테마로 정상임을 표시합니다.
                } else {
                    quotaCard.className = 'col-span-4 bg-primary-container/20 border border-primary rounded-xl p-6 shadow-sm flex flex-col justify-between h-32 relative overflow-hidden';
                    quotaText.className = 'font-label-md text-label-md text-primary font-semibold';
                    quotaIcon.className = 'material-symbols-outlined text-primary';
                    percentEl.className = 'font-display-lg text-display-lg text-primary';
                    labelEl.className = 'font-label-md text-label-md text-primary';
                    quotaBg.className = 'w-full bg-primary-container rounded-full h-1.5';
                    barEl.className = 'bg-primary h-1.5 rounded-full';
                    quotaIcon.textContent = 'check_circle';
                }
            }

            // 일일 사용량 막대그래프를 그립니다.
            const chartContainer = document.getElementById('usage-chart-container');
            if (chartContainer && data.daily_usage) {
                // 데이터 중 가장 높은 값을 구하여 막대 높이의 기준으로 삼습니다.
                const maxVal = Math.max(...data.daily_usage, 1);
                // 그래프 좌측에 Y축 라벨(숫자)을 추가합니다.
                chartContainer.innerHTML = `
                    <div class="absolute left-0 top-0 h-full flex flex-col justify-between text-outline font-mono-sm text-mono-sm pb-2 opacity-50 -ml-8">
                        <span>${maxVal}</span>
                        <span>${Math.round(maxVal/2)}</span>
                        <span>0</span>
                    </div>
                `;
                // 각 요일별 데이터를 순회하며 막대를 추가합니다.
                data.daily_usage.forEach(val => {
                    // 가장 큰 값 대비 현재 값의 비율을 %로 계산하여 막대 높이를 결정합니다.
                    const heightPercent = (val / maxVal) * 100;
                    chartContainer.innerHTML += `
                        <div class="w-full bg-primary-container hover:bg-primary transition-colors rounded-t-sm relative group" style="height: ${heightPercent}%">
                            <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-inverse-surface text-inverse-on-surface font-mono-sm text-mono-sm px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity z-20">${val}</div>
                        </div>
                    `;
                });
            }

            // 어떤 AI 모델을 얼마나 사용했는지 비율을 그립니다.
            const modelDist = document.getElementById('usage-model-distribution');
            if (modelDist && data.model_distribution) {
                modelDist.innerHTML = '';
                // 모델별로 부여할 색상 클래스 배열입니다.
                const colors = ['bg-primary', 'bg-secondary', 'bg-error'];
                // 전달받은 모델 사용 분포 배열을 순회합니다.
                data.model_distribution.forEach((model, i) => {
                    const color = colors[i % colors.length];
                    // 각각의 모델 이름, 퍼센트 텍스트, 그리고 색상이 입혀진 바를 추가합니다.
                    modelDist.innerHTML += `
                        <div>
                            <div class="flex justify-between items-center mb-2">
                                <span class="font-label-md text-label-md text-on-surface dark:text-[#f8f9fa] flex items-center gap-2">
                                    <div class="w-2 h-2 rounded-full ${color}"></div> ${escHtml(model.name)}
                                </span>
                                <span class="font-mono-sm text-mono-sm text-on-surface-variant dark:text-[#a0a0a0]">${model.percent}%</span>
                            </div>
                            <div class="w-full bg-surface-container-high rounded-full h-2">
                                <div class="${color} h-2 rounded-full" style="width: ${model.percent}%"></div>
                            </div>
                        </div>
                    `;
                });
            }
        } catch (e) {
            // 서버 통신이 실패할 경우, 화면이 깨지지 않도록 기본값(0)으로 채워 넣습니다.
            const countEl = document.getElementById('usage-total-count');
            if (countEl) countEl.textContent = '0';
            
            const monthlyEl = document.getElementById('usage-monthly-count');
            if (monthlyEl) monthlyEl.textContent = '0';
            
            const percentEl = document.getElementById('usage-quota-percent');
            if (percentEl) percentEl.textContent = '0%';
            
            const labelEl = document.getElementById('usage-quota-label');
            if (labelEl) labelEl.textContent = 'Data unavailable';
            
            const barEl = document.getElementById('usage-quota-bar');
            if (barEl) barEl.style.width = '0%';
        }
    }

    // --- Profile & Settings ---
    // 계정의 비밀번호를 변경하는 함수입니다.
    async function saveProfile() {
        const currentPw = document.getElementById('current_password').value;
        const newPw = document.getElementById('new_password').value;
        const confirmPw = document.getElementById('confirm_password').value;
        
        // 세 필드 중 하나라도 비어있으면 경고를 띄우고 중단합니다.
        if (!currentPw || !newPw || !confirmPw) { alert('모든 비밀번호 필드를 입력해주세요.'); return; }
        // 새 비밀번호와 확인용 비밀번호가 다르면 돌려보냅니다.
        if (newPw !== confirmPw) { alert('새 비밀번호와 확인 비밀번호가 일치하지 않습니다.'); return; }
        
        try {
            // 변경 API를 호출합니다.
            const res = await fetch(`${BASE_URL}/api/user/profile`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user.username, current_password: currentPw, new_password: newPw })
            });
            const data = await res.json();
            // 에러가 반환되면 예외를 발생시킵니다.
            if (!res.ok) throw new Error(data.detail);
            
            // 성공 알림을 띄우고 입력칸을 모두 비워줍니다.
            alert('비밀번호가 성공적으로 변경되었습니다.');
            document.getElementById('current_password').value = '';
            document.getElementById('new_password').value = '';
            document.getElementById('confirm_password').value = '';
        } catch (e) {
            alert(`비밀번호 변경 실패: ${e.message}`);
        }
    }

    // 계정을 완전히 삭제하고 탈퇴하는 함수입니다.
    async function deleteAccount() {
        // 중요한 동작이므로 사용자에게 다시 한번 확인받습니다.
        if (!confirm("정말 계정을 삭제하시겠습니까? (이 작업은 되돌릴 수 없습니다)")) return;
        
        try {
            // 삭제 API를 요청합니다.
            const res = await fetch(`${BASE_URL}/api/user/${user.username}`, { method: 'DELETE' });
            if (!res.ok) throw new Error();
            
            // 삭제 성공 시 로컬 스토리지를 비우고 로그인 화면으로 내보냅니다.
            localStorage.clear();
            window.location.href = 'login.html';
        } catch (e) {
            alert('계정 삭제에 실패했습니다.');
        }
    }

    // 다크 모드와 라이트 모드를 토글(반전)시키는 함수입니다.
    function toggleDarkMode() {
        // html 태그에 'dark' 클래스를 붙였다 뗐다 합니다.
        const isDark = document.documentElement.classList.toggle('dark');
        // 변경된 테마 설정을 로컬 스토리지에 기억시켜 다음 접속 시에도 유지되게 합니다.
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }

    // 사용자 로그아웃 처리를 합니다.
    function logout() {
        // 로컬에 저장된 사용자 세션 데이터를 지우고 로그인 창으로 보냅니다.
        localStorage.removeItem('pslw_user');
        window.location.href = 'login.html';
    }

    // --- Initialize ---
    // 웹 페이지의 HTML(DOM)이 모두 로드되었을 때 실행되는 초기 세팅 영역입니다.
    document.addEventListener('DOMContentLoaded', () => {
        // 로컬 스토리지에 다크 모드로 설정되어 있거나, 시스템 설정이 다크 모드일 경우 테마를 어둡게 맞춥니다.
        if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
            const toggle = document.getElementById('toggle-dark-mode');
            if (toggle) toggle.checked = true;
        }

        // 페이지 진입 즉시 대시보드의 요약 리스트를 불러옵니다.
        loadSummaries();

        // 브라우저 URL에 action=upload라는 주소가 붙어있다면, 화면 진입 즉시 업로드 창을 띄웁니다.
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('action') === 'upload') {
            switchView('view-dashboard');
            setTimeout(() => {
                const fi = document.getElementById('file-input');
                if (fi) fi.click();
            }, 100);
            // 업로드 창이 뜬 후에는 URL에서 action 파라미터를 깔끔하게 제거합니다.
            window.history.replaceState({}, document.title, window.location.pathname);
        }

        // 검색창과 필터 값이 변경될 때마다 화면을 갱신하도록 이벤트를 연결합니다.
        const searchInput = document.getElementById('history-search');
        if (searchInput) searchInput.addEventListener('input', () => { currentHistoryPage = 1; renderHistoryTable(); });
        
        ['history-filter-date', 'history-filter-provider', 'history-filter-type'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', () => { currentHistoryPage = 1; renderHistoryTable(); });
        });

        // 파일을 드래그 앤 드롭해서 업로드하는 박스의 이벤트 리스너들입니다.
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const defaultState = document.getElementById('upload-default-state');

        if(dropZone && fileInput && defaultState) {
            // 박스를 클릭했을 때 숨겨진 파일 선택기를 열어줍니다.
            dropZone.addEventListener('click', () => {
                if (!defaultState.classList.contains('hidden')) fileInput.click();
            });
            // 파일이 박스 위로 올라왔을 때 테두리 색을 바꿉니다.
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('border-primary');
            });
            // 파일이 박스를 벗어났을 때 색을 원상복구합니다.
            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('border-primary');
            });
            // 마우스를 놓아 파일을 떨궜을 때 해당 파일을 업로드 함수로 넘깁니다.
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-primary');
                if (e.dataTransfer.files.length > 0) uploadFile(e.dataTransfer.files[0]);
            });
            // 파일 선택기로 파일이 등록되었을 때도 똑같이 업로드 함수로 넘깁니다.
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) uploadFile(fileInput.files[0]);
            });
        }
        
        // 사이드바의 우측 상단 큰 업로드 버튼을 눌렀을 때의 동작을 정의합니다.
        const btnUploadAudio = document.getElementById('btn-upload-audio');
        if (btnUploadAudio) {
            btnUploadAudio.addEventListener('click', () => {
                // 클릭하면 무조건 대시보드 탭으로 화면을 넘기고 파일 선택기를 띄웁니다.
                switchView('view-dashboard');
                setTimeout(() => {
                    if (fileInput) fileInput.click();
                }, 100);
            });
        }

        // 설정 화면의 각종 저장 및 테스트 버튼에 이벤트 핸들러를 연결합니다.
        const saveApiBtn = document.getElementById('btn-save-api');
        if (saveApiBtn) saveApiBtn.addEventListener('click', saveApiSettings);
        const testBtn = document.getElementById('btn-test-connection');
        if (testBtn) testBtn.addEventListener('click', testApiConnection);

        const saveProfileBtn = document.getElementById('btn-save-profile');
        if (saveProfileBtn) saveProfileBtn.addEventListener('click', saveProfile);

        // 다크 모드 토글 버튼의 변경 이벤트를 연결합니다.
        const darkModeToggle = document.getElementById('toggle-dark-mode');
        if (darkModeToggle) darkModeToggle.addEventListener('change', toggleDarkMode);

        // 계정 삭제 버튼에 이벤트를 연결합니다.
        const deleteAccountBtn = document.getElementById('btn-delete-account');
        if (deleteAccountBtn) deleteAccountBtn.addEventListener('click', deleteAccount);
        
        // 비밀번호 필드의 눈 모양 아이콘을 눌렀을 때, 글자를 보이게 하거나 가리는 로직입니다.
        const toggleBtn = document.getElementById('togglePassword');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function() {
                const input = document.getElementById('apiKey');
                const icon = document.getElementById('toggleIcon');
                if (input && icon) {
                    if (input.type === 'password') {
                        input.type = 'text';
                        icon.textContent = 'visibility_off';
                    } else {
                        input.type = 'password';
                        icon.textContent = 'visibility';
                    }
                }
            });
        }
    });