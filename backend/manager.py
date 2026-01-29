import libtorrent as lt
import time
import os
import threading
import subprocess
import shutil

class TorrentManager:
    """
    TorrentManager - Core Logic Class
    
    This class manages the libtorrent session and all active downloads.
    It is implemented as a Singleton to ensure only one session exists.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TorrentManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # Initialize the libtorrent session
        # Listening on all interfaces at port 6881 (standard BitTorrent port)
        self.ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})
        
        # Dictionary to store torrent handles, keyed by info_hash
        self.downloads = {}
        
        # Default download directory in the user's home folder
        self.download_dir = os.path.expanduser("~/Downloads/Torrpeddo-Downloads")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            
        self._initialized = True
        print(f"Torrent Manager initialized. Downloads directory: {self.download_dir}")

    def set_download_dir(self, path):
        """Updates the global download path for all new torrents."""
        if os.path.exists(path):
            self.download_dir = path
            return True
        return False

    def add_magnet(self, magnet_uri):
        """Parses a magnet URI and adds it to the session."""
        params = lt.parse_magnet_uri(magnet_uri)
        params.save_path = self.download_dir
        handle = self.ses.add_torrent(params)
        info_hash = str(handle.info_hash())
        self.downloads[info_hash] = handle
        return info_hash

    def add_torrent_file(self, torrent_data):
        """Decodes .torrent file data and adds it to the session."""
        info = lt.torrent_info(lt.bdecode(torrent_data))
        params = {
            'save_path': self.download_dir,
            'ti': info
        }
        handle = self.ses.add_torrent(params)
        info_hash = str(handle.info_hash())
        self.downloads[info_hash] = handle
        return info_hash

    def get_all_status(self):
        """
        Retrieves live metrics for all active downloads.
        Returns a list of dictionaries containing progress, rates, and states.
        """
        status_list = []
        for info_hash, handle in self.downloads.items():
            s = handle.status()
            
            state_str = str(s.state)
            is_paused = s.paused
            if is_paused and state_str != "checking_resume_data":
                state_str = "Paused"

            # Check if files still exist on disk
            try:
                full_path = os.path.join(s.save_path, s.name)
                if not os.path.exists(full_path):
                    state_str = "Error: Missing Files"
            except Exception:
                pass

            status_list.append({
                'name': s.name,
                'progress': s.progress * 100,
                'download_rate': s.download_rate / 1000, # Convert to kB/s
                'upload_rate': s.upload_rate / 1000,   # Convert to kB/s
                'num_peers': s.num_peers,
                'state': state_str,
                'info_hash': info_hash,
                'is_seeding': s.is_seeding,
                'is_paused': is_paused
            })
        return status_list

    def remove_torrent(self, info_hash):
        """Removes a torrent from the session and the local tracking dict."""
        if info_hash in self.downloads:
            handle = self.downloads.pop(info_hash)
            self.ses.remove_torrent(handle)
            return True
        return False

    def open_folder(self, info_hash):
        """
        Attempts to open the containing folder of a torrent in the native file explorer.
        Uses xdg-open for Linux compatibility.
        """
        if info_hash in self.downloads:
            handle = self.downloads[info_hash]
            s = handle.status()
            full_path = os.path.join(s.save_path, s.name)
            
            target_path = full_path
            if os.path.isfile(full_path):
                 target_path = os.path.dirname(full_path)
            elif not os.path.exists(full_path):
                 target_path = s.save_path
            
            if not os.path.exists(target_path):
                return False, f"Path does not exist: {target_path}"

            try:
                if shutil.which('xdg-open') is None:
                     return False, "xdg-open not found on system"

                # Launch xdg-open non-blockingly
                subprocess.Popen(['xdg-open', target_path], stderr=subprocess.PIPE)
                return True, "Opened successfully"
            except Exception as e:
                print(f"Failed to open folder: {e}")
                return False, str(e)
        return False, "Torrent hash not found"

    def pause_torrent(self, info_hash):
        """Pauses a specific torrent."""
        if info_hash in self.downloads:
            handle = self.downloads[info_hash]
            handle.pause()
            return True
        return False

    def resume_torrent(self, info_hash):
        """Resumes a specific torrent."""
        if info_hash in self.downloads:
            handle = self.downloads[info_hash]
            handle.resume()
            return True
        return False

    def select_directory(self):
        """
        Launches a native directory selector using Tkinter.
        This is run in a separate subprocess to avoid blocking the main bridge loop.
        """
        try:
            cmd = "import tkinter as tk; from tkinter import filedialog; root = tk.Tk(); root.withdraw(); print(filedialog.askdirectory())"
            result = subprocess.run(['python3', '-c', cmd], capture_output=True, text=True)
            path = result.stdout.strip()
            return path if path else None
        except Exception as e:
            print(f"Failed to open directory selector: {e}")
            return None
