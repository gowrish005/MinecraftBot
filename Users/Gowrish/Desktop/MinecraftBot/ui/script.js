// Hell Craft Tech's Minecraft Bot Manager
// Built by LEKING001

var fso = new ActiveXObject("Scripting.FileSystemObject");
var shell = new ActiveXObject("WScript.Shell");
var currentDir = fso.GetParentFolderName(location.pathname.substr(1));
var runningProcesses = {};

// Initialize application
window.onload = function() {
    logMessage('Hell Craft Tech Bot Manager initialized', 'info');
    loadConfig();
    loadServerConfig();
    initializeAnimations();
};

// Load configuration from global_config.json
function loadConfig() {
    try {
        var configPath = currentDir + "\\global_config.json";
        logMessage('Loading configuration from: ' + configPath, 'info');
        
        if (!fso.FileExists(configPath)) {
            logMessage('Config file not found, creating default...', 'warning');
            createDefaultConfig();
            return;
        }
        
        var file = fso.OpenTextFile(configPath, 1);
        var content = file.ReadAll();
        file.Close();
        
        var config = JSON.parse(content);
        renderBotConfigs(config.accounts);
        logMessage('Configuration loaded successfully!', 'success');
    } catch(e) {
        logMessage('Error loading config: ' + e.message, 'error');
    }
}

// Create default configuration
function createDefaultConfig() {
    var defaultConfig = {
        accounts: {
            MC1: { username: "Bot1", password: "", type: "offline" },
            MC2: { username: "Bot2", password: "", type: "offline" },
            MC3: { username: "Bot3", password: "", type: "offline" },
            MC4: { username: "Bot4", password: "", type: "offline" }
        },
        server: {
            ip: "play.pika-network.net",
            version: "1.18.1",
            chatMessages: ["/login password", "/server survival", "/home base"],
            repeat: true,
            repeatDelay: 6
        }
    };
    
    try {
        var configPath = currentDir + "\\global_config.json";
        var file = fso.CreateTextFile(configPath, true);
        file.Write(JSON.stringify(defaultConfig, null, 2));
        file.Close();
        renderBotConfigs(defaultConfig.accounts);
        loadServerConfigFromData(defaultConfig.server);
        logMessage('Default configuration created!', 'success');
    } catch(e) {
        logMessage('Error creating config: ' + e.message, 'error');
    }
}

// Load server configuration
function loadServerConfig() {
    try {
        var configPath = currentDir + "\\global_config.json";
        if (!fso.FileExists(configPath)) return;
        
        var file = fso.OpenTextFile(configPath, 1);
        var content = file.ReadAll();
        file.Close();
        
        var config = JSON.parse(content);
        if (config.server) {
            loadServerConfigFromData(config.server);
        }
    } catch(e) {
        logMessage('Error loading server config: ' + e.message, 'error');
    }
}

// Load server config from data
function loadServerConfigFromData(serverConfig) {
    document.getElementById('serverIP').value = serverConfig.ip || 'play.pika-network.net';
    document.getElementById('serverVersion').value = serverConfig.version || '1.18.1';
    document.getElementById('repeatMessages').value = serverConfig.repeat ? 'true' : 'false';
    document.getElementById('repeatDelay').value = serverConfig.repeatDelay || 6;
    
    if (serverConfig.chatMessages && serverConfig.chatMessages.length > 0) {
        document.getElementById('chatMessages').value = serverConfig.chatMessages.join('\n');
    }
}

