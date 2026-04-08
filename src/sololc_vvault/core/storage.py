import os
from pathlib import Path

def get_vlt_path() -> Path:
    """Obtain and ensure that the ~/.vlt directory exists."""
    path = Path.home() / ".vlt"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        if os.name != 'nt':
            os.chmod(path, 0o700)
    return path

def get_vault_file() -> Path:
    return get_vlt_path() / "vault.yaml"

def write_vault(content: str):
    """Write encrypted content"""
    get_vault_file().write_text(content, encoding="utf-8")

def read_vault() -> str:
    """Read the content; if it does not exist, return an empty string."""
    file = get_vault_file()
    return file.read_text(encoding="utf-8") if file.exists() else ""