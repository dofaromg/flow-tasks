# Bug Fixes - October 2025

## Summary
This document describes the bugs that were identified and fixed in the particle_core module.

## Bugs Fixed

### 1. Deprecation Warning: `datetime.utcnow()` (Python 3.12+)

**Files affected:**
- `particle_core/src/logic_pipeline.py`
- `particle_core/src/rebuild_fn.py`

**Issue:**
The code was using `datetime.utcnow()` which is deprecated in Python 3.12 and scheduled for removal in future versions.

**Fix:**
Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)` to use timezone-aware datetime objects.

**Changes:**
```python
# Before
from datetime import datetime
timestamp = datetime.utcnow().isoformat()

# After
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).isoformat()
```

### 2. Negative Hash in Signature Generation

**File affected:**
- `particle_core/src/rebuild_fn.py`

**Issue:**
The `hash()` function can return negative values, which would cause formatting issues when creating signatures like `MRLSIG-{hash % 10000:04d}`.

**Fix:**
Wrapped the hash value with `abs()` to ensure the signature number is always positive.

**Changes:**
```python
# Before
"signature": f"MRLSIG-{hash(str(fn_steps)) % 10000:04d}"

# After
"signature": f"MRLSIG-{abs(hash(str(fn_steps))) % 10000:04d}"
```

### 3. Timestamp Consistency Issue

**File affected:**
- `particle_core/src/logic_pipeline.py`

**Issue:**
The `store_result()` method was calling `datetime.utcnow()` twice - once for the filename and once for the content timestamp. This could lead to timestamps being off by up to several seconds if the calls happened at different times.

**Fix:**
Create a single timestamp variable and use it for both the filename and content to ensure consistency.

**Changes:**
```python
# Before
data = {
    "timestamp": datetime.utcnow().isoformat(),
    ...
}
filename = f"logic_result_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

# After
now = datetime.now(timezone.utc)
data = {
    "timestamp": now.isoformat(),
    ...
}
filename = f"logic_result_{now.strftime('%Y%m%d_%H%M%S')}.json"
```

## Testing

All fixes have been verified with:
- Unit tests in `test_logic_pipeline.py`
- Integration tests in `test_integration.py`
- No deprecation warnings when running with `python3 -W all`

## Additional Changes

Updated `.gitignore` to exclude test artifacts:
- `particle_core/src/examples/*.json`
- `particle_core/src/test_output/`