// Render bot configuration cards
function renderBotConfigs(accounts) {
    var container = document.getElementById('botConfigs');
    container.innerHTML = '';
    
    for (var botName in accounts) {
        var account = accounts[botName];
        var accountType = account.type || 'offline';
        var showPassword = accountType !== 'offline';
        
        var card = document.createElement('div');
        card.className = 'bot-card slide-up';
        card.innerHTML = 
            '<div class="bot-header">' +
            '<div class="bot-name">' +
            '<span class="status-indicator status-stopped" id="status-' + botName + '"></span>' +
            botName +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2">' +
            '<div class="form-group">' +
            '<label class="form-label">Username</label>' +
            '<input type="text" class="form-input" id="username-' + botName + '" value="' + account.username + '" placeholder="Minecraft username">' +
            '</div>' +
            '<div class="form-group">' +
            '<label class="form-label">Account Type</label>' +
            '<select class="form-select" id="type-' + botName + '" onchange="togglePasswordField(\'' + botName + '\')">' +
            '<option value="offline"' + (accountType === 'offline' ? ' selected' : '') + '>Offline</option>' +
            '<option value="mojang"' + (accountType === 'mojang' ? ' selected' : '') + '>Mojang</option>' +
            '<option value="microsoft"' + (accountType === 'microsoft' ? ' selected' : '') + '>Microsoft</option>' +
            '</select>' +
            '</div>' +
            '</div>' +
            '<div class="form-group ' + (showPassword ? '' : 'hidden') + '" id="passwordGroup-' + botName + '">' +
            '<label class="form-label">Password</label>' +
            '<input type="password" class="form-input" id="password-' + botName + '" value="' + (account.password || '') + '" placeholder="Account password">' +
            '</div>' +
            '<div class="mb-3">' +
            '<button class="btn btn-primary btn-block" onclick="saveBotConfig(\'' + botName + '\')"><span>Save ' + botName + '</span></button>' +
            '</div>' +
            '<div class="btn-grid">' +
            '<button class="btn btn-success" onclick="installBot(\'' + botName + '\')"><span>Install</span></button>' +
            '<button class="btn btn-primary" onclick="startBot(\'' + botName + '\')"><span>Start</span></button>' +
            '<button class="btn btn-warning" onclick="stopBot(\'' + botName + '\')"><span>Stop</span></button>' +
            '<button class="btn btn-info" onclick="openFolder(\'' + botName + '\')"><span>Open</span></button>' +
            '</div>';
        
        container.appendChild(card);
    }
}

// Toggle password field visibility
function togglePasswordField(botName) {
    var accountType = document.getElementById('type-' + botName).value;
    var passwordGroup = document.getElementById('passwordGroup-' + botName);
    
    if (accountType === 'offline') {
        passwordGroup.className = 'form-group hidden';
    } else {
        passwordGroup.className = 'form-group';
    }
}

// Save all configuration
function saveConfig() {
    try {
        var config = { 
            accounts: {},
            server: {}
        };
        var botNames = ['MC1', 'MC2', 'MC3', 'MC4'];
        
        logMessage('Starting save process...', 'info');
        
        // Save bot accounts
        for (var i = 0; i < botNames.length; i++) {
            var botName = botNames[i];
            var username = document.getElementById('username-' + botName);
            var password = document.getElementById('password-' + botName);
            var type = document.getElementById('type-' + botName);
            
            if (!username || !password || !type) {
                logMessage('Error: Missing fields for ' + botName, 'error');
                continue;
            }
            
            config.accounts[botName] = {
                username: username.value,
                password: password.value,
                type: type.value
            };
            logMessage(botName + ': ' + username.value + ' (' + type.value + ')', 'info');
        }
        
        // Save server config
        var serverIP = document.getElementById('serverIP');
        var serverVersion = document.getElementById('serverVersion');
        var chatMessages = document.getElementById('chatMessages');
        var repeatMessages = document.getElementById('repeatMessages');
        var repeatDelay = document.getElementById('repeatDelay');
        
        if (!serverIP || !serverVersion || !chatMessages || !repeatMessages || !repeatDelay) {
            logMessage('Error: Missing server configuration fields!', 'error');
            alert('Error: Server configuration fields not found!');
            return;
        }
        
        var messagesText = chatMessages.value;
        var messagesArray = messagesText.split('\n').filter(function(line) {
            return line.trim() !== '';
        });
        
        config.server = {
            ip: serverIP.value,
            version: serverVersion.value,
            chatMessages: messagesArray,
            repeat: repeatMessages.value === 'true',
            repeatDelay: parseInt(repeatDelay.value)
        };
        
        logMessage('Server: ' + serverIP.value + ' v' + serverVersion.value, 'info');
        logMessage('Messages: ' + messagesArray.length + ' lines', 'info');
        
        // Save global config
        var configPath = currentDir + "\\global_config.json";
        logMessage('Saving to: ' + configPath, 'info');
        
        var file = fso.CreateTextFile(configPath, true);
        file.Write(JSON.stringify(config, null, 2));
        file.Close();
        
        logMessage('global_config.json saved!', 'success');
        
        // Update each bot's settings.json
        updateBotSettings(config.server);
        
        logMessage('Configuration saved successfully!', 'success');
        alert('Configuration saved successfully!');
    } catch(e) {
        logMessage('Error saving config: ' + e.message, 'error');
        alert('Error saving config: ' + e.message);
    }
}

