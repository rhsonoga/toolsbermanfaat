(function () {
    function initTabModules() {
        const activeMenu = document.body?.dataset?.activeMenu || 'home';

        if (window.BrowserTabsModule && typeof window.BrowserTabsModule.initBrowserTabs === 'function') {
            window.BrowserTabsModule.initBrowserTabs('kmz');
        }

        if (window.KmzConverterTabModule && typeof window.KmzConverterTabModule.initKmzConverterTab === 'function') {
            window.KmzConverterTabModule.initKmzConverterTab(activeMenu);
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
