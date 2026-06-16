#!/usr/bin/env node
/**
 * PreCompact Hook - Backup state before context compaction
 *
 * Triggered before Claude compacts context.
 * Creates a backup of important state to preserve across compaction.
 */

const fs = require('fs');
const path = require('path');
const { loadJsonFile, saveJsonFile, logMessage, getStateFilePath, MAX_BACKUPS } = require('./utils');

const stateDir = path.join(process.cwd(), '.claude', 'state');
const backupDir = path.join(stateDir, 'backups');

// Ensure backup directory exists
if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir, { recursive: true });
}

const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

// Files to backup
const filesToBackup = [
    'session_start.json',
    'file_changes.json',
    'active_agents.json',
    'prompts.json'
];

const backedUp = [];
const backupBundle = {};

for (const file of filesToBackup) {
    const sourcePath = path.join(stateDir, file);
    if (fs.existsSync(sourcePath)) {
        try {
            const content = fs.readFileSync(sourcePath, 'utf8');
            backupBundle[file] = JSON.parse(content);
            backedUp.push(file);
        } catch (e) {
            // Skip files that can't be read/parsed
        }
    }
}

// Write backup bundle
if (backedUp.length > 0) {
    const backupFile = path.join(backupDir, `pre-compact-${timestamp}.json`);
    saveJsonFile(backupFile, {
        timestamp: new Date().toISOString(),
        files: backupBundle
    });

    // Clean up old backups (keep last N)
    const backups = fs.readdirSync(backupDir)
        .filter(f => f.startsWith('pre-compact-'))
        .sort()
        .reverse();

    for (let i = MAX_BACKUPS; i < backups.length; i++) {
        try {
            fs.unlinkSync(path.join(backupDir, backups[i]));
        } catch (e) {
            // Ignore cleanup errors
        }
    }
}

// Generate compact context summary for cs-loop recovery
const summary = {
    timestamp: new Date().toISOString(),
    activeTask: null,
    recentDecisions: [],
    fileChanges: [],
    unresolved: []
};

// Extract active task from session state
const sessionState = backupBundle['session_start.json'];
if (sessionState) {
    summary.activeTask = sessionState.currentTask || sessionState.task || null;
}

// Extract recent file changes
const fileChanges = backupBundle['file_changes.json'];
if (fileChanges && Array.isArray(fileChanges)) {
    summary.fileChanges = fileChanges.slice(-10).map(f => ({
        file: f.file || f.path,
        action: f.action || f.type || 'modified'
    }));
} else if (fileChanges && typeof fileChanges === 'object') {
    summary.fileChanges = Object.keys(fileChanges).slice(-10).map(f => ({
        file: f,
        action: 'modified'
    }));
}

// Extract recent prompts for decision context
const prompts = backupBundle['prompts.json'];
if (prompts && Array.isArray(prompts)) {
    summary.recentDecisions = prompts.slice(-5).map(p => ({
        topics: p.topics || [],
        timestamp: p.timestamp
    }));
}

// Save compact context
const compactPath = path.join(stateDir, 'compact-context.json');
saveJsonFile(compactPath, summary);

// Log the backup
logMessage(`PreCompact backup created: ${backedUp.length} files`);

// Output
const output = {
    backedUp,
    timestamp,
    backupCount: backedUp.length
};

console.log(JSON.stringify(output));
