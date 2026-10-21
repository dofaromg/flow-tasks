# Install or Update the Atlas CLI

Use the Atlas CLI to provision and manage Atlas database deployments from the terminal.

- Package integrity verification: [Verify the Integrity of Atlas CLI Packages](https://mongodbcom-cdn.staging.corp.mongodb.com/docs/atlas/cli/verify-packages/#std-label-verify-packages)
- OS compatibility: [Check Compatibility](https://mongodbcom-cdn.staging.corp.mongodb.com/docs/atlas/cli/compatibility/#std-label-compatibility-atlas-cli)

## Install the Atlas CLI

Choose one installation method and follow the matching steps.

### Homebrew (macOS or Linux)

#### Prerequisites

1. macOS or Linux
2. Homebrew installed

#### Install

```sh
brew install mongodb-atlas
```

> You can also run `brew install mongodb-atlas-cli`, but both commands install Atlas CLI and `mongosh` together.

#### Verify

```sh
atlas
```

---

### Yum

#### Configure the repository

Create a repo file under `/etc/yum.repos.d/` based on your MongoDB edition and distro.

##### MongoDB Community Edition (`mongodb-org-7.0.repo`)

**RHEL**

```ini
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
```

**Amazon Linux 2023**

```ini
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2023/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
```

##### MongoDB Enterprise Edition (`mongodb-enterprise-7.0.repo`)

**RHEL**

```ini
[mongodb-enterprise-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.com/yum/redhat/$releasever/mongodb-enterprise/7.0/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
```

**Amazon Linux 2023**

```ini
[mongodb-enterprise-7.0]
name=MongoDB Enterprise Repository
baseurl=https://repo.mongodb.com/yum/amazon/2023/mongodb-enterprise/7.0/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
```

#### Install

Install Atlas CLI + `mongosh`:

```sh
sudo yum install -y mongodb-atlas
```

Install Atlas CLI only:

```sh
sudo yum install -y mongodb-atlas-cli
```

#### Verify

```sh
atlas
```

---

### Apt

#### Prerequisites

```sh
sudo apt-get install gnupg curl
```

#### Import the GPG key

```sh
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
  --dearmor
```

#### Add repository list file

Use the list file command matching your OS/version.

##### MongoDB Community Edition

**Ubuntu 22.04 (Jammy)**

```sh
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```

**Ubuntu 20.04 (Focal)**

```sh
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```

**Ubuntu 18.04 (Bionic)**

```sh
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```

**Debian 12 (Bookworm)**

```sh
echo "deb http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```

**Debian 11 (Bullseye)**

```sh
echo "deb http://repo.mongodb.org/apt/debian bullseye/mongodb-org/7.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```

##### MongoDB Enterprise Edition

**Ubuntu 22.04 (Jammy)**

```sh
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.com/apt/ubuntu jammy/mongodb-enterprise/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-enterprise.list
```

**Ubuntu 20.04 (Focal)**

```sh
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.com/apt/ubuntu focal/mongodb-enterprise/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-enterprise.list
```

**Ubuntu 18.04 (Bionic)**

```sh
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.com/apt/ubuntu bionic/mongodb-enterprise/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-enterprise.list
```

**Debian 11 (Bullseye)**

```sh
echo "deb http://repo.mongodb.com/apt/debian bullseye/mongodb-enterprise/7.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-enterprise.list
```

#### Install

```sh
sudo apt-get update
sudo apt-get install -y mongodb-atlas
```

Install Atlas CLI only:

```sh
sudo apt-get install -y mongodb-atlas-cli
```

#### Verify

```sh
atlas
```

---

### Chocolatey

#### Prerequisites

1. Verify Chocolatey system requirements.
2. Install Chocolatey via `cmd.exe` or `PowerShell.exe`.

#### Install

```sh
choco install mongodb-atlas
```

When prompted, enter `A`, then restart your terminal.

#### Verify

```sh
atlas
```

---

### Docker

#### Prerequisite

Install Docker Engine or Docker Desktop.

#### Pull image

Latest:

```sh
docker pull mongodb/atlas
```

Specific version:

```sh
docker pull mongodb/atlas:<tag>
```

For usage details, see [Run Atlas CLI Commands with Docker](https://mongodbcom-cdn.staging.corp.mongodb.com/docs/atlas/cli/atlas-cli-docker/#std-label-atlas-cli-docker).

---

### Download Binary

Download the correct package for your OS from MongoDB fast download URLs:

- Windows: `.zip` / `.msi`
- macOS: `.zip` (`x86_64` / `arm64`)
- Ubuntu/Debian: `.deb` (`x86_64` / `arm64`)
- RHEL/CentOS/SLES/AMZ: `.rpm` (`x86_64` / `arm64`)
- Linux: `.tar.gz` (`x86_64` / `arm64`)

Example (move binary into `PATH`):

```sh
cd atlascli_1.51.0-macOS_x86_64
mv atlas /usr/local/bin
```

#### Verify

```sh
atlas
```

## Update the Atlas CLI

Use the update command for the same package manager used for installation.

### Homebrew

```sh
brew update
brew upgrade mongodb-atlas
```

Or if installed via the alternate package name:

```sh
brew update
brew upgrade mongodb-atlas-cli
```

### Yum

```sh
yum update mongodb-atlas
```

Or Atlas CLI only:

```sh
yum update mongodb-atlas-cli
```

### Apt

```sh
sudo apt-get install --only-upgrade mongodb-atlas
```

Or Atlas CLI only:

```sh
sudo apt-get install --only-upgrade mongodb-atlas-cli
```

### Chocolatey

```sh
choco upgrade mongodb-atlas
```

### Download Binary

1. Remove old Atlas CLI binary.
2. Download and extract the newest binary for your OS.
3. Replace the executable in your `PATH`.

### Verify update

```sh
atlas --version
```

## Next Steps

- [Connect from the Atlas CLI](https://mongodbcom-cdn.staging.corp.mongodb.com/docs/atlas/cli/connect-atlas-cli/#std-label-connect-atlas-cli)
- [Atlas CLI command reference](https://mongodbcom-cdn.staging.corp.mongodb.com/docs/atlas/cli/command/atlas/#std-label-atlas)
