# Architecture

## Control plane

The FastAPI service owns authentication, tenant context, API requests, persistence and enqueueing. It never executes repository code in the HTTP process.

## Data plane

Workers consume queued runs and hand repository execution to a disposable sandbox. Production sandbox jobs run separately from the API control plane.

## Request lifecycle

```text
POST /runs
  -> authenticate
  -> resolve tenant
  -> enforce rate/concurrency limits
  -> persist queued run
  -> enqueue job
  -> return 202

worker
  -> load run
  -> analyze repository
  -> plan changes
  -> apply changes
  -> run tests in sandbox
  -> feed failure back into agent
  -> review result
  -> persist trace/metrics
  -> optionally create draft PR
```

## Tenant isolation

Tenant identity exists in the application authorization layer and the database policy layer. Queries must include tenant scope, while PostgreSQL RLS provides a second boundary.

## Why two planes?

Agent execution is slow, failure-prone and potentially hostile because repositories can contain arbitrary code. Keeping it outside the synchronous API process reduces blast radius and makes horizontal scaling possible.
