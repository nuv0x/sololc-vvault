import yaml
from typing import TypedDict, List, Optional
from urllib.parse import urlparse, parse_qs, unquote

def parse_vault_data(raw_yaml: str) -> list:
    """Parse the YAML string into a list of accounts"""
    if not raw_yaml:
        return []
    data = yaml.safe_load(raw_yaml)
    return data.get("accounts", [])

def serialize_vault_data(accounts: list) -> str:
    """Serialize the account list into a YAML string."""
    return yaml.dump({"accounts": accounts}, allow_unicode=True)

# Define the type to eliminate Pylance's Unknown warning.
class Account(TypedDict):
    name: str
    secret: str
    issuer: str
    category: str

def parse_otpauth_url(url: str) -> Account:
    """Pure function: Parsing the otpauth protocol string"""
    parsed = urlparse(url)
    if parsed.scheme != "otpauth":
        raise ValueError(f"Unsupported protocols: {parsed.scheme}")
    
    params = parse_qs(parsed.query)
    label = unquote(parsed.path.lstrip('/'))
    secret = params.get('secret', [None])[0]
    issuer_param = params.get('issuer', [None])[0]
    
    if not secret:
        raise ValueError("The URL is missing the secret parameter.")
        
    if ':' in label:
        issuer_label, name = label.split(':', 1)
    else:
        issuer_label, name = "Unknown", label
        
    return {
        "name": name.strip(),
        "secret": secret.strip(),
        "issuer": (issuer_param or issuer_label).strip(),
        "category": "Imported"
    }

def merge_accounts(existing: List[Account], new_list: List[Account]) -> List[Account]:
    """Pure function: Merge two account lists and remove duplicates by name"""
    new_names = {a['name'] for a in new_list}
    filtered_existing = [a for a in existing if a['name'] not in new_names]
    return filtered_existing + new_list

def add_account_to_list(accounts: List[Account], name: str, secret: str, issuer: str, category: str) -> List[Account]:
    """Pure function: Add a single account"""
    new_acc: Account = {
        "name": name,
        "secret": secret,
        "issuer": issuer,
        "category": category
    }
    return merge_accounts(accounts, [new_acc])