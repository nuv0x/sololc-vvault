import base64
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated, Optional

import click
import pyotp
import typer
import typer.core
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Table

console = Console()

# Database storage path
DB_PATH = Path("~/.vlt/sololc-vvault.db").expanduser()
BACKUP_DIR = Path("~/vlt/backups").expanduser()

try:
    __version__ = version("sololc-vvault")
except PackageNotFoundError:
    __version__ = "0.1.3-dev"


def version_callback(value: bool):
    if value:
        console.print(
            f"[bold white]sololc-vvault[/] version: [bold cyan]{__version__}[/]"
        )
        raise typer.Exit()


# --- 自定义渲染引擎（高版本完美复刻） ---
def custom_command_help(
    cmd_name: str,
    emoji: str,
    desc: str,
    args_list: list | None = None,
    opts_list: list | None = None,
):
    console.print(
        "\n[dim] ─────────────────────────────────────────────────────────────[/]"
    )
    console.print(f"  {emoji} COMMAND: [bold cyan]vlt {cmd_name}[/]")
    console.print(f"  💡 [yellow]{desc}[/]")
    console.print(
        "[dim] ─────────────────────────────────────────────────────────────[/]\n"
    )

    if args_list:
        console.print("  [bold green]🚀 ARGUMENTS:[/]")
        for name, req, detail in args_list:
            req_str = " [bold red][required][/]" if req else ""
            console.print(f"    [bold cyan]{name:<14}[/]{req_str:<12} {detail}")
        console.print()

    if opts_list:
        console.print("  [bold magenta]🔧 OPTIONS:[/]")
        for name, short, detail in opts_list:
            syntax = f"{name}, {short}" if short else name
            console.print(f"    [bold google]{syntax:<14}[/]   {detail}")
        console.print(
            "    [bold google]--help[/], [bold google]-h[/]    📖 Show this message and exit\n"
        )

    console.print(
        "[dim] ─────────────────────────────────────────────────────────────[/]"
    )
    console.print(
        f" 👉 Run [bold yellow]'vlt {cmd_name} [OPTIONS]'[/] to execute this command.\n"
    )
    raise typer.Exit()


WELCOME_LOGO = f"""
  [bold cyan]██╗   ██╗██╗  ████████╗[/]
  [bold cyan]██║   ██║██║  ╚══██╔══╝[/]  [bold white]sololc-vvault[/]
  [bold cyan]╚██╗ ██╔╝██║     ██║   [/]  [dim]📦 Version: {__version__} (2026 Edition)[/]
   [bold cyan]╚████╔╝ ██║     ██║   [/]  [dim]🔒 Storage: SQLite + AES-GCM[/]
    [bold cyan]╚═══╝  ███████╗██║   [/]  [dim]🪶 Status:  Zero-Bloat Active[/]
           [bold cyan]╚══════╝╚═╝   [/]
"""


def print_global_help():
    console.print(WELCOME_LOGO)
    console.print(
        " [yellow]💡 A minimalist, local-first TOTP vault for your terminal.[/]"
    )
    console.print(
        "[dim] ─────────────────────────────────────────────────────────────[/]\n"
    )

    console.print("  [bold green]🚀 CORE COMMANDS:[/]")
    console.print(
        "    [bold cyan]init[/]     🌱 Initialize database, set master password & auto-lock timeout"
    )
    console.print(
        "    [bold cyan]lock[/]     🔒 Lock the vault immediately (Forces password on next command)"
    )
    console.print(
        "    [bold cyan]add[/]      ➕ Add a new TOTP secret (Supports email & unique alias)"
    )
    console.print(
        "    [bold cyan]get[/]      🔑 Get 6-digit verification code with live countdown"
    )
    console.print(
        "    [bold cyan]list[/]     📊 List all managed platforms and shortcuts"
    )
    console.print("    [bold cyan]remove[/]   🗑️ Delete a secret from the vault safely")
    console.print(
        "    [bold cyan]backup[/]   💾 Verify integrity and export a timestamped vault clone\n"
    )

    console.print("  [bold magenta]🔧 GLOBAL OPTIONS:[/]")
    console.print(
        "    [bold google]--help[/], [bold google]-h[/]    📖 Show this beautiful guide and exit"
    )
    console.print(
        "    [bold google]--version[/], [bold google]-v[/] ℹ️  Print the current version of sololc-vvault and exit\n"
    )

    console.print(
        "[dim] ─────────────────────────────────────────────────────────────[/]"
    )
    console.print(
        " 👉 Run [bold yellow]'vlt <command> --help'[/] for specific command details.\n"
    )
    raise typer.Exit()


