from flask import Flask, render_template, request, jsonify
from backend.manager import TorrentManager
import os

app = Flask(__name__)
manager = TorrentManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(manager.get_all_status())

@app.route('/api/add-magnet', methods=['POST'])
def add_magnet():
    data = request.json
    magnet_url = data.get('magnet_url')
    if not magnet_url:
        return jsonify({'error': 'No magnet URL provided'}), 400
    try:
        info_hash = manager.add_magnet(magnet_url)
        return jsonify({'success': True, 'info_hash': info_hash})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-torrent', methods=['POST'])
def upload_torrent():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    try:
        torrent_data = file.read()
        info_hash = manager.add_torrent_file(torrent_data)
        return jsonify({'success': True, 'info_hash': info_hash})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    if request.method == 'GET':
        return jsonify({'download_dir': manager.download_dir})
    else:
        data = request.json
        new_dir = data.get('download_dir')
        if manager.set_download_dir(new_dir):
            return jsonify({'success': True})
        return jsonify({'error': 'Invalid directory'}), 400

@app.route('/api/remove/<info_hash>', methods=['DELETE'])
def remove_torrent(info_hash):
    if manager.remove_torrent(info_hash):
        return jsonify({'success': True})
    return jsonify({'error': 'Torrent not found'}), 404

@app.route('/api/pause/<info_hash>', methods=['POST'])
def pause_torrent(info_hash):
    if manager.pause_torrent(info_hash):
        return jsonify({'success': True})
    return jsonify({'error': 'Torrent not found'}), 404

@app.route('/api/resume/<info_hash>', methods=['POST'])
def resume_torrent(info_hash):
    if manager.resume_torrent(info_hash):
        return jsonify({'success': True})
    return jsonify({'error': 'Torrent not found'}), 404

@app.route('/api/select-dir', methods=['POST'])
def select_dir():
    path = manager.select_directory()
    if path:
        return jsonify({'path': path})
    return jsonify({'cancelled': True})

@app.route('/api/open-folder', methods=['POST'])
def open_folder():
    data = request.json
    info_hash = data.get('info_hash')
    success, message = manager.open_folder(info_hash)
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'error': message}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
