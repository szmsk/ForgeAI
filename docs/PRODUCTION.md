# ForgeAI production deployment

ForgeAI is designed as a multi-tenant SaaS, but production means more than putting FastAPI behind HTTPS. The deployment separates the API plane, queue, worker plane, database, object storage and untrusted-code execution.

## Isolation model

1. Every account belongs to exactly one tenant.
2. JWTs contain user and tenant IDs.
3. API queries always scope by tenant ID.
4. PostgreSQL Row-Level Security is enabled and forced on tenant-owned tables. The application sets `app.tenant_id` transaction-locally.
5. API keys are tenant-scoped and only the SHA-256 hash is stored.
6. Runs are queued in Redis and executed by workers, not by the HTTP process.
7. Untrusted repositories are never executed inside the API container.
8. Production sandbox backend is Kubernetes with a sandboxed runtime class such as gVisor or Kata Containers.
9. Sandbox jobs have non-root execution, RuntimeDefault seccomp, no service-account token, resource limits, TTL cleanup and restrictive network policy.
10. Repository archives and test output live in object storage, not on the API host.

PostgreSQL RLS is intentionally a second security boundary. PostgreSQL documents that when RLS is enabled and no policy allows access, access is default-deny; `FORCE ROW LEVEL SECURITY` also prevents the table owner from bypassing it. See the official PostgreSQL RLS documentation.

## Production dependencies

- Managed PostgreSQL with automated backups and point-in-time recovery.
- Managed Redis with TLS and persistence appropriate to queue durability requirements.
- S3-compatible object storage with encryption and lifecycle policies.
- Kubernetes cluster with a dedicated sandbox node pool.
- gVisor/Kata runtime class for untrusted execution.
- Ingress controller with TLS.
- OpenTelemetry Collector + Prometheus/Grafana or equivalent.
- Container image registry with vulnerability scanning.

## Sandbox security

Do not mount `/var/run/docker.sock` into the API deployment. Docker's own documentation notes that the daemon is a security-sensitive attack surface; rootless mode reduces daemon/container privileges. For production untrusted code, ForgeAI moves execution to a dedicated worker/sandbox plane and uses a VM/userspace-kernel sandbox runtime instead of treating a normal container as a complete security boundary.

The Kubernetes multi-tenancy model follows namespace/RBAC/resource-quota/network-policy principles. Kubernetes explicitly recommends stronger sandboxing for workloads that execute untrusted code because ordinary containers share the host kernel.

## Secrets

Do not commit `.env`, API keys or JWT secrets. Inject secrets using the cloud secret manager or an external-secrets controller. Rotate JWT signing keys and GitHub/LLM credentials. Prefer short-lived GitHub installation tokens over long-lived personal access tokens.

## Database migrations

Run migrations with a dedicated migration identity:

```bash
alembic upgrade head
```

The runtime DB identity must not be a superuser. RLS policies are part of the migration and should be tested in CI with at least two tenants.

## Operational controls

Recommended production SLOs:

- API availability >= 99.9%
- queue enqueue latency p95 < 250 ms
- sandbox start latency p95 < 10 s
- run success rate tracked separately from platform availability
- zero cross-tenant data-access incidents

Alert on:

- Redis queue depth
- worker crash loops
- sandbox timeout rate
- cross-tenant authorization failures
- database connection saturation
- LLM error rate and cost spikes
- artifact storage failures

## Backups and disaster recovery

PostgreSQL is the source of truth for tenants, users, runs and audit events. Object storage contains repository/test artifacts and must have versioning/lifecycle policy. Redis is treated as reconstructable queue state; jobs should remain idempotent using the run ID and idempotency key.

## What is intentionally not claimed

No software project can honestly claim that a multi-tenant system is universally secure merely because it has JWT, RLS and containers. The production boundary depends on the Kubernetes runtime, kernel, network policy, IAM, managed services, image supply chain and operational controls. ForgeAI therefore makes the security boundary explicit instead of hiding it behind the word "sandbox".