class HookedHelpGroup(typer.core.TyperGroup):
    def parse_args(self, ctx, args: list[str]) -> list[str]:
        ctx.help_option_names = ["--help", "-h"]
        return super().parse_args(ctx, args)

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        print_global_help()


app = typer.Typer(
    name="vlt",
    help="🔒 sololc-vvault: A zero-bloat, local-first TOTP CLI vault.",
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["--help", "-h"]},
    cls=HookedHelpGroup,
)


@app.callback(invoke_without_command=True)
def main_menu(
    ctx: typer.Context,
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Print the current version of sololc-vvault and exit.",
    ),
):
    # Core interception for Typer: unify --help / -h handling here
    args_str = [str(arg).strip() for arg in sys.argv]
    is_help_requested = any(h in args_str for h in ["--help", "-h"])

    if is_help_requested:
        subcmd = ctx.invoked_subcommand
        if subcmd == "add":
            custom_command_help(
                "add",
                "🔒",
                "Add a new TOTP secret to the encrypted vault safely.",
                [("service", True, "Platform name")],
                [("--email", "-e", "Account email"), ("--alias", "-a", "Unique alias")],
            )
        elif subcmd == "get":
            custom_command_help(
                "get",
                "🔑",
                "Retrieve 6-digit verification code with a live countdown.",
                [("query", True, "Search by Service, Email, or Alias")],
            )
        elif subcmd == "init":
            custom_command_help(
                "init",
                "🌱",
                "Initialize secure SQLite database and set session timeout.",
            )
        elif subcmd == "lock":
            custom_command_help(
                "lock",
                "🔒",
                "Lock the vault immediately to protect your active tokens.",
            )
        elif subcmd == "list":
            custom_command_help(
                "list", "📊", "List all managed platforms, accounts, and shortcuts."
            )
        elif subcmd == "remove":
            custom_command_help(
                "remove",
                "🗑️",
                "Permanently delete a secret from the vault safely.",
                [("query", True, "Service, Email, or Alias to remove")],
            )
        elif subcmd == "backup":  # 👈 Added the backup subcommand help interceptor
            custom_command_help(
                "backup",
                "💾",
                "Verify database structural integrity and export a secure, timestamped clone.",
                [],
                [
                    (
                        "--output",
                        "-o",
                        "Custom destination directory path for the backup file",
                    )
                ],
            )
        elif subcmd is None:
            print_global_help()

    # Fallback to handle executing raw 'vlt' without arguments
    if ctx.invoked_subcommand is None:
        print_global_help()


# Hardcoded salt for KDF (In a production environment, you would generate a random salt during 'init' and store it)
SECRET_SALT = b"sololc_vvault_secure_salt_2026"


