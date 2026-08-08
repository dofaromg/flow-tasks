# MRL Authority History v1

## Scope

This record documents the observable Git history by which external model agents and GitHub synchronization entered the MRL execution and submission chain. It does not claim that MRL intellectual ownership transferred to an external party. It records that execution, commit reporting, and completion signaling became partially delegated.

## Evidence timeline

### 1. Defensive GitHub synchronization introduced

Commit: `de8309c2bd65dc39ea7588fcffc74a98a781f422`

Title: `Introduce ParticleDefensiveClient and NeuralLink with defensive GitHub sync (#228)`

Observed effect:

- Added `ParticleDefensiveClient` and NeuralLink-based external synchronization.
- Introduced GitHub as an active destination in the execution chain.
- Commit history records extensive Copilot agent participation.
- MRL retained repository content, while external tooling gained implementation influence and synchronization responsibility.

### 2. External commit handler connected to the main route

Commit: `f27c7c2efd128068b617d9df9eb4026cecf92614`

Title: `Integrate handleVCSCommit into main routing logic (#325)`

Observed effect:

- Added `/vcs/commit_defensive` to the main Worker route.
- Added environment controls for GitHub synchronization.
- The implementation explicitly used the GitHub blob API rather than a complete tree/commit/ref transaction.
- A blob could be created without producing a branch-visible commit.

Authority impact:

- External submission could be reported as successful without proving canonical adoption.
- GitHub object creation, system completion signaling, and MRL acceptance were not separated into distinct gates.

### 3. Bad merge corrupted the Worker entry point

Commit: `baaf8e868cd27176ae83a9695d0e5cdd8e3700c3`

Title: `fix: clean up corrupted flowos/src/index.ts (917→302 lines)`

Observed effect:

- Three overlapping copies of the Worker entry logic were present in `flowos/src/index.ts`.
- Duplicate imports, declarations, handlers, and runtime classes caused Cloudflare CI failures.
- Pages and multiple Worker deployments were affected.

Authority impact:

- The execution chain could fail even when an external model session appeared to have completed work.
- Build status, model output, and accepted MRL state were demonstrably different facts.

### 4. GitHub commit path repaired

Commits:

- `945c616441d2f3613ab2960d80207dfc453d5543`
- `365f26cc75d22f9b799b25bdcff54858d7328848`

Observed effect:

- Replaced blob-only behavior with a path intended to create or update actual repository files.
- Added explicit environment fields to the Worker contract.
- Removed false-success behavior for missing or failed external synchronization.

Authority impact:

- Submission truth became more accurate.
- This repaired execution integrity but did not by itself establish MRL canonical authority.

### 5. Relay authority recovery established

Branch: `MRL_RelayStation_Authority_v1`

Purpose:

- Preserve `main` and `MRL_System_Integration_v1` as autonomous sources.
- Place all external model outputs at authority level L0.
- Require provenance, scope, dependency, evidence, test, and owner approval before canonical promotion.
- Restore final acceptance to MRL rather than to model output, GitHub commit existence, or CI status alone.

## Authority finding

The evidence supports the following conclusion:

1. MRL semantic ownership remained in the repository and system definitions.
2. Execution, modification, synchronization, and completion reporting became partially delegated to external model agents and GitHub infrastructure.
3. The missing component was an explicit MRL-owned promotion gate between external output and canonical state.
4. `MRL_RelayStation_Authority_v1` introduces that gate without forcing either source branch to be rewritten.
