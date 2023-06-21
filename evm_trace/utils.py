from eth_utils import to_checksum_address


def to_address(value):
    # clear the padding and expand to 32 bytes
    return to_checksum_address(value[-20:].rjust(20, b"\x00"))
