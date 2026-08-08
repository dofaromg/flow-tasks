# Cluster Configuration

`cluster/` defines the Kubernetes composition layer for MrLiouAI deployments.

## Purpose

- `base/` contains shared cluster resources, such as namespace configuration.
- `overlays/prod/` composes production-ready application manifests from `apps/`.
- `overlays/monitoring/` composes monitoring-specific resources.

## Entry Points

- Production overlay: `cluster/overlays/prod/kustomization.yaml`
- Monitoring overlay: `cluster/overlays/monitoring/kustomization.yaml`
- Base namespace: `cluster/base/namespace.yaml`

## Validate

```bash
# Render manifests without requiring cluster credentials
kubectl kustomize cluster/overlays/prod/ >/tmp/mrliouai-prod.yaml

# When connected to a cluster, run server/client validation before applying
kubectl apply --dry-run=client -k cluster/overlays/prod/
```

## Deploy

```bash
kubectl apply -k cluster/overlays/prod/
```

For production secrets, prefer Secret Manager, Sealed Secrets, or External Secrets rather than committing live credentials.
