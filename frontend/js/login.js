        // 현재 화면이 '로그인 모드'인지 '회원가입 모드'인지 추적하는 변수입니다. 기본값은 로그인(true)입니다.
        let isLoginMode = true;

        // 브라우저 로컬 스토리지에 사용자 정보가 이미 저장되어 있다면, 즉시 홈 화면으로 리다이렉트합니다.
        if (localStorage.getItem('pslw_user')) { window.location.href = 'home.html'; }

        // 비밀번호 입력칸의 가려짐/보임 상태를 전환하는 함수입니다.
        function togglePasswordVisibility() {
            const passwordInput = document.getElementById('password');
            const visibilityIcon = document.getElementById('visibility-icon');
            // 입력 타입이 비밀번호(점자)라면 텍스트로 바꾸고 아이콘도 변경합니다.
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                visibilityIcon.textContent = 'visibility_off';
            } else {
            // 입력 타입이 텍스트라면 다시 비밀번호 모드로 돌려놓습니다.
                passwordInput.type = 'password';
                visibilityIcon.textContent = 'visibility';
            }
        }

        // 로그인 모드와 회원가입 모드를 서로 전환하는 UI 변경 함수입니다.
        function toggleAuthMode() {
            // 현재 모드 상태를 반전시킵니다.
            isLoginMode = !isLoginMode;
            // 화면에서 조작해야 할 주요 HTML 요소들을 가져옵니다.
            const signupFields = document.getElementById('signup-fields');
            const submitBtnText = document.getElementById('submit-btn-text');
            const subtitle = document.getElementById('auth-subtitle');
            const togglePrompt = document.getElementById('toggle-prompt');
            const toggleAction = document.getElementById('toggle-action');
            const forgotPasswordLink = document.getElementById('forgot-password-link');
            const form = document.getElementById('auth-form');

            // 만약 회원가입 모드로 전환되었다면
            if (!isLoginMode) {
                // 회원가입 전용 입력 필드(API 키 등)를 보이게 만듭니다.
                signupFields.classList.remove('hidden');
                // 부드러운 애니메이션 효과를 위해 약간의 지연 후 투명도를 조절합니다.
                setTimeout(() => { signupFields.classList.remove('opacity-0'); }, 10);
                // 주요 텍스트들을 '계정 생성'에 맞게 수정합니다.
                submitBtnText.textContent = 'Create Account';
                subtitle.textContent = 'Join PSLW platform';
                togglePrompt.textContent = 'Already have an account?';
                toggleAction.textContent = 'Sign in';
                // 회원가입 시에는 비밀번호 찾기 링크를 숨깁니다.
                forgotPasswordLink.classList.add('hidden');
                // 제공자 선택(Provider)을 필수값으로 설정합니다.
                document.getElementById('provider').setAttribute('required', 'true');
            // 다시 로그인 모드로 전환되었다면
            } else {
                // 회원가입 전용 입력 필드를 애니메이션과 함께 서서히 숨깁니다.
                signupFields.classList.add('opacity-0');
                setTimeout(() => { signupFields.classList.add('hidden'); }, 300);
                // 주요 텍스트들을 '로그인'에 맞게 원상 복구합니다.
                submitBtnText.textContent = 'Sign In';
                subtitle.textContent = 'Sign in to your account';
                togglePrompt.textContent = "Don't have an account?";
                toggleAction.textContent = 'Register here';
                // 비밀번호 찾기 링크를 다시 표시합니다.
                forgotPasswordLink.classList.remove('hidden');
                // 제공자 선택(Provider)의 필수 조건을 해제합니다.
                document.getElementById('provider').removeAttribute('required');
            }
            // 폼 전체 크기를 살짝 줄였다가 다시 키우는 시각적 효과(바운스)를 줍니다.
            form.style.transform = 'scale(0.99)';
            setTimeout(() => {
                form.style.transform = 'scale(1)';
                form.style.transition = 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
            }, 150);
        }

        // 로그인/회원가입 중 발생한 에러 메시지를 화면에 그려주는 함수입니다.
        function showError(msg) {
            let el = document.getElementById('auth-error');
            // 에러 메시지 공간이 없다면 새로 만들어서 버튼 아래에 붙여줍니다.
            if (!el) {
                el = document.createElement('p');
                el.id = 'auth-error';
                el.className = 'text-error font-body-sm text-body-sm text-center mt-2';
                document.getElementById('submit-btn').insertAdjacentElement('afterend', el);
            }
            // 전달받은 메시지를 텍스트로 채웁니다.
            el.textContent = msg;
        }

        // 서버 통신 중일 때 버튼을 비활성화하고 '기다려주세요' 상태로 바꾸는 함수입니다.
        function setLoading(on) {
            const btn = document.getElementById('submit-btn');
            const txt = document.getElementById('submit-btn-text');
            // on이 true이면 버튼을 클릭 불가능하게 만들고 투명도를 낮춥니다.
            btn.disabled = on;
            btn.style.opacity = on ? '0.7' : '1';
            // 버튼 내부 텍스트를 대기 상태로 바꾸거나, 통신이 끝나면 원래 텍스트로 복구합니다.
            txt.textContent = on ? 'Please wait...' : (isLoginMode ? 'Sign In' : 'Create Account');
        }

        // 사용자가 폼에서 '제출(엔터 또는 버튼 클릭)'을 눌렀을 때의 동작을 정의합니다.
        document.getElementById('auth-form').addEventListener('submit', async (e) => {
            // 브라우저의 기본 폼 전송(새로고침)을 막습니다.
            e.preventDefault();
            const errEl = document.getElementById('auth-error');
            // 기존에 떠 있던 에러 메시지를 초기화합니다.
            if (errEl) errEl.textContent = '';

            // 사용자가 입력한 아이디와 비밀번호의 앞뒤 공백을 제거하고 가져옵니다.
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            // 아이디나 비밀번호가 비어있으면 에러를 띄우고 함수를 멈춥니다.
            if (!username || !password) { showError('Username and password are required.'); return; }

            // 통신 시작 상태(로딩)로 진입합니다.
            setLoading(true);
            try {
                // 현재 로그인 모드일 경우의 통신 로직입니다.
                if (isLoginMode) {
                    // 백엔드의 로그인 API로 아이디와 비밀번호를 POST 전송합니다.
                    const res = await fetch(`${BASE_URL}/api/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    const data = await res.json();
                    // 응답이 실패면 서버의 에러 메시지를 화면에 보여줍니다.
                    if (!res.ok) { showError(data.detail || 'Login failed.'); return; }
                    // 성공했다면 응답받은 사용자 정보를 로컬 스토리지에 저장하고 홈으로 이동합니다.
                    localStorage.setItem('pslw_user', JSON.stringify(data));
                    window.location.href = 'home.html';
                // 현재 회원가입 모드일 경우의 통신 로직입니다.
                } else {
                    // 제공자 모델과 API 키 값을 가져옵니다.
                    const provider = document.getElementById('provider').value;
                    const api_key = document.getElementById('apikey').value.trim();
                    // API 키가 누락되었으면 경고 후 멈춥니다.
                    if (!api_key) { showError('API Key is required.'); setLoading(false); return; }
                    
                    // 백엔드의 회원가입 API로 모든 정보를 취합해 전송합니다.
                    const res = await fetch(`${BASE_URL}/api/register`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password, provider, api_key })
                    });
                    const data = await res.json();
                    // 가입 실패 시 에러 내용을 출력합니다.
                    if (!res.ok) { showError(data.detail || 'Registration failed.'); return; }
                    
                    // 회원가입이 성공하면, 사용 편의성을 위해 곧바로 로그인 API를 연달아 호출하여 자동 로그인을 시도합니다.
                    const lr = await fetch(`${BASE_URL}/api/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    const ld = await lr.json();
                    // 자동 로그인에 성공하면 사용자 정보를 저장하고 홈으로 보냅니다.
                    if (lr.ok) {
                        localStorage.setItem('pslw_user', JSON.stringify(ld));
                        window.location.href = 'home.html';
                    } else {
                        // 만약 자동 로그인만 실패했다면 계정 생성 완료 메시지를 띄우고 수동 로그인 화면으로 돌려놓습니다.
                        showError('Account created! Please sign in.');
                        toggleAuthMode();
                    }
                }
            } catch {
                // 네트워크 오류 등으로 서버와 통신할 수 없는 상황을 처리합니다.
                showError('Cannot connect to server. Make sure the backend is running at localhost:8000.');
            } finally {
                // 성공이든 에러든 통신이 끝났으므로 버튼을 원래 상태로 되돌립니다.
                setLoading(false);
            }
        });