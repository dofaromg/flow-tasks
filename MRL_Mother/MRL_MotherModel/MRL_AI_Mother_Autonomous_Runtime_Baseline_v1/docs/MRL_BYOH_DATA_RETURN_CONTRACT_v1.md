# MRL BYOH Model Delivery and Data Return Contract v1

## Deployment boundary

GitHub carries the construction package. The user runs the supplied MRL model and runtime on hardware they control. No DL580, cloud vendor, CPU family or GPU family is canonical.

## Provider responsibilities

1. publish a model artifact with an `MRL_Model_Release_v1` manifest;
2. publish SHA-256, size, version, supported runtime and license reference;
3. maintain the GitHub construction package and compatibility tests;
4. receive only a user-created `MRL_Return_Bundle_v1`;
5. verify bundle coverage and hashes before processing returned files.

## User-hardware responsibilities

1. obtain the model through the approved delivery channel;
2. verify the model manifest and SHA-256 before loading it;
3. run inference locally;
4. keep local Memory, Evidence and Passport data local by default;
5. explicitly select any files to return and state their purpose;
6. initiate the upload themselves through the future authenticated receiving channel.

## Baseline return rule

There is no background telemetry and no automatic upload. The package creates a ZIP containing only explicitly selected files plus `MRL_RETURN_MANIFEST.json`. The manifest records hardware ID, model release ID, purpose, consent, file sizes and SHA-256 values. Secret-like filenames, empty files, disallowed extensions, duplicate names and oversized bundles are rejected locally.

The builder resolves every selected source and the output path before opening the ZIP. It rejects an output path that names or aliases a selected source, so a failed build cannot truncate that source.

建構器會先解析所有來源檔與輸出路徑，拒絕輸出路徑指向或別名連結到任何來源檔。ZIP 會先寫入目的目錄中的唯一暫存檔，關閉並同步完成後才以原子操作取代輸出檔；即使另一個程序在檢查後改動輸出路徑，也不會讓來源檔被截斷。

Practical local example／本機操作範例：

```powershell
.\scripts\MRL_prepare_return_bundle_v1.ps1 `
  -Files "C:\MRL_Data\evidence.jsonl" `
  -Output "C:\MRL_Exports\MRL_return_bundle.zip" `
  -Purpose "support evidence" `
  -HardwareId "MRL_hardware_01" `
  -ModelReleaseId "MRL_model_release_01" `
  -Consent

python -m runtime.MRL_return_bundle_v1 --help
```

The command only creates a local bundle; it does not upload it. 此命令只建立本機封包，不會自動上傳。

The receiving API, authentication, retention period, deletion workflow and commercial terms are a separate release Gate. Until those are implemented, bundle creation is ready but network submission remains `RECEIVER_GATE_OPEN`.

## State model

```text
MODEL_PUBLISHED
  → MODEL_VERIFIED_BY_USER
  → LOCAL_RUNTIME_PASS
  → USER_SELECTS_FILES
  → RETURN_BUNDLE_VERIFIED
  → USER_INITIATED_UPLOAD
  → PROVIDER_RECEIPT_VERIFIED
```

Failure at any state preserves the local source files and does not imply transfer.
