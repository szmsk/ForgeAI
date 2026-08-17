# Helm deployment

This directory is reserved for the Helm packaging layer.

The checked-in Kubernetes manifests under `deploy/k8s/` are the reference deployment. A production Helm chart should be generated from the exact environment-specific values used by the target cluster rather than committing fake defaults for credentials, domains or storage.
