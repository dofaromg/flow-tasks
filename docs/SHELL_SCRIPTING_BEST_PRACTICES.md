# Shell Scripting Best Practices

## Overview

This document outlines shell scripting best practices for the flow-tasks repository, with emphasis on common pitfalls and their solutions.

## Table of Contents

1. [Variable Scope in Loops](#variable-scope-in-loops)
2. [Error Handling](#error-handling)
3. [Portability](#portability)
4. [Security](#security)
5. [Testing](#testing)
6. [Documentation](#documentation)

## Variable Scope in Loops

### ⚠️ Common Pitfall: Subshell Variable Loss

**Problem:** Variables modified in pipes are lost due to subshell creation.

```bash
# ❌ BAD: Counter will be reset after the loop
COUNT=0
cat file.txt | while read line; do
  COUNT=$((COUNT + 1))
done
echo $COUNT  # Always shows 0!
```

**Solution:** Use process substitution to avoid subshells.

```bash
# ✅ GOOD: Counter persists after the loop
COUNT=0
while read line; do
  COUNT=$((COUNT + 1))
done < <(cat file.txt)
echo $COUNT  # Shows correct count
```

**See Also:** `docs/SUBSHELL_BUG_FIX.md` for comprehensive documentation.

### Alternative: Temporary Files

```bash
# ✅ GOOD: Use temporary file for counter
> /tmp/count.txt
cat file.txt | while read line; do
  echo "x" >> /tmp/count.txt
done
COUNT=$(wc -l < /tmp/count.txt)
echo $COUNT
rm /tmp/count.txt
```

## Error Handling

### Always Use `set -e`

Exit immediately on error:

```bash
#!/bin/bash
set -e  # Exit on any error

command1
command2  # If this fails, script exits immediately
command3
```

### Handle Expected Errors

```bash
# ✅ GOOD: Handle expected failures
if ! command_that_might_fail; then
  echo "Command failed, but we expected this"
  # Handle gracefully
fi

# ✅ GOOD: Continue on error for specific command
command_that_might_fail || true

# ✅ GOOD: Disable exit-on-error temporarily
set +e
risky_command
EXIT_CODE=$?
set -e
if [ $EXIT_CODE -ne 0 ]; then
  echo "Risky command failed with code $EXIT_CODE"
fi
```

### Validate Prerequisites

```bash
# ✅ GOOD: Check for required commands
command -v kubectl &> /dev/null || {
  echo "Error: kubectl not installed"
  exit 1
}

# ✅ GOOD: Check for required files
if [ ! -f "config.yaml" ]; then
  echo "Error: config.yaml not found"
  exit 1
fi
```

## Portability

### Use Portable Date Commands

```bash
# ✅ GOOD: Handle both GNU and BSD date
TIMESTAMP=$(date -d "$DATE_STR" +%s 2>/dev/null || \
            date -j -f "%Y-%m-%dT%H:%M:%SZ" "$DATE_STR" +%s 2>/dev/null)
```

### Avoid Bashisms in Portable Scripts

```bash
#!/bin/sh  # POSIX shell, not bash

# ❌ BAD: Bash-specific
[[ $VAR == "value" ]]  # [[ ]] is bash-specific

# ✅ GOOD: POSIX-compatible
[ "$VAR" = "value" ]   # Single [ ] is portable
```

### Use Standard Commands

```bash
# ❌ BAD: Non-standard tool
readlink -f file.txt   # Not available on macOS

# ✅ GOOD: Standard approach
realpath file.txt      # More portable (if available)
# or
cd "$(dirname "$file")" && pwd  # Pure shell approach
```

## Security

### Always Quote Variables

```bash
# ❌ BAD: Unquoted variables can cause word splitting
rm $FILE

# ✅ GOOD: Quoted variables are safe
rm "$FILE"

# ✅ GOOD: Quote in arrays
FILES=("file 1.txt" "file 2.txt")
for file in "${FILES[@]}"; do
  echo "$file"
done
```

### Avoid Command Injection

```bash
# ❌ BAD: User input directly in eval
eval "$USER_INPUT"

# ✅ GOOD: Validate input first
if [[ "$USER_INPUT" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  # Safe to use
else
  echo "Invalid input"
  exit 1
fi
```

### Use Temporary Files Safely

```bash
# ❌ BAD: Predictable temp file name
TEMP_FILE=/tmp/myapp.tmp

# ✅ GOOD: Use mktemp
TEMP_FILE=$(mktemp) || exit 1
trap "rm -f $TEMP_FILE" EXIT

# Use $TEMP_FILE safely
# Automatically cleaned up on exit
```

## Testing

### Write Testable Scripts

```bash
#!/bin/bash

# Main function for logic
main() {
  local input="$1"
  # ... script logic ...
  echo "Result: $result"
}

# Only execute main if not being sourced
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  main "$@"
fi

# Now you can source this script in tests:
# source script.sh
# test_result=$(main "test input")
```

### Validate Syntax

```bash
# Check syntax without executing
bash -n script.sh

# Use shellcheck for comprehensive checking
shellcheck script.sh
```

### Create Test Scripts

See `scripts/test_subshell_bug_fix.sh` for example test structure:

```bash
#!/bin/bash
set -e

echo "Test 1: Test description"
# ... test code ...
if [ condition ]; then
  echo "  ✅ Test passed"
else
  echo "  ❌ Test failed"
  exit 1
fi
```

## Documentation

### Script Header

```bash
#!/bin/bash

# Script Name
# Brief description of what the script does
#
# Usage: ./script.sh [options] arguments
#
# Options:
#   -h, --help     Show this help message
#   -v, --verbose  Enable verbose output
#
# Examples:
#   ./script.sh input.txt
#   ./script.sh -v data/
#
# Author: Your Name
# Date: 2026-01-14

set -e
```

### Inline Comments

```bash
# ✅ GOOD: Explain WHY, not WHAT
# Process substitution avoids subshell bug with WARNING_COUNT
while read item; do
  WARNING_COUNT=$((WARNING_COUNT + 1))
done < <(generate_list)

# ❌ BAD: Obvious comments
# Increment counter
COUNT=$((COUNT + 1))  # Add 1 to COUNT
```

### Function Documentation

```bash
# Description: Process user data and generate report
# Arguments:
#   $1 - Input file path
#   $2 - Output directory (optional, defaults to ./output)
# Returns:
#   0 - Success
#   1 - Input file not found
#   2 - Invalid data format
# Example:
#   process_data "input.csv" "/tmp/reports"
process_data() {
  local input_file="$1"
  local output_dir="${2:-./output}"
  
  # ... function implementation ...
}
```

## Scripts Checklist

Before committing a shell script, verify:

- [ ] Starts with proper shebang (`#!/bin/bash` or `#!/bin/sh`)
- [ ] Uses `set -e` for error handling
- [ ] Quotes all variable references (`"$VAR"`)
- [ ] No subshell bugs (use `< <()` for counters)
- [ ] Has descriptive comments explaining complex logic
- [ ] Validates prerequisites (tools, files, permissions)
- [ ] Handles errors gracefully
- [ ] Uses temporary files safely (with cleanup)
- [ ] Passes `bash -n` syntax check
- [ ] Passes `shellcheck` if available
- [ ] Has execute permissions (`chmod +x`)
- [ ] Tested on target platforms

## Examples in This Repository

### Good Examples

- `scripts/monitor-codespaces.sh` - Properly uses process substitution
- `scripts/validate_deployment.sh` - Good error handling and checks
- `scripts/test_subshell_bug_fix.sh` - Well-structured test script

### Workflow Scripts

- `.github/workflows/codespace-monitoring.yml` - Proper variable handling in workflow

## References

- **Subshell Bug:** `docs/SUBSHELL_BUG_FIX.md`
- **ShellCheck:** https://www.shellcheck.net/
- **Google Shell Style Guide:** https://google.github.io/styleguide/shellguide.html
- **Bash Reference Manual:** https://www.gnu.org/software/bash/manual/

## Related Commits

- `81bdb7a` - Fix WARNING_COUNT subshell bug in monitor-codespaces.sh

## Questions?

If you find a shell scripting issue or have questions about best practices, please:

1. Check existing documentation in `docs/`
2. Review similar scripts in `scripts/`
3. Run `shellcheck` to identify potential issues
4. Create an issue if you need clarification
