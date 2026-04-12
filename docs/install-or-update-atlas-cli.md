# Install or Update the Atlas CLI

Install the Atlas CLI to quickly provision and manage Atlas database deployments from the terminal.

To verify packages before installation, see [Verify the Integrity of Atlas CLI Packages](https://mongodbcom-cdn.staging.corp.mongodb.com/docs/atlas/cli/verify-packages/#std-label-verify-packages).

## Install the Atlas CLI

Select one of the following installation methods and follow the steps to install the Atlas CLI.

To check whether your operating system is compatible with the Atlas CLI, see [Check Compatibility](https://mongodbcom-cdn.staging.corp.mongodb.com/docs/atlas/cli/compatibility/#std-label-compatibility-atlas-cli).

### Homebrew

#### Complete the Prerequisites

To install the Atlas CLI using Homebrew, you must:

1. Use a MacOS or Linux operating system.
2. Install [Homebrew](https://brew.sh/).

#### Install and Verify

Install the Atlas CLI and [`mongosh`](https://www.mongodb.com/docs/mongodb-shell/#mongodb-binary-bin.mongosh):

```sh
brew install mongodb-atlas
```

You can also use:

```sh
brew install mongodb-atlas-cli
```

> You can't install the Atlas CLI alone on Homebrew.

Verify successful installation:

```sh
atlas
```

### Yum

#### Configure `yum` for your edition of MongoDB

For **MongoDB Community Edition**, create `/etc/yum.repos.d/mongodb-org-7.0.repo` (replace `7.0` as needed).

**RHEL**

```text
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
```

**Amazon Linux 2023**

```text
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2023/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
```

For **MongoDB Enterprise Edition**, create `/etc/yum.repos.d/mongodb-enterprise-7.0.repo` (replace `7.0` as needed).

**RHEL**

```text
[mongodb-enterprise-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.com/yum/redhat/$releasever/mongodb-enterprise/7.0/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
```

**Amazon Linux 2023**

```text
[mongodb-enterprise-7.0]
name=MongoDB Enterprise Repository
baseurl=https://repo.mongodb.com/yum/amazon/2023/mongodb-enterprise/7.0/$basearch/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
```

Install Atlas CLI and `mongosh`:

```sh
sudo yum install -y mongodb-atlas
```

Install Atlas CLI only:

```sh
sudo yum install -y mongodb-atlas-cli
```

Verify installation:

```sh
atlas
```

### Apt

#### Complete the Prerequisites

Install `gnupg` and `curl`:

```sh
sudo apt-get install gnupg curl
```

#### Import the public key used by `apt`

```sh
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
  --dearmor
```

A successful command returns `OK`.

#### Create list files for your distribution

For **MongoDB Community Edition**:

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

For **MongoDB Enterprise Edition**:

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

Refresh package database:

```sh
sudo apt-get update
```

Install Atlas CLI and `mongosh`:

```sh
sudo apt-get install -y mongodb-atlas
```

Install Atlas CLI only:

```sh
sudo apt-get install -y mongodb-atlas-cli
```

Verify installation:

```sh
atlas
```

### Chocolatey

#### Complete the Prerequisites

1. Ensure your system meets [Chocolatey requirements](https://docs.chocolatey.org/en-us/choco/setup#requirements).
2. Install Chocolatey by following [Installing Chocolatey](https://docs.chocolatey.org/en-us/choco/setup#installing-chocolatey).

#### Install and Verify

```shell
choco install mongodb-atlas
```

When prompted, enter `A` to confirm installation. Close and reopen your terminal after installation.

Verify:

```sh
atlas
```

### Docker

#### Complete the Prerequisites

Install [Docker Engine](https://docs.docker.com/engine/install/) or [Docker Desktop](https://docs.docker.com/desktop/).

#### Pull and Use the Image

Pull latest image:

```sh
docker pull mongodb/atlas
```

Pull specific version:

```sh
docker pull mongodb/atlas:<tag>
```

To run Atlas CLI commands with Docker, see [Run Atlas CLI Commands with Docker](https://mongodbcom-cdn.staging.corp.mongodb.com/docs/atlas/cli/atlas-cli-docker/#std-label-atlas-cli-docker).

### Download Binary

Download and extract the binary for your platform:

- Windows: [.zip](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_windows_x86_64.zip), [.msi](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_windows_x86_64.msi)
- MacOS: [.zip (x86-64)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_macos_x86_64.zip), [.zip (ARM)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_macos_arm64.zip)
- Ubuntu/Debian: [.deb (x86-64)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_x86_64.deb), [.deb (ARM)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_arm64.deb)
- RHEL/CentOS/SLES/AMZ: [.rpm (x86-64)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_x86_64.rpm), [.rpm (ARM)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_arm64.rpm)
- Linux: [.tar.gz (x86-64)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_x86_64.tar.gz), [.tar.gz (ARM)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_arm64.tar.gz)

Replace or remove any existing MongoDB CLI binaries to prevent conflicts, then run the executable.

(Optional) Add Atlas CLI to your `PATH`:

```sh
cd atlascli_1.51.0-macOS_x86_64
mv atlas /usr/local/bin
```

Verify installation:

```sh
atlas
```

## Update the Atlas CLI

Follow the method matching your installation.

### Homebrew

```sh
brew update
brew upgrade mongodb-atlas
```

Or:

```sh
brew update
brew upgrade mongodb-atlas-cli
```

Verify:

```sh
atlas --version
```

### Yum

```sh
yum update mongodb-atlas
```

Or:

```sh
yum update mongodb-atlas-cli
```

Verify:

```sh
atlas --version
```

### Apt

```sh
sudo apt-get install --only-upgrade mongodb-atlas
```

Or:

```sh
sudo apt-get install --only-upgrade mongodb-atlas-cli
```

Verify:

```sh
atlas --version
```

### Chocolatey

```shell
choco upgrade mongodb-atlas
```

Verify:

```sh
atlas --version
```

### Download Binary

- Remove existing Atlas CLI binaries.
- Download and extract the latest binary for your platform.
- Run the executable.

Verify:

```sh
atlas --version
```

## Take the Next Steps

[Connect from the Atlas CLI](https://mongodbcom-cdn.staging.corp.mongodb.com/docs/atlas/cli/connect-atlas-cli/#std-label-connect-atlas-cli) to start using the [Atlas CLI commands](https://mongodbcom-cdn.staging.corp.mongodb.com/docs/atlas/cli/command/atlas/#std-label-atlas).
