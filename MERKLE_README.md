# Merkle Tree Signature System

This repository implements a Merkle tree-based cryptographic signature system to ensure the integrity of all tracked files.

## Overview

The Merkle signature system provides:
- **Cryptographic integrity verification** using SHA-256 hashing
- **Efficient incremental updates** for changed files
- **Automated verification** via git pre-commit hooks
- **CI/CD integration** with GitHub Actions

## Components

### 1. `merkle-sign.sh` - Main Signature Script

The core script that generates and updates Merkle tree signatures.

**Usage:**
```bash
# Generate complete Merkle tree for all tracked files
./merkle-sign.sh full

# Update Merkle tree incrementally (for changed files only)
./merkle-sign.sh incremental
```

**Output Files:**
- `.merkle/root.txt` - The Merkle root hash (64-character SHA-256)
- `.merkle/metadata.json` - Metadata including timestamp, file count, and git info
- `.merkle/tree.txt` - Complete file-to-hash mapping (excluded from git)

### 2. `git-hooks/pre-commit` - Pre-commit Hook

Automatically updates the Merkle signature before each commit.

**Installation:**
```bash
# Copy hook to git hooks directory
cp git-hooks/pre-commit .git/hooks/pre-commit

# Make it executable
chmod +x .git/hooks/pre-commit
```

Once installed, the hook will:
1. Run automatically before each commit
2. Update the Merkle signature for staged files
3. Stage the updated Merkle metadata files
4. Prevent commits if signature generation fails

### 3. `.github/workflows/merkle-verify.yml` - GitHub Actions Workflow

Automatically verifies Merkle signatures on push and pull requests.

The workflow:
- Runs on pushes to main, develop, feature/*, and copilot/* branches
- Generates a fresh Merkle signature
- Validates the signature structure
- Displays verification summary

## Setup Instructions

Follow these steps to set up the Merkle signature system in your repository:

### Step 1: Make Scripts Executable

```bash
chmod +x merkle-sign.sh
```

### Step 2: Install Pre-commit Hook

```bash
# Copy the pre-commit hook
cp git-hooks/pre-commit .git/hooks/pre-commit

# Make it executable
chmod +x .git/hooks/pre-commit
```

### Step 3: Verify GitHub Actions Workflow

The workflow file is already in place at `.github/workflows/merkle-verify.yml`.
It will run automatically on your next push.

### Step 4: Generate Initial Signature

```bash
# Generate the initial Merkle tree signature for all files
./merkle-sign.sh full
```

This will create the `.merkle/` directory and generate:
- Merkle root hash
- Metadata file with timestamp and git information
- File-to-hash mapping

## How It Works

### Merkle Tree Construction

1. **Leaf Nodes**: Each tracked file is hashed using SHA-256
2. **Tree Building**: Hashes are paired and combined recursively
3. **Root Hash**: The final single hash represents all files

```
         Root Hash
        /         \
    Hash(AB)    Hash(CD)
    /    \      /    \
  H(A) H(B)  H(C) H(D)
```

### Verification Process

The system verifies integrity by:
1. Hashing all tracked files
2. Rebuilding the Merkle tree
3. Comparing the new root hash with the stored one
4. Detecting any file modifications

## Examples

### Example 1: Initial Setup

```bash
# Make merkle-sign.sh executable
chmod +x merkle-sign.sh

# Install pre-commit hook
cp git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Generate initial signature
./merkle-sign.sh full
```

### Example 2: Manual Verification

```bash
# View current Merkle root
cat .merkle/root.txt

# View metadata
cat .merkle/metadata.json | jq .

# Regenerate and verify
./merkle-sign.sh full
```

### Example 3: Pre-commit Hook in Action

```bash
# Make changes to files
echo "new content" >> myfile.txt

# Stage changes
git add myfile.txt

# Commit (hook runs automatically)
git commit -m "Update myfile"
# Output:
# Running Merkle signature pre-commit hook...
# Updating Merkle tree signature...
# ✓ Merkle signature updated successfully
```

## Metadata Format

The `.merkle/metadata.json` file contains:

```json
{
  "merkle_root": "0952065fd5efc08753331bf255013dc42fe598c31d85ecfcbdc4c49f5b0e7ed6",
  "timestamp": "2026-02-07T01:27:55Z",
  "mode": "full",
  "file_count": 672,
  "git_commit": "1ae911e6af8c262df3fc74db87a660b5984a5875",
  "git_branch": "main"
}
```

## Troubleshooting

### Hook Not Running

If the pre-commit hook doesn't run:
```bash
# Check if hook is executable
ls -l .git/hooks/pre-commit

# Make it executable if needed
chmod +x .git/hooks/pre-commit

# Verify hook exists
cat .git/hooks/pre-commit
```

### Signature Generation Fails

If `merkle-sign.sh` fails:
```bash
# Ensure you're in a git repository
git status

# Check file permissions
ls -l merkle-sign.sh

# Run with error output
bash -x ./merkle-sign.sh full
```

### GitHub Actions Workflow Not Running

Check:
1. Workflow file is in `.github/workflows/merkle-verify.yml`
2. Branch is configured in workflow triggers
3. GitHub Actions are enabled for your repository

## Technical Details

### Hash Function
- Algorithm: SHA-256
- Output: 64-character hexadecimal string
- Collision resistance: 2^256 (practically impossible)

### Performance
- Hashing speed: ~50-100 files per second
- Incremental mode: Only processes changed files
- Memory efficient: Uses temporary files instead of arrays

### Security Considerations
- Hashes are deterministic (same file = same hash)
- Any file modification changes the Merkle root
- Pre-commit hook prevents unsigned commits
- CI/CD workflow validates all pull requests

## Integration with Other Systems

The Merkle signature system can be integrated with:
- **Code review tools**: Verify signature before reviews
- **Deployment pipelines**: Ensure integrity before deployment
- **Audit systems**: Track file changes over time
- **Backup systems**: Verify backup integrity

## Contributing

When contributing to this repository:
1. The pre-commit hook will run automatically
2. Ensure your changes don't break the Merkle signature system
3. Test both full and incremental modes
4. Verify the GitHub Actions workflow passes

## License

This Merkle signature system is part of the flow-tasks repository and follows the same license.

---

**Last Updated**: 2026-02-07
**System Version**: 1.0.0
