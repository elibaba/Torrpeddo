
"""
torrent_file.py - Torrent File Parser

Parses .torrent files and calculates info_hash.
"""

import hashlib
import os
from . import bencode

class TorrentFile:
    def __init__(self, filepath=None, raw_data=None):
        if filepath:
            with open(filepath, 'rb') as f:
                self.raw_data = f.read()
        elif raw_data:
            self.raw_data = raw_data
        else:
            raise ValueError("Must provide filepath or raw_data")

        self.meta = bencode.decode(self.raw_data)
        self.info = self.meta.get(b'info')
        if not self.info:
            raise ValueError("Invalid torrent file: missing info dict")
            
        self.announce = self.meta.get(b'announce')
        self.announce_list = self.meta.get(b'announce-list')
        
        # Calculate Info Hash (SHA1 of the bencoded 'info' dictionary)
        self.info_hash_bytes = hashlib.sha1(bencode.encode(self.info)).digest()
        self.info_hash_hex = self.info_hash_bytes.hex()
        
        # Parse File Structure
        self.name = self.info.get(b'name').decode('utf-8')
        self.piece_length = self.info.get(b'piece length')
        self.pieces = self.info.get(b'pieces')
        
        self.files = []
        self.total_size = 0
        
        if b'files' in self.info:
            # Multi-file torrent
            for f in self.info[b'files']:
                path_parts = [p.decode('utf-8') for p in f[b'path']]
                length = f[b'length']
                self.files.append({'path': os.path.join(*path_parts), 'length': length})
                self.total_size += length
        else:
            # Single-file torrent
            length = self.info.get(b'length')
            self.files.append({'path': self.name, 'length': length})
            self.total_size = length

    def __repr__(self):
        return f"<TorrentFile: {self.name}, Size: {self.total_size}, Hash: {self.info_hash_hex}>"
