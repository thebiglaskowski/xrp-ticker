# Test-First Skill

## Trigger

Before implementing any new functionality or fixing bugs.

## Action

1. **Check existing coverage** - Does a test exist for this behavior?
2. **Write failing test first** - Capture expected behavior
3. **Implement minimally** - Make the test pass
4. **Refactor if needed** - Clean up while green

## For Bug Fixes

1. Write a test that reproduces the bug (should fail)
2. Fix the bug
3. Verify test passes
4. Commit both together

## For New Features

1. Write test for happy path
2. Implement happy path
3. Write tests for edge cases
4. Handle edge cases
5. Refactor

## Skip Conditions

- Exploratory/spike work (temporary code)
- Pure refactoring (existing tests cover)
- Configuration changes (no behavior change)

## Reminder

If you can't write a test, you might not understand the requirement well enough.
