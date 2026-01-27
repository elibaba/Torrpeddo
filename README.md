# Torrpeddo

An experimental, single-user torrent client built with Python and Flask.

## Features

- **Magnet Link Support**: Easily add downloads via magnet URIs.
- **.torrent File Upload**: Support for traditional torrent files.
- **Real-time Monitoring**: Live status updates for download/upload speeds, progress, and peers.
- **Customizable Destination**: Set your download folder directly from the web UI.
- **Premium UI**: Modern dark-mode interface with glassmorphism and smooth animations.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Torrpeddo.git
   cd Torrpeddo
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: On Linux, you might need to install `libtorrent` system-wide:*
   `sudo apt-get install python3-libtorrent`

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the dashboard**:
   Open `http://localhost:5000` in your web browser.

## Tech Stack

- **Backend**: Flask (Python)
- **Torrent Engine**: libtorrent
- **Frontend**: Vanilla HTML/CSS/JS

## Project Structure

```text
Torrpeddo/
├── app.py              # Flask entry point
├── backend/
│   └── manager.py      # Core torrent logic
├── static/             # Frontend assets
│   └── css/
├── templates/          # HTML templates
└── requirements.txt    # Python dependencies
```
