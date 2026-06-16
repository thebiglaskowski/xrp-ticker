#!/usr/bin/env node
/**
 * PreToolUse Hook for Bash - Validate dangerous commands
 *
 * Triggered before Bash tool execution.
 * Blocks dangerous commands that could harm the system.
 */

const { parseHookInput, logMessage } = require('./utils');

// Dangerous command patterns
const DANGEROUS_PATTERNS = [
    // Destructive file operations
    { pattern: /rm\s+-rf\s+[\/~]/, reason: 'Recursive delete from root or home' },
    { pattern: /rm\s+-rf\s+\*/, reason: 'Recursive delete all files' },
    { pattern: /rm\s+-rf\s+\./, reason: 'Recursive delete current directory' },

    // Disk operations
    { pattern: />\s*\/dev\/sd/, reason: 'Direct write to disk device' },
    { pattern: /mkfs/, reason: 'Filesystem creation' },
    { pattern: /dd\s+if=.*of=\/dev/, reason: 'Direct disk write with dd' },

    // Permission changes
    { pattern: /chmod\s+-R\s+777\s+\//, reason: 'Recursive chmod 777 from root' },
    { pattern: /chown\s+-R\s+.*\s+\//, reason: 'Recursive chown from root' },

    // System modification
    { pattern: /:(){ :|:& };:/, reason: 'Fork bomb' },
    { pattern: />\s*\/dev\/null\s*2>&1\s*&\s*disown/, reason: 'Background process hiding' },

    // Network attacks
    { pattern: /nc\s+-l.*-e\s+\/bin/, reason: 'Netcat reverse shell' },

    // History manipulation
    { pattern: /history\s+-c/, reason: 'Clear command history' },
    { pattern: /shred.*\.bash_history/, reason: 'Shred bash history' },

    // Supply-chain attacks — piping remote scripts to shell
    { pattern: /curl.*\|\s*(sh|bash|zsh)/, reason: 'Piping curl to shell' },
    { pattern: /wget.*\|\s*(sh|bash|zsh)/, reason: 'Piping wget to shell' },

    // Encoded command injection
    { pattern: /base64\s+(-d|--decode).*\|\s*(sh|bash|zsh)/, reason: 'Base64-encoded command injection' },

    // Destructive find operations
    { pattern: /\bfind\s+\/\s+.*-delete\b/, reason: 'find with -delete from root' },
    { pattern: /\bfind\s+\/\s+.*-exec\s+rm\b/, reason: 'find with -exec rm from root' },

    // Scripting language one-liners (obfuscation risk)
    { pattern: /\bpython[23]?\s+-c\s+['"].*(?:import\s+os|subprocess|eval|exec)/, reason: 'Python one-liner with dangerous imports' },
    { pattern: /\bperl\s+-e\s+['"].*(?:system|exec|unlink)/, reason: 'Perl one-liner with dangerous functions' },
    { pattern: /\bruby\s+-e\s+['"].*(?:system|exec|File\.delete)/, reason: 'Ruby one-liner with dangerous functions' },
    { pattern: /\bnode\s+-e\s+['"].*(?:child_process|fs\.rm|fs\.unlink)/, reason: 'Node one-liner with dangerous modules' }
];

// Warning patterns (allow but log)
const WARNING_PATTERNS = [
    { pattern: /sudo\s+/, reason: 'Using sudo' },
    { pattern: /npm\s+install\s+-g/, reason: 'Global npm install' },
    { pattern: /pip\s+install\s+--user/, reason: 'User pip install' }
];

/**
 * Normalize a command string to prevent regex bypasses.
 * Handles: variable substitution, full paths, extra whitespace, encoding tricks.
 * @param {string} cmd - Raw command string
 * @returns {string} Normalized command for pattern matching
 */
function normalizeCommand(cmd) {
    let normalized = cmd;

    // Collapse whitespace (prevents spacing-based bypasses)
    normalized = normalized.replace(/\s+/g, ' ').trim();

    // Strip variable substitution patterns: ${var}, $var, $(cmd)
    // e.g., ${rm} -rf / → rm -rf /
    normalized = normalized.replace(/\$\{(\w+)\}/g, '$1');
    normalized = normalized.replace(/\$(\w+)/g, '$1');

    // Strip full binary paths: /usr/bin/rm → rm, /bin/bash → bash
    normalized = normalized.replace(/(?:\/usr\/local\/s?bin|\/usr\/s?bin|\/s?bin)\/(\w+)/g, '$1');

    // Strip common quoting tricks: 'r''m' → rm, "rm" → rm
    // But preserve quoted arguments (only strip single-char concatenation)
    normalized = normalized.replace(/(['"])(\w)\1/g, '$2');

    // Normalize backslash continuations: r\m → rm
    normalized = normalized.replace(/\\(?=\w)/g, '');

    return normalized;
}

// Parse input from hook
const parsed = parseHookInput();
const rawCommand = parsed.tool_input?.command || parsed.command || '';

// Normalize command before checking patterns
const command = normalizeCommand(rawCommand);

// Check for dangerous patterns (test both raw and normalized)
for (const { pattern, reason } of DANGEROUS_PATTERNS) {
    if (pattern.test(command) || pattern.test(rawCommand)) {
        const output = {
            decision: 'block',
            reason: `BLOCKED: ${reason}`,
            pattern: pattern.toString(),
            command: command.substring(0, 500)
        };
        console.log(JSON.stringify(output));

        // Log the blocked command
        logMessage(`BLOCKED dangerous command: ${reason}`, 'BLOCKED');

        process.exit(0);
    }
}

// Check for warning patterns
const warnings = [];
for (const { pattern, reason } of WARNING_PATTERNS) {
    if (pattern.test(command)) {
        warnings.push(reason);
    }
}

// Log warnings if any
if (warnings.length > 0) {
    logMessage(warnings.join(', '), 'WARNING');
}

// Allow the command
const output = {
    decision: 'allow',
    warnings: warnings.length > 0 ? warnings : undefined
};

console.log(JSON.stringify(output));
