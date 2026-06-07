
    const userRaw = localStorage.getItem('pslw_user');
    if (!userRaw) { window.location.href = 'login.html'; }
    const user = JSON.parse(userRaw || '{}');

    function escHtml(str) {
        const d = document.createElement('div');
        d.appendChild(document.createTextNode(str || ''));
        return d.innerHTML;
    }

    function switchView(viewId) {
        const sections = ['view-dashboard', 'view-api-settings', 'view-history', 'view-usage', 'view-settings'];
        sections.forEach((id) => {
            const section = document.getElementById(id);
            if (!section) return;
            section.className = id === viewId ? 'block' : 'hidden';
        });

        const navLinks = document.querySelectorAll('nav a[onclick^="switchView"]');
        navLinks.forEach(link => {
            if (link.getAttribute('onclick').includes(viewId)) {
                link.className = "flex items-center gap-3 px-4 py-3 text-primary bg-surface-container-highest border-l-4 border-primary font-label-md text-label-md cursor-pointer active:scale-[0.98] transition-transform";
                const icon = link.querySelector('.material-symbols-outlined');
                if(icon) icon.style.fontVariationSettings = "'FILL' 1";
            } else {
                link.className = "flex items-center gap-3 px-4 py-3 text-on-surface-variant dark:text-[#a0a0a0] font-label-md text-label-md hover:bg-surface-container-high transition-colors duration-200 cursor-pointer active:scale-[0.98] rounded-lg";
                const icon = link.querySelector('.material-symbols-outlined');
                if(icon) icon.style.fontVariationSettings = "'FILL' 0";
            }
        });

        if (viewId === 'view-history' || viewId === 'view-dashboard') loadSummaries();
        if (viewId === 'view-usage') loadUsage();
        if (viewId === 'view-api-settings') prefillApiSettings();
    }

    // --- Dashboard & History ---
    let allHistoryItems = [];
    let currentHistoryPage = 1;
    const ITEMS_PER_PAGE = 5;

    async function loadSummaries() {
        try {
            const res = await fetch(`${BASE_URL}/api/summaries/${user.username}`);
            if (!res.ok) throw new Error();
            allHistoryItems = await res.json();
            renderCards(allHistoryItems);
            renderHistoryTable();
        } catch { console.error('Failed to load summaries'); }
    }

    function renderCards(items) {
        const grid = document.getElementById('summaries-grid');
        if (!grid) return;
        grid.innerHTML = '';
        if (items.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center text-on-surface-variant dark:text-[#a0a0a0] py-xl">
                    <span class="material-symbols-outlined text-[48px] mb-md block text-outline">inbox</span>
                    <p class="font-body-md text-body-md">No summaries yet. Upload an audio file to get started.</p>
                </div>`;
            return;
        }
        items.slice(0, 6).forEach(item => {
            const card = document.createElement('div');
            card.className = 'bg-surface-container-lowest dark:bg-[#1e1e1e] border border-outline-variant dark:border-[#333333] rounded-xl p-lg flex flex-col justify-between hover:shadow-[0px_10px_15px_-3px_rgba(15,23,42,0.05)] transition-shadow duration-300';
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
            grid.appendChild(card);
        });
    }

    function renderHistoryTable() {
        const tbody = document.getElementById('history-tbody');
        if (!tbody) return;
        
        // Filters
        const searchVal = document.getElementById('history-search')?.value.toLowerCase() || '';
        
        let filtered = allHistoryItems.filter(item => {
            if (searchVal && !item.filename.toLowerCase().includes(searchVal) && !item.id.toString().includes(searchVal)) return false;
            return true;
        });
        
        const totalItems = filtered.length;
        const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE) || 1;
        if (currentHistoryPage > totalPages) currentHistoryPage = totalPages;
        if (currentHistoryPage < 1) currentHistoryPage = 1;
        
        const startIdx = (currentHistoryPage - 1) * ITEMS_PER_PAGE;
        const paginated = filtered.slice(startIdx, startIdx + ITEMS_PER_PAGE);
        
        tbody.innerHTML = '';
        if (paginated.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="py-12 text-center text-on-surface-variant dark:text-[#cccccc]">No history available.</td></tr>`;
        } else {
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
                tbody.appendChild(tr);
            });
        }
        
        // Render pagination controls
        const paginationDiv = document.getElementById('history-pagination');
        if (paginationDiv) {
            let buttonsHtml = '';
            for (let i = 1; i <= totalPages; i++) {
                if (i === currentHistoryPage) {
                    buttonsHtml += `<button class="w-8 h-8 flex items-center justify-center rounded bg-primary text-on-primary font-label-md text-label-md">${i}</button>`;
                } else {
                    buttonsHtml += `<button onclick="changePage(${i})" class="w-8 h-8 flex items-center justify-center rounded text-on-surface-variant dark:text-[#a0a0a0] hover:bg-surface-container font-label-md text-label-md transition-colors">${i}</button>`;
                }
            }
            
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

    function changePage(p) {
        currentHistoryPage = p;
        renderHistoryTable();
    }

    function viewSummary(id) { window.location.href = `summary.html?id=${id}`; }

    async function deleteSummary(id) {
        if (!confirm('이 요약을 삭제하시겠습니까?')) return;
        try {
            const res = await fetch(`${BASE_URL}/api/summary/${id}`, { method: 'DELETE' });
            if (res.ok) { 
                await loadSummaries(); 
                // 삭제 완료 후 현재 페이지(히스토리 또는 대시보드) 화면 새로고침
            } else { 
                alert('삭제 실패'); 
            }
        } catch { 
            alert('서버 연결 오류'); 
        }
    }

    // --- File Upload ---
    async function uploadFile(file) {
        const defaultState = document.getElementById('upload-default-state');
        const loadingState = document.getElementById('upload-loading-state');
        const dropZone = document.getElementById('drop-zone');
        if(!defaultState || !loadingState) return;

        defaultState.classList.add('hidden');
        loadingState.classList.remove('hidden');
        loadingState.classList.add('flex');
        dropZone.classList.add('upload-loading');
        
        const loadingText = loadingState.querySelector('h3');
        if(loadingText) loadingText.textContent = "요약 중입니다. 잠시만 기다려주세요...";

        function resetUploadUI() {
            loadingState.classList.add('hidden');
            loadingState.classList.remove('flex');
            defaultState.classList.remove('hidden');
            dropZone.classList.remove('upload-loading');
            document.getElementById('file-input').value = '';
        }

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('username', user.username);
            const res = await fetch(`${BASE_URL}/api/upload`, { method: 'POST', body: formData });
            
            if (!res.ok) { 
                const data = await res.json(); 
                alert(`업로드 실패: ${data.detail}`); 
                resetUploadUI();
                return;
            }
            
            const data = await res.json();
            const taskId = data.task_id;
            
            // Polling
            const pollInterval = setInterval(async () => {
                try {
                    const statusRes = await fetch(`${BASE_URL}/api/status/${taskId}`);
                    if(!statusRes.ok) throw new Error("Status check failed");
                    const statusData = await statusRes.json();
                    
                    if (statusData.status === "completed") {
                        clearInterval(pollInterval);
                        await loadSummaries();
                        resetUploadUI();
                    } else if (statusData.status === "failed") {
                        clearInterval(pollInterval);
                        alert(`요약 실패: ${statusData.error}`);
                        resetUploadUI();
                    }
                } catch(e) {
                    clearInterval(pollInterval);
                    alert("상태 확인 중 오류가 발생했습니다.");
                    resetUploadUI();
                }
            }, 5000);

        } catch (err) { 
            alert('업로드 중 오류가 발생했습니다.'); 
            resetUploadUI();
        }
    }

    // --- API Settings ---
    function prefillApiSettings() {
        const providerSelect = document.getElementById('api-provider');
        if (providerSelect && user.provider) {
            providerSelect.value = user.provider;
        }
    }

    async function saveApiSettings() {
        const provider = document.getElementById('api-provider').value;
        const apiKey = document.getElementById('apiKey').value;
        const statusBadge = document.getElementById('api-status-badge');
        
        if (!apiKey.trim()) { alert('API Key를 입력해주세요.'); return; }
        
        try {
            const res = await fetch(`${BASE_URL}/api/user/api-keys`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user.username, provider: provider, api_key: apiKey })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);
            
            user.provider = provider;
            user.api_key = apiKey;
            localStorage.setItem('pslw_user', JSON.stringify(user));
            if(statusBadge) {
                statusBadge.innerHTML = `<span class="material-symbols-outlined" style="font-size: 16px;">check_circle</span> Status: Connected (${provider})`;
                statusBadge.className = 'flex items-center gap-2 text-primary font-label-md text-label-md bg-primary-container/20 px-3 py-1.5 rounded-full border border-primary/20';
            }
            alert('API 키가 성공적으로 저장되었습니다.');
        } catch (e) {
            alert(`API 키 저장 실패: ${e.message}`);
        }
    }

    async function testApiConnection() {
        await saveApiSettings(); // 저장 테스트로 갈음
    }

    // --- Usage ---
    async function loadUsage() {
        try {
            const res = await fetch(`${BASE_URL}/api/usage/${user.username}`);
            if (!res.ok) throw new Error();
            const data = await res.json();
            
            const countEl = document.getElementById('usage-total-count');
            if (countEl) countEl.textContent = data.total_processed;
            
            const monthlyEl = document.getElementById('usage-monthly-count');
            if (monthlyEl) monthlyEl.textContent = data.monthly_requests;
            
            const percentEl = document.getElementById('usage-quota-percent');
            if (percentEl) percentEl.textContent = data.quota_percent + '%';
            
            const labelEl = document.getElementById('usage-quota-label');
            if (labelEl) labelEl.textContent = data.quota_label;
            
            const barEl = document.getElementById('usage-quota-bar');
            if (barEl) barEl.style.width = data.quota_percent + '%';

            // Dynamic classes for quota status
            const quotaCard = document.getElementById('usage-quota-card');
            const quotaText = document.getElementById('usage-quota-text');
            const quotaIcon = document.getElementById('usage-quota-icon');
            const quotaBg = document.getElementById('usage-quota-bg');
            if (quotaCard && quotaText && quotaIcon && quotaBg && percentEl && labelEl && barEl) {
                if (data.quota_percent >= 80) {
                    quotaCard.className = 'col-span-4 bg-error-container/20 border border-error rounded-xl p-6 shadow-sm flex flex-col justify-between h-32 relative overflow-hidden';
                    quotaText.className = 'font-label-md text-label-md text-error font-semibold';
                    quotaIcon.className = 'material-symbols-outlined text-error';
                    percentEl.className = 'font-display-lg text-display-lg text-error';
                    labelEl.className = 'font-label-md text-label-md text-error';
                    quotaBg.className = 'w-full bg-error-container rounded-full h-1.5';
                    barEl.className = 'bg-error h-1.5 rounded-full';
                    quotaIcon.textContent = 'warning';
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

            // Dynamic Chart
            const chartContainer = document.getElementById('usage-chart-container');
            if (chartContainer && data.daily_usage) {
                const maxVal = Math.max(...data.daily_usage, 1);
                chartContainer.innerHTML = `
                    <div class="absolute left-0 top-0 h-full flex flex-col justify-between text-outline font-mono-sm text-mono-sm pb-2 opacity-50 -ml-8">
                        <span>${maxVal}</span>
                        <span>${Math.round(maxVal/2)}</span>
                        <span>0</span>
                    </div>
                `;
                data.daily_usage.forEach(val => {
                    const heightPercent = (val / maxVal) * 100;
                    chartContainer.innerHTML += `
                        <div class="w-full bg-primary-container hover:bg-primary transition-colors rounded-t-sm relative group" style="height: ${heightPercent}%">
                            <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-inverse-surface text-inverse-on-surface font-mono-sm text-mono-sm px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity z-20">${val}</div>
                        </div>
                    `;
                });
            }

            // Model Distribution
            const modelDist = document.getElementById('usage-model-distribution');
            if (modelDist && data.model_distribution) {
                modelDist.innerHTML = '';
                const colors = ['bg-primary', 'bg-secondary', 'bg-error'];
                data.model_distribution.forEach((model, i) => {
                    const color = colors[i % colors.length];
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
            // Fallback mock data
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
    async function saveProfile() {
        const currentPw = document.getElementById('current_password').value;
        const newPw = document.getElementById('new_password').value;
        const confirmPw = document.getElementById('confirm_password').value;
        
        if (!currentPw || !newPw || !confirmPw) { alert('모든 비밀번호 필드를 입력해주세요.'); return; }
        if (newPw !== confirmPw) { alert('새 비밀번호와 확인 비밀번호가 일치하지 않습니다.'); return; }
        
        try {
            const res = await fetch(`${BASE_URL}/api/user/profile`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user.username, current_password: currentPw, new_password: newPw })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);
            
            alert('비밀번호가 성공적으로 변경되었습니다.');
            document.getElementById('current_password').value = '';
            document.getElementById('new_password').value = '';
            document.getElementById('confirm_password').value = '';
        } catch (e) {
            alert(`비밀번호 변경 실패: ${e.message}`);
        }
    }

    async function deleteAccount() {
        if (!confirm("정말 계정을 삭제하시겠습니까? (이 작업은 되돌릴 수 없습니다)")) return;
        
        try {
            const res = await fetch(`${BASE_URL}/api/user/${user.username}`, { method: 'DELETE' });
            if (!res.ok) throw new Error();
            
            localStorage.clear();
            window.location.href = 'login.html';
        } catch (e) {
            alert('계정 삭제에 실패했습니다.');
        }
    }

    function toggleDarkMode() {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }

    function logout() {
        localStorage.removeItem('pslw_user');
        window.location.href = 'login.html';
    }

    // --- Initialize ---
    document.addEventListener('DOMContentLoaded', () => {
        // Init theme
        if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
            const toggle = document.getElementById('toggle-dark-mode');
            if (toggle) toggle.checked = true;
        }

        loadSummaries();

        // URL Parameter Routing for Upload
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('action') === 'upload') {
            switchView('view-dashboard');
            setTimeout(() => {
                const fi = document.getElementById('file-input');
                if (fi) fi.click();
            }, 100);
            window.history.replaceState({}, document.title, window.location.pathname);
        }


        // Search & Filters
        const searchInput = document.getElementById('history-search');
        if (searchInput) searchInput.addEventListener('input', () => { currentHistoryPage = 1; renderHistoryTable(); });
        
        ['history-filter-date', 'history-filter-provider', 'history-filter-type'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', () => { currentHistoryPage = 1; renderHistoryTable(); });
        });

        // Drag & Drop
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const defaultState = document.getElementById('upload-default-state');

        if(dropZone && fileInput && defaultState) {
            dropZone.addEventListener('click', () => {
                if (!defaultState.classList.contains('hidden')) fileInput.click();
            });
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('border-primary');
            });
            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('border-primary');
            });
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-primary');
                if (e.dataTransfer.files.length > 0) uploadFile(e.dataTransfer.files[0]);
            });
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) uploadFile(fileInput.files[0]);
            });
        }
        
        // Sidebar Upload Audio
        const btnUploadAudio = document.getElementById('btn-upload-audio');
        if (btnUploadAudio) {
            btnUploadAudio.addEventListener('click', () => {
                switchView('view-dashboard');
                setTimeout(() => {
                    if (fileInput) fileInput.click();
                }, 100);
            });
        }

        // API Settings
        const saveApiBtn = document.getElementById('btn-save-api');
        if (saveApiBtn) saveApiBtn.addEventListener('click', saveApiSettings);
        const testBtn = document.getElementById('btn-test-connection');
        if (testBtn) testBtn.addEventListener('click', testApiConnection);

        // Profile settings
        const saveProfileBtn = document.getElementById('btn-save-profile');
        if (saveProfileBtn) saveProfileBtn.addEventListener('click', saveProfile);

        // Dark mode
        const darkModeToggle = document.getElementById('toggle-dark-mode');
        if (darkModeToggle) darkModeToggle.addEventListener('change', toggleDarkMode);

        // Delete Account
        const deleteAccountBtn = document.getElementById('btn-delete-account');
        if (deleteAccountBtn) deleteAccountBtn.addEventListener('click', deleteAccount);
        
        // Password Toggle
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