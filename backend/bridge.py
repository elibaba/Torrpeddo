"""
bridge.py - Python IPC Bridge

This script serves as the glue between the Electron desktop app and the 
TorrentManager (libtorrent). It reads JSON-formatted commands from 
standard input and returns JSON-formatted responses to standard output.
"""

import sys
import json
import os

# Add the current directory to sys.path so we can properly import the backend module
sys.path.append(os.getcwd())

from backend.manager import TorrentManager

def main():
    # Initialize the core TorrentManager singleton
    manager = TorrentManager()
    
    # Continuous loop to listen for commands from Electron
    while True:
        try:
            # Read a line from stdin (JSON command from main.js)
            line = sys.stdin.readline()
            if not line:
                break
            
            command_data = json.loads(line)
            cmd = command_data.get('command')
            args = command_data.get('args', {})
            request_id = command_data.get('id')
            
            # Prepare the response with the matching request ID
            response = {'id': request_id}
            
            # Dispatch commands to the TorrentManager
            if cmd == 'get_status':
                # Returns current download metrics for all active torrents
                response['data'] = manager.get_all_status()
            elif cmd == 'get_config':
                # Returns the current download directory
                response['data'] = {'download_dir': manager.download_dir}
            elif cmd == 'set_config':
                # Updates the download directory
                new_dir = args.get('download_dir')
                success = manager.set_download_dir(new_dir)
                response['data'] = {'success': success}
            elif cmd == 'add_torrent_file':
                # Loads a .torrent file from a local path providing full disk access via Electron
                filepath = args.get('filepath')
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        torrent_data = f.read()
                    info_hash = manager.add_torrent_file(torrent_data)
                    response['data'] = {'success': True, 'info_hash': info_hash}
                else:
                    response['data'] = {'success': False, 'error': 'File not found'}
            elif cmd == 'add_magnet':
                # Adds a magnet URI to the download queue
                url = args.get('magnet_url')
                info_hash = manager.add_magnet(url)
                response['data'] = {'success': True, 'info_hash': info_hash}
            elif cmd == 'remove_torrent':
                # Stops and removes a torrent from the session
                info_hash = args.get('info_hash')
                success = manager.remove_torrent(info_hash)
                response['data'] = {'success': success}
            elif cmd == 'pause_torrent':
                # Pauses an active download
                info_hash = args.get('info_hash')
                success = manager.pause_torrent(info_hash)
                response['data'] = {'success': success}
            elif cmd == 'resume_torrent':
                # Resumes a paused download
                info_hash = args.get('info_hash')
                success = manager.resume_torrent(info_hash)
                response['data'] = {'success': success}
            elif cmd == 'open_folder':
                # Opens the containing folder of a downloaded torrent in the native file explorer
                info_hash = args.get('info_hash')
                success, message = manager.open_folder(info_hash)
                response['data'] = {'success': success, 'message': message}
            else:
                # Handle unknown command scenarios
                response['error'] = 'Unknown command'
            
            # Output the response as JSON to stdout
            print(json.dumps(response))
            sys.stdout.flush() # Ensure it's sent immediately
            
        except Exception as e:
            # Catch and report global bridge errors
            print(json.dumps({'error': str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
