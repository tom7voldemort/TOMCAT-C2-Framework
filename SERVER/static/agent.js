// TOMCAT C2 - Agents Management Functions

let selectedAgentId = null;

// Update agents table
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
        cell.style.color = '#00cccc';
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

// Select agent
function selectAgent(agentId) {
    selectedAgentId = agentId;
    document.getElementById('selectedAgent').textContent = 'Agent ' + agentId;
    addLog('[*] Selected Agent ID: ' + agentId, 'info');
    
    // Update table selection
    const rows = document.querySelectorAll('.agents-table-row');
    rows.forEach(row => {
        row.classList.remove('selected');
    });
    
    // Add selected class to clicked row
    event.currentTarget.classList.add('selected');
}