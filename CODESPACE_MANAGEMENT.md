# GitHub Codespaces Management Guide

## Overview

This guide provides comprehensive recommendations for managing GitHub Codespaces to prevent automatic deletion and optimize your development workflow.

## Understanding Codespace Retention

### Retention Policy

GitHub automatically deletes inactive codespaces based on the following retention periods:

- **Active codespaces**: Indefinite retention
- **Inactive codespaces**: 
  - Free/Personal accounts: 30 days of inactivity
  - Organization accounts: Configurable (default 30 days)
  - Enterprise accounts: Configurable retention period

### What Counts as Activity?

A codespace is considered "active" when you:
- Connect to it via browser or VS Code
- Make git commits
- Run commands in the terminal
- Edit files
- Keep a browser/VS Code session open

## Preventing Codespace Deletion

### Method 1: Regular Connection (Recommended)

Connect to your codespace at least once every 30 days:

```bash
# View all your codespaces
gh codespace list

# Connect to a specific codespace
gh codespace ssh -c CODESPACE_NAME

# Or use the web interface
# Visit: https://github.com/codespaces
```

### Method 2: Automated Keep-Alive Script

Create a scheduled task to connect to your codespace periodically:

```bash
# Add to your local crontab (runs every 7 days)
0 0 */7 * * gh codespace ssh -c YOUR_CODESPACE_NAME -- echo "keep-alive"
```

### Method 3: GitHub Actions Workflow

Use the automated workflow included in this repository (see `.github/workflows/codespace-monitoring.yml`)

### Method 4: Codespace Management via CLI

Install and use GitHub CLI for better codespace management:

```bash
# Install GitHub CLI
# macOS: brew install gh
# Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md
# Windows: See https://github.com/cli/cli/releases

# List all codespaces
gh codespace list

# View codespace details
gh codespace view -c CODESPACE_NAME

# Connect to codespace
gh codespace code -c CODESPACE_NAME

# Delete inactive codespaces manually
gh codespace delete -c CODESPACE_NAME
```

## Best Practices

### 1. Use Multiple Codespaces Strategically

- **Main development**: Active development work
- **Testing/Staging**: Separate codespace for testing
- **Documentation**: Dedicated codespace for docs

### 2. Codespace Naming Convention

Use descriptive names to identify purpose:
```
PROJECT_NAME-feature-FEATURE_NAME
PROJECT_NAME-bugfix-BUG_ID
PROJECT_NAME-docs-TOPIC
```

### 3. Regular Cleanup

Review and delete unused codespaces monthly:

```bash
# List all codespaces with details
gh codespace list --json name,state,lastUsedAt

# Delete old codespaces
gh codespace delete -c CODESPACE_NAME
```

### 4. Configure Codespace Settings

In your repository's `.devcontainer/devcontainer.json`:

```json
{
  "image": "mcr.microsoft.com/devcontainers/universal:2",
  "features": {},
  "customizations": {
    "vscode": {
      "settings": {
        "files.autoSave": "afterDelay"
      }
    }
  },
  "postCreateCommand": "echo 'Codespace initialized'",
  "remoteUser": "codespace"
}
```

### 5. Use Prebuilds

Enable prebuilds for faster codespace startup:
- Go to repository Settings → Codespaces
- Enable prebuilds for main branches
- Configure prebuild triggers

## Monitoring and Alerts

### Email Notifications

GitHub sends email notifications when codespaces are approaching deletion:
- **7 days before deletion**: First warning
- **3 days before deletion**: Second warning
- **1 day before deletion**: Final warning

**Action Required**: Click "Continue using" link in the email or connect to the codespace.

### Dashboard Monitoring

Regularly check your codespace dashboard:
- Visit: https://github.com/codespaces
- Review "Retention period" column
- Take action on codespaces approaching deletion

## Automated Monitoring Script

Use the included monitoring script to track codespace status:

```bash
# Run the codespace monitoring script
./scripts/monitor-codespaces.sh

# View codespace retention status
./scripts/check-codespace-retention.sh
```

## Troubleshooting

### Codespace Deleted Accidentally

**Prevention**: 
- Enable GitHub backup/sync for your work
- Regular git commits and pushes
- Use persistent storage (dotfiles repository)

**Recovery**:
- Recent work: Check git history on GitHub
- Uncommitted work: Generally unrecoverable
- Create new codespace from the same branch

### Cannot Connect to Codespace

1. Check codespace status: `gh codespace list`
2. Restart codespace: `gh codespace rebuild -c CODESPACE_NAME`
3. Check GitHub status page: https://www.githubstatus.com/

### Codespace Running Slowly

1. Check resource usage in codespace dashboard
2. Consider upgrading machine type
3. Clean up unused files/dependencies
4. Restart codespace

## Cost Optimization

### Free Tier Limits

GitHub Free/Pro accounts include:
- 120 core-hours per month (Free)
- 180 core-hours per month (Pro)
- 15 GB storage per month

### Cost-Saving Tips

1. **Stop codespaces when not in use**:
   ```bash
   gh codespace stop -c CODESPACE_NAME
   ```

2. **Use smaller machine types** for simple tasks

3. **Delete unused codespaces** regularly

4. **Use prebuilds** to reduce startup time and core-hour usage

5. **Set idle timeout**:
   - Default: 30 minutes
   - Configure in GitHub settings

## Integration with This Repository

### Quick Start

1. **Create codespace** from this repository:
   ```bash
   gh codespace create --repo dofaromg/flow-tasks
   ```

2. **Connect to codespace**:
   ```bash
   gh codespace code
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r particle_core/requirements.txt
   npm install
   ```

4. **Start development**:
   ```bash
   # Python development
   python particle_core/demo.py demo
   
   # Next.js development
   npm run dev
   ```

### Repository-Specific Configuration

This repository includes:
- `.devcontainer/devcontainer.json`: Base configuration
- `scripts/monitor-codespaces.sh`: Monitoring script
- `.github/workflows/codespace-monitoring.yml`: Automated monitoring workflow

## Additional Resources

- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
- [Codespace Lifecycle](https://docs.github.com/en/codespaces/developing-in-codespaces/codespaces-lifecycle)
- [Managing Codespaces](https://docs.github.com/en/codespaces/managing-your-codespaces)
- [GitHub CLI Documentation](https://cli.github.com/manual/)

## Quick Reference Commands

```bash
# List all codespaces
gh codespace list

# Create new codespace
gh codespace create --repo OWNER/REPO

# Connect to codespace
gh codespace code -c CODESPACE_NAME
gh codespace ssh -c CODESPACE_NAME

# Stop codespace
gh codespace stop -c CODESPACE_NAME

# Delete codespace
gh codespace delete -c CODESPACE_NAME

# View codespace logs
gh codespace logs -c CODESPACE_NAME

# Port forwarding
gh codespace ports -c CODESPACE_NAME
```

## Summary

To prevent codespace deletion:
1. ✅ Connect to your codespace at least once every 30 days
2. ✅ Enable email notifications and respond promptly
3. ✅ Use automated monitoring and keep-alive scripts
4. ✅ Regular cleanup of unused codespaces
5. ✅ Commit and push work frequently

For the **miniature computing-machine** codespace mentioned in the notification:
- **Action Required**: Connect before December 20, 2025
- **Quick Action**: Visit https://github.com/codespaces and click "Continue using"
- **Alternative**: Run `gh codespace code` or `gh codespace ssh` to keep it active

---

**Last Updated**: 2025-12-13  
**Repository**: dofaromg/flow-tasks
