"""EIP-55 checksummed EVM addresses. Keccak comes from PyCryptodome, not SHA3."""

from Crypto.Hash import keccak

_HEX = set("0123456789abcdef")


class AddressError(ValueError):
    """The value is not a checksummed EVM address."""


def _keccak_hex(text: str) -> str:
    digest = keccak.new(digest_bits=256)
    digest.update(text.encode("ascii"))
    return digest.hexdigest()


def to_checksum_address(address: str) -> str:
    """Return the EIP-55 form, or raise AddressError."""
    raw = address.strip()
    if not raw.startswith("0x") and not raw.startswith("0X"):
        raise AddressError("address must start with 0x")
    body = raw[2:].lower()
    if len(body) != 40 or any(char not in _HEX for char in body):
        raise AddressError("address must be 20 bytes of hex")
    hashed = _keccak_hex(body)
    chars = [
        char.upper() if int(hashed[index], 16) >= 8 else char for index, char in enumerate(body)
    ]
    return "0x" + "".join(chars)


def require_checksum_address(address: str) -> str:
    """Accept only the canonical checksummed form."""
    checksummed = to_checksum_address(address)
    if address.strip() != checksummed:
        raise AddressError("address must be checksummed")
    return checksummed
