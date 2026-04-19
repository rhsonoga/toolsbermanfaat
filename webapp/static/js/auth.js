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
    // Always setup UI elements, even if Supabase is not configured
    setupTopActionButtons();
    setupModalBackdrops();
    setupModalCloseButtons();  // Setup close buttons - always needed
    updateLoginLogoutUI();
    checkVerificationMessage();
    
    const hasSupabase = window.supabaseReady === true;
    
    if (!hasSupabase) {
        console.warn('Auth Module: Supabase not configured on server');
        return;
    }
    
    // Only setup form handlers if Supabase is configured
    initSignupForm();
    initLoginForm();
    initLogoutButton();
    initResendButton();
}

// ============================================================
// MODAL CLOSE BUTTONS
// ============================================================

/**
 * Setup modal close buttons (Cancel buttons).
 * These are always needed, regardless of Supabase configuration.
 */
function setupModalCloseButtons() {
    const signupCloseBtn = document.getElementById('signupCloseBtn');
    if (signupCloseBtn) {
        signupCloseBtn.addEventListener('click', () => closeModal('signupModal'));
    }
    
    const loginCloseBtn = document.getElementById('loginCloseBtn');
    if (loginCloseBtn) {
        loginCloseBtn.addEventListener('click', () => closeModal('loginModal'));
    }
}

// ============================================================
// FORM HANDLERS
// ============================================================

/**
 * Compatibility wrapper: delegate signup initialization to modular auth file.
 */
function initSignupForm() {
    if (window.AuthSignupLogin && typeof window.AuthSignupLogin.initSignupForm === 'function') {
        window.AuthSignupLogin.initSignupForm();
        return;
    }

    console.warn('Auth Module: Signup/Login module not loaded (initSignupForm)');
}

/**
 * Compatibility wrapper for external callers.
 */
async function handleSignupSubmit(e) {
    if (window.AuthSignupLogin && typeof window.AuthSignupLogin.handleSignupSubmit === 'function') {
        return window.AuthSignupLogin.handleSignupSubmit(e);
    }

    console.warn('Auth Module: Signup/Login module not loaded (handleSignupSubmit)');
}

/**
 * Compatibility wrapper: delegate login initialization to modular auth file.
 */
function initLoginForm() {
    if (window.AuthSignupLogin && typeof window.AuthSignupLogin.initLoginForm === 'function') {
        window.AuthSignupLogin.initLoginForm();
        return;
    }

    console.warn('Auth Module: Signup/Login module not loaded (initLoginForm)');
}

/**
 * Compatibility wrapper for external callers.
 */
async function handleLoginSubmit(e) {
    if (window.AuthSignupLogin && typeof window.AuthSignupLogin.handleLoginSubmit === 'function') {
        return window.AuthSignupLogin.handleLoginSubmit(e);
    }

    console.warn('Auth Module: Signup/Login module not loaded (handleLoginSubmit)');
}

// ============================================================
// LOGOUT
// ============================================================

/**
 * Compatibility wrapper: delegate logout initialization to modular auth file.
 */
function initLogoutButton() {
    if (window.AuthLogout && typeof window.AuthLogout.initLogoutButton === 'function') {
        window.AuthLogout.initLogoutButton();
        return;
    }

    console.warn('Auth Module: Logout module not loaded (initLogoutButton)');
}

/**
 * Compatibility wrapper for external callers.
 */
async function handleLogoutClick(e) {
    if (window.AuthLogout && typeof window.AuthLogout.handleLogoutClick === 'function') {
        return window.AuthLogout.handleLogoutClick(e);
    }

    console.warn('Auth Module: Logout module not loaded (handleLogoutClick)');
}

// ============================================================
// VERIFICATION & RESEND
// ============================================================

/**
 * Compatibility wrapper: delegate resend initialization to modular auth file.
 */
function initResendButton() {
    if (window.AuthVerification && typeof window.AuthVerification.initResendButton === 'function') {
        window.AuthVerification.initResendButton();
        return;
    }

    console.warn('Auth Module: Verification module not loaded (initResendButton)');
}

/**
 * Compatibility wrapper for external callers.
 */
async function handleResendClick(e) {
    if (window.AuthVerification && typeof window.AuthVerification.handleResendClick === 'function') {
        return window.AuthVerification.handleResendClick(e);
    }

    console.warn('Auth Module: Verification module not loaded (handleResendClick)');
}

/**
 * Compatibility wrapper for verification message processing.
 */
function checkVerificationMessage() {
    if (window.AuthVerification && typeof window.AuthVerification.checkVerificationMessage === 'function') {
        return window.AuthVerification.checkVerificationMessage();
    }

    console.warn('Auth Module: Verification module not loaded (checkVerificationMessage)');
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

// Also export key functions globally for use in event listeners
window.openModal = openModal;
window.closeModal = closeModal;
window.initAuthModule = initAuthModule;
window.setupModalBackdrops = setupModalBackdrops;
window.setupTopActionButtons = setupTopActionButtons;
window.showFeedback = showFeedback;
window.updateAuthStrip = updateAuthStrip;
window.updateLoginLogoutUI = updateLoginLogoutUI;
window.createVerificationBanner = createVerificationBanner;

// ============================================================
// AUTO-INITIALIZATION
// ============================================================

// Auto-initialize auth module when DOM is ready
if (document.readyState === 'loading') {
    // DOM is still loading
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[Auth Module] DOM loaded, initializing...');
        initAuthModule();
    });
} else {
    // DOM is already loaded (script loaded after DOMContentLoaded)
    console.log('[Auth Module] DOM already loaded, initializing...');
    initAuthModule();
}
