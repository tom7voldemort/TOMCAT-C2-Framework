// TOMCAT C2 - Server Management Functions

let autoRefreshInterval = null;

// Start server
function startServer() {
    const host = document.getElementById('hostInput').value;
    const port = document.getElementById('portInput').value;
    
    addLog('[*] Starting server...', 'info');
    
    fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ host: host, port: port })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addLog('[+] ' + data.message, 'success');
            addLog('[+] Session Key: ' + data.key, 'info');
            document.getElementById('statusDot').className = 'status-dot status-online';
            document.getElementById('statusText').textContent = 'Server Online';
            document.getElementById('serverInfo').textContent = 'Listening On: ' + data.host + ':' + data.port;
            document.getElementById('encryptionKey').textContent = data.key;
            document.getElementById('keyDisplay').style.display = 'block';
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            
            // Start auto refresh
            if (!autoRefreshInterval) {
                autoRefreshInterval = setInterval(refreshData, 3000);
            }
        } else {
            addLog('[!] Error: ' + data.message, 'error');
        }
    })
    .catch(error => {
        addLog('[!] Error: ' + error, 'error');
    });
}

// Stop server
function stopServer() {
    addLog('[*] Stopping server...', 'warning');
    
    fetch('/api/stop', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addLog('[!] ' + data.message, 'warning');
            document.getElementById('statusDot').className = 'status-dot status-offline';
            document.getElementById('statusText').textContent = 'Server Offline';
            document.getElementById('serverInfo').textContent = 'Ready';
            document.getElementById('keyDisplay').style.display = 'none';
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            
            // Stop auto refresh
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }
            
            // Clear agents
            updateAgentsTable([]);
        } else {
            addLog('[!] Error: ' + data.message, 'error');
        }
    })
    .catch(error => {
        addLog('[!] Error: ' + error, 'error');
    });
}

// Refresh data
function refreshData() {
    // Get server status
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (data.running) {
                document.getElementById('statusDot').className = 'status-dot status-online';
                document.getElementById('statusText').textContent = 'Server Online';
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
            } else {
                document.getElementById('statusDot').className = 'status-dot status-offline';
                document.getElementById('statusText').textContent = 'Server Offline';
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }
        })
        .catch(error => {
            console.error('Error fetching status:', error);
        });

    // Get agents list
    fetch('/api/agents')
        .then(response => response.json())
        .then(data => {
            updateAgentsTable(data.agents);
        })
        .catch(error => {
            console.error('Error fetching agents:', error);
        });
}

// Add log message
function addLog(message, type) {
    const outputBox = document.getElementById('outputBox');
    const logClass = 'log-' + type;
    
    const logEntry = document.createElement('span');
    logEntry.className = logClass;
    logEntry.textContent = message;
    
    outputBox.appendChild(document.createTextNode('\n'));
    outputBox.appendChild(logEntry);
    
    outputBox.scrollTop = outputBox.scrollHeight;
}

// Clear log
function clearLog() {
    const outputBox = document.getElementById('outputBox');
    outputBox.innerHTML = '';
    addLog('~>> Log cleared', 'info');
    addLog('~>> Ready for new commands...', 'info');
}

// Initialize on load
window.addEventListener('load', function() {
    refreshData();
});