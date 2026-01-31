
"""
manager.py - Raw Torrent Manager

Integrates bencode, tracker, and peer modules to manage downloads without libtorrent.
"""

import threading
import os
import sys
import time
import random
from . import torrent_file
from . import tracker
from . import peer

class RawTorrentManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RawTorrentManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.downloads = {} # info_hash -> TorrentState
        self.download_dir = os.path.abspath(os.getcwd())
        
        # Peer ID: -TP1000- + 12 random bytes
        self.peer_id = b'-TP1000-' + os.urandom(12)
        
        self.seed_ratio = 1.0
        self.seeding_enabled = True
        
        self._initialized = True
        print(f"Raw Torrent Manager initialized. Peer ID: {self.peer_id}", file=sys.stderr)

    def update_settings(self, settings):
        if 'download_dir' in settings:
            path = settings['download_dir']
            if path and os.path.isdir(path):
                self.download_dir = path
        # Other settings logic...
        return True

    def get_config(self):
        return {
            'download_dir': self.download_dir,
            'seed_ratio': self.seed_ratio,
            'seeding_enabled': self.seeding_enabled
        }

    def add_torrent_file(self, torrent_data):
        try:
            tf = torrent_file.TorrentFile(raw_data=torrent_data)
            info_hash = tf.info_hash_hex
            
            with self._lock:
                if info_hash in self.downloads:
                    return info_hash
                    
                state = {
                    'tf': tf,
                    'status': 'Downloading',
                    'peers': [], # List of PeerConnection objects
                    'progress': 0.0,
                    'uploaded': 0,
                    'downloaded': 0,
                    'paused': False
                }
                self.downloads[info_hash] = state
            
            # Start Tracking
            threading.Thread(target=self._start_torrent, args=(info_hash,), daemon=True).start()
            
            return info_hash
        except Exception as e:
            print(f"Error adding torrent: {e}", file=sys.stderr)
            raise e

    def _start_torrent(self, info_hash):
        state = self.downloads[info_hash]
        tf = state['tf']
        
        print(f"Starting torrent: {tf.name}")
        
        # 1. Get Peers from Tracker
        if tf.announce:
            peers_list = tracker.get_peers(tf.announce, tf.info_hash_bytes, self.peer_id)
            print(f"Found {len(peers_list)} peers for {tf.name}")
            
            # 2. Connect to Peers
            for ip, port in peers_list[:10]: # Limit to 10 for now
                p = peer.PeerConnection(ip, port, tf.info_hash_bytes, self.peer_id, self)
                state['peers'].append(p)
                p.start()
        
    def get_all_status(self):
        status_list = []
        with self._lock:
            for info_hash, state in self.downloads.items():
                tf = state['tf']
                active_peers = sum(1 for p in state['peers'] if p.connected)
                
                status_list.append({
                    'name': tf.name,
                    'progress': state['progress'],
                    'download_rate': 0.0, # TODO: Calculate rate
                    'upload_rate': 0.0,
                    'num_peers': active_peers,
                    'state': state['status'],
                    'info_hash': info_hash,
                    'is_seeding': False,
                    'is_paused': state['paused'],
                    'is_cancelled': False
                })
        return status_list

    # Stubs for compatibility
    def add_magnet(self, magnet_uri):
        print("Magnet links not supported in Raw Backend yet.", file=sys.stderr)
        return "0000000000000000000000000000000000000000"

    def pause_torrent(self, info_hash):
        if info_hash in self.downloads:
            self.downloads[info_hash]['paused'] = True
            # TODO: Disconnect peers?
            return True
        return False

    def resume_torrent(self, info_hash):
         if info_hash in self.downloads:
            self.downloads[info_hash]['paused'] = False
            return True
         return False

    def remove_torrent(self, info_hash):
        if info_hash in self.downloads:
            del self.downloads[info_hash]
            return True
        return False

    def delete_torrent_and_files(self, info_hash):
        return self.remove_torrent(info_hash)

    def open_folder(self, info_hash):
        return False, "Not implemented"
