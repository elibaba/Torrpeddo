# Torrpeddo Documentation

## Backend Architecture

### TorrentManager (`backend/manager.py`)
The `TorrentManager` class is a Singleton that manages the `libtorrent` session. 
- `add_magnet(uri)`: Parses and adds a magnet link to the session.
- `add_torrent_file(data)`: Decodes and adds a `.torrent` file.
- `get_all_status()`: Returns a list of all active torrents with their current metrics.
- `set_download_dir(path)`: Updates the global download path for new torrents.

### Flask API (`app.py`)
Provides RESTful endpoints for the frontend to interact with the `TorrentManager`.

## Frontend Design

The frontend is built with **Vanilla CSS** and **HTML5**. It uses a dark-themed "Premium" design system featuring:
- **Inter Font**: High-quality typography.
- **Glassmorphism**: Backdrop blur effects on cards.
- **Dynamic Updates**: The dashboard polls the `/api/status` endpoint every 2 seconds to provide live feedback.

## Configuration

Downloads are saved to `~/Downloads/Torrpeddo-Downloads` by default. This can be changed in the UI "Destination" section.
