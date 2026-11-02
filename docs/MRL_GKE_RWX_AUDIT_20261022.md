# MRL GKE storage audit — 2026-10-22

origin_signature: MrLiouWord

Source baseline: `dofaromg/flow-tasks` main
`8bc1ce8371a51a5af562c8ae0c623c92abbb9682`.
Project `flowmemorysync`, cluster `modular-cluster`, zone `asia-east1-a`.
Names, historical source files and deployment resources are preserved.

## Evidence and current limits / 證據與驗收邊界

- Historical: Drive `GKE_MIGRATION.md`, modified 2026-07-29, identifies this
  project, cluster and repository. Its checklist still leaves deployment testing
  unchecked; it is not a live inventory.
- Current source: all tracked YAML/YML and Terraform filename candidates were
  inspected in the baseline checkout. Only `apps/mongodb/pvc.yaml` declares a
  PVC: `flowagent/mongodb-pvc`, 10Gi, `ReadWriteOnce`, `standard-rwo`.
  `apps/mongodb/deployment.yaml` consumes it. Production Kustomize includes it.
  No RWX claim or volumeClaimTemplates was found. No Terraform files or VPC-SC
  configuration was found. These absences apply to this checkout only.
- Related repository spot-checks: the same MongoDB PVC blob
  `b96e6e43759c6887114fb12806e22dfbba4b6fb4` was read from default branches of
  `dofaromg/Mrliouword-`, `dofaromg/55555`, `dofaromg/Mrl_w01234567`,
  `dofaromg/MrliouAI-box`, `Mrliou/MRL-Autonomous-Evolution-Stack-AES-`.
  These are source spot-checks, not exhaustive audits or proof of deployment.
- Original Google Cloud email (2026-10-02 Taiwan time), message
  `1a0f935bf7088d3a`, was read directly. It names `flowmemorysync` plus
  `centering-seer-471116-n7`, `studio-4307550372-1333e`,
  `aerial-mission-464718-r0`. API backfill starts 2026-10-27; the default RWX
  rollout starts with control planes 1.37+. API enablement alone has no charge.
- Live cluster version, addon, PVCs, StorageClasses, API enablement, Filestore
  instances, billing and organization perimeter/IaC state: **UNVERIFIED**.
  This execution environment has no gcloud/kubectl credentials or GCP connector.
  No production mutation, API enablement or paid resource creation was performed.

## Minimal preventive change / 最小防護

The existing CD workflow renders manifests then applies them without a storage
policy check. It now checks the exact rendered file before apply. The read-only
checker rejects RWX PVCs and claim templates with missing/null/non-string
`storageClassName`. Explicit `""` is retained: it requests static binding rather
than dynamic provisioning. A named class still needs operator verification that
its provider, capacity and costs are approved. The guard does not select a
provider, change access modes or retrofit bound PVCs.

```bash
kubectl kustomize cluster/overlays/prod > /tmp/MRL-prod.yaml
python scripts/MRL_check_rwx_storage.py /tmp/MRL-prod.yaml
python -m pytest tests/test_MRL_rwx_storage.py -q
```

## Outstanding read-only live checks / 待取得實況證據

Local validation: eight targeted regression tests passed; production Kustomize
rendered 13 objects and the storage guard passed with one explicit RWO claim.
Workflow step ordering and Python compilation passed. Client dry-run was
attempted but blocked by absent cluster discovery credentials/context.
Broader existing integration/comprehensive checks returned 3 passed, 2 failed:
task processing invokes npm lint/build without installed app dependencies;
the Flask API test could not reach its local server. These are not storage
regression passes. Generated task test reports were reverted from this change.

Run in an already authenticated Cloud Shell. The explicit context avoids querying
an unrelated current cluster. If it is absent, obtain approved read access first.
Do not create a test PVC. Keep raw inventories private.

```bash
gcloud container clusters describe modular-cluster --zone=asia-east1-a --project=flowmemorysync --format=json
gcloud services list --enabled --project=flowmemorysync --format=json
kubectl --context=gke_flowmemorysync_asia-east1-a_modular-cluster get pvc -A -o json > /tmp/MRL-live-pvc.json
kubectl --context=gke_flowmemorysync_asia-east1-a_modular-cluster get statefulsets -A -o json > /tmp/MRL-live-statefulsets.json
kubectl --context=gke_flowmemorysync_asia-east1-a_modular-cluster get storageclasses -o json
kubectl --context=gke_flowmemorysync_asia-east1-a_modular-cluster get pv -o json
kubectl --context=gke_flowmemorysync_asia-east1-a_modular-cluster get deployments,statefulsets,daemonsets,jobs,cronjobs,pods -A -o json
python scripts/MRL_check_rwx_storage.py /tmp/MRL-live-pvc.json
python scripts/MRL_check_rwx_storage.py /tmp/MRL-live-statefulsets.json
gcloud filestore instances list --project=flowmemorysync --format=json
gcloud projects describe flowmemorysync --format=json
```

Join workload `claimName` + namespace to PVCs, then PVC `volumeName` to PV CSI
driver/volume handle and StorageClass provisioner. Report each workload and source
SHA separately. A live PVC may have a default class injected; compare its source
manifest and StatefulSet templates as well. Existing bound claims alone do not
prove new provisioning or charges. Permission errors are UNKNOWN, never empty
successful inventories. Repeat for other affected projects only after identifying
their real clusters and repository owners.

For VPC-SC, use the project's number and parent hierarchy to locate the actual
Access Context Manager policy and perimeter (including dry-run spec). Read:

```bash
gcloud access-context-manager policies list --organization=ORGANIZATION_ID --format=json
gcloud access-context-manager perimeters list --policy=POLICY_ID --format=json
```

`ORGANIZATION_ID` and `POLICY_ID` must come from verified organization data.
Check `status/spec.resources`, `restrictedServices`,
`vpcAccessibleServices.enableRestriction`, `allowedServices`, ingress/egress,
and private/restricted API routing. `restrictedServices` protects services;
it is not itself an allow-list. `RESTRICTED-SERVICES` in allowedServices has
special semantics. Do not blindly append to every field or relax a perimeter.
Prepare any necessary change against its actual policy owner, then review it.

Locate the authoritative Terraform repository and backend/state owner. Inspect
`google_project_services`, per-service `google_project_service` for_each sets,
`disable_on_destroy`, `disable_dependent_services`, and automation that reconciles
the enabled API set. An individual google_project_service resource does not by
itself prove an authoritative complete API list. Review `terraform plan` in its
existing authenticated workspace; do not run apply. Explicitly adopt
`file.googleapis.com` only where the real ownership model requires it. No
invented Terraform or perimeter configuration is added to this repository.

## Sources

- https://mail.google.com/mail/u/#all/1a0f935bf7088d3a
  (private mailbox evidence; sign in to the authorized mailbox and locate message
  `1a0f935bf7088d3a`, Google Cloud notification dated 2026-10-02 Taiwan time).
  The account selector is omitted to avoid publishing personal account data;
  the original notification remains in the private mailbox.
- https://drive.google.com/file/d/1VpjhAEcE9BODyxB1iCg6Wrbn0pLXUUn0/view
- https://github.com/dofaromg/flow-tasks/blob/8bc1ce8371a51a5af562c8ae0c623c92abbb9682/apps/mongodb/pvc.yaml
- https://docs.cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/filestore-csi-driver
- https://docs.cloud.google.com/vpc-service-controls/docs/vpc-accessible-services
