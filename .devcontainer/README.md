# Development Container Configuration

## Overview

This directory contains the configuration for GitHub Codespaces and VS Code Dev Containers.

## Configuration

### devcontainer.json

The `devcontainer.json` file defines:

- **Base Image**: `mcr.microsoft.com/devcontainers/universal:2`
  - Includes: Python, Node.js, Git, Docker, and common development tools

- **Features**:
  - GitHub CLI (`gh`) for codespace management
  - kubectl, Helm, and Minikube for Kubernetes development

- **VS Code Extensions**:
  - Python language support
  - Docker and Kubernetes tools
  - YAML support
  - GitHub Copilot

- **Post-Create Command**:
  - Automatically installs Python dependencies
  - Installs Node.js dependencies
  - Sets up the development environment

- **Port Forwarding**:
  - Port 3000: Next.js development server
  - Port 8000: Python API server

## Usage

### Creating a Codespace

1. **Via GitHub Web**:
   - Go to repository page
   - Click "Code" → "Codespaces" → "Create codespace on main"

2. **Via GitHub CLI**:
   ```bash
   gh codespace create --repo dofaromg/flow-tasks
   ```

3. **Via VS Code**:
   - Install "GitHub Codespaces" extension
   - Command Palette → "Codespaces: Create New Codespace"

### Customization

To customize the development environment:

1. **Add VS Code Extensions**:
   ```json
   "extensions": [
     "your-publisher.your-extension"
   ]
   ```

2. **Add Development Tools**:
   ```json
   "features": {
     "ghcr.io/devcontainers/features/tool-name:1": {}
   }
   ```

3. **Modify Post-Create Command**:
   ```json
   "postCreateCommand": "bash scripts/setup-dev.sh"
   ```

### Environment Variables

Set environment variables in your codespace:

```bash
# In codespace terminal
export VARIABLE_NAME=value

# Or add to ~/.bashrc for persistence
echo 'export VARIABLE_NAME=value' >> ~/.bashrc
```

For secrets, use GitHub Codespaces secrets:
- Go to: https://github.com/settings/codespaces
- Add your secrets
- They'll be available as environment variables in codespaces

## Lifecycle Management

### Preventing Deletion

Your codespace will be deleted after 30 days of inactivity. To prevent deletion:

1. **Connect regularly** (recommended: at least once every 2 weeks)
2. **Use monitoring scripts**: `./scripts/monitor-codespaces.sh`
3. **Enable automated workflow**: See `.github/workflows/codespace-monitoring.yml`

### Manual Management

```bash
# List all codespaces
gh codespace list

# Stop codespace (saves core-hours)
gh codespace stop -c CODESPACE_NAME

# Delete codespace
gh codespace delete -c CODESPACE_NAME

# Rebuild codespace (apply config changes)
gh codespace rebuild -c CODESPACE_NAME
```

## Troubleshooting

### Codespace Won't Start

1. Check GitHub status: https://www.githubstatus.com/
2. Try rebuilding: `gh codespace rebuild`
3. Delete and recreate if necessary

### Extensions Not Loading

1. Rebuild codespace: `gh codespace rebuild`
2. Check extension compatibility
3. Manually install: Extensions view → Install

### Dependencies Not Installing

1. Check `postCreateCommand` logs in the terminal
2. Manually run: 
   ```bash
   pip install -r requirements.txt
   npm install
   ```
3. Check for network issues or rate limits

### Port Not Forwarding

1. Check port is listening: `netstat -tuln | grep PORT`
2. Forward manually: Ports view → Forward a Port
3. Check firewall settings

## Resources

- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
- [Dev Container Specification](https://containers.dev/)
- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)
- [Codespace Management Guide](../CODESPACE_MANAGEMENT.md)

## Support

For issues or questions:
1. Check [CODESPACE_MANAGEMENT.md](../CODESPACE_MANAGEMENT.md)
2. Open an issue in this repository
3. Contact repository maintainers
