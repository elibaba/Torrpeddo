"""
bridge.py - Python IPC Bridge

This script serves as the glue between the Electron desktop app and the 
TorrentManager (libtorrent). It reads JSON-formatted commands from 
standard input and returns JSON-formatted responses to standard output.
"""

import sys
import json
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from backend.manager import TorrentManager

def main():
    # Initialize the core TorrentManager singleton
    manager = TorrentManager()
    
    # Continuous loop to listen for commands from Electron
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                command_data = json.loads(line)
                cmd = command_data.get('command')
                args = command_data.get('args', {})
                request_id = command_data.get('id')
                
                response = {'id': request_id}
                
                # Dispatch commands
                if cmd == 'get_status':
                    response['data'] = manager.get_all_status()
                elif cmd == 'get_config':
                    response['data'] = {'download_dir': manager.download_dir}
                elif cmd == 'set_config':
                    new_dir = args.get('download_dir')
                    success = manager.set_download_dir(new_dir)
                    response['data'] = {'success': success}
                elif cmd == 'add_torrent_file':
                    filepath = args.get('filepath')
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            torrent_data = f.read()
                        info_hash = manager.add_torrent_file(torrent_data)
                        response['data'] = {'success': True, 'info_hash': info_hash}
                    else:
                        response['data'] = {'success': False, 'error': 'File not found'}
                elif cmd == 'add_magnet':
                    url = args.get('magnet_url')
                    info_hash = manager.add_magnet(url)
                    response['data'] = {'success': True, 'info_hash': info_hash}
                elif cmd == 'remove_torrent':
                    info_hash = args.get('info_hash')
                    success = manager.remove_torrent(info_hash)
                    response['data'] = {'success': success}
                elif cmd == 'delete_torrent_and_files':
                    info_hash = args.get('info_hash')
                    success = manager.delete_torrent_and_files(info_hash)
                    response['data'] = {'success': success}
                elif cmd == 'pause_torrent':
                    info_hash = args.get('info_hash')
                    success = manager.pause_torrent(info_hash)
                    response['data'] = {'success': success}
                elif cmd == 'resume_torrent':
                    info_hash = args.get('info_hash')
                    success = manager.resume_torrent(info_hash)
                    response['data'] = {'success': success}
                elif cmd == 'open_folder':
                    info_hash = args.get('info_hash')
                    success, message = manager.open_folder(info_hash)
                    response['data'] = {'success': success, 'message': message}
                else:
                    response['error'] = 'Unknown command'
                
                print(json.dumps(response))
                sys.stdout.flush()
                
            except Exception as e:
                print(f"Bridge Error processing command: {e}", file=sys.stderr)
                try:
                    err_response = {'id': request_id if 'request_id' in locals() else None, 'error': str(e)}
                    print(json.dumps(err_response))
                    sys.stdout.flush()
                except:
                    pass
            sys.stdout.flush()
            
        except Exception as e:
            print(json.dumps({'error': str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