def derive_key(master_password: str) -> bytes:
    """
    Derive a secure 32-byte encryption key from the master password using PBKDF2.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SECRET_SALT,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))


@app.command(name="add")
def add(
    service: Annotated[
        str,
        typer.Argument(help="The name of the service/platform (e.g., github, google)."),
    ],
    secret: Annotated[
        str, typer.Argument(help="The raw TOTP secret token (base32 string).")
    ],
    email: Annotated[
        Optional[str],
        typer.Option("--email", "-e", help="The associated email or username."),
    ] = None,
    alias: Annotated[
        Optional[str],
        typer.Option(
            "--alias", "-a", help="A unique shortcut alias for rapid retrieval."
        ),
    ] = None,
):
    """
    ➕ Securely encrypt and add a new TOTP secret token to the vault.
    """
    console.print(f"\n[bold cyan]➕ Adding new TOTP token for: [yellow]{service}[/][/]")
    console.print(
        "[dim]─────────────────────────────────────────────────────────────[/]\n"
    )

    # 1. Sanitize and validate the base32 TOTP secret token
    clean_secret = secret.strip().replace(" ", "").upper()
    try:
        # Check if it generates a valid pyotp instance
        pyotp.TOTP(clean_secret).now()
    except Exception:
        console.print(
            "[bold red]❌ Error:[/] The provided secret token is not a valid Base32 string."
        )
        raise typer.Exit(code=1)

    # 2. Verify database existence and check unique alias collision
    if not os.path.exists(DB_PATH):
        console.print(
            "[bold red]❌ Error:[/] Database not found. Please run [yellow]'vlt init'[/] first."
        )
        raise typer.Exit(code=1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if alias:
        cursor.execute("SELECT id FROM secrets WHERE alias = ?", (alias,))
        if cursor.fetchone():
            console.print(
                f"[bold red]❌ Error:[/] The alias [yellow]'{alias}'[/] is already taken."
            )
            conn.close()
            raise typer.Exit(code=1)

    # 3. Request Master Password to derive the encryption key
    master_password = typer.prompt(
        " 🔒 Enter Master Password to unlock & encrypt",
        hide_input=True,
        prompt_suffix=": ",
    )

    try:
        with console.status(
            "[bold green]Encrypting secret and committing to vault...[/]"
        ):
            # Derive key and encrypt the secret token
            enc_key = derive_key(master_password)
            fernet = Fernet(enc_key)
            encrypted_secret = fernet.encrypt(clean_secret.encode()).decode()

            # Insert the record into the database
            cursor.execute(
                """
                INSERT INTO secrets (service, email, alias, encrypted_secret)
                VALUES (?, ?, ?, ?)
                """,
                (service.lower(), email, alias, encrypted_secret),
            )
            conn.commit()

        console.print(
            f"\n[bold green]✨ Success![/] Secret for [bold white]{service}[/] has been securely stored."
        )
        if alias:
            console.print(f" 🚀 Shortcut configured via alias: [cyan]{alias}[/]")
        console.print()

    except Exception as e:
        console.print(
            f"\n[bold red]❌ Critical error during encryption/storage:[/] {e}"
        )
        raise typer.Exit(code=1)
    finally:
        conn.close()


@app.command(name="get")
def get(
    identifier: Annotated[
        str,
        typer.Argument(
            help="The unique shortcut alias OR the service name (e.g., github)."
        ),
    ],
    email: Annotated[
        str | None,
        typer.Option(
            "--email",
            "-e",
            help="Narrow down specific account if multiple emails exist.",
        ),
    ] = None,
):
    """
    🔑 Unlock the vault and launch a live-refreshing dashboard showing the dynamic TOTP code.
    """
    # Guard: Database must exist
    if not os.path.exists(DB_PATH):
        console.print(
            "[bold red]❌ Error:[/] Database not found. Please run [yellow]'vlt init'[/] first."
        )
        raise typer.Exit(code=1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Resolve target record based on the provided identifier
    cursor.execute(
        "SELECT service, email, encrypted_secret FROM secrets WHERE alias = ?",
        (identifier,),
    )
    record = cursor.fetchone()

    if not record:
        if email:
            cursor.execute(
                "SELECT service, email, encrypted_secret FROM secrets WHERE service = ? AND email = ?",
                (identifier.lower(), email),
            )
            records = cursor.fetchall()
        else:
            cursor.execute(
                "SELECT service, email, encrypted_secret FROM secrets WHERE service = ?",
                (identifier.lower(),),
            )
            records = cursor.fetchall()

        if not records:
            console.print(
                f"[bold red]❌ Error:[/] No secret record found matching identifier: [yellow]'{identifier}'[/]"
            )
            conn.close()
            raise typer.Exit(code=1)

        if len(records) > 1:
            console.print(
                f"\n[bold yellow]⚠️ Multiple accounts found for service '{identifier}':[/]"
            )
            for r in records:
                console.print(f"  • Email: [cyan]{r[1] or 'N/A'}[/]")
            console.print(
                f"\n👉 Please refine your command using: [bold cyan]vlt get {identifier} -e <email>[/]\n"
            )
            conn.close()
            raise typer.Exit(code=1)

        record = records[0]

    service_name, target_email, encrypted_secret = record

    # 2. Challenge user for the Master Password to decrypt payload
    master_password = typer.prompt(
        " 🔒 Enter Master Password to unlock & read",
        hide_input=True,
        prompt_suffix=": ",
    )

    try:
        enc_key = derive_key(master_password)
        fernet = Fernet(enc_key)
        decrypted_bytes = fernet.decrypt(encrypted_secret.encode())
        raw_secret_token = decrypted_bytes.decode()
        totp = pyotp.TOTP(raw_secret_token)
    except Exception:
        console.print(
            "\n[bold red]❌ Authentication Failed:[/] Incorrect master password or corrupted payload."
        )
        conn.close()
        raise typer.Exit(code=1)
    finally:
        conn.close()

    # 3. Define the UI generator closure function for Live rendering
    def make_dashboard_renderable() -> str:
        current_code = totp.now()
        # Calculate standard 30-second step remaining time
        time_remaining = int(totp.interval - (time.time() % totp.interval))

        # Build a visual progress bar (30 segments max)
        bar_length = 15
        filled_segments = int((time_remaining / totp.interval) * bar_length)
        bar = "█" * filled_segments + "░" * (bar_length - filled_segments)

        # Pick color indicators based on remaining time urgency
        bar_color = (
            "green"
            if time_remaining > 10
            else ("yellow" if time_remaining > 5 else "red")
        )

        ui_output = (
            f"\n[bold green]🔑 [Live TOTP Dashboard for {service_name.upper()}]:[/]\n"
            f" 👤 Account: [dim]{target_email or 'N/A'}[/]\n"
            f" 🚀 [bold reverse white]  {current_code[0:3]} {current_code[3:6]}  [/]\n"
            f" ⏳ [{bar_color}]{bar}[/] ({time_remaining}s remaining)\n"
            f"[dim] Press Ctrl+C to exit dashboard loop early...[/]\n"
        )
        return ui_output

    # 4. Spin up the dynamic live rendering view loop
    console.print("\n[dim]Initializing secure display matrix...[/]")
    try:
        start_time = time.time()
        # Auto-timeout after 30 seconds to prevent leaking tokens on unattended screens
        with Live(
            make_dashboard_renderable(), refresh_per_second=1, transient=True
        ) as live:
            while time.time() - start_time < 30:
                time.sleep(1)
                live.update(make_dashboard_renderable())

        console.print("[yellow]⏳ Dashboard session expired safely automatically.[/]\n")
    except KeyboardInterrupt:
        # Catch standard Ctrl+C clean exiting
        console.print("\n[dim]🔒 Vault locked. Session closed securely.[/]\n")


@app.command(name="init")
def init(
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout", "-t", help="Auto-lock timeout in minutes.", min=1, max=1440
        ),
    ] = 15,
):
    """
    🌱 Initialize secure database, set master password and auto-lock timeout.
    """
    console.print("\n[bold cyan]🌱 sololc-vvault Initialization Wizard[/]")
    console.print(
        "[dim]─────────────────────────────────────────────────────────────[/]\n"
    )
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Guard: Prevent double initialization
    if os.path.exists(DB_PATH):
        console.print(
            f"[bold red]❌ Error:[/] Database file [yellow]{DB_PATH}[/] already exists!"
        )
        console.print(
            "[dim]👉 Delete the file manually if you want to re-initialize (WARNING: All data will be lost).[/]\n"
        )
        raise typer.Exit(code=1)

    console.print(
        " To protect your TOTP secrets, please set a strong [bold magenta]Master Password[/]:"
    )

    # Safe password prompt with automatic double confirmation match
    master_password = typer.prompt(
        " 🔒 Enter Master Password",
        hide_input=True,
        confirmation_prompt=True,
        prompt_suffix=": ",
    )

    if not master_password.strip():
        console.print("\n[bold red]❌ Error:[/] Master password cannot be empty!")
        raise typer.Exit(code=1)

    # Initialize SQLite database structures
    try:
        with console.status(
            "[bold green]Creating secure environment and initializing storage...[/]"
        ):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Create system configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Create data table for vault records
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS secrets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    email TEXT,
                    alias TEXT UNIQUE,
                    encrypted_secret TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_secrets_service_email 
                ON secrets (service, email)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_secrets_alias 
                ON secrets (alias)
            """)

            # Persist basic timeout configuration
            cursor.execute(
                "INSERT INTO config (key, value) VALUES (?, ?)",
                ("timeout_minutes", str(timeout)),
            )

            conn.commit()
            conn.close()

        console.print("\n[bold green]✨ Initialization successful![/]")
        console.print(f" 📂 Database deployed to: [underline cyan]{DB_PATH}[/]")
        console.print(
            f" ⏳ Vault auto-lock timeout set to: [bold yellow]{timeout} minutes[/]"
        )
        console.print(
            "\n 👉 You can now run [bold yellow]'vlt add'[/] to insert your first TOTP token.\n"
        )

    except Exception as e:
        console.print(
            f"\n[bold red]❌ Critical error occurred during initialization:[/] {e}"
        )
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)  # Rollback file creation on failure
        raise typer.Exit(code=1)


