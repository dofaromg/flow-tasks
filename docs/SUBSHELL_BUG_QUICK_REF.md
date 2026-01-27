# Subshell Bug Fix - Quick Reference

## The Problem

```bash
# ❌ BUGGY: Counter is lost
COUNT=0
echo "data" | while read line; do
  COUNT=$((COUNT + 1))
done
echo $COUNT  # Shows 0 (BUG!)
```

## The Fix

```bash
# ✅ CORRECT: Counter is preserved
COUNT=0
while read line; do
  COUNT=$((COUNT + 1))
done < <(echo "data")
echo $COUNT  # Shows correct value
```

## Why?

- Pipe `|` creates a subshell for the `while` loop
- Variables modified in the subshell don't affect the parent shell
- Process substitution `< <(...)` avoids the subshell

## Where Fixed

- ✅ `scripts/monitor-codespaces.sh` (line 94)
- ✅ `.github/workflows/codespace-monitoring.yml` (line 75)

## Testing

```bash
bash scripts/test_subshell_bug_fix.sh
```

## Learn More

- **Detailed Guide**: [docs/SUBSHELL_BUG_FIX.md](SUBSHELL_BUG_FIX.md)
- **Best Practices**: [docs/SHELL_SCRIPTING_BEST_PRACTICES.md](SHELL_SCRIPTING_BEST_PRACTICES.md)
- **Commit**: `81bdb7a` - Fix WARNING_COUNT subshell bug
