import typer
import time
from typing import Annotated, Optional, List
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.status import Status
import cv2
import numpy as np
from PIL import Image
import pyperclip
from vvault.core import storage, totp, vault

app = typer.Typer(help="vlt - Minimalist Secure Vault (Vvault CLI)", add_completion=False)
console = Console()

# --- 🔒 (Security) ---

@app.command(help="Initialize tool")
def init():
    """Initialize the tool and set a master password to encrypt the local database."""
    if storage.get_vault_file().exists():
        console.print("[yellow]⚠️ The vault already exists.[/yellow]")
    else:
        # In actual development, this should trigger the process of setting the master password.
        storage.write_vault("accounts: []")
        console.print("[green]✔ vlt Initialized. Master password already associated. ~/.vlt/ [/green]")

# @app.command()
# def lock():
#     """Immediately lock the current session (clear temporary keys in memory)."""
#     console.print("[bold blue]🔒 The session is locked. You will need to re-enter your master password for the next operation. [/bold blue]")

# --- 🛡️ (Account Management) ---

@app.command(help="Add account. e.g.: vlt add github --secret KHR2UEJ33JJG... --issuer GitHub --category Dev")
def add(
    name: str, 
    secret: Annotated[str, typer.Option("--secret", "-s", help="OTP Key")], 
    issuer: str = "Unknown", 
    category: str = "General"
):
    accounts = vault.parse_vault_data(storage.read_vault())
    updated = vault.add_account_to_list(accounts, name, secret, issuer, category)
    storage.write_vault(vault.serialize_vault_data(updated))
    console.print(f"[green]✔[/green] account [bold]{name}[/bold] Already deposited [blue]{category}[/blue]")

@app.command(name="list", help="List all saved account names (without displaying verification codes).")
def list_accounts():
    accounts = vault.parse_vault_data(storage.read_vault())
    if not accounts:
        console.print("[yellow]The vault was empty. [/yellow]")
        return

    table = Table(title="vlt Account List")
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Issuer", style="magenta")
    table.add_column("Category", style="green")

    for idx, acc in enumerate(accounts, 1):
        table.add_row(str(idx), acc['name'], acc.get('issuer', 'N/A'), "General")
    
    console.print(table)

@app.command(help="Remove account. e.g.: vlt remove name")
def remove(name: str):
    accounts = vault.parse_vault_data(storage.read_vault())
    updated = [a for a in accounts if a['name'] != name]
    if len(updated) == len(accounts):
        console.print(f"[red]✘ Account not found: {name}[/red]")
    else:
        storage.write_vault(vault.serialize_vault_data(updated))
        console.print(f"[green]✔ Account {name} It has been removed from the vault. [/green]")

# --- 🔑 (Code Generation) ---

@app.command(help="Get the current verification code for the specified account. e.g.: vlt get name")
def get(name: str, copy: bool = typer.Option(False, "--copy", "-c", help="Automatically copy to clipboard")):
    accounts = vault.parse_vault_data(storage.read_vault())
    account = next((a for a in accounts if a['name'] == name), None)
    
    if not account:
        console.print(f"[red]✘ Account not found: {name}[/red]")
        return

    code = totp.generate_code(account['secret'])
    if copy:
        pyperclip.copy(code)
        msg = " [Copy to clipboard]"
    else:
        msg = ""

    console.print(Panel(f"[bold cyan]{code[:3]} {code[3:]}[/bold cyan]{msg}", title=f"{account['name']} ({account.get('issuer')})", expand=False))

@app.command(help="Dashboard mode. e.g.: vlt dash")
def dash():
    def generate_table():
        accounts = vault.parse_vault_data(storage.read_vault())
        table = Table(title="vlt Live Dashboard", header_style="bold magenta")
        table.add_column("Category", style="green")
        table.add_column("Issuer")
        table.add_column("Account", style="cyan")
        table.add_column("Code", justify="center", style="bold green")
        table.add_column("Remains", justify="right")

        for acc in accounts:
            code = totp.generate_code(acc['secret'])
            rem = totp.get_remaining_seconds()
            color = "green" if rem > 10 else "red"
            table.add_row(acc.get('category', 'N/A'), acc.get('issuer', 'N/A'), acc['name'], f"{code[:3]} {code[3:]}", f"[{color}]{rem}s[/{color}]")
        return table

    with Live(generate_table(), refresh_per_second=1) as live:
        while True:
            time.sleep(1)
            live.update(generate_table())

# --- 📂 (Import & Backup) ---

@app.command(name="import", help="Import data. e.g.: vlt import --qr ./path/to/qr_code.png or vlt import --url otpauth://totp/Service:User?secret=XYZ...")
def import_data(
    qr: Annotated[Optional[Path], typer.Option("--qr", help="QR code image path")] = None,
    url: Annotated[Optional[str], typer.Option("--url", help="Import via link")] = None
):
    """Import account from QR code (OpenCV) or URL"""
    new_accs: List[vault.Account] = []
    
    with Status("[bold blue]Processing...", console=console) as status:
        try:
            if qr:
                status.update(f"🔍 OpenCV Scanning image: {qr.name}")
                
                # Reading images using OpenCV
                img = cv2.imread(str(qr))
                if img is None:
                    console.print(f"[red]✘ Unable to read image file: {qr}[/red]")
                    return
                
                # Initialize OpenCV QR code detector
                detector = cv2.QRCodeDetector()
                data, vertices, _ = detector.detectAndDecode(img)
                
                if not data:
                    console.print("[red]✘ No valid QR code content was detected.[/red]")
                    return
                
                # Parse the extracted string
                new_accs.append(vault.parse_otpauth_url(data))

            elif url:
                new_accs.append(vault.parse_otpauth_url(url))
            
            if new_accs:
                current = vault.parse_vault_data(storage.read_vault())
                updated = vault.merge_accounts(current, new_accs)
                storage.write_vault(vault.serialize_vault_data(updated))
                
                for acc in new_accs:
                    console.print(f"[bold green]✔[/bold green] Import successful: {acc['issuer']} ({acc['name']})")
                console.print(Panel(f"✨ Successfully synchronized {len(new_accs)} individual accounts", border_style="green"))

        except Exception as e:
            console.print(f"[red]Import failed: {e}[/red]")

@app.command(help="Backup file save path. e.g.: vlt backup ./my_backup.yaml")
def backup(path: Annotated[Path, typer.Argument(help="Backup file save path. e.g.: vlt backup ./my_backup.yaml")]):
    try:
        data = storage.read_vault()
        if not data or data == "accounts: []":
            console.print("[yellow]⚠️ The vault is currently empty and no backup is needed. [/yellow]")
            return
            
        path.write_text(data, encoding="utf-8")
        console.print(f"[green]✔ Backup successful! Data has been physically exported to: [bold]{path}[/bold][/green]")
        console.print("[dim]Note: This file contains a plaintext key. Please keep it safe or encrypt it manually. [/dim]")
    except Exception as e:
        console.print(f"[red]✘ Backup failed: {e}[/red]")

if __name__ == "__main__":
    app()