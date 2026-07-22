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
            },
            webSecurity: {
                description: text('webSecurityDescription'),
                help: '/help#7',
                nodes: [
                    node('request', 'process', text('browserRequest')),
                    node('https', 'decision', text('httpsActive')),
                    node('transport', 'success', text('encryptedTransport')),
                    node('anonymous', 'decision', text('authenticationRequired')),
                    node('login', 'process', text('verifyCredentials')),
                    node('lockout', 'decision', text('bruteForceAllowed')),
                    node('secondFactor', 'optional', text('secondFactorCheck')),
                    node('role', 'decision', text('roleAllowsPage')),
                    node('csrf', 'decision', text('csrfRequiredForChange')),
                    node('allow', 'success', text('serveAuthorizedPage')),
                    node('reject', 'error', text('rejectAndAudit')),
                    node('warning', 'error', text('unencryptedOrAnonymous'))
                ],
                edges: [
                    edge('request', 'https'), edge('https', 'transport', text('yes')),
                    edge('https', 'warning', text('no')), edge('transport', 'anonymous'),
                    edge('warning', 'anonymous'), edge('anonymous', 'login', text('yes')),
                    edge('anonymous', 'role', text('no')), edge('login', 'lockout'),
                    edge('lockout', 'reject', text('blocked')), edge('lockout', 'secondFactor', text('allowed')),
                    edge('secondFactor', 'role'), edge('role', 'reject', text('no')),
                    edge('role', 'csrf', text('yes')), edge('csrf', 'reject', text('invalid')),
                    edge('csrf', 'allow', text('valid'))
                ],
                links: {https: '/options', login: '/login', secondFactor: '/twofactor', role: '/options', reject: '/log'}
            },
            https: {
                description: text('httpsDescription'),
                help: '/help#9',
                nodes: [
                    node('setting', 'process', text('httpsConfiguration')),
                    node('source', 'decision', text('certificateSource')),
                    node('own', 'optional', text('ownCertificate')),
                    node('letsencrypt', 'optional', "Let's Encrypt"),
                    node('files', 'decision', text('certificateFilesValid')),
                    node('listener', 'process', text('startHttpsListener')),
                    node('handshake', 'decision', text('tlsHandshakeValid')),
                    node('encrypted', 'success', text('encryptedConnection')),
                    node('proxy', 'optional', text('reverseProxyHeaders')),
                    node('fallback', 'error', text('httpsFallbackWarning')),
                    node('browserError', 'error', text('browserCertificateWarning'))
                ],
                edges: [
                    edge('setting', 'source'), edge('source', 'own'), edge('source', 'letsencrypt'),
                    edge('own', 'files'), edge('letsencrypt', 'files'),
                    edge('files', 'listener', text('valid')), edge('files', 'fallback', text('invalid')),
                    edge('listener', 'handshake'), edge('handshake', 'encrypted', text('yes')),
                    edge('handshake', 'browserError', text('no')), edge('encrypted', 'proxy', text('optional'))
                ],
                links: {setting: '/options', files: '/options', fallback: '/diagnostics'}
            },
            twoFactor: {
                description: text('twoFactorDescription'),
                help: '/help#2',
                nodes: [
                    node('password', 'process', text('usernameAndPassword')),
                    node('primary', 'decision', text('primaryCredentialsValid')),
                    node('enabled', 'decision', text('twoFactorEnabled')),
                    node('method', 'decision', text('selectedSecondFactor')),
                    node('totp', 'optional', text('totpCodeAndClock')),
                    node('email', 'optional', text('emailOneTimeCode')),
                    node('backup', 'optional', text('oneTimeBackupCode')),
                    node('verify', 'decision', text('secondFactorValid')),
                    node('session', 'success', text('createAuthenticatedSession')),
                    node('reject', 'error', text('rejectAndAudit')),
                    node('revoke', 'process', text('revokeRememberedLogins'))
                ],
                edges: [
                    edge('password', 'primary'), edge('primary', 'reject', text('no')),
                    edge('primary', 'enabled', text('yes')), edge('enabled', 'session', text('no')),
                    edge('enabled', 'method', text('yes')), edge('method', 'totp'),
                    edge('method', 'email'), edge('method', 'backup'),
                    edge('totp', 'verify'), edge('email', 'verify'), edge('backup', 'verify'),
                    edge('verify', 'session', text('yes')), edge('verify', 'reject', text('no')),
                    edge('revoke', 'password')
                ],
                links: {password: '/login', enabled: '/twofactor', email: '/plugins/email_notifications_ssl', reject: '/log', revoke: '/options'}
            },
            securityTokens: {
                description: text('securityTokensDescription'),
                help: '/help#7',
                nodes: [
                    node('page', 'process', text('authenticatedFormPage')),
                    node('sessionToken', 'process', text('sessionCookie')),
                    node('csrfToken', 'process', text('csrfFormToken')),
                    node('submit', 'process', text('stateChangingRequest')),
                    node('sessionValid', 'decision', text('sessionStillValid')),
                    node('csrfValid', 'decision', text('csrfTokenMatches')),
                    node('apply', 'success', text('applyAndAuditChange')),
                    node('reject', 'error', text('rejectExpiredOrInvalidToken')),
                    node('fullLogin', 'process', text('successfulFullLogin')),
                    node('remember', 'optional', text('randomRememberMeToken')),
                    node('hash', 'process', text('storeTokenHashOnly')),
                    node('cookie', 'wait', text('secureRememberMeCookie')),
                    node('restore', 'decision', text('tokenValidAndUserAllowed')),
                    node('revoke', 'error', text('expireOrRevokeToken'))
                ],
                edges: [
                    edge('page', 'sessionToken'), edge('page', 'csrfToken'),
                    edge('sessionToken', 'submit'), edge('csrfToken', 'submit'),
                    edge('submit', 'sessionValid'), edge('sessionValid', 'reject', text('no')),
                    edge('sessionValid', 'csrfValid', text('yes')), edge('csrfValid', 'reject', text('no')),
                    edge('csrfValid', 'apply', text('yes')), edge('fullLogin', 'remember'),
                    edge('remember', 'hash'), edge('remember', 'cookie'),
                    edge('cookie', 'restore'), edge('hash', 'restore'),
                    edge('restore', 'sessionToken', text('yes')), edge('restore', 'revoke', text('no'))
                ],
                links: {page: '/options', fullLogin: '/login', revoke: '/options', reject: '/login'}
            },
            apiSecurity: {
                description: text('apiSecurityDescription'),
                help: '/help#7',
                nodes: [
                    node('request', 'process', text('apiOrSensorRequest')),
                    node('sensor', 'decision', text('sensorEndpoint')),
                    node('authRequired', 'decision', text('sensorAuthRequired')),
                    node('basic', 'process', text('httpBasicAuthentication')),
                    node('throttle', 'decision', text('bruteForceAllowed')),
                    node('role', 'decision', text('apiRoleAllowsOperation')),
                    node('change', 'decision', text('stateChangingApiRequest')),
                    node('csrf', 'decision', text('apiCsrfTokenValid')),
                    node('cors', 'optional', text('corsBrowserReadRule')),
                    node('execute', 'success', text('executeAndAuditApiAction')),
                    node('reject', 'error', text('rejectAndAudit')),
                    node('sensorData', 'success', text('acceptSensorMeasurement'))
                ],
                edges: [
                    edge('request', 'sensor'), edge('sensor', 'authRequired', text('yes')),
                    edge('sensor', 'basic', text('no')), edge('authRequired', 'basic', text('yes')),
                    edge('authRequired', 'sensorData', text('no')), edge('basic', 'throttle'),
                    edge('throttle', 'reject', text('blocked')), edge('throttle', 'role', text('allowed')),
                    edge('role', 'reject', text('no')), edge('role', 'change', text('yes')),
                    edge('change', 'csrf', text('yes')), edge('change', 'cors', text('no')),
                    edge('csrf', 'reject', text('invalid')), edge('csrf', 'execute', text('valid')),
                    edge('cors', 'execute'), edge('role', 'sensorData', text('sensor'))
                ],
                links: {request: '/help#7', authRequired: '/options', csrf: '/options', cors: '/options', reject: '/log', sensorData: '/sensors'}
            },
            irrigationPriority: {
                description: text('irrigationPriorityDescription'),
                help: '/help#8',
                nodes: [
                    node('scheduled', 'process', text('scheduledProgramRuns')),
                    node('manual', 'optional', text('manualModeRuns')),
                    node('runonce', 'optional', text('runOnceRuns')),
                    node('queue', 'process', text('mergeRunQueue')),
                    node('priority', 'decision', text('selectRunPriority')),
                    node('capacity', 'decision', text('outputUsageAvailable')),
                    node('delay', 'wait', text('stationAndGroupDelay')),
                    node('postpone', 'wait', text('postponeConflictingRun')),
                    node('start', 'success', text('startEligibleStations')),
                    node('finish', 'process', text('releaseCapacityAndContinue'))
                ],
                edges: [
                    edge('scheduled', 'queue'), edge('manual', 'queue'), edge('runonce', 'queue'),
                    edge('queue', 'priority'), edge('priority', 'capacity'),
                    edge('capacity', 'delay', text('yes')), edge('capacity', 'postpone', text('no')),
                    edge('postpone', 'capacity'), edge('delay', 'start'), edge('start', 'finish'),
                    edge('finish', 'priority', text('next'))
                ],
                links: {scheduled: '/programs', manual: '/', runonce: '/runonce', postpone: '/programs', start: '/'}
            },
            rainWaterBalance: {
                description: text('rainWaterBalanceDescription'),
                help: '/help#9',
                nodes: [
                    node('program', 'process', text('weatherAwareProgram')),
                    node('rainSensor', 'decision', text('rainSensorWet')),
                    node('rainDelay', 'decision', text('manualRainDelayActive')),
                    node('forecast', 'process', text('normalizedWeatherForecast')),
                    node('balance', 'process', text('updateWaterBalance')),
                    node('need', 'decision', text('irrigationNeeded')),
                    node('factor', 'process', text('calculateDurationFactor')),
                    node('skip', 'error', text('skipAndRecordReason')),
                    node('schedule', 'success', text('scheduleAdjustedDuration')),
                    node('history', 'process', text('storeBalanceAndResult'))
                ],
                edges: [
                    edge('program', 'rainSensor'), edge('rainSensor', 'skip', text('yes')),
                    edge('rainSensor', 'rainDelay', text('no')), edge('rainDelay', 'skip', text('yes')),
                    edge('rainDelay', 'forecast', text('no')), edge('forecast', 'balance'),
                    edge('balance', 'need'), edge('need', 'skip', text('no')),
                    edge('need', 'factor', text('yes')), edge('factor', 'schedule'),
                    edge('schedule', 'history'), edge('skip', 'history')
                ],
                links: {program: '/programs', rainSensor: '/options', rainDelay: '/', forecast: '/options#weatherSection', history: '/log'}
            },
            outputHardware: {
                description: text('outputHardwareDescription'),
                help: '/help#9',
                nodes: [
                    node('request', 'process', text('stationOutputRequest')),
                    node('mapping', 'process', text('resolveOutputMapping')),
                    node('master', 'optional', text('applyMasterSequence')),
                    node('backend', 'decision', text('selectedOutputBackend')),
                    node('gpio', 'optional', 'GPIO'),
                    node('shift', 'optional', text('shiftRegister')),
                    node('remote', 'optional', text('pluginOrRemoteOutput')),
                    node('invert', 'decision', text('activeLowOutput')),
                    node('write', 'process', text('writeRequestedState')),
                    node('ack', 'success', text('commandAcceptedByDriver')),
                    node('feedback', 'optional', text('optionalPhysicalFeedback')),
                    node('safeOff', 'error', text('safeOutputsOff'))
                ],
                edges: [
                    edge('request', 'mapping'), edge('mapping', 'master'), edge('master', 'backend'),
                    edge('backend', 'gpio'), edge('backend', 'shift'), edge('backend', 'remote'),
                    edge('gpio', 'invert'), edge('shift', 'invert'), edge('remote', 'invert'),
                    edge('invert', 'write'), edge('write', 'ack'), edge('ack', 'feedback'),
                    edge('write', 'safeOff', text('failed'))
                ],
                links: {request: '/stations', mapping: '/options', ack: '/diagnostics', safeOff: '/diagnostics'}
            },
            userRoles: {
                description: text('userRolesDescription'),
                help: '/help#7',
                nodes: [
                    node('request', 'process', text('protectedPageOrAction')),
                    node('session', 'decision', text('authenticatedSessionPresent')),
                    node('anonymous', 'optional', text('anonymousVisitor')),
                    node('role', 'decision', text('currentUserRole')),
                    node('admin', 'optional', text('administratorRole')),
                    node('user', 'optional', text('operatorRole')),
                    node('public', 'optional', text('publicRole')),
                    node('policy', 'decision', text('routePolicyAllowsRole')),
                    node('csrf', 'decision', text('csrfRequiredForChange')),
                    node('allow', 'success', text('allowScopedOperation')),
                    node('reject', 'error', text('denyAndAuditAccess'))
                ],
                edges: [
                    edge('request', 'session'), edge('session', 'role', text('yes')),
                    edge('session', 'anonymous', text('no')), edge('anonymous', 'public'),
                    edge('role', 'admin'), edge('role', 'user'), edge('role', 'public'),
                    edge('admin', 'policy'), edge('user', 'policy'), edge('public', 'policy'),
                    edge('policy', 'reject', text('no')), edge('policy', 'csrf', text('yes')),
                    edge('csrf', 'reject', text('invalid')), edge('csrf', 'allow', text('valid'))
                ],
                links: {request: '/login', admin: '/options', user: '/', policy: '/help#7', reject: '/log'}
            },
            eventsIncidents: {
                description: text('eventsIncidentsDescription'),
                help: '/help#5',
                nodes: [
                    node('operation', 'process', text('systemOperationOrFailure')),
                    node('event', 'process', text('categorizedOperationalEvent')),
                    node('eventLog', 'success', text('persistentEventsLog')),
                    node('problem', 'decision', text('recoverableCoreProblem')),
                    node('registry', 'error', text('activeProblemRegistry')),
                    node('modal', 'error', text('diagnosticErrorModal')),
                    node('incident', 'process', text('persistentIncidentHistory')),
                    node('retry', 'decision', text('laterRetrySuccessful')),
                    node('resolved', 'success', text('resolveActiveIncident')),
                    node('debug', 'optional', text('technicalDebugTraceback'))
                ],
                edges: [
                    edge('operation', 'event'), edge('event', 'eventLog'),
                    edge('operation', 'problem'), edge('problem', 'registry', text('yes')),
                    edge('problem', 'debug', text('technicalDetails')), edge('registry', 'modal'),
                    edge('registry', 'incident'), edge('incident', 'retry'),
                    edge('retry', 'resolved', text('yes')), edge('retry', 'registry', text('no')),
                    edge('resolved', 'incident')
                ],
                links: {eventLog: '/log', registry: '/diagnostics', modal: '/diagnostics', incident: '/diagnostics', debug: '/plugins/system_debug'}
            },
            notifications: {
                description: text('notificationsDescription'),
                help: '/help#1',
                nodes: [
                    node('trigger', 'process', text('notificationTrigger')),
                    node('enabled', 'decision', text('notificationEnabledForEvent')),
                    node('provider', 'decision', text('notificationProviderReady')),
                    node('compose', 'process', text('composeLocalizedMessage')),
                    node('sections', 'optional', text('addStationSensorAndMeterData')),
                    node('connect', 'process', text('secureSmtpConnection')),
                    node('send', 'decision', text('messageAcceptedByServer')),
                    node('success', 'success', text('recordNotificationSuccess')),
                    node('retry', 'wait', text('boundedRetryQueue')),
                    node('error', 'error', text('recordNotificationFailure'))
                ],
                edges: [
                    edge('trigger', 'enabled'), edge('enabled', 'provider', text('yes')),
                    edge('enabled', 'error', text('no')), edge('provider', 'compose', text('yes')),
                    edge('provider', 'error', text('no')), edge('compose', 'sections'),
                    edge('sections', 'connect'), edge('connect', 'send'),
                    edge('send', 'success', text('yes')), edge('send', 'retry', text('no')),
                    edge('retry', 'connect', text('retry')), edge('retry', 'error', text('exhausted'))
                ],
                links: {trigger: '/log', provider: '/plugins/email_notifications_ssl', success: '/log', error: '/log'}
            },
            startupShutdown: {
                description: text('startupShutdownDescription'),
                help: '/help#3',
                nodes: [
                    node('service', 'process', text('systemServiceStartsOSPy')),
                    node('settings', 'decision', text('loadAndValidateSettings')),
                    node('outputs', 'process', text('initializeOutputsSafeOff')),
                    node('core', 'process', text('startCoreWorkers')),
                    node('dependencies', 'process', text('resolvePluginDependencyOrder')),
                    node('plugins', 'process', text('startAndCheckPlugins')),
                    node('ready', 'success', text('webSchedulerAndWatchdogReady')),
                    node('failure', 'error', text('safeStartupFailure')),
                    node('shutdown', 'process', text('shutdownRequested')),
                    node('irrigation', 'process', text('stopIrrigationAndMasters')),
                    node('reverse', 'process', text('stopPluginsInReverseOrder')),
                    node('threads', 'wait', text('joinManagedWorkers')),
                    node('off', 'success', text('outputsOffAndProcessEnds'))
                ],
                edges: [
                    edge('service', 'settings'), edge('settings', 'outputs', text('valid')),
                    edge('settings', 'failure', text('invalid')), edge('outputs', 'core'),
                    edge('core', 'dependencies'), edge('dependencies', 'plugins'),
                    edge('plugins', 'ready'), edge('ready', 'shutdown'),
                    edge('failure', 'outputs'), edge('shutdown', 'irrigation'),
                    edge('irrigation', 'reverse'), edge('reverse', 'threads'), edge('threads', 'off')
                ],
                links: {service: '/diagnostics', settings: '/options', plugins: '/plugins_manage', ready: '/diagnostics', shutdown: '/options'}
            },
            pluginPermissions: {
                description: text('pluginPermissionsDescription'),
                help: '/help#1',
                nodes: [
                    node('manifest', 'process', text('manifestPermissionDeclaration')),
                    node('compare', 'decision', text('permissionSetAlreadyApproved')),
                    node('changed', 'decision', text('newPermissionsRequested')),
                    node('review', 'wait', text('administratorReviewsMeanings')),
                    node('approve', 'decision', text('administratorApprovesSet')),
                    node('persist', 'process', text('persistApprovalAndAudit')),
                    node('preflight', 'decision', text('preactivationTest')),
                    node('start', 'success', text('importAndStartPlugin')),
                    node('block', 'error', text('blockInstallUpdateOrActivation')),
                    node('revoke', 'error', text('revocationDisablesPlugin'))
                ],
                edges: [
                    edge('manifest', 'compare'), edge('compare', 'preflight', text('yes')),
                    edge('compare', 'changed', text('no')), edge('changed', 'review', text('yes')),
                    edge('changed', 'block', text('invalid')), edge('review', 'approve'),
                    edge('approve', 'persist', text('yes')), edge('approve', 'block', text('no')),
                    edge('persist', 'preflight'), edge('preflight', 'start', text('passed')),
                    edge('preflight', 'block', text('failed')), edge('persist', 'revoke', text('laterRevoked'))
                ],
                links: {manifest: '/plugins_manage', review: '/plugins_manage', start: '/diagnostics', block: '/plugins_manage', revoke: '/plugins_manage'}
            },
            sensorLifecycle: {
                description: text('sensorLifecycleDescription'),
                help: '/help#20',
                nodes: [
                    node('discover', 'process', text('discoverOrCreateSensor')),
                    node('identity', 'process', text('identifyByMacAndCurrentIp')),
                    node('receive', 'process', text('pollOrReceiveMeasurement')),
                    node('validate', 'decision', text('measurementAndIdentityValid')),
                    node('state', 'process', text('updateValueSignalAndLastResponse')),
                    node('stale', 'decision', text('responseWithinExpectedInterval')),
                    node('rules', 'decision', text('thresholdOrProgramRuleMatched')),
                    node('normal', 'success', text('sensorHealthy')),
                    node('action', 'error', text('blockStopOrStartConfiguredAction')),
                    node('history', 'optional', text('storeHistoryEventAndNotification')),
                    node('offline', 'error', text('markSensorNotResponding'))
                ],
                edges: [
                    edge('discover', 'identity'), edge('identity', 'receive'),
                    edge('receive', 'validate'), edge('validate', 'state', text('yes')),
                    edge('validate', 'history', text('no')), edge('state', 'stale'),
                    edge('stale', 'offline', text('no')), edge('stale', 'rules', text('yes')),
                    edge('rules', 'normal', text('no')), edge('rules', 'action', text('yes')),
                    edge('action', 'history'), edge('normal', 'history'), edge('offline', 'history')
                ],
                links: {discover: '/sensors?search', identity: '/sensors', state: '/sensors', action: '/programs', history: '/log'}
            },
            networkExposure: {
                description: text('networkExposureDescription'),
                help: '/help#7',
                nodes: [
                    node('client', 'process', text('browserOrIntegrationClient')),
                    node('location', 'decision', text('clientOnTrustedHomeNetwork')),
                    node('lan', 'optional', text('localLanAccess')),
                    node('internet', 'error', text('internetExposure')),
                    node('firewall', 'decision', text('firewallAndPortPolicy')),
                    node('proxy', 'optional', text('reverseProxyOrVpn')),
                    node('tls', 'decision', text('httpsAndTrustedCertificate')),
                    node('listener', 'process', text('ospyWebListener')),
                    node('auth', 'decision', text('strongLoginAndTwoFactor')),
                    node('allow', 'success', text('restrictedAuthenticatedAccess')),
                    node('risk', 'error', text('publicHttpOrAnonymousRisk'))
                ],
                edges: [
                    edge('client', 'location'), edge('location', 'lan', text('yes')),
                    edge('location', 'internet', text('no')), edge('lan', 'listener'),
                    edge('internet', 'firewall'), edge('firewall', 'risk', text('openUnsafe')),
                    edge('firewall', 'proxy', text('restricted')), edge('proxy', 'tls'),
                    edge('tls', 'risk', text('no')), edge('tls', 'listener', text('yes')),
                    edge('listener', 'auth'), edge('auth', 'allow', text('yes')),
                    edge('auth', 'risk', text('no'))
                ],
                links: {firewall: '/help#7', proxy: '/help#7', tls: '/options', auth: '/twofactor', risk: '/diagnostics'}
            },
            cleanInstallation: {
                description: text('cleanInstallationDescription'),
                help: '/help#0',
                nodes: [
                    node('platform', 'decision', text('supportedLinuxAndPython')),
                    node('menu', 'process', text('chooseInstallDirectoryAndPackages')),
                    node('existing', 'decision', text('existingGitCheckout')),
                    node('preserve', 'error', text('stopWithoutDeletingExistingInstall')),
                    node('download', 'process', text('downloadStableMasterCheckout')),
                    node('dependencies', 'process', text('installCoreAndSelectedDependencies')),
                    node('sqlite', 'decision', text('sqliteMemoryIntegrityCheck')),
                    node('service', 'process', text('installValidatedSystemdService')),
                    node('hardware', 'optional', text('configureGroupsAndOptionalI2c')),
                    node('start', 'decision', text('startAndVerifyService')),
                    node('login', 'success', text('openPortAndChangeGeneratedPassword')),
                    node('diagnose', 'error', text('showServiceFailureAndDiagnostics'))
                ],
                edges: [
                    edge('platform', 'menu', text('supported')), edge('platform', 'diagnose', text('unsupported')),
                    edge('menu', 'existing'), edge('existing', 'preserve', text('yes')),
                    edge('existing', 'download', text('no')), edge('download', 'dependencies'),
                    edge('dependencies', 'sqlite'), edge('sqlite', 'service', text('passed')),
                    edge('sqlite', 'diagnose', text('failed')), edge('service', 'hardware'),
                    edge('hardware', 'start'), edge('start', 'login', text('yes')),
                    edge('start', 'diagnose', text('no'))
                ],
                links: {platform: '/help#0', preserve: '/help#0', service: '/diagnostics', login: '/login', diagnose: '/diagnostics'}
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
