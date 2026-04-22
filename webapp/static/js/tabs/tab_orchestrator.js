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

        if (window.PremiumAccessTabModule && typeof window.PremiumAccessTabModule.initPremiumAccessTab === 'function') {
            window.PremiumAccessTabModule.initPremiumAccessTab();
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
