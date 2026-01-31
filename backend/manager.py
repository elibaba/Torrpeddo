import libtorrent as lt
import time
import os
import threading
import subprocess
import shutil
import sys

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
        self.ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})
        
        # Dictionary to store torrent handles, keyed by info_hash
        self.downloads = {}
        
        # Default download directory
        self.download_dir = os.path.abspath(os.getcwd())
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            
        self._initialized = True
        print(f"Torrent Manager initialized. Downloads directory: {self.download_dir}", file=sys.stderr)

    def set_download_dir(self, path):
        """Updates the global download path for all new torrents."""
        if os.path.exists(path):
            self.download_dir = path
            return True
        return False

    def add_magnet(self, magnet_uri):
        """Parses a magnet URI and adds it to the session."""
        def _add_task():
            try:
                params = lt.parse_magnet_uri(magnet_uri)
                params.save_path = self.download_dir
                handle = self.ses.add_torrent(params)
                info_hash = str(handle.info_hash())
                
                with self._lock:
                    self.downloads[info_hash] = handle
                
                print(f"Torrent added via magnet: {info_hash}", file=sys.stderr)
            except Exception as e:
                print(f"Error adding magnet in thread: {e}", file=sys.stderr)

        thread = threading.Thread(target=_add_task, daemon=True)
        thread.start()
        
        temp_params = lt.parse_magnet_uri(magnet_uri)
        return str(temp_params.info_hash)

    def add_torrent_file(self, torrent_data):
        """Decodes .torrent file data and adds it to the session."""
        def _add_task():
            try:
                info = lt.torrent_info(lt.bdecode(torrent_data))
                atp = lt.add_torrent_params()
                atp.ti = info
                atp.save_path = self.download_dir
                handle = self.ses.add_torrent(atp)
                info_hash = str(handle.info_hash())
                
                with self._lock:
                    self.downloads[info_hash] = handle
                
                print(f"DEBUG: Torrent file added successfully: {info_hash}", file=sys.stderr)
            except Exception as e:
                print(f"Error adding torrent file in thread: {e}", file=sys.stderr)

        thread = threading.Thread(target=_add_task, daemon=True)
        thread.start()
        
        info = lt.torrent_info(lt.bdecode(torrent_data))
        return str(info.info_hash())

    def get_all_status(self):
        """Retrieves live metrics for all active downloads."""
        status_list = []
        
        with self._lock:
            active_hashes = list(self.downloads.keys())
        
        for info_hash in active_hashes:
            try:
                handle = self.downloads.get(info_hash)
                if not handle: continue

                s = handle.status()
                state_str = str(s.state)
                is_paused = s.paused
                
                if is_paused and state_str != "checking_resume_data":
                    state_str = "Paused"

                try:
                    if s.has_metadata and s.progress > 0:
                        full_path = os.path.join(s.save_path, s.name)
                        if not os.path.exists(full_path):
                            state_str = "Error: Missing Files"
                except Exception:
                    pass

                status_list.append({
                    'name': s.name if s.has_metadata else 'Fetching metadata...',
                    'progress': s.progress * 100,
                    'download_rate': float(s.download_rate / 1000),
                    'upload_rate': float(s.upload_rate / 1000),
                    'num_peers': int(s.num_peers),
                    'state': state_str,
                    'info_hash': info_hash,
                    'is_seeding': bool(s.is_seeding),
                    'is_paused': bool(is_paused),
                    'is_cancelled': False
                })
            except Exception as e:
                print(f"Error getting status for {info_hash}: {e}", file=sys.stderr)
                pass

        return status_list

    def remove_torrent(self, info_hash):
        """Removes a torrent completely from tracking."""
        with self._lock:
            if info_hash in self.downloads:
                handle = self.downloads.pop(info_hash)
                self.ses.remove_torrent(handle)
                return True
        return False

    def delete_torrent_and_files(self, info_hash):
        """Removes a torrent and deletes its files from disk."""
        with self._lock:
            if info_hash in self.downloads:
                handle = self.downloads.pop(info_hash)
                s = handle.status()
                path_to_delete = os.path.join(s.save_path, s.name)
                
                # Stop and remove
                handle.pause()
                self.ses.remove_torrent(handle)
                
                if path_to_delete:
                    def _deferred_delete(path):
                        import time
                        time.sleep(1.0)
                        try:
                            if os.path.exists(path):
                                if os.path.isdir(path):
                                    shutil.rmtree(path)
                                else:
                                    os.remove(path)
                                print(f"Disk cleanup complete for: {path}", file=sys.stderr)
                        except Exception as e:
                            print(f"Deferred deletion error for {path}: {e}", file=sys.stderr)
                    
                    threading.Thread(target=_deferred_delete, args=(path_to_delete,), daemon=True).start()
                    return True
        return False

    def open_folder(self, info_hash):
        """Opens the containing folder of a torrent."""
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
                subprocess.Popen(['xdg-open', target_path], stderr=subprocess.PIPE)
                return True, "Opened successfully"
            except Exception as e:
                print(f"Failed to open folder: {e}", file=sys.stderr)
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
