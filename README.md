<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/nuv0x/sololc-vvault@main/assets/sololc-vvault.svg" width="160" height="160" alt="vlt logo">
</p>

# 🛡️ sololc-vvault (vlt)

[![PyPI version](https://img.shields.io/pypi/v/sololc-vvault.svg?color=blue)](https://pypi.org/project/sololc-vvault/)
[![Python versions](https://img.shields.io/pypi/pyversions/sololc-vvault.svg)](https://pypi.org/project/sololc-vvault/)
[![License](https://img.shields.io/badge/License-BSD--3--Clause-orange.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Sponsor](https://img.shields.io/badge/Sponsor-Ko--fi-F16061?logo=ko-fi&logoColor=white)](https://ko-fi.com/sololc)

**Zero-Knowledge, Offline-First, and High-Performance CLI Authenticator.**

`vlt` (pronounced *Volt*) is a modern 2FA (Two-Factor Authentication) manager designed for the terminal. It provides industrial-grade security with a minimalist user experience, ensuring your TOTP secrets remain yours alone.

> 🚀 **Building fast, secure, and offline-first tools for the modern terminal.**
> 💡 **Passionate about developer productivity and system transparency.**
> 🏠 **Keep it local. ⚡ Keep it simple.**

---

## 🔒 Security Architecture

Unlike many common authenticators, `vlt` employs a strict **Zero-Knowledge** encryption model. Your data is never stored in plain text.

* **Data Stratification**: The storage model strictly separates unencrypted metadata (`service`, `email`, `alias`) from the actual secrets to allow rapid, zero-password vault indexing.
* **Key Derivation (KDF)**: We use **PBKDF2HMAC** with a SHA-256 primitives backend hashing across 100,000 iterations combined with a hardware-isolated secret salt to securely derive high-entropy keys from your Master Password.
* **Encryption**: The primary token payload blocks are armored using **AES-256 (Fernet specification)**, ensuring both payload confidentiality and absolute cryptographic authenticity.
* **Local-Only**: No cloud synchronization, no remote telemetry trackers, and zero external analytics. Your secure vault database lives exclusively in your designated local file system.

## ✨ Features

* **⚡️ Live Dashboard View**: An interactive terminal canvas powered by `Rich.Live` to monitor active tokens with live, real-time countdown progress bars.
* **📊 Minimalist Table Matrix**: High-scannable table output formatted through minimalist, clean-bordered frames for clean terminal logging histories.
* **🧹 Clean Memory Cleanup**: Transitory terminal screens clear out completely on loop exit (`transient=True`), avoiding active token shoulder-surfing leaks.
* **🚀 Shortcut Aliasing**: Configure rapid unique alias strings to bypass long query parameters during verification code lookups.

## 🚀 Installation

Ensure you have **Python 3.11+** installed. We recommend using [uv](https://github.com/astral-sh/uv) for the most optimal package environment experience.

```bash
# Clone the repository
git clone [https://github.com/nuv0x/sololc-vvault.git](https://github.com/nuv0x/sololc-vvault.git)
cd sololc-vvault

# Sync dependencies and install the tool in editable environment mode
uv sync
pip install -e .
```
## 📖 Usage Guide
sololc-vvault provides a clean, single-letter command interface exposed through the punchy vlt binary shorthand.

1. Initialization
Set up your encrypted SQLite database storage system baseline directory.
```bash
vlt init
```

2. Secure Token Entry
Securely encrypt and write a new base32 TOTP secret token string straight into the vault.
```bash
# Standard addition
vlt add github JBSWY3DPEHPK3PXP --email user@example.com

# Rapid addition configuring a custom shortcut alias
vlt add google JBSWY3DPEHPK3PXP --alias my-google
```

3. Verification Retrieval & Live Tracking
Unlock the vault using your Master Password and launch a real-time tracking dashboard. It will automatically update the token and countdown bar every second according to strict Unix Epoch 30-second windows.
```bash
# Get via standard service search name
vlt get github

# Narrow down specific instances across shared service names
vlt get github --email user@example.com

# Instant retrieval using your unique shortcut alias
vlt get my-google
```
4. Metadata Auditing
List all configured services, emails, and shortcut configurations at a glance without inputting your Master Password.
```bash
vlt list
```
5. Failure-Safe Removal
Permanently purge a secret entry from the vault indices using explicit protective warning confirmation flags.
```bash
vlt remove my-google
```

6. Atomic Backups
Perform a comprehensive SQLite PRAGMA integrity_check database structure health audit and export a timestamped backup clone file.
```bash
# Run a standard backup to the default directory (~/.sololc-vvault-backups/)
vlt backup

# Export a timestamped clone directly to a targeted path
vlt backup --output ~/Desktop/vault_backups/
```

7. Explicit Lockdowns
Forcefully clear active system execution parameters and run an explicit structural maintenance audit against the underlying environment storage framework.
```bash
vlt lock
```

## 🛠️ Project Structure
The codebase is engineered with structural performance, standard static compliance, and strict functional typing:
* main.py: The application entry point and central layout system orchestrated via Typer commands and custom terminal interceptors.
* Database Engine: Driven by highly optimized indexing maps (idx_secrets_service_email and idx_secrets_alias) utilizing local SQLite drivers.
* ~/.vlt/: The default local data storage path.

## ☕ Support the Project
If vlt makes your terminal life easier, consider supporting its development!

* [![Support me on Ko-fi](https://img.shields.io/badge/Support%20me%20on%20Ko--fi-F16061?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/sololc)


## 🤝 Contributing
Contributions are completely welcome! If you have functional ideas for security modifications or feature proposals, feel free to submit issues or pull requests.
