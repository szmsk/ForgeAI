# Threat model

## Assets

- tenant data
- source code
- GitHub credentials
- LLM credentials
- run traces
- artifacts
- billing/cost data

## Threats

| Threat | Control |
|---|---|
| Cross-tenant read | JWT tenant claim + query scoping + PostgreSQL RLS |
| Stolen API key | hashed storage, revocation, tenant scope, rate limit |
| Replay | idempotency key + run state |
| Malicious repository | dedicated sandbox plane + gVisor/Kata + non-root |
| Container breakout | sandbox runtime + seccomp + no token + dedicated nodes |
| Resource exhaustion | CPU/RAM/PID/job quotas + timeouts |
| Secret exfiltration | secrets never mounted into sandbox; restrictive egress |
| Prompt injection from source code | repository treated as untrusted input; tools constrained by policy |
| LLM runaway cost | per-tenant concurrency, iteration/time limits, token accounting |
| Supply-chain compromise | pinned/base image policy, registry scanning, CI checks |
| Queue duplication | idempotent run IDs and idempotency keys |
| API abuse | rate limits, request-size limits, authentication |

## Residual risk

The LLM is not a security boundary. Source code can contain adversarial instructions. Authorization must be enforced by application and infrastructure policy, not by model instructions.
