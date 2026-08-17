## What changed?

<!-- Describe the change in 2-5 sentences. -->

## Why?

<!-- Explain the problem this solves. -->

## Validation

- [ ] `pytest -q`
- [ ] `ruff check app tests`
- [ ] `python -m compileall -q app`
- [ ] `npm run build` (if frontend changed)

## Security / tenancy impact

- [ ] No new secrets or credentials were added
- [ ] Tenant isolation was preserved
- [ ] Untrusted code is still executed only through the sandbox boundary
- [ ] Security-sensitive changes are documented
