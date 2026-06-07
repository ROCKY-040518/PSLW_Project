        let isLoginMode = true;

        // 이미 로그인된 경우 홈으로 리다이렉트
        if (localStorage.getItem('pslw_user')) { window.location.href = 'home.html'; }

        function togglePasswordVisibility() {
            const passwordInput = document.getElementById('password');
            const visibilityIcon = document.getElementById('visibility-icon');
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                visibilityIcon.textContent = 'visibility_off';
            } else {
                passwordInput.type = 'password';
                visibilityIcon.textContent = 'visibility';
            }
        }

        function toggleAuthMode() {
            isLoginMode = !isLoginMode;
            const signupFields = document.getElementById('signup-fields');
            const submitBtnText = document.getElementById('submit-btn-text');
            const subtitle = document.getElementById('auth-subtitle');
            const togglePrompt = document.getElementById('toggle-prompt');
            const toggleAction = document.getElementById('toggle-action');
            const forgotPasswordLink = document.getElementById('forgot-password-link');
            const form = document.getElementById('auth-form');

            if (!isLoginMode) {
                signupFields.classList.remove('hidden');
                setTimeout(() => { signupFields.classList.remove('opacity-0'); }, 10);
                submitBtnText.textContent = 'Create Account';
                subtitle.textContent = 'Join PSLW platform';
                togglePrompt.textContent = 'Already have an account?';
                toggleAction.textContent = 'Sign in';
                forgotPasswordLink.classList.add('hidden');
                document.getElementById('provider').setAttribute('required', 'true');
            } else {
                signupFields.classList.add('opacity-0');
                setTimeout(() => { signupFields.classList.add('hidden'); }, 300);
                submitBtnText.textContent = 'Sign In';
                subtitle.textContent = 'Sign in to your account';
                togglePrompt.textContent = "Don't have an account?";
                toggleAction.textContent = 'Register here';
                forgotPasswordLink.classList.remove('hidden');
                document.getElementById('provider').removeAttribute('required');
            }
            form.style.transform = 'scale(0.99)';
            setTimeout(() => {
                form.style.transform = 'scale(1)';
                form.style.transition = 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
            }, 150);
        }

        function showError(msg) {
            let el = document.getElementById('auth-error');
            if (!el) {
                el = document.createElement('p');
                el.id = 'auth-error';
                el.className = 'text-error font-body-sm text-body-sm text-center mt-2';
                document.getElementById('submit-btn').insertAdjacentElement('afterend', el);
            }
            el.textContent = msg;
        }

        function setLoading(on) {
            const btn = document.getElementById('submit-btn');
            const txt = document.getElementById('submit-btn-text');
            btn.disabled = on;
            btn.style.opacity = on ? '0.7' : '1';
            txt.textContent = on ? 'Please wait...' : (isLoginMode ? 'Sign In' : 'Create Account');
        }

        document.getElementById('auth-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const errEl = document.getElementById('auth-error');
            if (errEl) errEl.textContent = '';

            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            if (!username || !password) { showError('Username and password are required.'); return; }

            setLoading(true);
            try {
                if (isLoginMode) {
                    const res = await fetch(`${BASE_URL}/api/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    const data = await res.json();
                    if (!res.ok) { showError(data.detail || 'Login failed.'); return; }
                    localStorage.setItem('pslw_user', JSON.stringify(data));
                    window.location.href = 'home.html';
                } else {
                    const provider = document.getElementById('provider').value;
                    const api_key = document.getElementById('apikey').value.trim();
                    if (!api_key) { showError('API Key is required.'); setLoading(false); return; }
                    const res = await fetch(`${BASE_URL}/api/register`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password, provider, api_key })
                    });
                    const data = await res.json();
                    if (!res.ok) { showError(data.detail || 'Registration failed.'); return; }
                    // 회원가입 후 자동 로그인
                    const lr = await fetch(`${BASE_URL}/api/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });
                    const ld = await lr.json();
                    if (lr.ok) {
                        localStorage.setItem('pslw_user', JSON.stringify(ld));
                        window.location.href = 'home.html';
                    } else {
                        showError('Account created! Please sign in.');
                        toggleAuthMode();
                    }
                }
            } catch {
                showError('Cannot connect to server. Make sure the backend is running at localhost:8000.');
            } finally {
                setLoading(false);
            }
        });