# Torrpeddo Project Book

## Project Description
Torrpeddo is a high-performance, premium torrent client designed for simplicity and efficiency. It leverages the powerful `libtorrent` library as its core engine and features a modern, responsive UI built with Electron.

## Key Concepts

### Multi-threaded Downloading
Torrpeddo utilizes the advanced multi-threading capabilities of the `libtorrent` 2.0+ engine. Unlike simpler clients that may download linearly, Torrpeddo leverages a thread pool to:
- Handle multiple torrent fragments simultaneously.
- Manage asynchronous disk I/O to prevent UI blocking.
- Maintain high-speed network connections across hundreds of peers in parallel.

The Python `TorrentManager` has also been refactored to handle torrent additions in separate execution threads, ensuring the IPC bridge between Electron and Python remains fluid and responsive.

### Electron-Python IPC Bridge
The application architecture separates the frontend (Electron) from the backend (Python/libtorrent) using a robust JSON-RPC bridge over stdin/stdout. This allows for:
- Native desktop performance.
- Seamless integration with operating system APIs.
- Modular development where the backend logic is decoupled from the user interface.

## Usage Instructions

1. **Adding Torrents**: Simply click "Add Magnet" or "Open Torrent File" in the UI. 
2. **Managing Downloads**: You can pause, resume, or remove torrents directly from the main dashboard.
3. **Open Downloads**: Once a download is complete (or in progress), use the "Open Folder" button to locate your files instantly.
4. **Settings**: Configure your default download directory in the settings panel to keep your downloads organized.

## Development Process

The development of Torrpeddo followed a rigorous architectural plan:
1. **Engine Selection**: `libtorrent` was chosen for its proven performance and feature set.
2. **Framework Migration**: Initially conceived as a Flask app, Torrpeddo was refactored into a native Electron app to provide a superior desktop experience.
3. **Optimizations**: Continuous refinements were made to the IPC bridge, logging mechanisms, and multi-threading implementation to ensure peak efficiency.
4. **Documentation**: Comprehensive documentation and this project book were generated to ensure the project remains maintainable and transparent.

---
(c) 2026 Torrpeddo Team. All rights reserved.
