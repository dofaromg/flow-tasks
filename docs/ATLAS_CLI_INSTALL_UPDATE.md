# Install or Update the Atlas CLI
# 安裝或更新 Atlas CLI

Use the Atlas CLI to quickly provision and manage Atlas database deployments from the terminal.

使用 Atlas CLI 從終端機快速配置和管理 Atlas 資料庫部署。

- Package integrity verification / 套件完整性驗證: [Verify the Integrity of Atlas CLI Packages](https://www.mongodb.com/docs/atlas/cli/verify-packages/#std-label-verify-packages)
- OS compatibility / 作業系統相容性: [Check Compatibility](https://www.mongodb.com/docs/atlas/cli/compatibility/#std-label-compatibility-atlas-cli)

---

## Install the Atlas CLI / 安裝 Atlas CLI

Select one of the following installation methods and follow the steps to install the Atlas CLI.

選擇以下其中一種安裝方法並按照步驟安裝 Atlas CLI。

### Homebrew

#### Complete the Prerequisites / 完成先決條件

To install the Atlas CLI using Homebrew, you must:

1. Use a MacOS or Linux operating system.
2. Install [Homebrew](https://brew.sh/).

#### Install and Verify / 安裝並驗證

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

---

### Yum

#### Configure `yum` for your edition of MongoDB / 為您的 MongoDB 版本配置 `yum`

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

---

### Apt

#### Complete the Prerequisites / 完成先決條件

Install `gnupg` and `curl`:

```sh
sudo apt-get install gnupg curl
```

#### Import the public key used by `apt` / 匯入 `apt` 使用的公開金鑰

```sh
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
  --dearmor
```

A successful command returns `OK`.

#### Create list files for your distribution / 為您的發行版建立清單檔案

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
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```

**Debian 11 (Bullseye)**

```sh
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian bullseye/mongodb-org/7.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
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
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.com/apt/debian bullseye/mongodb-enterprise/7.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-enterprise.list
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

---

### Chocolatey

#### Complete the Prerequisites / 完成先決條件

1. Ensure your system meets [Chocolatey requirements](https://docs.chocolatey.org/en-us/choco/setup#requirements).
2. Install Chocolatey by following [Installing Chocolatey](https://docs.chocolatey.org/en-us/choco/setup#installing-chocolatey).

#### Install and Verify / 安裝並驗證

```shell
choco install mongodb-atlas
```

When prompted, enter `A` to confirm installation. Close and reopen your terminal after installation.

Verify:

```sh
atlas
```

---

### Docker

#### Complete the Prerequisites / 完成先決條件

Install [Docker Engine](https://docs.docker.com/engine/install/) or [Docker Desktop](https://docs.docker.com/desktop/).

#### Pull and Use the Image / 拉取並使用映像

Pull latest image:

```sh
docker pull mongodb/atlas
```

Pull specific version:

```sh
docker pull mongodb/atlas:<tag>
```

To run Atlas CLI commands with Docker, see [Run Atlas CLI Commands with Docker](https://www.mongodb.com/docs/atlas/cli/atlas-cli-docker/#std-label-atlas-cli-docker).

---

### Download Binary / 下載二進位檔案

Download and extract the binary for your platform:

- Windows: [.zip](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_windows_x86_64.zip), [.msi](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_windows_x86_64.msi)
- MacOS: [.zip (x86-64)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_macos_x86_64.zip), [.zip (ARM)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_macos_arm64.zip)
- Ubuntu/Debian: [.deb (x86-64)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_x86_64.deb), [.deb (ARM)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_arm64.deb)
- RHEL/CentOS/SLES/AMZ: [.rpm (x86-64)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_x86_64.rpm), [.rpm (ARM)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_arm64.rpm)
- Linux: [.tar.gz (x86-64)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_x86_64.tar.gz), [.tar.gz (ARM)](https://fastdl.mongodb.org/mongocli/mongodb-atlas-cli_1.51.0_linux_arm64.tar.gz)

Replace or remove any existing MongoDB CLI binaries to prevent conflicts, then add the Atlas CLI to your `PATH`:

```sh
cd atlascli_<version>-macOS_x86_64

# Option 1: Install system-wide (may require sudo):
sudo mv atlas /usr/local/bin

# Option 2: Install to a user-writable directory (ensure it's on your PATH):
# mkdir -p "$HOME/.local/bin"
# mv atlas "$HOME/.local/bin/"
# export PATH="$HOME/.local/bin:$PATH"
```

Verify installation:

```sh
atlas
```

---

## Update the Atlas CLI / 更新 Atlas CLI

Follow the method matching your installation.

按照您安裝時所使用的方法進行更新。

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

### Download Binary / 下載二進位檔案

- Remove existing Atlas CLI binaries.
- Download and extract the latest binary for your platform.
- Run the executable.

Verify:

```sh
atlas --version
```

---

## Next Steps / 後續步驟

[Connect from the Atlas CLI](https://www.mongodb.com/docs/atlas/cli/connect-atlas-cli/#std-label-connect-atlas-cli) to start using the [Atlas CLI commands](https://www.mongodb.com/docs/atlas/cli/command/atlas/#std-label-atlas).
