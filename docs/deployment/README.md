# Deployment Documentation

Deployment material for MrLiouAI is split between root guides and Kubernetes manifests.

## Start Here

- [Main README deployment sections](../../README.md)
- [Deployment guide](../../DEPLOYMENT.md)
- [GKE migration](../../GKE_MIGRATION.md)
- [Applications manifest guide](../../apps/README.md)
- [Cluster overlay guide](../../cluster/README.md)

## Validation

```bash
kubectl kustomize cluster/overlays/prod/ >/tmp/mrliouai-prod.yaml
python process_tasks.py
```

Use `kubectl apply --dry-run=client -k cluster/overlays/prod/` when a Kubernetes API context is available.
