# Severity Level Guide

Quick reference for classifying issues.

## S0 — Blocker
**Fix immediately. Stop other work.**

- Security vulnerabilities
- Data loss or corruption
- System crashes
- Production down
- Blocking other teams

**Response:** Drop everything, fix now.

## S1 — Critical
**Fix before proceeding with other work.**

- Major functionality broken
- Significant user impact
- No workaround available
- Blocking release

**Response:** Prioritize within the day.

## S2 — Major
**Fix soon, but work can continue.**

- Functionality degraded
- Workaround exists
- Limited user impact
- Quality concern

**Response:** Plan for this sprint.

## S3 — Minor
**Fix when convenient.**

- Polish issues
- Minor inconvenience
- Cosmetic problems
- Nice-to-have improvements

**Response:** Add to backlog.

## Quick Decision Tree

```
Is it a security issue? → S0
Is data at risk? → S0
Is production down? → S0
Is major feature broken? → S1
Can users work around it? → S2
Is it just annoying? → S3
```
