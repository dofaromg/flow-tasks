# Mrliou MRL APIWorks evidence entry v1

This is a review entrance for the existing APIWorks BYOH product, not a new
mother definition, canonical route, public service, or transaction system.
`origin_signature: MrLiouWord` remains the product's declared attribution.

## Build and verify

From this commercial package, with Python 3.10+ and Git available:

```sh
python scripts/Mrliou_MRL_build_evidence_entry_v1.py --output /absolute/new/private/review
python /absolute/new/private/review/VERIFY_EVIDENCE.py /absolute/new/private/review
```

The output directory must not exist and must be outside the repository. The
builder does not fetch, upload, deploy, charge, create customer evidence, or
change runtime/product source. It executes the existing local verification and
test suites, including loopback HTTP test fixtures, and rebuilds the product
ZIP. A failed check stops the build; retained partial output is not a completed
review. Do not run source or tests from an untrusted checkout.

## Expected dependency structure

| Layer | Evidence | Limit |
| --- | --- | --- |
| Original material | Git commit IDs and author/committer dates for selected files | Earliest reachable commit is not original creation or public publication proof |
| Definition | Product manifest, SKU, specification, acceptance and data boundary files | Product scope, not proof of universal physical claims |
| Executable behavior | Runtime, product and closure verifier/test logs | Loopback test fixtures are not real local-model/customer acceptance |
| Source roles | Declared origin, separate Git author and committer fields | Commit identity does not decide conceptual authorship or prove autonomous AI invention |
| Real value | Explicit unverified order, payment, deployment, acceptance and payout fields | No revenue or customer claim is inferred from engineering success |

Content mappings name an actual operation, its specification, implementation,
and a test that exercises it. Similar names alone are not considered evidence.
The complete MRL historical archive and external derivation chains are outside
this product review's verified coverage; they remain work to be collected.

## Integrity and publication boundary

`Expected_File_List.txt` is fixed before building the output. Source copies,
commands, logs, source roles, product ZIP, and the five-layer ledger are retained.
The standalone verifier rejects missing/extra/empty files, checksum failures,
duplicate/unsafe ZIP members, symlinks, and inconsistent bundle manifests. ZIP
members are checked against the pre-build source inventory, not just the ZIP's
own manifest. It also binds the reported ZIP size/hash and source copies.

The upstream ZIP builder includes filesystem timestamps. Rebuilding equal
payloads does not guarantee equal ZIP bytes. Record SHA-256 for each delivery;
do not reuse an old ZIP hash. The output's checksum list is an integrity
inventory, not a digital signature. Pin its hash or the outer review ZIP hash in
an independently trusted record to detect wholesale replacement.

Review artifacts are private staging by default. No Notion page contents,
customer identity, credentials, private memory, model weights, transaction
references, or unapproved mother topology are collected. A separate authorized
private record can link the review to historical material without publishing it.

The review's engineering gate cannot promote customer acceptance, payment,
payout, or realized revenue. Real deployment still needs an authorized customer
node, installed model/configuration and a separately recorded acceptance run.

## Browser acceptance

The commercial-closure workflow builds the evidence entry from the checked-out
commit, renders it with Chromium at desktop (1365×980) and mobile (390×844)
viewports, and uploads a seven-file browser-evidence artifact. The gate requires:

- five visible sections and the expected title/content;
- every local link to resolve inside the generated entry;
- no browser console/page errors;
- no document-level horizontal overflow at either viewport;
- non-empty PNG and rendered-DOM evidence with bound SHA-256 values;
- exact expected/actual file coverage and a second independent verify-only run.

This closes the repeatable browser-rendering gap. It does not claim that an
arbitrary external browser/device, customer model node or public deployment has
been accepted.
