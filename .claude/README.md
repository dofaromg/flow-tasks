# Claude AI Integration

This directory contains Claude AI integration files that enhance repository workflows and code review processes.

## Directory Structure

```
.claude/
├── agents/           # Custom AI agents
├── commands/         # Command templates
└── skills/          # Reusable skills and utilities
```

## Contents

### Agents (`agents/`)

Custom AI agents that can be invoked for specific tasks:

- **code-reviewer.md**: Performs thorough code reviews focusing on Python/Jupyter best practices and project-specific standards

### Commands (`commands/`)

Command templates for various repository tasks:

- **add-registry.md**: Add entries to a registry
- **link-review.md**: Review and validate links
- **model-check.md**: Check model configurations
- **notebook-review.md**: Quick notebook review
- **review-issue.md**: Review GitHub issues
- **review-pr-ci.md**: Review pull requests with CI integration
- **review-pr.md**: Review pull requests

### Skills (`skills/`)

Reusable skills and utilities:

- **cookbook-audit/**: Audit and validation tools for notebooks
  - `SKILL.md`: Skill documentation
  - `style_guide.md`: Style guide and best practices
  - `validate_notebook.py`: Automated notebook validation script
  - `.gitignore`: Ignore temporary files

## Usage

These files are used by Claude AI to provide enhanced functionality when working with this repository. They define:

1. **Custom agents** with specific expertise and tool access
2. **Command workflows** that can be invoked to perform common tasks
3. **Skills** that provide reusable functionality

## Origin

This structure was implemented based on the [Anthropic Claude Cookbooks repository](https://github.com/dofaromg/claude-cookbooks/commit/b5caba8debed0ffdef166a2baf8da0c7f3461b50).

## Customization

While these files were originally designed for notebook-based repositories, they provide a useful framework that can be adapted for the flow-tasks repository's specific needs:

- GKE deployment configurations
- Particle Language Core System
- CI/CD workflows
- GitOps patterns

Feel free to modify or extend these files to better suit this repository's requirements.
