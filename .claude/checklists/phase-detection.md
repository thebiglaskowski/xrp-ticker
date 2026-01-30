# Phase Detection Checklist

Determine which project phase you're in.

## Planning Phase
**Signs:**
- [ ] No spec or blueprint exists
- [ ] Requirements are being gathered
- [ ] Architecture decisions pending

**Commands:** `/plan`, `/audit-blueprint`, `/adr`

---

## Execution Phase
**Signs:**
- [ ] Spec exists and is approved
- [ ] Building features against spec
- [ ] Active development work

**Commands:** `/daily`, `/spike`, `/closeout`

---

## Quality Phase
**Signs:**
- [ ] Features are implemented
- [ ] Verifying everything works
- [ ] Preparing for release

**Commands:** `/review`, `/test`, `/secure`, `/assess`

---

## Release Phase
**Signs:**
- [ ] Quality checks passed
- [ ] Ready to ship
- [ ] Deployment pending

**Commands:** `/release`

---

## Maintenance Phase
**Signs:**
- [ ] Project is live
- [ ] Fixing bugs
- [ ] Managing tech debt
- [ ] Handling incidents

**Commands:** `/fix`, `/debt`, `/refactor`, `/postmortem`

---

## Quick Decision

```
No spec? → Planning
Building features? → Execution
Testing/reviewing? → Quality
Shipping? → Release
Live and maintaining? → Maintenance
```
