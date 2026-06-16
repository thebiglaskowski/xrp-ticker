#!/usr/bin/env node
/**
 * SubagentStart Hook - Track subagent spawning
 *
 * Triggered when a subagent (Task tool) is started.
 * Tracks agent metadata for synthesis and cost allocation.
 */

const { parseHookInput, loadState, saveState, logMessage } = require('./utils');

// Parse input from hook
const parsed = parseHookInput();
const agentId = parsed.agent_id || parsed.task_id || `agent-${Date.now()}`;
const agentType = parsed.tool_input?.subagent_type || 'general-purpose';
const description = parsed.tool_input?.description || '';
const model = parsed.tool_input?.model || 'sonnet';
const runInBackground = parsed.tool_input?.run_in_background || false;

// Load active agents
const activeAgents = loadState('active_agents.json', {});

// Track this agent
activeAgents[agentId] = {
    id: agentId,
    type: agentType,
    description,
    model,
    runInBackground,
    startTime: new Date().toISOString(),
    status: 'running'
};

// Detect if agent matches a known agent definition from agents/*.yaml
let agentRole = null;
let rulesLoaded = [];
let expertise = [];

try {
    const fs = require('fs');
    const path = require('path');
    const agentsDir = path.resolve(__dirname, '..', '..', 'agents');

    if (fs.existsSync(agentsDir)) {
        const agentFiles = fs.readdirSync(agentsDir)
            .filter(f => f.endsWith('.yaml'));

        // Try to match agent role from description or type
        const searchText = (description + ' ' + agentType).toLowerCase();

        for (const file of agentFiles) {
            const roleName = file.replace('.yaml', '');
            if (searchText.includes(roleName)) {
                const yamlPath = path.join(agentsDir, file);
                const content = fs.readFileSync(yamlPath, 'utf8');

                agentRole = roleName;

                // Extract rules_to_load (simple line-based YAML parsing)
                const lines = content.split('\n');
                let inRules = false;
                let inExpertise = false;

                for (const line of lines) {
                    // Detect top-level keys
                    if (/^[a-z]/.test(line)) {
                        inRules = line.startsWith('rules_to_load:');
                        inExpertise = line.startsWith('expertise:');
                        continue;
                    }
                    if (inRules) {
                        const match = line.match(/^\s+-\s+(.+)/);
                        if (match) rulesLoaded.push(match[1].trim());
                    }
                    if (inExpertise) {
                        const match = line.match(/^\s+-\s+(.+)/);
                        if (match) expertise.push(match[1].trim());
                    }
                }

                break; // Use first match
            }
        }
    }
} catch {
    // Agent definition detection is best-effort
}

// Add agent role info to tracked data
if (agentRole) {
    activeAgents[agentId].agentRole = agentRole;
    activeAgents[agentId].rulesLoaded = rulesLoaded;
    activeAgents[agentId].expertise = expertise;
}

saveState('active_agents.json', activeAgents);

// Log the agent start
logMessage(`SubagentStart id=${agentId} type=${agentType} model=${model}${agentRole ? ` role=${agentRole}` : ''}`);

// Output
const output = {
    tracked: true,
    agentId,
    agentType,
    model,
    activeCount: Object.keys(activeAgents).length
};

if (agentRole) {
    output.agentRole = agentRole;
    output.rulesLoaded = rulesLoaded;
    output.expertise = expertise;
}

console.log(JSON.stringify(output));