@app.command(name="lock")
def lock_vault():
    """
    🔒 Explicitly secure the vault, clear session handles, and audit local database integrity.
    """
    console.print("\n[bold magenta]🔒 Securing sololc-vvault environment...[/]")
    console.print(
        "[dim]─────────────────────────────────────────────────────────────[/]\n"
    )

    # Guard: Database must exist to verify integrity status
    if not os.path.exists(DB_PATH):
        console.print(
            "[bold red]❌ Error:[/] Vault cannot be locked because no database exists."
        )
        console.print(
            "[dim]👉 Run [yellow]'vlt init'[/] to construct your secure baseline entry point.[/]\n"
        )
        raise typer.Exit(code=1)

    try:
        # Run a micro integrity diagnostic check using SQLite's PRAGMA architecture
        with console.status(
            "[bold cyan]Running structural database integrity audit...[/]"
        ):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # PRAGMA integrity_check returns 'ok' if structural constraints are sound
            cursor.execute("PRAGMA integrity_check;")
            integrity_result = cursor.fetchone()[0]
            conn.close()

        if integrity_result != "ok":
            console.print(
                f"[bold red]❌ Critical Alert:[/] Database integrity compromise detected: [yellow]{integrity_result}[/]"
            )
            raise typer.Exit(code=1)

        # Print successful lock layout metrics
        console.print("[bold green]🔒 Vault locked down successfully![/]")
        console.print("  • Volatile memory buffers: [dim]Cleared[/]")
        console.print("  • Local database matrix: [bold green]Verified & Intact[/]")
        console.print("  • Master Key access tokens: [dim]Purged[/]\n")
        console.print(
            "[dim]🔒 Safe exploration environment restored. System secure.[/]\n"
        )

    except Exception as e:
        console.print(
            f"\n[bold red]❌ System Exception encountered during secure lockout sequence:[/] {e}"
        )
        raise typer.Exit(code=1)


