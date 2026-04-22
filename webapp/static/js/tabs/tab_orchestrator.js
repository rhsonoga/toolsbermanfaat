(function () {
    function initTabModules() {
        const activeMenu = document.body?.dataset?.activeMenu || 'home';
        const kmzMenus = new Set(['cable', 'hpdb', 'boq']);
        const defaultBrowserTab = kmzMenus.has(activeMenu) ? 'kmz' : 'history';

        if (window.BrowserTabsModule && typeof window.BrowserTabsModule.initBrowserTabs === 'function') {
            window.BrowserTabsModule.initBrowserTabs(defaultBrowserTab);
        }

        if (window.KmzConverterTabModule && typeof window.KmzConverterTabModule.initKmzConverterTab === 'function') {
            window.KmzConverterTabModule.initKmzConverterTab(kmzMenus.has(activeMenu) ? activeMenu : 'cable');
        }

        if (window.PremiumOverlayModule && typeof window.PremiumOverlayModule.initPremiumOverlay === 'function') {
            const hpdbWrapper = document.getElementById('hpdb_panel_wrapper');
            const boqWrapper = document.getElementById('boq_panel_wrapper');
            
            if (hpdbWrapper) {
                const hpdbAuthStatus = hpdbWrapper.getAttribute('data-auth-status') || 'not_login';
                window.PremiumOverlayModule.initPremiumOverlay('hpdb_panel_wrapper', hpdbAuthStatus);
            }
            
            if (boqWrapper) {
                const boqAuthStatus = boqWrapper.getAttribute('data-auth-status') || 'not_login';
                window.PremiumOverlayModule.initPremiumOverlay('boq_panel_wrapper', boqAuthStatus);
            }
        }

        if (window.TutorialTabModule && typeof window.TutorialTabModule.initTutorialTab === 'function') {
            window.TutorialTabModule.initTutorialTab();
        }

        if (window.GisTabModule && typeof window.GisTabModule.initGisTab === 'function') {
            window.GisTabModule.initGisTab();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTabModules);
    } else {
        initTabModules();
    }
})();
