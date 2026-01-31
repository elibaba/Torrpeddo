
"""
peer.py - Peer Connection Handler

Manages a single TCP connection to a peer using the BitTorrent protocol.
"""

import socket
import struct
import threading
import time

class PeerConnection:
    def __init__(self, ip, port, info_hash, peer_id, torrent_manager):
        self.ip = ip
        self.port = port
        self.info_hash = info_hash
        self.my_peer_id = peer_id
        self.manager = torrent_manager
        
        self.sock = None
        self.connected = False
        self.choked = True
        self.interested = False
        
        self.peer_choking = True
        self.peer_interested = False
        
        self.buffer = b""
        self.thread = None
        
    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
    def _run(self):
        try:
            self.sock = socket.create_connection((self.ip, self.port), timeout=5)
            # Send Handshake
            handshake = self._make_handshake()
            self.sock.sendall(handshake)
            
            # Receive Handshake
            response = self._recv_handshake()
            if not self._validate_handshake(response):
                print(f"Handshake failed with {self.ip}")
                self.close()
                return

            self.connected = True
            print(f"Connected to peer: {self.ip}")
            
            # Send Interested
            self._send_message(2) # Interested
            self.interested = True

            # Receive Loop
            while self.connected:
                # Read message length prefix (4 bytes)
                length_prefix = self._recv_exact(4)
                if not length_prefix:
                    break
                    
                length = struct.unpack("!I", length_prefix)[0]
                if length == 0:
                    continue # Keep-alive
                
                # Read message ID
                msg_id = self._recv_exact(1)[0]
                payload_len = length - 1
                payload = self._recv_exact(payload_len)
                
                self._handle_message(msg_id, payload)
                
        except Exception as e:
            print(f"Peer error {self.ip}: {e}")
        finally:
            self.close()

    def _make_handshake(self):
        pstr = b"BitTorrent protocol"
        reserved = b"\x00" * 8
        return struct.pack(f"!B{len(pstr)}s8s20s20s", len(pstr), pstr, reserved, self.info_hash, self.my_peer_id)

    def _recv_handshake(self):
        # pstrlen (1) + pstr (19) + reserved (8) + info_hash (20) + peer_id (20) = 68 bytes
        return self._recv_exact(68)

    def _validate_handshake(self, response):
        if not response or len(response) < 68:
            return False
        
        pstrlen = response[0]
        if pstrlen != 19:
            return False
            
        pstr = response[1:20]
        if pstr != b"BitTorrent protocol":
            return False
            
        r_info_hash = response[28:48]
        if r_info_hash != self.info_hash:
            return False
            
        return True

    def _recv_exact(self, n):
        data = b""
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _send_message(self, msg_id, payload=b""):
        length = 1 + len(payload)
        msg = struct.pack("!IB", length, msg_id) + payload
        self.sock.sendall(msg)

    def _handle_message(self, msg_id, payload):
        if msg_id == 0: # Choke
            self.peer_choking = True
            print(f"{self.ip} Choked us")
        elif msg_id == 1: # Unchoke
            self.peer_choking = False
            print(f"{self.ip} Unchoked us")
            # TODO: Start requesting pieces!
        elif msg_id == 4: # Have
            piece_index = struct.unpack("!I", payload)[0]
            # self.manager.update_peer_have(self.ip, piece_index)
        elif msg_id == 5: # Bitfield
            pass # TODO: Parse bitfield
        elif msg_id == 7: # Piece
            index = struct.unpack("!I", payload[0:4])[0]
            begin = struct.unpack("!I", payload[4:8])[0]
            block = payload[8:]
            print(f"Received block for piece {index}, offset {begin}, len {len(block)}")
            # self.manager.handle_block(index, begin, block)

    def close(self):
        self.connected = False
        if self.sock:
            self.sock.close()
