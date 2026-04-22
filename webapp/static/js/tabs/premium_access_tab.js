(function () {
    function initPremiumAccessTab() {
        if (!window.PremiumOverlayModule || typeof window.PremiumOverlayModule.initPremiumOverlay !== 'function') {
            return;
        }

        const wrappers = [
            { id: 'hpdb_panel_wrapper', fallback: 'not_login' },
            { id: 'boq_panel_wrapper', fallback: 'not_login' },
        ];

        wrappers.forEach(({ id, fallback }) => {
            const panelWrapper = document.getElementById(id);
            if (!panelWrapper) return;

            const authStatus = panelWrapper.getAttribute('data-auth-status') || fallback;
            window.PremiumOverlayModule.initPremiumOverlay(id, authStatus);
        });
    }

    window.PremiumAccessTabModule = {
        initPremiumAccessTab,
    };
})();
