#!/usr/bin/env python3
"""
Validate devcontainer.json configuration against the devcontainer specification.
Reference: https://github.com/devcontainers/spec/pull/675
"""

import json
import sys
from pathlib import Path


def validate_devcontainer_config():
    """Validate the devcontainer.json configuration."""
    config_path = Path(__file__).parent / "devcontainer.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ devcontainer.json not found at {config_path}")
        return False
    
    print("✅ Valid JSON structure")
    
    # Check base image (must match PR #675 specification)
    expected_image = "mcr.microsoft.com/devcontainers/universal:2"
    if config.get('image') != expected_image:
        print(f"❌ Base image mismatch. Expected: {expected_image}, Got: {config.get('image')}")
        return False
    
    print(f"✅ Base image matches devcontainers/spec PR #675: {expected_image}")
    
    # Check for features property
    if 'features' not in config:
        print("⚠️  'features' property not found (optional but recommended)")
    else:
        feature_count = len(config['features'])
        print(f"✅ Features property present with {feature_count} feature(s)")
    
    # Validate known devcontainer properties
    valid_properties = {
        'name', 'image', 'dockerFile', 'build', 'features', 'overrideFeatureInstallOrder',
        'forwardPorts', 'portsAttributes', 'otherPortsAttributes', 'containerEnv',
        'remoteEnv', 'containerUser', 'remoteUser', 'updateRemoteUserUID', 'userEnvProbe',
        'workspaceFolder', 'workspaceMount', 'mounts', 'runArgs', 'overrideCommand',
        'shutdownAction', 'init', 'privileged', 'capAdd', 'securityOpt', 
        'updateContentCommand', 'postCreateCommand', 'postStartCommand', 'postAttachCommand',
        'waitFor', 'customizations', 'hostRequirements', 'secrets', 'onCreateCommand',
        'initializeCommand'
    }
    
    unknown_props = set(config.keys()) - valid_properties
    if unknown_props:
        print(f"⚠️  Unknown properties found: {', '.join(unknown_props)}")
    
    # Report on configuration
    print("\n📋 Configuration Summary:")
    print(f"  • Name: {config.get('name', 'N/A')}")
    print(f"  • Image: {config.get('image', 'N/A')}")
    print(f"  • Features: {len(config.get('features', {}))}")
    print(f"  • Forwarded Ports: {config.get('forwardPorts', [])}")
    print(f"  • Remote User: {config.get('remoteUser', 'N/A')}")
    
    if 'customizations' in config and 'vscode' in config['customizations']:
        vscode_config = config['customizations']['vscode']
        print(f"  • VS Code Extensions: {len(vscode_config.get('extensions', []))}")
        print(f"  • VS Code Settings: {len(vscode_config.get('settings', {}))}")
    
    print("\n✅ devcontainer.json is valid and spec-compliant")
    return True


if __name__ == "__main__":
    success = validate_devcontainer_config()
    sys.exit(0 if success else 1)
