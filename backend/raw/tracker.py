
"""
tracker.py - HTTP Tracker Client

Handles communication with HTTP trackers to retrieve peer lists.
"""

import requests
import struct
import socket
import random
import urllib.parse
from . import bencode

def get_peers(tracker_url, info_hash_bytes, peer_id, port=6881):
    """
    Connects to the tracker and returns a list of (ip, port) tuples.
    
    Args:
        tracker_url (str): The announce URL.
        info_hash_bytes (bytes): The 20-byte SHA1 hash of the info dict.
        peer_id (str): Our 20-byte peer ID.
        port (int): Port we are listening on.
        
    Returns:
        list: List of (ip, port) tuples.
    """
    params = {
        'info_hash': info_hash_bytes,
        'peer_id': peer_id,
        'port': port,
        'uploaded': 0,
        'downloaded': 0,
        'left': 0, # Should be real remaining bytes
        'compact': 1,
        'event': 'started'
    }

    try:
        response = requests.get(tracker_url, params=params, timeout=10)
        response.raise_for_status()
        
        tracker_response = bencode.decode(response.content)
        
        if b'failure reason' in tracker_response:
             raise Exception(f"Tracker failure: {tracker_response[b'failure reason'].decode('utf-8')}")
             
        peers_data = tracker_response.get(b'peers')
        return parse_peers(peers_data)

    except Exception as e:
        print(f"Tracker error: {e}")
        return []

def parse_peers(peers_bin):
    """
    Parses a compact peer list (6 bytes per peer).
    """
    peers = []
    if isinstance(peers_bin, list):
         # Non-compact dictionary format (rare)
         for p in peers_bin:
             peers.append((p[b'ip'].decode('utf-8'), p[b'port']))
    elif isinstance(peers_bin, bytes):
        # Compact format: 4 bytes IP + 2 bytes Port
        for i in range(0, len(peers_bin), 6):
            ip = socket.inet_ntoa(peers_bin[i:i+4])
            port = struct.unpack("!H", peers_bin[i+4:i+6])[0]
            peers.append((ip, port))
            
    return peers
