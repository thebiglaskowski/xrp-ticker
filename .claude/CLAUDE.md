# Project Orchestrator

## Prompt Library

**Location:** `C:\scripts\prompts\`

> Update this path if your prompts library is elsewhere.

---

## How This Works

1. **Assess** the current task or project state
2. **Load** the appropriate prompt from the library
3. **Follow** its process completely
4. **Produce** the outputs it specifies

Use slash commands (`/command`) for quick access to common workflows.

---

## Phase Detection

At the start of each session, determine the project phase:

```
┌─────────────────────────────────────────────────────────┐
│                    PROJECT PHASE?                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  No spec/blueprint exists?                               │
│  └─► PLANNING PHASE (/plan, /audit-blueprint)           │
│                                                          │
│  Spec exists, building features?                         │
│  └─► EXECUTION PHASE (/daily, /spike)                   │
│                                                          │
│  Features complete, verifying quality?                   │
│  └─► QUALITY PHASE (/review, /test, /secure)            │
│                                                          │
│  Ready to ship?                                          │
│  └─► RELEASE PHASE (/release)                           │
│                                                          │
│  Existing project needs assessment?                      │
│  └─► MAINTENANCE PHASE (/assess, /debt, /refactor)      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Command Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/plan` | Create feature specification | Starting new feature |
| `/audit-blueprint` | Validate plan before building | After creating spec |
| `/daily` | Continue development work | Each coding session |
| `/spike` | Technical research | Hit an unknown |
| `/review` | Code review | Before merging |
| `/test` | Test coverage gate | Before release |
| `/secure` | Security audit | User-facing features |
| `/release` | Release checklist | Before shipping |
| `/assess` | Full codebase audit | Project health check |
| `/debt` | Track technical debt | Identify/manage debt |
| `/refactor` | Safe refactoring | Code improvement |
| `/fix` | Bug hunting | Fixing bugs |
| `/postmortem` | Incident analysis | After production issues |
| `/migrate` | Migration planning | Data/schema changes |
| `/adr` | Document decision | Recording tech decisions |
| `/onboard` | Create onboarding docs | New team members |
| `/closeout` | Complete milestone | Finishing a unit of work |

---

## Phase Workflows

### PLANNING PHASE

**Goal:** Turn ideas into executable plans.

```
1. /plan          → Create detailed specification
2. /audit-blueprint → Validate plan is complete
3. /adr           → Document key decisions
4. Proceed to EXECUTION when audit passes
```

### EXECUTION PHASE

**Goal:** Build what was planned.

```
Each session:
1. /daily         → Review state, identify next task, build it

When blocked by unknowns:
2. /spike         → Time-boxed research

After each milestone:
3. /closeout      → Verify completion, update docs
```

### QUALITY PHASE

**Goal:** Verify everything works and is documented.

```
1. /test          → Verify test coverage (must pass)
2. /review        → Review all changes
3. /secure        → Security audit (if user-facing)
4. /assess        → Final completion audit
```

### RELEASE PHASE

**Goal:** Ship with confidence.

```
1. /release       → Pre-release checklist
2. Deploy
3. Monitor
```

### MAINTENANCE PHASE

**Goal:** Keep existing projects healthy.

```
For health checks:
1. /assess        → Full codebase audit
2. /debt          → Catalog technical debt
3. Prioritize findings

For improvements:
4. /refactor      → Safe code improvement
5. /fix           → Bug hunting

For incidents:
6. /postmortem    → Learn from failures
```

---

## Core Principles (Always Apply)

These principles apply regardless of which prompt is loaded:

1. **Evidence over assumption** — Verify, don't guess
2. **Test before changing** — No changes without test coverage
3. **Document what you change** — Update Bundle required
4. **Small incremental steps** — Commit often, revert easily
5. **No guessing** — Ask if requirements are unclear
6. **Blueprint is law** — Don't deviate without approval

---

## Update Bundle (Required After Implementation)

After ANY work that changes behavior, interfaces, or configuration:

```markdown
## Update Bundle

### STATUS.md
[Current project state - what's done, what's next]

### CHANGELOG.md
[What changed and why - user-facing description]

### Documentation
[Any docs that need updates, or "None"]

### KNOWN_ISSUES.md
[Any limitations discovered, or "None"]
```

---

## Severity Levels (For All Audits)

| Level | Meaning | Action |
|-------|---------|--------|
| **S0** | Blocker / Security / Data loss | Fix immediately |
| **S1** | Major functionality broken | Fix before proceeding |
| **S2** | Degraded but functional | Fix soon |
| **S3** | Minor / Polish | Fix when convenient |

---

## Project State Files

This project should maintain:

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `STATUS.md` | Current state, next steps | Every session |
| `CHANGELOG.md` | Version history | Every release/feature |
| `KNOWN_ISSUES.md` | Tracked limitations | As discovered |
| `docs/decisions/` | ADRs | When decisions made |

---

## Context Management

**Important:** Never load multiple full prompts simultaneously.

1. Load ONE prompt at a time
2. Complete its process fully
3. Produce its outputs
4. Then move to the next prompt if needed

For quick checks, use the checklists in `.claude/checklists/` instead of full prompts.

---

## Getting Help

- View available commands: Check `.claude/commands/`
- Quick checklists: Check `.claude/checklists/`
- Full prompt details: Read from `C:\scripts\prompts\[category]/[PROMPT].md`
