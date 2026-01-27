import libtorrent as lt
import time
import os
import threading
import subprocess
import shutil


class TorrentManager:
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
        
        self.ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})
        self.downloads = {}
        self.download_dir = os.path.expanduser("~/Downloads/Torrpeddo-Downloads")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            
        self._initialized = True
        print(f"Torrent Manager initialized. Downloads directory: {self.download_dir}")

    def set_download_dir(self, path):
        if os.path.exists(path):
            self.download_dir = path
            return True
        return False

    def add_magnet(self, magnet_uri):
        params = lt.parse_magnet_uri(magnet_uri)
        params.save_path = self.download_dir
        handle = self.ses.add_torrent(params)
        info_hash = str(handle.info_hash())
        self.downloads[info_hash] = handle
        return info_hash

    def add_torrent_file(self, torrent_data):
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
        status_list = []
        for info_hash, handle in self.downloads.items():
            s = handle.status()
            
            
            state_str = str(s.state)
            is_paused = s.paused
            if is_paused and state_str != "checking_resume_data":
                state_str = "Paused"

            # Check if file exists
            try:
                full_path = os.path.join(s.save_path, s.name)
                if not os.path.exists(full_path):
                    state_str = "Error: Missing Files"
            except Exception:
                pass

            status_list.append({
                'name': s.name,
                'progress': s.progress * 100,
                'download_rate': s.download_rate / 1000, # kB/s
                'upload_rate': s.upload_rate / 1000, # kB/s
                'num_peers': s.num_peers,
                'state': state_str,
                'info_hash': info_hash,
                'is_seeding': s.is_seeding,
                'is_paused': is_paused
            })
        return status_list

    def remove_torrent(self, info_hash):
        if info_hash in self.downloads:
            handle = self.downloads.pop(info_hash)
            self.ses.remove_torrent(handle)
            return True
        return False

    def open_folder(self, info_hash):
        if info_hash in self.downloads:
            handle = self.downloads[info_hash]
            s = handle.status()
            full_path = os.path.join(s.save_path, s.name)
            
            target_path = full_path
            if os.path.isfile(full_path):
                 target_path = os.path.dirname(full_path)
            elif not os.path.exists(full_path):
                 # If full_path doesn't exist, try save_path
                 target_path = s.save_path
            
            print(f"Attempting to open folder: {target_path}")
            
            if not os.path.exists(target_path):
                return False, f"Path does not exist: {target_path}"

            try:
                # Check if xdg-open exists
                if shutil.which('xdg-open') is None:
                     return False, "xdg-open not found on server"

                # Use subprocess.run to capture stderr if it fails immediately, 
                # though Popen is better for non-blocking GUI launch.
                # However, Popen might not retrieve exit code immediately.
                # Let's try Popen but log if it raises.
                subprocess.Popen(['xdg-open', target_path], stderr=subprocess.PIPE)
                return True, "Opened successfully"
            except Exception as e:
                print(f"Failed to open folder: {e}")
                return False, str(e)
        return False, "Torrent hash not found"

    def pause_torrent(self, info_hash):
        if info_hash in self.downloads:
            handle = self.downloads[info_hash]
            handle.pause()
            return True
        return False

    def resume_torrent(self, info_hash):
        if info_hash in self.downloads:
            handle = self.downloads[info_hash]
            handle.resume()
            return True
        return False

    def select_directory(self):
        try:
            # Run tkinter in a separate process to avoid main thread issues with Flask
            cmd = "import tkinter as tk; from tkinter import filedialog; root = tk.Tk(); root.withdraw(); print(filedialog.askdirectory())"
            result = subprocess.run(['python3', '-c', cmd], capture_output=True, text=True)
            path = result.stdout.strip()
            return path if path else None
        except Exception as e:
            print(f"Failed to open directory selector: {e}")
            return None
