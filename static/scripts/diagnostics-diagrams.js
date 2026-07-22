(function(window, document, jQuery) {
    'use strict';

    var labels = window.ospyDiagramLabels || {};
    var renderSequence = 0;
    var zoom = 1;
    var currentTopic = 'programs';

    function text(key, fallback) {
        return labels[key] || fallback || key;
    }

    function node(id, type, label) {
        return {id: id, type: type || 'process', label: label};
    }

    function edge(from, to, label) {
        return {from: from, to: to, label: label || ''};
    }

    function topicDefinitions() {
        return {
            programs: {
                description: text('programsDescription'),
                help: '/help#8',
                nodes: [
                    node('program', 'process', text('programDefinition')),
                    node('calculate', 'process', text('scheduleCalculation')),
                    node('valid', 'decision', text('runAllowed')),
                    node('blocked', 'error', text('blockedRun')),
                    node('queue', 'wait', text('runQueue')),
                    node('master', 'optional', text('masterStation')),
                    node('station', 'process', text('stationOutput')),
                    node('finish', 'success', text('runLog'))
                ],
                edges: [
                    edge('program', 'calculate'), edge('calculate', 'valid'),
                    edge('valid', 'blocked', text('no')), edge('valid', 'queue', text('yes')),
                    edge('queue', 'master', text('ifConfigured')), edge('master', 'station'),
                    edge('queue', 'station', text('withoutMaster')), edge('station', 'finish')
                ],
                links: {program: '/programs', blocked: '/log', finish: '/log'}
            },
            startDecision: {
                description: text('startDecisionDescription'),
                help: '/help#9',
                nodes: [
                    node('request', 'process', text('runRequest')),
                    node('enabled', 'decision', text('systemEnabled')),
                    node('mode', 'decision', text('correctMode')),
                    node('rain', 'decision', text('rainBlocking')),
                    node('sensor', 'decision', text('sensorBlocking')),
                    node('available', 'decision', text('stationAvailable')),
                    node('reject', 'error', text('runRejected')),
                    node('start', 'success', text('startStation'))
                ],
                edges: [
                    edge('request', 'enabled'), edge('enabled', 'reject', text('no')),
                    edge('enabled', 'mode', text('yes')), edge('mode', 'reject', text('no')),
                    edge('mode', 'rain', text('yes')), edge('rain', 'reject', text('blocked')),
                    edge('rain', 'sensor', text('clear')), edge('sensor', 'reject', text('blocked')),
                    edge('sensor', 'available', text('clear')), edge('available', 'reject', text('no')),
                    edge('available', 'start', text('yes'))
                ],
                links: {request: '/runonce', rain: '/options', sensor: '/sensors', start: '/'}
            },
            master: {
                description: text('masterDescription'),
                help: '/help#9',
                nodes: [
                    node('request', 'process', text('stationRun')),
                    node('assigned', 'decision', text('masterAssigned')),
                    node('pre', 'wait', text('masterPreDelay')),
                    node('masterOn', 'process', text('masterOn')),
                    node('stationOn', 'success', text('stationOn')),
                    node('stationOff', 'process', text('stationOff')),
                    node('post', 'wait', text('masterPostDelay')),
                    node('masterOff', 'success', text('masterOff')),
                    node('direct', 'optional', text('runWithoutMaster'))
                ],
                edges: [
                    edge('request', 'assigned'), edge('assigned', 'pre', text('yes')),
                    edge('assigned', 'direct', text('no')), edge('pre', 'masterOn'),
                    edge('masterOn', 'stationOn'), edge('stationOn', 'stationOff'),
                    edge('stationOff', 'post'), edge('post', 'masterOff'),
                    edge('direct', 'stationOn')
                ],
                links: {assigned: '/stations', pre: '/options', post: '/options'}
            },
            weather: {
                description: text('weatherDescription'),
                help: '/help#9',
                nodes: [
                    node('provider', 'decision', text('weatherProvider')),
                    node('openmeteo', 'optional', 'Open-Meteo'),
                    node('chmi', 'optional', 'CHMI'),
                    node('shmi', 'optional', 'SHMI'),
                    node('stormglass', 'optional', 'StormGlass'),
                    node('normalize', 'process', text('normalizeWeather')),
                    node('cache', 'wait', text('weatherCache')),
                    node('level', 'process', text('waterLevelAdjustment')),
                    node('consumers', 'success', text('weatherConsumers')),
                    node('fallback', 'error', text('cachedFallback'))
                ],
                edges: [
                    edge('provider', 'openmeteo'), edge('provider', 'chmi'),
                    edge('provider', 'shmi'), edge('provider', 'stormglass'),
                    edge('openmeteo', 'normalize'), edge('chmi', 'normalize'),
                    edge('shmi', 'normalize'), edge('stormglass', 'normalize'),
                    edge('normalize', 'cache'), edge('cache', 'level'),
                    edge('level', 'consumers'), edge('normalize', 'fallback', text('onError')),
                    edge('fallback', 'level')
                ],
                links: {provider: '/options#weatherSection', consumers: '/', level: '/programs'}
            },
            sensors: {
                description: text('sensorsDescription'),
                help: '/help#20',
                nodes: [
                    node('discover', 'process', text('sensorDiscovery')),
                    node('receive', 'process', text('receiveMeasurement')),
                    node('validate', 'decision', text('validMeasurement')),
                    node('reject', 'error', text('rejectMeasurement')),
                    node('store', 'process', text('updateSensor')),
                    node('rules', 'decision', text('sensorRules')),
                    node('continue', 'success', text('continueIrrigation')),
                    node('action', 'error', text('sensorAction')),
                    node('notify', 'optional', text('logAndNotify'))
                ],
                edges: [
                    edge('discover', 'receive'), edge('receive', 'validate'),
                    edge('validate', 'reject', text('no')), edge('validate', 'store', text('yes')),
                    edge('store', 'rules'), edge('rules', 'continue', text('normal')),
                    edge('rules', 'action', text('threshold')), edge('action', 'notify')
                ],
                links: {discover: '/sensors?search', store: '/sensors', notify: '/log'}
            },
            plugins: {
                description: text('pluginsDescription'),
                help: '/help#1',
                nodes: [
                    node('archive', 'process', text('pluginArchive')),
                    node('manifest', 'decision', 'plugin.json'),
                    node('compatibility', 'decision', text('compatibilityCheck')),
                    node('permissions', 'decision', text('permissionApproval')),
                    node('preflight', 'decision', text('preactivationTest')),
                    node('dependencies', 'wait', text('dependencyOrder')),
                    node('start', 'success', text('startPlugin')),
                    node('health', 'process', 'health()'),
                    node('stop', 'process', text('safeStop')),
                    node('blocked', 'error', text('installationBlocked'))
                ],
                edges: [
                    edge('archive', 'manifest'), edge('manifest', 'blocked', text('invalid')),
                    edge('manifest', 'compatibility', text('valid')), edge('compatibility', 'blocked', text('incompatible')),
                    edge('compatibility', 'permissions', text('compatible')), edge('permissions', 'blocked', text('notApproved')),
                    edge('permissions', 'preflight', text('approved')), edge('preflight', 'blocked', text('failed')),
                    edge('preflight', 'dependencies', text('passed')), edge('dependencies', 'start'),
                    edge('start', 'health'), edge('health', 'stop', text('shutdown'))
                ],
                links: {archive: '/plugins_install', permissions: '/plugins_manage', health: '/diagnostics'}
            },
            update: {
                description: text('updateDescription'),
                help: '/help#1',
                nodes: [
                    node('channel', 'decision', text('updateChannel')),
                    node('fetch', 'process', text('fetchRevision')),
                    node('tests', 'decision', text('updateChecks')),
                    node('prepare', 'process', text('safeOutputShutdown')),
                    node('checkout', 'process', text('installCommit')),
                    node('restart', 'wait', text('restartOSPy')),
                    node('watchdog', 'decision', text('healthyStart')),
                    node('confirm', 'success', text('confirmUpdate')),
                    node('rollback', 'error', text('automaticRollback'))
                ],
                edges: [
                    edge('channel', 'fetch'), edge('fetch', 'tests'),
                    edge('tests', 'prepare', text('passed')), edge('tests', 'rollback', text('failed')),
                    edge('prepare', 'checkout'), edge('checkout', 'restart'),
                    edge('restart', 'watchdog'), edge('watchdog', 'confirm', text('yes')),
                    edge('watchdog', 'rollback', text('no'))
                ],
                links: {channel: '/plugins/system_update', tests: '/help#3', rollback: '/plugins/system_update'}
            },
            storage: {
                description: text('storageDescription'),
                help: '/help#9',
                nodes: [
                    node('change', 'process', text('settingsChange')),
                    node('validate', 'decision', text('validateSettings')),
                    node('sqlite', 'process', text('sqlitePrimary')),
                    node('atomic', 'process', text('atomicWrite')),
                    node('verify', 'decision', text('checksumVerification')),
                    node('shelve', 'optional', text('shelveFallback')),
                    node('backup', 'success', text('verifiedSnapshot')),
                    node('recover', 'error', text('automaticRecovery'))
                ],
                edges: [
                    edge('change', 'validate'), edge('validate', 'sqlite', text('valid')),
                    edge('validate', 'recover', text('invalid')), edge('sqlite', 'atomic'),
                    edge('atomic', 'verify'), edge('verify', 'shelve', text('passed')),
                    edge('shelve', 'backup'), edge('verify', 'recover', text('failed')),
                    edge('recover', 'shelve')
                ],
                links: {change: '/options#settingsStorageSection', backup: '/options#systemBackupSection', recover: '/diagnostics'}
            },
            backup: {
                description: text('backupDescription'),
                help: '/help#9',
                nodes: [
                    node('create', 'process', text('createBackup')),
                    node('collect', 'process', text('collectBackupData')),
                    node('validate', 'decision', text('validateBackup')),
                    node('download', 'success', text('downloadArchive')),
                    node('upload', 'process', text('uploadBackup')),
                    node('verify', 'decision', text('verifyRestore')),
                    node('safety', 'wait', text('createSafetyBackup')),
                    node('apply', 'process', text('applyRestore')),
                    node('restart', 'success', text('restartAndVerify')),
                    node('reject', 'error', text('rejectArchive'))
                ],
                edges: [
                    edge('create', 'collect'), edge('collect', 'validate'),
                    edge('validate', 'download', text('valid')), edge('validate', 'reject', text('invalid')),
                    edge('upload', 'verify'), edge('verify', 'safety', text('valid')),
                    edge('verify', 'reject', text('invalid')), edge('safety', 'apply'),
                    edge('apply', 'restart')
                ],
                links: {create: '/options#systemBackupSection', upload: '/options#systemBackupSection', restart: '/diagnostics'}
            }
        };
    }

    function escapeLabel(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/[\r\n]+/g, ' ');
    }

    function nodeSyntax(item) {
        var label = escapeLabel(item.label);
        if (item.type === 'decision') return item.id + '{"' + label + '"}';
        if (item.type === 'wait') return item.id + '(["' + label + '"])';
        if (item.type === 'optional') return item.id + '[["' + label + '"]]';
        return item.id + '["' + label + '"]';
    }

    function buildSource(topic) {
        var lines = ['flowchart LR'];
        topic.nodes.forEach(function(item) {
            lines.push('  ' + nodeSyntax(item) + ':::' + item.type);
        });
        topic.edges.forEach(function(item) {
            var connector = item.label ? '-->|"' + escapeLabel(item.label) + '"|' : '-->';
            lines.push('  ' + item.from + connector + item.to);
        });
        lines.push('  classDef process fill:#e7f0ff,stroke:#2f5e9e,color:#17233b,stroke-width:2px');
        lines.push('  classDef decision fill:#fff3cd,stroke:#b77900,color:#4b3500,stroke-width:2px');
        lines.push('  classDef wait fill:#fff0d9,stroke:#d48200,color:#4d2e00,stroke-width:2px');
        lines.push('  classDef success fill:#e4f4e4,stroke:#2e8b32,color:#173a19,stroke-width:2px');
        lines.push('  classDef error fill:#fde6e8,stroke:#b51f2e,color:#591018,stroke-width:2px');
        lines.push('  classDef optional fill:#eceff4,stroke:#6d7788,color:#2f3540,stroke-width:2px');
        return lines.join('\n');
    }

    function applyZoom() {
        var svg = document.querySelector('#ospyDiagramCanvas svg');
        if (!svg) return;
        svg.style.maxWidth = 'none';
        svg.style.width = Math.round(zoom * 100) + '%';
        svg.style.height = 'auto';
        jQuery('#diagramZoomValue').text(Math.round(zoom * 100) + ' %');
    }

    function attachNodeLinks(svg, links) {
        if (!svg || !links) return;
        Array.prototype.forEach.call(svg.querySelectorAll('.node'), function(element) {
            Object.keys(links).some(function(nodeId) {
                if (element.id.indexOf('-' + nodeId + '-') === -1) return false;
                element.classList.add('ospyDiagramLinkedNode');
                element.setAttribute('role', 'link');
                element.setAttribute('tabindex', '0');
                element.setAttribute('aria-label', text('openRelatedPage') + ': ' + element.textContent.trim());
                var openLink = function() { window.location.href = links[nodeId]; };
                element.addEventListener('click', openLink);
                element.addEventListener('keydown', function(event) {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        openLink();
                    }
                });
                return true;
            });
        });
    }

    function renderTopic(topicId) {
        var topics = topicDefinitions();
        var topic = topics[topicId] || topics.programs;
        currentTopic = topics[topicId] ? topicId : 'programs';
        zoom = 1;
        jQuery('#diagramDescription').text(topic.description || '');
        jQuery('#diagramRelatedHelp').attr('href', topic.help || '/help');
        jQuery('#ospyDiagramCanvas').empty().attr('aria-busy', 'true');
        jQuery('#diagramRenderError').hide().text('');

        if (!window.mermaid || typeof window.mermaid.render !== 'function') {
            jQuery('#diagramRenderError').text(text('rendererUnavailable')).show();
            return;
        }

        renderSequence += 1;
        window.mermaid.render('ospyDiagramSvg' + renderSequence, buildSource(topic)).then(function(result) {
            var canvas = document.getElementById('ospyDiagramCanvas');
            canvas.innerHTML = result.svg;
            canvas.setAttribute('aria-busy', 'false');
            if (result.bindFunctions) result.bindFunctions(canvas);
            attachNodeLinks(canvas.querySelector('svg'), topic.links);
            applyZoom();
        }).catch(function(error) {
            jQuery('#ospyDiagramCanvas').attr('aria-busy', 'false');
            jQuery('#diagramRenderError').text(text('renderFailed') + ': ' + String(error)).show();
        });
    }

    function svgBlob() {
        var svg = document.querySelector('#ospyDiagramCanvas svg');
        if (!svg) return null;
        var copy = svg.cloneNode(true);
        copy.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        return new Blob([new XMLSerializer().serializeToString(copy)], {type: 'image/svg+xml;charset=utf-8'});
    }

    function downloadBlob(blob, extension) {
        if (!blob) return;
        var url = URL.createObjectURL(blob);
        var anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = 'ospy-' + currentTopic + '.' + extension;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        window.setTimeout(function() { URL.revokeObjectURL(url); }, 1000);
    }

    function downloadPng() {
        var svg = document.querySelector('#ospyDiagramCanvas svg');
        var blob = svgBlob();
        if (!svg || !blob) return;
        var viewBox = (svg.getAttribute('viewBox') || '0 0 1200 700').split(/\s+/).map(Number);
        var width = Math.max(1, viewBox[2] || 1200);
        var height = Math.max(1, viewBox[3] || 700);
        var scale = Math.min(2, 3000 / Math.max(width, height));
        var canvas = document.createElement('canvas');
        canvas.width = Math.round(width * scale);
        canvas.height = Math.round(height * scale);
        var context = canvas.getContext('2d');
        context.fillStyle = '#ffffff';
        context.fillRect(0, 0, canvas.width, canvas.height);
        var image = new Image();
        var url = URL.createObjectURL(blob);
        image.onload = function() {
            context.drawImage(image, 0, 0, canvas.width, canvas.height);
            URL.revokeObjectURL(url);
            canvas.toBlob(function(png) { downloadBlob(png, 'png'); }, 'image/png');
        };
        image.onerror = function() {
            URL.revokeObjectURL(url);
            jQuery('#diagramRenderError').text(text('pngFailed')).show();
        };
        image.src = url;
    }

    function toggleWide(forceOff) {
        var section = jQuery('#systemDiagramSection');
        var active = forceOff ? false : !section.hasClass('diagramWideMode');
        section.toggleClass('diagramWideMode', active);
        jQuery('body').toggleClass('diagramWideBody', active);
        jQuery('#diagramWide').text(active ? text('exitWideView') : text('wideView'));
    }

    jQuery(function() {
        if (!document.getElementById('systemDiagramSection')) return;
        if (window.mermaid) {
            window.mermaid.initialize({
                startOnLoad: false,
                securityLevel: 'strict',
                theme: 'neutral',
                flowchart: {htmlLabels: false, curve: 'basis', useMaxWidth: false}
            });
        }

        jQuery('#diagramTopic').on('change', function() { renderTopic(this.value); });
        jQuery('#diagramZoomIn').on('click', function() { zoom = Math.min(2.5, zoom + 0.2); applyZoom(); });
        jQuery('#diagramZoomOut').on('click', function() { zoom = Math.max(0.5, zoom - 0.2); applyZoom(); });
        jQuery('#diagramZoomReset').on('click', function() { zoom = 1; applyZoom(); });
        jQuery('#diagramWide').on('click', function() { toggleWide(false); });
        jQuery('#diagramPrint').on('click', function() {
            document.body.classList.add('diagramPrintMode');
            window.print();
        });
        window.addEventListener('afterprint', function() { document.body.classList.remove('diagramPrintMode'); });
        jQuery('#diagramDownloadSvg').on('click', function() { downloadBlob(svgBlob(), 'svg'); });
        jQuery('#diagramDownloadPng').on('click', downloadPng);
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && jQuery('#systemDiagramSection').hasClass('diagramWideMode')) toggleWide(true);
        });
        renderTopic(jQuery('#diagramTopic').val() || 'programs');
    });
})(window, document, jQuery);
