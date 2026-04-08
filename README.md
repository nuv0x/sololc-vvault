# 🛡️ Vvault (vlt)

**An elegant, functional, and secure CLI authenticator built for power users.**

`Vvault` (pronounced *Volt*) is a modern 2FA (Two-Factor Authentication) secret manager designed for the terminal. It balances industrial-grade security with a "bright and shiny" user experience, allowing you to manage your TOTP tokens with style and speed.

## ✨ Features

* **⚡️ Live Dashboard**: A visually stunning, real-time terminal UI to monitor all your TOTP codes and their expiration countdowns.
* **🔒 Local-First Security**: Secrets are stored physically in the `~/.vlt/` directory with strict file permissions.
* **📂 Smart Import**: Seamlessly import accounts via QR code images or standard `otpauth://` URL links.
* **📋 Clipboard Integration**: Copy verification codes directly to your clipboard with a single flag for lightning-fast logins.
* **🛠️ Modern Tech Stack**: Powered by `uv`, `Typer`, `Rich`, and `QReader` for a lightweight yet robust experience.

## 🚀 Installation

Ensure you have **Python 3.12+** installed. We recommend using [uv](https://github.com/astral-sh/uv) for the fastest installation and performance.

```bash
# Clone the repository
git clone [https://github.com/nuv0x/Vvault.git](https://github.com/nuv0x/Vvault.git)
cd Vvault

# Install dependencies and install the tool in editable mode
uv sync
pip install -e .
```

## 📖 Usage Guide
Vvault uses the short and punchy vlt command.

1. Initialization
Set up your secure storage directory at ~/.vlt/.
```bash
vlt init
```

2. Adding Accounts
You can add accounts manually or import them intelligently via QR codes.

Manual Add:
```bash
vlt add github --secret KHR2UEJ33JJG... --issuer GitHub --category Dev
```

QR Code Import:
```bash
vlt import --qr ./path/to/qr_code.png
```

URL Import:
```bash
vlt import --url "otpauth://totp/Service:User?secret=XYZ..."
```

3. Management & Viewing
Launch Live Dashboard:
```bash
vlt dash
```

Get a Single Code:
```bash
vlt get github          # Display the code
vlt get github --copy   # Display and automatically copy to clipboard
```

List All Accounts:
```bash
vlt list
```

4. Backup
Keep your data safe by exporting your vault.
```bash
vlt backup ./my_backup.yaml
```

## 🛠️ Project Structure
The project follows a modular, functional design for clarity and maintainability:
* src/relay_2fa/core/: Core logic layer containing TOTP generation, physical storage, and vault operations.
* src/relay_2fa/main.py: Interaction layer featuring the polished CLI interface built with Typer and Rich.
* ~/.vlt/: The default local data storage path.

## 🤝 Contributing
Contributions are welcome! If you have ideas for new features (such as supporting the Google Migration protocol or adding Master Password encryption), please feel free to:
* Fork the Project
* Create your Feature Branch (git checkout -b feature/AmazingFeature)
* Commit your Changes (git commit -m 'Add some AmazingFeature')
* Push to the Branch (git push origin feature/AmazingFeature)
* Open a Pull Request
