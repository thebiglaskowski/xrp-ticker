# Commit Style Skill

## Trigger

When creating git commits.

## Format

```
<type>: <subject>

[optional body]

[optional footer]
```

## Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Formatting, no code change
- `refactor` - Code change that neither fixes nor adds
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

## Rules

1. Subject line: imperative mood, no period, max 50 chars
2. Body: wrap at 72 chars, explain what and why
3. Reference issues: `Fixes #123` or `Relates to #456`

## Examples

```
feat: add user authentication flow

Implements JWT-based auth with refresh tokens.
Session timeout set to 24 hours.

Fixes #42
```

```
fix: prevent crash on empty input

Added null check before processing user data.
```
