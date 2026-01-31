
"""
bencode.py - Bencode Decoder/Encoder

Implements the BitTorrent Bencoding specification.
"""

from typing import Any, Tuple, Union

def decode(data: bytes) -> Any:
    """Decodes bencoded data."""
    if not data:
        return None
    decoded, _ = _decode_next(data, 0)
    return decoded

def _decode_next(data: bytes, offset: int) -> Tuple[Any, int]:
    """
    Decodes the next item in the buffer.
    Returns (decoded_item, new_offset).
    """
    char = data[offset:offset+1]

    # Integer: i<contents>e
    if char == b'i':
        end = data.index(b'e', offset)
        num = int(data[offset+1:end])
        return num, end + 1

    # String: <length>:<contents>
    elif char.isdigit():
        colon = data.index(b':', offset)
        length = int(data[offset:colon])
        start = colon + 1
        return data[start:start+length], start + length

    # List: l<contents>e
    elif char == b'l':
        lst = []
        offset += 1
        while data[offset:offset+1] != b'e':
            item, offset = _decode_next(data, offset)
            lst.append(item)
        return lst, offset + 1

    # Dictionary: d<contents>e
    elif char == b'd':
        dct = {}
        offset += 1
        while data[offset:offset+1] != b'e':
            key, offset = _decode_next(data, offset)
            # Keys must be strings (bytes)
            # We decoded it as bytes above, but for convenience we might want to keep it as bytes
            # or decode "utf-8" safely later. For now, keep as bytes.
            val, offset = _decode_next(data, offset)
            dct[key] = val
        return dct, offset + 1

    else:
        raise ValueError(f"Invalid bencode prefix at offset {offset}: {char}")

def encode(data: Any) -> bytes:
    """Encodes a Python object into bencode format."""
    if isinstance(data, int):
        return b'i' + str(data).encode('utf-8') + b'e'
    
    elif isinstance(data, (bytes, str)):
        if isinstance(data, str):
            data = data.encode('utf-8')
        return str(len(data)).encode('utf-8') + b':' + data
    
    elif isinstance(data, list):
        encoded = b'l'
        for item in data:
            encoded += encode(item)
        return encoded + b'e'
    
    elif isinstance(data, dict):
        encoded = b'd'
        # Keys must be sorted strings
        # We need to ensure keys are bytes for sorting if they are mixed, 
        # but standard bencode expects strict byte string keys.
        # We'll assume keys are either bytes or strings.
        
        # Helper to get bytes for sorting
        def get_key_bytes(k):
             return k.encode('utf-8') if isinstance(k, str) else k

        sorted_keys = sorted(data.keys(), key=get_key_bytes)
        
        for key in sorted_keys:
            encoded += encode(key)
            encoded += encode(data[key])
        return encoded + b'e'
    
    else:
        raise TypeError(f"Cannot bencode type: {type(data)}")
