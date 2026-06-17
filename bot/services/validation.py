import re

def is_valid_wallet(address: str) -> bool:
    """
    Validate TRC-20 wallet address.
    Starts with 'T', length 34, base58 characters.
    """
    if not address.startswith("T"):
        return False
    if len(address) != 34:
        return False
    base58_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
    return bool(re.match(base58_pattern, address))
