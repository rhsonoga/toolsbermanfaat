(function () {
    function initKmzConverterTab(activeFromServer) {
        const menuBtns = document.querySelectorAll('.menu-btn');
        const panels = document.querySelectorAll('.panel');

        function setActive(panelName) {
            menuBtns.forEach((btn) => btn.classList.toggle('active', btn.dataset.panel === panelName));
            panels.forEach((panel) => {
                panel.style.display = panel.dataset.panel === panelName ? 'block' : 'none';
            });
        }

        if (menuBtns.length && panels.length) {
            menuBtns.forEach((btn) => {
                btn.addEventListener('click', function () {
                    setActive(this.dataset.panel);
                });
            });

            setActive(activeFromServer || 'home');
            if (activeFromServer === 'home' || !activeFromServer) {
                const homePanel = document.querySelector('.panel-home');
                if (homePanel) {
                    homePanel.style.display = 'block';
                }
                menuBtns.forEach((btn) => btn.classList.remove('active'));
            }
        }

        const cableName = document.getElementById('cable_name');
        const cableType = document.getElementById('cable_type');
        const cableCat = document.getElementById('cable_cat');
        const cableRoute = document.getElementById('cable_route');
        const cableFdt = document.getElementById('cable_fdt');
        const cableFat = document.getElementById('cable_fat');
        const cableCode = document.getElementById('cable_code');
        const cableOlt = document.getElementById('cable_olt');
        const cableSeg = document.getElementById('cable_seg');
        const cableOutput = document.getElementById('cableOutput');
        const generateBtn = document.getElementById('generateBtn');
        const clearBtn = document.getElementById('clearBtn');
        const topToggle = document.getElementById('topToggle');

        function syncCableHidden() {
            const postLineName = document.getElementById('post_line_name');
            const postCableType = document.getElementById('post_cable_type');
            const postCableCat = document.getElementById('post_cable_cat');
            const postCableRoute = document.getElementById('post_cable_route');
            const postCableFdt = document.getElementById('post_cable_fdt');
            const postCableFat = document.getElementById('post_cable_fat');
            const postCableCode = document.getElementById('post_cable_code');
            const postCableOlt = document.getElementById('post_cable_olt');
            const postCableSeg = document.getElementById('post_cable_seg');

            if (!cableName || !cableType || !cableCat || !cableRoute || !cableFdt || !cableFat || !cableCode || !cableOlt || !cableSeg) return;
            if (!postLineName || !postCableType || !postCableCat || !postCableRoute || !postCableFdt || !postCableFat || !postCableCode || !postCableOlt || !postCableSeg) return;

            postLineName.value = cableName.value;
            postCableType.value = cableType.value;
            postCableCat.value = cableCat.value;
            postCableRoute.value = cableRoute.value;
            postCableFdt.value = cableFdt.value;
            postCableFat.value = cableFat.value;
            postCableCode.value = cableCode.value;
            postCableOlt.value = cableOlt.value;
            postCableSeg.value = cableSeg.value;
        }

        function updateCableUIState() {
            if (!cableName || !cableFdt || !cableCode || !cableOlt || !cableSeg) return;

            const mode = cableName.value || '';
            const states = { fdt: false, fat: false, olt: false, code: false, seg: false };
            if (mode.includes('MAINFEEDER') || mode.includes('HUBFEEDER')) {
                states.fdt = true;
                states.code = true;
                cableFdt.value = '0';
                cableCode.value = '';
            } else if (mode.includes('SUBFEEDER')) {
                states.seg = true;
                cableSeg.value = '';
            } else if (['LINE A', 'LINE B', 'LINE C', 'LINE D'].some((x) => mode.includes(x))) {
                states.olt = true;
                states.seg = true;
                cableOlt.value = '';
                cableSeg.value = '';
            }
            cableFdt.disabled = states.fdt;
            cableCode.disabled = states.code;
            cableOlt.disabled = states.olt;
            cableSeg.disabled = states.seg;
            validateCable();
        }

        function validateCable() {
            if (!cableName || !cableRoute || !cableFat || !cableType || !generateBtn || !cableFdt || !cableCode || !cableOlt || !cableSeg) return;

            const mode = cableName.value || '';
            let required = [cableRoute.value, cableFat.value, cableType.value];
            if (mode.includes('SUBFEEDER')) {
                required = required.concat([cableFdt.value, cableCode.value, cableOlt.value]);
            } else if (mode.includes('MAINFEEDER') || mode.includes('HUBFEEDER')) {
                required = required.concat([cableOlt.value, cableSeg.value]);
            } else if (mode.includes('LINE')) {
                required = required.concat([cableFdt.value, cableCode.value]);
            }
            generateBtn.disabled = !required.every(Boolean);
        }

        [cableName, cableType, cableCat, cableRoute, cableFdt, cableFat, cableCode, cableOlt, cableSeg].forEach((el) => {
            if (!el) return;
            el.addEventListener('input', () => {
                syncCableHidden();
                validateCable();
            });
            el.addEventListener('change', () => {
                syncCableHidden();
                validateCable();
                updateCableUIState();
            });
        });

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                [cableRoute, cableFdt, cableFat, cableCode, cableOlt, cableSeg].forEach((el) => {
                    if (el) el.value = '';
                });
                if (cableCat) cableCat.selectedIndex = 0;
                if (cableName && cableName.options.length) cableName.selectedIndex = 0;
                if (cableType && cableType.options.length) cableType.selectedIndex = 0;
                if (cableOutput) cableOutput.value = '';
                syncCableHidden();
                updateCableUIState();
            });
        }

        if (topToggle) {
            topToggle.addEventListener('change', () => {
                document.body.classList.toggle('top-mode', topToggle.checked);
            });
        }

        if (generateBtn) {
            generateBtn.addEventListener('click', syncCableHidden);
        }

        const oltModal = document.getElementById('oltModal');
        const oltNotes = document.getElementById('oltNotes');
        const oltListBtn = document.getElementById('oltListBtn');
        const oltSaveBtn = document.getElementById('oltSaveBtn');
        const oltCloseBtn = document.getElementById('oltCloseBtn');

        if (oltListBtn && oltModal && oltNotes) {
            oltListBtn.addEventListener('click', () => {
                oltNotes.value = localStorage.getItem('olt_notes') || '';
                oltModal.style.display = 'flex';
                oltModal.setAttribute('aria-hidden', 'false');
            });
        }

        if (oltSaveBtn && oltModal && oltNotes) {
            oltSaveBtn.addEventListener('click', () => {
                localStorage.setItem('olt_notes', oltNotes.value || '');
                oltModal.style.display = 'none';
                oltModal.setAttribute('aria-hidden', 'true');
            });
        }

        if (oltCloseBtn && oltModal) {
            oltCloseBtn.addEventListener('click', () => {
                oltModal.style.display = 'none';
                oltModal.setAttribute('aria-hidden', 'true');
            });
        }

        if (oltModal) {
            oltModal.addEventListener('click', (e) => {
                if (e.target === oltModal) {
                    oltModal.style.display = 'none';
                    oltModal.setAttribute('aria-hidden', 'true');
                }
            });
        }

        function bindFileMirror(fileInputId, displayId) {
            const input = document.getElementById(fileInputId);
            const display = document.getElementById(displayId);
            if (!input || !display) return;
            input.addEventListener('change', () => {
                display.value = input.files && input.files.length ? input.files[0].name : '';
            });
        }

        bindFileMirror('hpdb_source_file', 'hpdb_source_display');
        bindFileMirror('hpdb_basic_file', 'hpdb_path_display');
        bindFileMirror('boq_source_file', 'boq_source_display');

        const hpdbBrowseBtn = document.getElementById('hpdbBrowseBtn');
        const hpdbBasicBrowseBtn = document.getElementById('hpdbBasicBrowseBtn');
        const boqBrowseBtn = document.getElementById('boqBrowseBtn');

        if (hpdbBrowseBtn) {
            hpdbBrowseBtn.addEventListener('click', () => {
                const input = document.getElementById('hpdb_source_file');
                if (input) input.click();
            });
        }

        if (hpdbBasicBrowseBtn) {
            hpdbBasicBrowseBtn.addEventListener('click', () => {
                const input = document.getElementById('hpdb_basic_file');
                if (input) input.click();
            });
        }

        if (boqBrowseBtn) {
            boqBrowseBtn.addEventListener('click', () => {
                const input = document.getElementById('boq_source_file');
                if (input) input.click();
            });
        }

        const hpdbSourceFile = document.getElementById('hpdb_source_file');
        if (hpdbSourceFile) {
            hpdbSourceFile.addEventListener('change', () => {
                const file = hpdbSourceFile.files[0];
                const step2 = document.getElementById('hpdb_source_file_step2');
                const step3 = document.getElementById('hpdb_source_file_step3');
                const display = document.getElementById('hpdb_source_display');

                if (step2) step2.files = hpdbSourceFile.files;
                if (step3) step3.files = hpdbSourceFile.files;
                if (display) display.value = file ? file.name : '';
            });
        }

        const boqSourceFile = document.getElementById('boq_source_file');
        if (boqSourceFile) {
            boqSourceFile.addEventListener('change', () => {
                const file = boqSourceFile.files[0];
                const display = document.getElementById('boq_source_display');
                if (display) display.value = file ? file.name : '';
            });
        }

        updateCableUIState();
        syncCableHidden();
        validateCable();
    }

    window.KmzConverterTabModule = {
        initKmzConverterTab,
    };
})();
