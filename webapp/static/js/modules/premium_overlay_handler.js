(function () {
    /**
     * Premium Overlay Handler Module
     * 
     * Manages premium overlay display for protected panels (HPDB, BOQ).
     * Shows overlay with signup/login prompts when user is not verified.
     * 
     * Usage:
     *   PremiumOverlayModule.initPremiumOverlay(panelId, authStatus)
     *   
     * auth status values:
     *   'verified': User is logged in and verified - no overlay
     *   'need_verify': User is logged in but not verified - show overlay
     *   'not_login': User is not logged in - show overlay
     */

    function initPremiumOverlay(panelId, authStatus) {
        if (!panelId) return;
        
        const panelElement = document.getElementById(panelId);
        if (!panelElement) return;

        // If user is verified, don't show overlay
        if (authStatus === 'verified') {
            removePremiumOverlay(panelElement);
            return;
        }

        // For not_login or need_verify, apply overlay
        applyPremiumOverlay(panelElement, authStatus);
    }

    function applyPremiumOverlay(panelElement, authStatus) {
        if (!panelElement.classList.contains('panel-wrapper')) {
            panelElement.classList.add('panel-wrapper');
        }

        const contentWrapper = ensurePanelContentWrapper(panelElement);
        contentWrapper.classList.add('blurred');

        const existingOverlay = getDirectChildByClass(panelElement, 'panel-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'panel-overlay active';

        // Create content
        const content = document.createElement('div');
        content.className = 'premium-content';

        // Icon
        const icon = document.createElement('span');
        icon.className = 'premium-icon';
        icon.textContent = '✨';

        // Title
        const title = document.createElement('div');
        title.className = 'premium-title';
        title.textContent = 'UPGRADE TO PREMIUM';

        // Subtitle
        const subtitle = document.createElement('div');
        subtitle.className = 'premium-subtitle';
        if (authStatus === 'need_verify') {
            subtitle.textContent = 'Verifikasi email Anda untuk mengakses tool ini.';
        } else {
            subtitle.textContent = 'Buat akun untuk mengakses tool premium ini.';
        }

        // Actions container
        const actions = document.createElement('div');
        actions.className = 'premium-actions';

        // Signup button
        const signupBtn = document.createElement('a');
        signupBtn.className = 'premium-signup-btn';
        signupBtn.href = '#signup';
        const primaryAction = authStatus === 'need_verify' ? 'verify' : 'signup';
        signupBtn.textContent = authStatus === 'need_verify' ? 'VERIFIKASI EMAIL' : 'SIGN UP';
        signupBtn.addEventListener('click', (e) => {
            e.preventDefault();
            triggerAuthAction(primaryAction);
        });

        actions.appendChild(signupBtn);

        // Login link (only for not_login)
        if (authStatus === 'not_login') {
            const loginText = document.createElement('div');
            loginText.style.marginTop = '8px';
            loginText.style.fontSize = '12px';
            loginText.style.color = '#b0b0b0';

            const loginLink = document.createElement('a');
            loginLink.className = 'premium-login-link';
            loginLink.href = '#login';
            loginLink.textContent = 'Sudah punya akun? Login di sini';
            loginLink.addEventListener('click', (e) => {
                e.preventDefault();
                triggerAuthAction('login');
            });

            loginText.appendChild(loginLink);
            actions.appendChild(loginText);
        }

        // Assemble content
        content.appendChild(icon);
        content.appendChild(title);
        content.appendChild(subtitle);
        content.appendChild(actions);

        // Assemble overlay
        overlay.appendChild(content);

        // Add overlay to panel as a sibling of the blurred content
        panelElement.appendChild(overlay);
    }

    function ensurePanelContentWrapper(panelElement) {
        let contentWrapper = getDirectChildByClass(panelElement, 'panel-content');

        if (contentWrapper) {
            return contentWrapper;
        }

        contentWrapper = document.createElement('div');
        contentWrapper.className = 'panel-content';

        const childNodes = Array.from(panelElement.children);
        childNodes.forEach((child) => {
            if (child.classList.contains('panel-overlay')) {
                return;
            }
            contentWrapper.appendChild(child);
        });

        panelElement.appendChild(contentWrapper);
        return contentWrapper;
    }

    function removePremiumOverlay(panelElement) {
        const overlay = getDirectChildByClass(panelElement, 'panel-overlay');
        if (overlay) {
            overlay.remove();
        }

        const contentWrapper = getDirectChildByClass(panelElement, 'panel-content');
        if (contentWrapper) {
            contentWrapper.classList.remove('blurred');
        }
    }

    function getDirectChildByClass(panelElement, className) {
        return Array.from(panelElement.children).find((child) => child.classList.contains(className)) || null;
    }

    function triggerAuthAction(action) {
        // Normalize action and open the corresponding auth modal.
        let normalizedAction = action;
        if (action === 'not_login') normalizedAction = 'signup';
        if (action === 'need_verify') normalizedAction = 'verify';

        if (typeof window.openModal === 'function') {
            if (normalizedAction === 'signup') {
                window.openModal('signupModal');
            } else {
                // login + verify both use login modal flow
                window.openModal('loginModal');
            }
        }

        // Keep custom event for future hooks.
        window.dispatchEvent(new CustomEvent('auth:action', {
            detail: { action: normalizedAction }
        }));
    }

    // Expose module to window
    window.PremiumOverlayModule = {
        initPremiumOverlay: initPremiumOverlay,
        applyPremiumOverlay: applyPremiumOverlay,
        removePremiumOverlay: removePremiumOverlay,
        triggerAuthAction: triggerAuthAction
    };
})();
