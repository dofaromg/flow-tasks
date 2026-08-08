# RootLaw Symbiosis Audit

## Overview

The RootLaw Symbiosis Audit is a GitHub Actions workflow that automatically validates the integrity and consistency of the RootLaw Package v1 on every push to the repository.

## Purpose

This audit system serves two main purposes:

1. **Integrity Protection**: Prevents accidental or intentional deletion of any of the 42 Root Laws
2. **Symbiosis Validation**: Ensures that the absorption mapping between files and laws remains consistent

## Components

### 1. GitHub Actions Workflow (`.github/workflows/rootlaw-symbiosis-audit.yml`)

Runs automatically on every push and performs:
- Chinese law pattern verification using grep
- Full symbiosis audit using the Python script

### 2. Symbiosis Audit Script (`scripts/symbiosis_audit.py`)

A comprehensive Python script that:
- Validates the existence of the Absorption Map
- Verifies all 42 Root Laws are present in RootLaws_v1.md
- Checks for required sections in the absorption map
- Validates related files (Execution_Laws.md, Evidence_Index.md, etc.)
- Returns appropriate exit codes for CI/CD integration

### 3. RootLaws File Format

The `RootLaw_Package_v1.midlock/RootLaws_v1.md` file uses a bilingual format:

```
第1條 Law 1: <title>
第2條 Law 2: <title>
...
第42條 Law 42: <title>
```

This format:
- Uses Chinese numbering (第N條) for cultural alignment
- Includes English "Law N" for international clarity
- Is compatible with both grep pattern matching and Python parsing

## Usage

### Running Locally

Test the grep pattern:
```bash
grep -c "第.*條" RootLaw_Package_v1.midlock/RootLaws_v1.md
```

Run the symbiosis audit:
```bash
python3 scripts/symbiosis_audit.py --map RootLaw_Package_v1.midlock/Absorption_Map.md
```

Run the full test suite:
```bash
python3 test_rootlaw_audit.py
```

### Exit Codes

- **0**: All checks passed
- **1**: One or more checks failed (missing laws, invalid structure, etc.)

## What Gets Checked

### Integrity Checks
- ✅ Exactly 42 laws present (第1條 through 第42條)
- ✅ No laws accidentally deleted
- ✅ Proper law numbering sequence

### Structure Checks
- ✅ Absorption Map exists and is valid
- ✅ Required sections present in Absorption Map
- ✅ RootLaws_v1.md referenced in mapping
- ✅ Related files exist (Execution_Laws.md, Evidence_Index.md, etc.)

### Symbiosis Checks
- ✅ File-to-law mappings are consistent
- ✅ All referenced files exist
- ✅ Law range (1-42) properly documented

## Error Detection Examples

### Missing Laws
If laws 4-39 were deleted:
```
❌ Error: Missing laws in RootLaws_v1.md: [4, 5, 6, ..., 38, 39]
```

### Invalid Structure
If the Absorption Map is missing required sections:
```
❌ Error: Missing required section '## Mapping Table' in absorption map
```

### Missing Files
If referenced files don't exist:
```
⚠️  Warning: Expected file not found: RootLaw_Package_v1.midlock/Evidence_Index.md
```

## CI/CD Integration

The workflow runs automatically on:
- Push to any branch
- Pull request creation/updates

Failed audits will:
- Block the workflow from passing
- Display detailed error messages
- Require fixes before proceeding

## Maintenance

### Adding New Laws
When adding laws beyond 42, update:
1. The expected law count in `scripts/symbiosis_audit.py`
2. The RootLaws_v1.md file with proper numbering
3. The Absorption Map to reflect the new range

### Modifying Checks
The audit script is modular and can be extended with additional checks:
- Add new validation functions
- Update the `main()` function to call them
- Ensure proper exit codes are returned

## Benefits

1. **Automatic Protection**: No manual oversight needed
2. **Early Detection**: Catches issues immediately on push
3. **Clear Feedback**: Detailed error messages guide fixes
4. **Bilingual Support**: Works with Chinese and English formats
5. **Extensible**: Easy to add new validation rules

## Related Files

- `.github/workflows/rootlaw-symbiosis-audit.yml` - Workflow definition
- `scripts/symbiosis_audit.py` - Audit script
- `test_rootlaw_audit.py` - Test suite
- `RootLaw_Package_v1.midlock/` - Law package directory
  - `RootLaws_v1.md` - Main laws file
  - `Absorption_Map.md` - File-to-law mapping
  - `Execution_Laws.md` - Execution rules
  - `Evidence_Index.md` - Evidence registry
  - `Progress_Snapshot.md` - Operational status
