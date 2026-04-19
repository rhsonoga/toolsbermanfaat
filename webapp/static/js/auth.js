/**
 * Authentication Module
 * 
 * Handles signup, login, logout, and verification flows.
 * Separated from main.js for better maintainability and modularity.
 */

// ============================================================
// INITIALIZATION
// ============================================================

/**
 * Initialize all auth-related event listeners and functionality.
 * Call this function once when the page loads.
 */
function initAuthModule() {
    const hasSupabase = window.supabaseReady === true;
    
    if (!hasSupabase) {
        console.warn('Auth Module: Supabase not configured on server');
        return;
    }
    
    initSignupForm();
    initLoginForm();
    initLogoutButton();
    initResendButton();
    checkVerificationMessage();
    updateLoginLogoutUI();
}

// ============================================================
// FORM HANDLERS
// ============================================================

/**
 * Initialize signup form event listeners.
 */
function initSignupForm() {
    const signupForm = document.getElementById('signupForm');
    if (!signupForm) return;
    
    signupForm.addEventListener('submit', handleSignupSubmit);
    
    const closeBtn = document.getElementById('signupCloseBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => closeModal('signupModal'));
    }
}

/**
 * Handle signup form submission.
 */
async function handleSignupSubmit(e) {
    e.preventDefault();
    
    const fullName = document.getElementById('signupName');
    const email = document.getElementById('signupEmail');
    const password = document.getElementById('signupPassword');
    
    if (!fullName?.value || !email?.value || !password?.value) {
        showFeedback('signupFeedback', 'Semua field wajib diisi.', false);
        return;
    }
    
    const payload = {
        full_name: fullName.value,
        email: email.value,
        password: password.value
    };
    
    try {
        showFeedback('signupFeedback', 'Sedang memproses...', true);
        
        const res = await fetch('/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        
        if (!res.ok || !data.ok) {
            showFeedback('signupFeedback', data.error || 'Registrasi gagal.', false);
            return;
        }
        
        // Success
        showFeedback('signupFeedback', data.message || 'Registrasi berhasil. Cek email Anda!', true);
        
        // Clear form
        signupForm.reset();
        
        // Close modal after 2 seconds
        setTimeout(() => {
            closeModal('signupModal');
        }, 2000);
        
    } catch (err) {
        showFeedback('signupFeedback', `Error: ${err.message}`, false);
    }
}

/**
 * Initialize login form event listeners.
 */
function initLoginForm() {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) return;
    
    loginForm.addEventListener('submit', handleLoginSubmit);
    
    const closeBtn = document.getElementById('loginCloseBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => closeModal('loginModal'));
    }
}

/**
 * Handle login form submission.
 */
async function handleLoginSubmit(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail');
    const password = document.getElementById('loginPassword');
    
    if (!email?.value || !password?.value) {
        showFeedback('loginFeedback', 'Email dan password wajib diisi.', false);
        return;
    }
    
    const payload = {
        email: email.value,
        password: password.value
    };
    
    try {
        showFeedback('loginFeedback', 'Sedang login...', true);
        
        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        
        if (!res.ok || !data.ok) {
            showFeedback('loginFeedback', data.error || 'Login gagal.', false);
            return;
        }
        
        // Success
        showFeedback('loginFeedback', data.message || 'Login berhasil!', true);
        updateAuthStrip(data.user?.email || '');
        updateLoginLogoutUI();
        
        // Close modal after 1.5 seconds
        setTimeout(() => {
            closeModal('loginModal');
        }, 1500);
        
    } catch (err) {
        showFeedback('loginFeedback', `Error: ${err.message}`, false);
    }
}

// ============================================================
// LOGOUT
// ============================================================

/**
 * Initialize logout button.
 */
function initLogoutButton() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (!logoutBtn) return;
    
    logoutBtn.addEventListener('click', handleLogoutClick);
}

/**
 * Handle logout button click.
 */
