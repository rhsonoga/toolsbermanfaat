/**
 * Signup/Login form module.
 * Isolated from the main auth orchestrator to reduce regression risk.
 */
(function () {
    function initSignupForm() {
        const signupForm = document.getElementById('signupForm');
        if (!signupForm) return;

        signupForm.addEventListener('submit', handleSignupSubmit);
    }

    async function handleSignupSubmit(e) {
        e.preventDefault();

        const fullName = document.getElementById('signupName');
        const email = document.getElementById('signupEmail');
        const password = document.getElementById('signupPassword');

        if (!fullName?.value || !email?.value || !password?.value) {
            if (typeof window.showFeedback === 'function') {
                window.showFeedback('signupFeedback', 'Semua field wajib diisi.', false);
            }
            return;
        }

        const payload = {
            full_name: fullName.value,
            email: email.value,
            password: password.value,
        };

        try {
            if (typeof window.showFeedback === 'function') {
                window.showFeedback('signupFeedback', 'Sedang memproses...', true);
            }

            const res = await fetch('/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await res.json();

            if (!res.ok || !data.ok) {
                if (typeof window.showFeedback === 'function') {
                    window.showFeedback('signupFeedback', data.error || 'Registrasi gagal.', false);
                }
                return;
            }

            if (typeof window.showFeedback === 'function') {
                window.showFeedback('signupFeedback', data.message || 'Registrasi berhasil. Cek email Anda!', true);
            }

            if (e.target && typeof e.target.reset === 'function') {
                e.target.reset();
            }

            setTimeout(() => {
                if (typeof window.closeModal === 'function') {
                    window.closeModal('signupModal');
                }
            }, 2000);
        } catch (err) {
            if (typeof window.showFeedback === 'function') {
                window.showFeedback('signupFeedback', `Error: ${err.message}`, false);
            }
        }
    }

    function initLoginForm() {
        const loginForm = document.getElementById('loginForm');
        if (!loginForm) return;

        loginForm.addEventListener('submit', handleLoginSubmit);
    }

    async function handleLoginSubmit(e) {
        e.preventDefault();

        const email = document.getElementById('loginEmail');
        const password = document.getElementById('loginPassword');

        if (!email?.value || !password?.value) {
            if (typeof window.showFeedback === 'function') {
                window.showFeedback('loginFeedback', 'Email dan password wajib diisi.', false);
            }
            return;
        }

        const payload = {
            email: email.value,
            password: password.value,
        };

        try {
            if (typeof window.showFeedback === 'function') {
                window.showFeedback('loginFeedback', 'Sedang login...', true);
            }

            const res = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await res.json();

            if (!res.ok || !data.ok) {
                if (typeof window.showFeedback === 'function') {
                    window.showFeedback('loginFeedback', data.error || 'Login gagal.', false);
                }
                return;
            }

            if (typeof window.showFeedback === 'function') {
                window.showFeedback('loginFeedback', data.message || 'Login berhasil!', true);
            }
            if (typeof window.updateAuthStrip === 'function') {
                window.updateAuthStrip(data.user?.email || '');
            }
            if (typeof window.updateLoginLogoutUI === 'function') {
                window.updateLoginLogoutUI();
            }

            setTimeout(() => {
                if (typeof window.closeModal === 'function') {
                    window.closeModal('loginModal');
                }
            }, 1500);
        } catch (err) {
            if (typeof window.showFeedback === 'function') {
                window.showFeedback('loginFeedback', `Error: ${err.message}`, false);
            }
        }
    }

    window.AuthSignupLogin = {
        initSignupForm,
        handleSignupSubmit,
        initLoginForm,
        handleLoginSubmit,
    };
})();