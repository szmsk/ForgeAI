# ForgeAI

> **Production-oriented, multi-tenant autonomous AI software engineering platform.**

ForgeAI turns a software-engineering task into a controlled agent run: it analyzes a repository, creates a plan, proposes code changes, executes tests in an isolated sandbox, feeds failures back into the agent loop, records an auditable trace and can open a draft GitHub pull request.

The project is designed as an **AI platform engineering** portfolio project, not as a chat UI with an LLM attached.

[Architecture](docs/ARCHITECTURE.md) · [Threat model](docs/THREAT_MODEL.md) · [Production deployment](docs/PRODUCTION.md) · [Security](SECURITY.md)

## Why ForgeAI?

The interesting engineering problem is not generating code. It is operating an agent that can change untrusted repositories without mixing tenants, blocking API requests, leaking secrets or silently declaring failure a success.

ForgeAI therefore separates the system into a control plane and a data plane:

- **Control plane:** authentication, tenant isolation, API, persistence, queueing and observability.
- **Data plane:** disposable workers and sandbox jobs that execute repository code.

## Architecture

```text
                           ┌──────────────────────┐
                           │       Browser        │
                           └──────────┬───────────┘
                                      │ TLS
                           ┌──────────▼───────────┐
                           │    FastAPI Control    │
                           │ auth · tenancy · API  │
                           └──────┬─────────┬─────┘
                                  │         │
                       ┌──────────▼───┐ ┌──▼─────────┐
                       │ PostgreSQL   │ │   Redis    │
                       │ RLS + audit  │ │ queue/rate │
                       └──────────────┘ └─────┬──────┘
                                              │
                                      ┌───────▼────────┐
                                      │ Worker / Agent │
                                      └───────┬────────┘
                                              │
                                  ┌───────────▼───────────┐
                                  │ Disposable Sandbox Job │
                                  │ K8s + gVisor/Kata     │
                                  │ non-root + limits     │
                                  │ restrictive network   │
                                  └───────────┬───────────┘
                                              │
                             ┌────────────────┼───────────────┐
                             ▼                ▼               ▼
                          GitHub             S3         OpenTelemetry
                         branches/PRs      artifacts     traces/metrics
```

## Core capabilities

| Area | Implementation |
| --- | --- |
| Multi-tenancy | tenant-scoped JWT/API keys + PostgreSQL RLS |
| Async execution | Redis queue + dedicated workers |
| Agent loop | analyze → plan → edit → test → debug → review |
| Code execution | disposable Docker dev sandbox / Kubernetes production path |
| Sandbox hardening | non-root, resource limits, PID limits, no-new-privileges, restrictive network |
| GitHub | clone, branch, commit and draft PR workflow |
| Storage | S3-compatible artifact storage |
| Observability | OpenTelemetry traces + Prometheus metrics |
| Evaluation | deterministic benchmark foundation + run metrics |
| Frontend | Next.js + TypeScript tenant dashboard |

## Multi-tenant security model

Every authenticated request carries a tenant identity. Application queries are tenant-scoped and PostgreSQL Row-Level Security is used as a second authorization boundary.

Additional controls include:

- tenant-scoped idempotency keys
- per-tenant rate limits
- per-tenant concurrent-run limits
- hashed API keys
- no secret files in the repository
- audit-friendly run events
- separate execution workers

**Important:** ordinary containers are not treated as a sufficient security boundary for arbitrary hostile code. Public production deployments should run sandbox jobs in a dedicated Kubernetes environment with a stronger runtime such as gVisor or Kata Containers and an appropriate network policy.

## Repository layout

```text
forgeai/
├── backend/                 # FastAPI control plane + workers
│   ├── app/                 # API, agent, auth, DB, queue, sandbox
│   ├── alembic/             # database migrations
│   └── tests/               # deterministic tests
├── frontend/                # Next.js dashboard
├── benchmarks/              # agent evaluation tasks
├── deploy/k8s/              # Kubernetes reference manifests
├── deploy/helm/             # Helm chart scaffold
├── infra/                   # observability configuration
├── docs/                    # architecture, security and operations
├── scripts/                 # repository hygiene tooling
├── .github/                 # CI, Dependabot, templates, CODEOWNERS
└── docker-compose.yml       # local development stack
```

## Quick start

### Prerequisites

- Docker Desktop or Docker Engine
- Git
- Node.js 22+ only if developing the frontend outside Docker
- Python 3.12+ only if developing the backend outside Docker

### Run locally

```bash
git clone https://github.com/szmsk/forgeai.git
cd forgeai
cp backend/.env.example backend/.env
docker compose up --build
```

Open:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- MinIO console: `http://localhost:9001`

The local setup uses a deterministic demo mode unless an LLM endpoint is configured.

### Backend checks

```bash
cd backend
pip install -e '.[dev]'
pytest -q
ruff check app tests
python -m compileall -q app
```

### Secret scan

Before pushing a branch:

```bash
python scripts/secret_scan.py
```

The scan is intentionally lightweight. It is a repository hygiene check, not a replacement for a dedicated secret-scanning service.

## Configuration

Copy the examples and replace only the values required for your environment:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Never commit `.env`, `.env.local`, credentials, private keys or provider tokens. The repository `.gitignore` explicitly excludes these patterns.

## Production deployment

The repository includes Kubernetes reference manifests for the control plane and worker path. Read [docs/PRODUCTION.md](docs/PRODUCTION.md) before exposing the system to untrusted repositories.

A production deployment should provide:

1. TLS at the ingress.
2. Managed PostgreSQL with backups and encryption.
3. Managed Redis with authentication and TLS.
4. S3-compatible object storage with least-privilege credentials.
5. Dedicated sandbox worker nodes.
6. gVisor or Kata Containers for untrusted code execution.
7. Kubernetes NetworkPolicies and RBAC.
8. Secret management through the cloud/Kubernetes secret manager, not Git.
9. Centralized logs, traces, metrics and alerting.
10. Resource quotas and cost controls per tenant.

## Evaluation

The benchmark suite is deliberately separate from unit tests. Agent success is probabilistic and should be measured as an application metric.

```bash
python benchmarks/run.py
```

Useful production metrics include:

- task success rate
- test pass rate
- mean/percentile execution time
- iterations per successful run
- input/output token usage
- cost per successful task
- sandbox failure rate
- regression rate
- queue latency

Do not publish benchmark numbers until they have been generated from a reproducible run.

## CI / dependency hygiene

GitHub Actions runs backend linting, compilation and tests plus a frontend production build. Dependabot is enabled for Python, npm and GitHub Actions dependencies.

The frontend intentionally uses pinned package versions. Generate and commit `frontend/package-lock.json` from a networked development machine before treating CI as a fully reproducible release pipeline.

## Status

**Portfolio status:** production-oriented reference implementation.

The architecture contains the major boundaries expected from a multi-tenant AI platform, but a real production deployment still requires environment-specific hardening, load testing, managed infrastructure, secret management and operational runbooks.

## Roadmap

- [ ] streaming run events over WebSocket/SSE
- [ ] GitHub App authentication instead of long-lived personal tokens
- [ ] stronger microVM sandbox option
- [ ] durable workflow engine for long-running jobs
- [ ] tenant billing/quotas
- [ ] distributed benchmark runner
- [ ] evaluation datasets and regression gates
- [ ] SSO / OIDC
- [ ] production-grade frontend run replay

## License

MIT. See [LICENSE](LICENSE).
