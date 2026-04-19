/**
 * Verification module.
 * Isolated from the main auth orchestrator to reduce regression risk.
 */
(function () {
    function initResendButton() {
        const resendBtn = document.getElementById('resendVerificationBtn');
        if (!resendBtn) return;

        resendBtn.addEventListener('click', handleResendClick);
    }

    async function handleResendClick(e) {
        if (e && typeof e.preventDefault === 'function') {
            e.preventDefault();
        }

        let email = prompt('Masukkan email Anda untuk mengirim ulang verifikasi:');
        if (!email || !email.trim()) {
            return;
        }

        email = email.trim();

        try {
            const res = await fetch('/auth/resend-verification', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });

            const data = await res.json();

            if (!res.ok || !data.ok) {
                alert(data.error || 'Gagal mengirim email verifikasi');
                return;
            }

            alert(data.message || 'Email verifikasi sudah dikirim. Cek inbox Anda!');
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    }

    function checkVerificationMessage() {
        const params = new URLSearchParams(window.location.search);
        const verified = params.get('verified');
        const error = params.get('verification_error');

        let banner = document.getElementById('verificationBanner');

        if (verified === 'true') {
            if (typeof window.updateAuthStrip === 'function') {
                window.updateAuthStrip(document.querySelector('[data-user-email]')?.dataset.userEmail || 'User');
            }
            if (typeof window.updateLoginLogoutUI === 'function') {
                window.updateLoginLogoutUI();
            }

            if (!banner && typeof window.createVerificationBanner === 'function') {
                banner = window.createVerificationBanner('success');
            } else if (banner) {
                banner.className = 'verification-banner verification-success';
                banner.textContent = 'Email berhasil diverifikasi! Anda sekarang bisa menggunakan semua converter.';
                banner.style.display = 'block';
            }

            setTimeout(() => {
                if (banner) banner.style.display = 'none';
            }, 5000);
        } else if (error) {
            if (!banner && typeof window.createVerificationBanner === 'function') {
                banner = window.createVerificationBanner('error');
            } else if (banner) {
                banner.className = 'verification-banner verification-error';
                banner.style.display = 'block';
            }

            if (!banner) return;

            if (error === 'token_expired') {
                banner.innerHTML = 'Link verifikasi sudah kadaluarsa. <button id="resendVerificationBtn">Kirim Ulang</button>';
            } else {
                banner.innerHTML = 'Terjadi kesalahan verifikasi. <button id="resendVerificationBtn">Coba Lagi</button>';
            }

            const resendBtn = banner.querySelector('#resendVerificationBtn');
            if (resendBtn) {
                resendBtn.addEventListener('click', handleResendClick);
            }
        }
    }

    window.AuthVerification = {
        initResendButton,
        handleResendClick,
        checkVerificationMessage,
    };
})();