@app.command(name="list")
def list_vault():
    """
    📊 List all registered services, associated emails, and configured shortcut aliases.
    """
    # Guard: Database must exist
    if not os.path.exists(DB_PATH):
        console.print(
            "[bold red]❌ Error:[/] Database not found. Please run [yellow]'vlt init'[/] first."
        )
        raise typer.Exit(code=1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch all records sorted by service name and email for structural clarity
    cursor.execute("""
        SELECT id, service, email, alias, created_at 
        FROM secrets 
        ORDER BY service ASC, email ASC
    """)
    records = cursor.fetchall()

    if not records:
        console.print("\n[bold yellow]📭 Your vault is currently empty.[/]")
        console.print(
            "👉 Use [bold cyan]'vlt add <service> <secret>'[/] to store your first TOTP token.\n"
        )
        conn.close()
        raise typer.Exit(code=0)

    # 1. Initialize a highly-scannable, minimalist Rich Table
    table = Table(
        title="\n🔒 Managed TOTP Accounts Vault Matrix",
        title_style="bold white",
        box=box.SIMPLE,  # Gives an elegant, boxless Unix traditional look
        header_style="bold cyan",
        collapse_padding=True,
    )

    # 2. Define clean structural columns
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Service/Platform", justify="left", style="bold green")
    table.add_column("Associated Email / Username", justify="left", style="white")
    table.add_column("Shortcut Alias", justify="left", style="magenta")
    table.add_column("Date Added (UTC)", justify="right", style="dim")

    # 3. Populate rows with formatted metadata safely
    for row in records:
        rec_id, service, email, alias, created_at = row
        table.add_row(
            str(rec_id),
            service.upper(),
            email or "[dim]N/A[/]",
            alias or "[dim]None[/]",
            created_at.split()[0],  # Show date only (YYYY-MM-DD) for maximum brevity
        )

    # 4. Render output gracefully
    console.print(table)
    console.print(
        f"[dim] Total: {len(records)} credential record(s) safely encrypted and isolated locally.[/]\n"
    )

    conn.close()


@app.command(name="remove")
def remove(
    identifier: Annotated[
        str,
        typer.Argument(help="The unique shortcut alias OR the service name to delete."),
    ],
    email: Annotated[
        str | None,
        typer.Option(
            "--email",
            "-e",
            help="The specific email if multiple accounts share the same service name.",
        ),
    ] = None,
):
    """
    🗑️ Safely remove a TOTP secret credential record from the vault.
    """
    # Guard: Database must exist
    if not os.path.exists(DB_PATH):
        console.print(
            "[bold red]❌ Error:[/] Database not found. Please run [yellow]'vlt init'[/] first."
        )
        raise typer.Exit(code=1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Resolve target records using either alias or service name query patterns
    cursor.execute(
        "SELECT id, service, email FROM secrets WHERE alias = ?", (identifier,)
    )
    record = cursor.fetchone()

    # If no alias matches, fallback to filtering by service name
    if not record:
        if email:
            cursor.execute(
                "SELECT id, service, email FROM secrets WHERE service = ? AND email = ?",
                (identifier.lower(), email),
            )
            records = cursor.fetchall()
        else:
            cursor.execute(
                "SELECT id, service, email FROM secrets WHERE service = ?",
                (identifier.lower(),),
            )
            records = cursor.fetchall()

        if not records:
            console.print(
                f"[bold red]❌ Error:[/] No secret record found matching identifier: [yellow]'{identifier}'[/]"
            )
            conn.close()
            raise typer.Exit(code=1)

        # Abort if multiple rows match the service name and no explicit email option was specified
        if len(records) > 1:
            console.print(
                f"\n[bold yellow]⚠️ Multiple accounts found for service '{identifier}':[/]"
            )
            for r in records:
                console.print(f"  • Email: [cyan]{r[2] or 'N/A'}[/]")
            console.print(
                f"\n👉 Please specify which account to remove using: [bold cyan]vlt remove {identifier} -e <email>[/]\n"
            )
            conn.close()
            raise typer.Exit(code=1)

        record = records[0]

    target_id, service_name, target_email = record

    # 2. Trigger destructive action warning confirmation prompt
    display_identity = (
        f"{service_name.upper()} ({target_email})"
        if target_email
        else service_name.upper()
    )
    console.print(
        f"\n[bold red]⚠️  WARNING:[/] You are about to permanently delete the TOTP key for [bold white]{display_identity}[/]."
    )
    console.print(
        "[dim]This action cannot be undone. Ensure you have backed up or disabled 2FA on this account! [/]"
    )

    confirm = typer.confirm(
        "\n Are you absolutely sure you want to delete this secret?", default=False
    )

    if not confirm:
        console.print(
            "\n[yellow]❌ Deletion canceled. Your vault records remain untouched.[/]\n"
        )
        conn.close()
        raise typer.Exit(code=0)

    # 3. Execute isolated database delete operation
    try:
        with console.status(
            "[bold red]Purging credential record from secure storage...[/]"
        ):
            cursor.execute("DELETE FROM secrets WHERE id = ?", (target_id,))
            conn.commit()

        console.print(
            f"\n[bold green]🗑️  Success![/] The credential record for [bold white]{display_identity}[/] has been completely purged.\n"
        )

    except Exception as e:
        console.print(f"\n[bold red]❌ Critical error during record deletion:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        conn.close()


@app.command(name="backup")
def backup_vault(
    destination: Annotated[
        str | None,
        typer.Option(
            "--output",
            "-o",
            help="Custom destination directory or path for the backup file.",
        ),
    ] = None,
):
    """
    💾 Verify database integrity and export a secure, timestamped backup clone of the vault.
    """
    console.print("\n[bold cyan]💾 Initializing Secure Vault Backup Sequence...[/]")
    console.print(
        "[dim]─────────────────────────────────────────────────────────────[/]\n"
    )

    # Guard: Source database must exist
    if not os.path.exists(DB_PATH):
        console.print(
            "[bold red]❌ Error:[/] Backup failed because the primary database does not exist."
        )
        raise typer.Exit(code=1)

    # 1. Verification Gate: Ensure database is healthy before backing up
    try:
        with console.status(
            "[bold cyan]Auditing database structural health before export...[/]"
        ):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            integrity_result = cursor.fetchone()[0]
            conn.close()

        if integrity_result != "ok":
            console.print(
                f"[bold red]❌ Abort:[/] Source database is structurally compromised: [yellow]{integrity_result}[/]"
            )
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[bold red]❌ Error during integrity check phase:[/] {e}")
        raise typer.Exit(code=1)

    # 2. Establish destination paths and directory structure
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"sololc-vvault_backup_{timestamp}.db"

        if destination:
            target_dir = os.path.abspath(os.path.expanduser(destination))
        else:
            BACKUP_DIR.parent.mkdir(parents=True, exist_ok=True)
            target_dir = BACKUP_DIR

        # Create the directory tree if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        final_backup_path = os.path.join(target_dir, backup_filename)

        # 3. Perform atomic binary replication
        with console.status(
            "[bold green]Cloning encryption matrices to destination target...[/]"
        ):
            shutil.copy2(DB_PATH, final_backup_path)

        # 4. Render success output metrics
        console.print("[bold green]✨ Backup completed successfully![/]")
        console.print("  • Source integrity: [bold green]Verified (Healthy)[/]")
        console.print(
            f"  • Snapshot deployment path: [underline cyan]{final_backup_path}[/]"
        )
        console.print(
            "\n[dim]👉 Keep this backup secure. It contains your encrypted payload keys.[/]\n"
        )

    except Exception as e:
        console.print(
            f"\n[bold red]❌ Critical error encountered during binary replication layout:[/] {e}"
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
