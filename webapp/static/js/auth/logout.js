/**
 * Logout module.
 * Isolated from the main auth orchestrator to reduce regression risk.
 */
(function () {
    function initLogoutButton() {
        const logoutBtn = document.getElementById('logoutBtn');
        if (!logoutBtn) return;

        logoutBtn.addEventListener('click', handleLogoutClick);
    }

    async function handleLogoutClick(e) {
        e.preventDefault();

        if (!confirm('Yakin ingin logout?')) {
            return;
        }

        try {
            const res = await fetch('/auth/logout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });

            const data = await res.json();

            if (!res.ok || !data.ok) {
                alert('Logout gagal: ' + (data.error || 'Unknown error'));
                return;
            }

            if (typeof window.updateAuthStrip === 'function') {
                window.updateAuthStrip('');
            }
            if (typeof window.updateLoginLogoutUI === 'function') {
                window.updateLoginLogoutUI();
            }

            setTimeout(() => {
                window.location.href = '/';
            }, 500);
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    }

    window.AuthLogout = {
        initLogoutButton,
        handleLogoutClick,
    };
})();