async function handleLogoutClick(e) {
    e.preventDefault();
    
    if (!confirm('Yakin ingin logout?')) {
        return;
    }
    
    try {
        const res = await fetch('/auth/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await res.json();
        
        if (!res.ok || !data.ok) {
            alert('Logout gagal: ' + (data.error || 'Unknown error'));
            return;
        }
        
        // Success
        updateAuthStrip('');
        updateLoginLogoutUI();
        
        // Redirect to home
        setTimeout(() => {
            window.location.href = '/';
        }, 500);
        
    } catch (err) {
        alert(`Error: ${err.message}`);
    }
}

// ============================================================
// VERIFICATION & RESEND
// ============================================================

/**
 * Initialize resend verification button.
 */
function initResendButton() {
    const resendBtn = document.getElementById('resendVerificationBtn');
    if (!resendBtn) return;
    
    resendBtn.addEventListener('click', handleResendClick);
}

/**
 * Handle resend verification button click.
 */
async function handleResendClick(e) {
    e.preventDefault();
    
    let email = prompt('Masukkan email Anda untuk mengirim ulang verifikasi:');
    if (!email || !email.trim()) {
        return;
    }
    
    email = email.trim();
    
    try {
        const res = await fetch('/auth/resend-verification', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
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

/**
 * Check for verification messages in URL query parameters.
 */
function checkVerificationMessage() {
    const params = new URLSearchParams(window.location.search);
    const verified = params.get('verified');
    const error = params.get('verification_error');
    
    let banner = document.getElementById('verificationBanner');
    
    if (verified === 'true') {
        updateAuthStrip(document.querySelector('[data-user-email]')?.dataset.userEmail || 'User');
        updateLoginLogoutUI();
        
        // Show success banner
        if (!banner) {
            banner = createVerificationBanner('success');
        } else {
            banner.className = 'verification-banner verification-success';
            banner.textContent = 'Email berhasil diverifikasi! Anda sekarang bisa menggunakan semua converter.';
            banner.style.display = 'block';
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (banner) banner.style.display = 'none';
        }, 5000);
        
    } else if (error) {
        if (!banner) {
            banner = createVerificationBanner('error');
        } else {
            banner.className = 'verification-banner verification-error';
            banner.style.display = 'block';
        }
        
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

// ============================================================
// UI HELPERS
// ============================================================

/**
 * Show feedback message in modal.
 */
function showFeedback(feedbackId, message, isSuccess) {
    const el = document.getElementById(feedbackId);
    if (!el) return;
    
    el.textContent = message;
    el.className = isSuccess ? 'auth-feedback ok' : 'auth-feedback error';
    el.style.display = 'block';
    
    // Auto-hide after 5 seconds
    if (isSuccess) {
        setTimeout(() => {
            el.style.display = 'none';
        }, 5000);
    }
}

/**
 * Update auth strip to show login status.
 */
function updateAuthStrip(email) {
    const strip = document.getElementById('authStrip');
    if (!strip) return;
    
    strip.textContent = email && email.trim() 
        ? `Login sebagai ${email}` 
        : 'Belum login';
}

/**
 * Update UI based on login status (show/hide sign up, login, logout buttons).
 */
function updateLoginLogoutUI() {
    const authStrip = document.getElementById('authStrip');
    const signupBtn = document.getElementById('openSignupBtn');
    const loginBtn = document.getElementById('openLoginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    
    // Check if user is logged in from auth strip
    const isLoggedIn = authStrip && !authStrip.textContent.includes('Belum login');
    
    if (isLoggedIn) {
        if (signupBtn) signupBtn.style.display = 'none';
        if (loginBtn) loginBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'block';
    } else {
        if (signupBtn) signupBtn.style.display = 'block';
        if (loginBtn) loginBtn.style.display = 'block';
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
}

/**
 * Open modal.
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
}

/**
 * Close modal.
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
}

/**
 * Create verification banner element.
 */
function createVerificationBanner(type) {
    const container = document.querySelector('.panel-home');
    if (!container) return null;
    
    const banner = document.createElement('div');
    banner.id = 'verificationBanner';
    banner.className = `verification-banner verification-${type}`;
    
    if (type === 'success') {
        banner.textContent = 'Email berhasil diverifikasi! Anda sekarang bisa menggunakan semua converter.';
    } else {
        banner.textContent = 'Email belum diverifikasi. Silakan cek inbox Anda.';
    }
    
    // Insert before welcome label
    const welcomeLabel = container.querySelector('.welcome-label');
    if (welcomeLabel) {
        welcomeLabel.parentNode.insertBefore(banner, welcomeLabel);
    } else {
        container.insertBefore(banner, container.firstChild);
    }
    
    return banner;
}

// ============================================================
// MODAL BACKDROP HANDLING
// ============================================================

/**
 * Setup modal backdrop click handling.
 */
function setupModalBackdrops() {
    const signupModal = document.getElementById('signupModal');
    const loginModal = document.getElementById('loginModal');
    
    if (signupModal) {
        signupModal.addEventListener('click', (e) => {
            if (e.target === signupModal) closeModal('signupModal');
        });
    }
    
    if (loginModal) {
        loginModal.addEventListener('click', (e) => {
            if (e.target === loginModal) closeModal('loginModal');
        });
    }
}

/**
 * Setup top action button event listeners.
 */
function setupTopActionButtons() {
    const signupBtn = document.getElementById('openSignupBtn');
    const loginBtn = document.getElementById('openLoginBtn');
    const settingBtn = document.getElementById('openSettingBtn');
    
    if (signupBtn) {
        signupBtn.addEventListener('click', () => openModal('signupModal'));
    }
    
    if (loginBtn) {
        loginBtn.addEventListener('click', () => openModal('loginModal'));
    }
    
    if (settingBtn) {
        settingBtn.addEventListener('click', () => {
            alert('Halaman setting akan segera tersedia.');
        });
    }
}

// ============================================================
// PUBLIC API (for external use)
// ============================================================

// Export functions for use in other scripts or inline code
window.AuthModule = {
    init: initAuthModule,
    openModal,
    closeModal,
    showFeedback,
    updateAuthStrip,
    updateLoginLogoutUI,
    handleSignupSubmit,
    handleLoginSubmit,
    handleLogoutClick,
    handleResendClick,
};
