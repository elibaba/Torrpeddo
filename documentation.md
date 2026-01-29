# Torrpeddo Documentation

## Backend Architecture

### TorrentManager (`backend/manager.py`)
The `TorrentManager` class is a Singleton that manages the `libtorrent` session. 
- `add_magnet(uri)`: Parses and adds a magnet link to the session.
- `add_torrent_file(data)`: Decodes and adds a `.torrent` file.
- `get_all_status()`: Returns a list of all active torrents with their current metrics.
- `set_download_dir(path)`: Updates the global download path for new torrents.

### IPC Bridge (`backend/bridge.py`)
A Python script that acts as an interface between the Electron main process and the `TorrentManager`. It communicates via JSON over standard input/output.

### Electron App (`main.js` & `preload.js`)
- `main.js`: Manages the lifecycle of the Electron app and the Python bridge process.
- `preload.js`: Safely exposes the bridge API to the renderer process.

## Frontend Design

The frontend is built with **Vanilla CSS** and **HTML5**, running in the Electron renderer process. It uses a dark-themed "Premium" design system featuring:
- **Inter Font**: High-quality typography.
- **Glassmorphism**: Backdrop blur effects on cards.
- **IPC Communication**: The dashboard communicates with the backend via asynchronous IPC commands instead of HTTP.

## Configuration

Downloads are saved to `~/Downloads/Torrpeddo-Downloads` by default. This can be changed in the UI "Destination" section.