// Save individual bot configuration
function saveBotConfig(botName) {
    try {
        logMessage('Saving ' + botName + ' configuration...', 'info');
        
        // Load existing global config
        var configPath = currentDir + "\\global_config.json";
        var file = fso.OpenTextFile(configPath, 1);
        var content = file.ReadAll();
        file.Close();
        
        var config = JSON.parse(content);
        
        // Update this bot's account info
        var username = document.getElementById('username-' + botName);
        var password = document.getElementById('password-' + botName);
        var type = document.getElementById('type-' + botName);
        
        if (!username || !password || !type) {
            logMessage('Error: Missing fields for ' + botName, 'error');
            alert('Error: Could not find configuration fields for ' + botName);
            return;
        }
        
        config.accounts[botName] = {
            username: username.value,
            password: password.value,
            type: type.value
        };
        
        // Save updated global config
        var outFile = fso.CreateTextFile(configPath, true);
        outFile.Write(JSON.stringify(config, null, 2));
        outFile.Close();
        
        logMessage(botName + ': Saved - ' + username.value + ' (' + type.value + ')', 'success');
        alert(botName + ' configuration saved successfully!');
        
    } catch(e) {
        logMessage(botName + ': Error saving - ' + e.message, 'error');
        alert('Error saving ' + botName + ': ' + e.message);
    }
}

// Update individual bot settings.json files
function updateBotSettings(serverConfig) {
    var botNames = ['MC1', 'MC2', 'MC3', 'MC4'];
    
    for (var i = 0; i < botNames.length; i++) {
        try {
            var botName = botNames[i];
            var settingsPath = currentDir + "\\" + botName + "\\settings.json";
            
            if (!fso.FileExists(settingsPath)) continue;
            
            var file = fso.OpenTextFile(settingsPath, 1);
            var content = file.ReadAll();
            file.Close();
            
            var settings = JSON.parse(content);
            
            // Update server settings
            settings.server.ip = serverConfig.ip;
            settings.server.version = serverConfig.version;
            
            // Update chat messages
            settings.utils['chat-messages'].messages = serverConfig.chatMessages;
            settings.utils['chat-messages'].repeat = serverConfig.repeat;
            settings.utils['chat-messages']['repeat-delay'] = serverConfig.repeatDelay;
            
            // Save updated settings
            var outFile = fso.CreateTextFile(settingsPath, true);
            outFile.Write(JSON.stringify(settings, null, 2));
            outFile.Close();
            
            logMessage(botName + ': Settings updated', 'success');
        } catch(e) {
            logMessage(botName + ': Error updating settings - ' + e.message, 'error');
        }
    }
}

// Install all dependencies
function installAll() {
    var botNames = ['MC1', 'MC2', 'MC3', 'MC4'];
    var progressBar = document.getElementById('progressBar');
    var progressFill = document.getElementById('progressFill');
    
    progressBar.style.display = 'block';
    progressFill.style.width = '0%';
    progressFill.innerText = '0%';
    
    logMessage('Starting installation for all bots...', 'info');
    
    var completed = 0;
    for (var i = 0; i < botNames.length; i++) {
        (function(botName, index) {
            setTimeout(function() {
                installBot(botName, function() {
                    completed++;
                    var percent = Math.round((completed / botNames.length) * 100);
                    progressFill.style.width = percent + '%';
                    progressFill.innerText = percent + '%';
                    
                    if (completed === botNames.length) {
                        setTimeout(function() {
                            progressBar.style.display = 'none';
                            logMessage('All installations completed!', 'success');
                            alert('All dependencies installed successfully!');
                        }, 1000);
                    }
                });
            }, index * 1000);
        })(botNames[i], i);
    }
}

