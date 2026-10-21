# Expected File List

This file freezes the delivery scope for the local backfill package.

## Expected top-level package artifacts

1. README_BACKFILL.md
2. install_to_D_modules.ps1
3. verify_backfill.ps1
4. MRL_FireCore_v1_0_BACKFILL_MANIFEST.json
5. MRL_FireCore_v1_0_AUDIT_REPORT.md
6. MRL_FireCore_v1_0_SHA256SUMS.txt
7. docs/*
8. config/*
9. schemas/*
10. scripts/*
11. modules/mrl-firecore-auth/*
12. modules/mrl-firecore-store/*
13. modules/mrl-firecore-vault/*
14. modules/mrl-firecore-live/*
15. modules/mrl-firecore-push/*
16. modules/mrl-firecore-trace/*
17. sdk/ios/*
18. sdk/web/*
19. runtime/dl580-signing-service/*

## Coverage rule

Delivery is valid only when every expected module exists, every expected file is non-empty, and the SHA256 evidence file can be generated without errors.
