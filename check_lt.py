import libtorrent as lt
import sys

print(f"Libtorrent version: {lt.version}")
try:
    print(f"Has auto_managed flag: {lt.torrent_flags.auto_managed}")
except AttributeError:
    print("MISSING auto_managed flag")

try:
    s = lt.session()
    print("Session created")
except Exception as e:
    print(f"Session creation failed: {e}")