// Install bot dependencies
function installBot(botName, callback) {
    try {
        var botPath = currentDir + "\\" + botName;
        
        if (!fso.FolderExists(botPath)) {
            logMessage(botName + ': Folder not found!', 'error');
            if (callback) callback();
            return;
        }
        
        var packagePath = botPath + "\\package.json";
        if (!fso.FileExists(packagePath)) {
            logMessage(botName + ': package.json not found!', 'error');
            if (callback) callback();
            return;
        }
        
        updateStatus(botName, 'installing');
        logMessage(botName + ': Installing dependencies...', 'info');
        
        var cmd = 'cd /d "' + botPath + '" && npm install';
        var exec = shell.Exec('cmd.exe /c ' + cmd);
        
        var checkInterval = setInterval(function() {
            if (exec.Status === 1) {
                clearInterval(checkInterval);
                var exitCode = exec.ExitCode;
                
                if (exitCode === 0) {
                    logMessage(botName + ': Dependencies installed successfully!', 'success');
                    updateStatus(botName, 'stopped');
                } else {
                    logMessage(botName + ': Installation failed with exit code ' + exitCode, 'error');
                    updateStatus(botName, 'stopped');
                }
                
                if (callback) callback();
            }
        }, 500);
        
    } catch(e) {
        logMessage(botName + ': Installation error - ' + e.message, 'error');
        updateStatus(botName, 'stopped');
        if (callback) callback();
    }
}

// Start a bot
function startBot(botName) {
    try {
        var botPath = currentDir + "\\" + botName;
        
        if (!fso.FolderExists(botPath)) {
            logMessage(botName + ': Folder not found!', 'error');
            return;
        }
        
        if (runningProcesses[botName]) {
            logMessage(botName + ': Bot is already running!', 'warning');
            return;
        }
        
        logMessage(botName + ': Starting bot...', 'info');
        
        var cmd = 'start "' + botName + ' Bot" cmd /k "cd /d ' + botPath + ' && npm start"';
        shell.Run(cmd, 1, false);
        
        runningProcesses[botName] = true;
        updateStatus(botName, 'running');
        logMessage(botName + ': Bot started in new window!', 'success');
        
    } catch(e) {
        logMessage(botName + ': Start error - ' + e.message, 'error');
    }
}

// Stop a bot
function stopBot(botName) {
    try {
        logMessage(botName + ': Stopping bot...', 'warning');
        
        var cmd = 'taskkill /FI "WINDOWTITLE eq ' + botName + ' Bot*" /F';
        shell.Run('cmd.exe /c ' + cmd, 0, false);
        
        runningProcesses[botName] = false;
        updateStatus(botName, 'stopped');
        logMessage(botName + ': Bot stopped!', 'success');
        
    } catch(e) {
        logMessage(botName + ': Stop error - ' + e.message, 'error');
    }
}

// Start all bots
function startAllBots() {
    var botNames = ['MC1', 'MC2', 'MC3', 'MC4'];
    logMessage('Starting all bots...', 'info');
    
    for (var i = 0; i < botNames.length; i++) {
        (function(botName, index) {
            setTimeout(function() {
                startBot(botName);
            }, index * 500);
        })(botNames[i], i);
    }
}

// Stop all bots
function stopAllBots() {
    var botNames = ['MC1', 'MC2', 'MC3', 'MC4'];
    logMessage('Stopping all bots...', 'warning');
    
    for (var i = 0; i < botNames.length; i++) {
        stopBot(botNames[i]);
    }
}

// Open bot folder
function openFolder(botName) {
    try {
        var botPath = currentDir + "\\" + botName;
        shell.Run('explorer.exe "' + botPath + '"');
        logMessage(botName + ': Opened folder in Explorer', 'info');
    } catch(e) {
        logMessage(botName + ': Error opening folder - ' + e.message, 'error');
    }
}

// Update bot status indicator
function updateStatus(botName, status) {
    var statusElement = document.getElementById('status-' + botName);
    if (statusElement) {
        statusElement.className = 'status-indicator status-' + status;
    }
}

// Log message to console
function logMessage(message, type) {
    var logContainer = document.getElementById('logContainer');
    var timestamp = new Date().toLocaleTimeString();
    var logClass = 'log-' + (type || 'info');
    var entry = document.createElement('div');
    entry.className = 'log-entry ' + logClass;
    entry.innerText = '[' + timestamp + '] ' + message;
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Initialize animations
function initializeAnimations() {
    var cards = document.querySelectorAll('.card, .bot-card');
    cards.forEach(function(card, index) {
        setTimeout(function() {
            card.classList.add('fade-in');
        }, index * 100);
    });
}
