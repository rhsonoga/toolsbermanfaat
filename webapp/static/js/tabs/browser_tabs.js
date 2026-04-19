(function () {
    function setBrowserTab(tabName) {
        const browserTabs = document.querySelectorAll('.browser-tab');
        const browserPages = document.querySelectorAll('.browser-page');

        browserTabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.browserTab === tabName));
        browserPages.forEach((page) => page.classList.toggle('active', page.dataset.browserPage === tabName));
    }

    function initBrowserTabs(defaultTab) {
        const browserTabs = document.querySelectorAll('.browser-tab');

        if (!browserTabs.length) return;

        browserTabs.forEach((tab) => {
            tab.addEventListener('click', function () {
                setBrowserTab(this.dataset.browserTab);
            });
        });

        setBrowserTab(defaultTab || 'kmz');
    }

    window.BrowserTabsModule = {
        initBrowserTabs,
        setBrowserTab,
    };
})();
