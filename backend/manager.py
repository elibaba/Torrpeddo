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
        # Listening on all interfaces at port 6881 (standard BitTorrent port)
        self.ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})
        
        # Dictionary to store torrent handles, keyed by info_hash
        self.downloads = {}
        
        # Dictionary to store cancelled torrent data, keyed by info_hash
        # Stores { 'name': str, 'save_path': str }
        self.cancelled = {}
        
        # Default download directory: Use the folder from which the application was launched
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
        """
        Parses a magnet URI and adds it to the session.
        
        Refactored to use multi-threading:
        While libtorrent 2.0+ is internally multi-threaded, we handle the 
        addition of new torrents in a separate Python thread to ensure 
        the manager remains responsive even during metadata fetching.
        """
        def _add_task():
            try:
                params = lt.parse_magnet_uri(magnet_uri)
                params.save_path = self.download_dir
                
                # Each torrent added to the session benefit from libtorrent's
                # internal multi-threading. It uses a thread pool to manage 
                # multiple torrent fragments simultaneously and performs 
                # asynchronous disk I/O.
                handle = self.ses.add_torrent(params)
                info_hash = str(handle.info_hash())
                
                with self._lock:
                    self.downloads[info_hash] = handle
                
                print(f"Torrent added via magnet: {info_hash}", file=sys.stderr)
            except Exception as e:
                print(f"Error adding magnet in thread: {e}", file=sys.stderr)

        # Start the addition in a daemon thread to avoid blocking the main IPC loop
        thread = threading.Thread(target=_add_task, daemon=True)
        thread.start()
        
        # We return a temporary identifier or wait for metadata if needed.
        # For simplicity in this refactor, we return the expected hash if possible,
        # or a placeholder if parsing is slow. 
        # Actually, parse_magnet_uri is fast, so we can get the hash here.
        temp_params = lt.parse_magnet_uri(magnet_uri)
        return str(temp_params.info_hash)

    def add_torrent_file(self, torrent_data):
        """
        Decodes .torrent file data and adds it to the session.
        
        This method is refactored to emphasize multi-threaded operation.
        The actual fragment downloading is handled by libtorrent's 
        internal engine, which utilizes a pool of threads to maintain 
        simultaneous connections and piece requests.
        """
        def _add_task():
            try:
                info = lt.torrent_info(lt.bdecode(torrent_data))
                params = {
                    'save_path': self.download_dir,
                    'ti': info
                }
                
                # Libtorrent internally parallelizes the download of fragments.
                # By adding the torrent to the session, we trigger its 
                # high-performance, multi-threaded downloading engine.
                handle = self.ses.add_torrent(params)
                info_hash = str(handle.info_hash())
                
                with self._lock:
                    self.downloads[info_hash] = handle
                
                print(f"Torrent file added: {info_hash}", file=sys.stderr)
            except Exception as e:
                print(f"Error adding torrent file in thread: {e}", file=sys.stderr)

        thread = threading.Thread(target=_add_task, daemon=True)
        thread.start()
        
        # Return the info_hash immediately by parsing the data synchronously
        info = lt.torrent_info(lt.bdecode(torrent_data))
        return str(info.info_hash())

    def get_all_status(self):
        """
        Retrieves live metrics for all active and cancelled downloads.
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
                if s.has_metadata and s.progress > 0:
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
                'is_paused': is_paused,
                'is_cancelled': False
            })

        # Add cancelled torrents for UI visibility
        for info_hash, data in self.cancelled.items():
            status_list.append({
                'name': data['name'],
                'progress': 0,
                'download_rate': 0,
                'upload_rate': 0,
                'num_peers': 0,
                'state': 'Cancelled',
                'info_hash': info_hash,
                'is_seeding': False,
                'is_paused': False,
                'is_cancelled': True
            })

        return status_list

    def remove_torrent(self, info_hash):
        """Removes a torrent (active or cancelled) completely from tracking."""
        with self._lock:
            if info_hash in self.downloads:
                handle = self.downloads.pop(info_hash)
                self.ses.remove_torrent(handle)
                return True
            if info_hash in self.cancelled:
                self.cancelled.pop(info_hash)
                return True
        return False

    def cancel_torrent(self, info_hash):
        """Stops a torrent and moves it to the cancelled state without deleting files."""
        with self._lock:
            if info_hash in self.downloads:
                handle = self.downloads.pop(info_hash)
                s = handle.status()
                # Store data for potential cleanup later
                self.cancelled[info_hash] = {
                    'name': s.name,
                    'save_path': s.save_path
                }
                # Unset auto-managed to prevent session-level restarts before removal
                handle.unset_flags(lt.torrent_flags.auto_managed)
                self.ses.remove_torrent(handle)
                print(f"Torrent cancelled: {info_hash}", file=sys.stderr)
                return True
        return False

    def delete_torrent_and_files(self, info_hash):
        """Completely removes a torrent and deletes its files from disk."""
        with self._lock:
            path_to_delete = None
            
            if info_hash in self.downloads:
                handle = self.downloads.pop(info_hash)
                s = handle.status()
                path_to_delete = os.path.join(s.save_path, s.name)
                # Stop and remove
                handle.unset_flags(lt.torrent_flags.auto_managed)
                handle.pause()
                self.ses.remove_torrent(handle)
            elif info_hash in self.cancelled:
                data = self.cancelled.pop(info_hash)
                path_to_delete = os.path.join(data['save_path'], data['name'])
            
            if path_to_delete:
                # We give the OS a small moment to release any file locks if it was active
                # although remove_torrent is async, pause() helps.
                def _deferred_delete(path):
                    import time
                    time.sleep(1.0) # Small grace period for handles to close
                    try:
                        if os.path.exists(path):
                            if os.path.isdir(path):
                                shutil.rmtree(path)
                            else:
                                os.remove(path)
                            print(f"Disk cleanup complete for: {path}", file=sys.stderr)
                    except Exception as e:
                        print(f"Deferred deletion error for {path}: {e}", file=sys.stderr)
                
                # Run in thread to not block the IPC bridge
                threading.Thread(target=_deferred_delete, args=(path_to_delete,), daemon=True).start()
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
                print(f"Failed to open folder: {e}", file=sys.stderr)
                return False, str(e)
        return False, "Torrent hash not found"

    def pause_torrent(self, info_hash):
        """Pauses a specific torrent by disabling auto-management and calling pause."""
        if info_hash in self.downloads:
            handle = self.downloads[info_hash]
            # Ensure libtorrent doesn't auto-resume it
            handle.unset_flags(lt.torrent_flags.auto_managed)
            handle.pause()
            return True
        return False

    def resume_torrent(self, info_hash):
        """Resumes a specific torrent by re-enabling auto-management and calling resume."""
        if info_hash in self.downloads:
            handle = self.downloads[info_hash]
            handle.set_flags(lt.torrent_flags.auto_managed)
            handle.resume()
            return True
        return False
