import socket
import threading
import json
import struct
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_loader import load_config
from motd_centering import center_text_by_width, load_font_widths

config = load_config()

HOST = config.get('server', {}).get('host', '0.0.0.0')
PORT = config.get('server', {}).get('port', 25565)

SERVER_LIST_MESSAGE = config.get('server', {}).get('messages', {}).get('motd', {}).get('line_1', 'This server is offline.') + '\n' + config.get('server', {}).get('messages', {}).get('motd', {}).get('line_2', '')
LOGIN_KICK_MESSAGE = config.get('server', {}).get('messages', {}).get('kick_message', "§cThe server is currently §lCLOSED.")
CENTER_MOTD = [True if val == '1' else False for val in tuple(config.get('server', {}).get('messages', {}).get('motd', {}).get('centered', "00"))]

PROTOCOL_VERSION = config.get('minecraft', {}).get('protocol_version', 47)
MINECRAFT_VERSION = config.get('minecraft', {}).get('version', "Maintenance")

FONT_WIDTHS = load_font_widths()

def pack_varint(data):
    ordinal = b''
    while data != 0:
        byte = data & 0x7F
        data >>= 7
        ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))
    return ordinal

def read_varint(conn):
    data = 0
    for i in range(5):
        try:
            ordinal = conn.recv(1)
            if len(ordinal) == 0:
                break
            byte = ord(ordinal)
            data |= (byte & 0x7F) << 7*i
            if not (byte & 0x80):
                break
        except (ConnectionResetError, BrokenPipeError, OSError):
            break
    return data

def pack_data(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return pack_varint(len(data)) + data

def safe_recv(conn, size):
    data = b''
    while len(data) < size:
        try:
            chunk = conn.recv(size - len(data))
            if not chunk:
                break
            data += chunk
        except (ConnectionResetError, BrokenPipeError, OSError):
            break
    return data

def handle_client(conn, addr):
    addr_str = f"{addr[0]}:{addr[1]}" if isinstance(addr, tuple) else str(addr)
    print(f"[INFO] Connection from {addr_str}")

    try:
        conn.settimeout(30.0)

        length = read_varint(conn)
        if length <= 0 or length > 1024:
            print(f"[WARN] Invalid handshake length from {addr_str}: {length}")
            return

        packet_id = read_varint(conn)

        if packet_id != 0x00:
            print(f"[WARN] Invalid handshake packet ID from {addr_str}: {packet_id}")
            return

        proto_version = read_varint(conn)

        addr_length = read_varint(conn)
        if addr_length > 0 and addr_length < 256:
            server_address = safe_recv(conn, addr_length).decode('utf-8', errors='ignore')
        else:
            server_address = "unknown"

        port_data = safe_recv(conn, 2)
        if len(port_data) == 2:
            server_port = struct.unpack('>H', port_data)[0]
        else:
            server_port = 0

        next_state = read_varint(conn)

        if next_state == 1:
            print(f"[INFO] MOTD request from {addr_str}")

            try:
                status_length = read_varint(conn)
                status_packet_id = read_varint(conn)

                if status_packet_id != 0x00:
                    print(f"[WARN] Invalid status packet ID: {status_packet_id}")
                    return
            except Exception as e:
                print(f"[WARN] Error reading status request from {addr_str}: {e}")
                return

            final_motd = SERVER_LIST_MESSAGE
            motd_lines = final_motd.split('\n')

            if CENTER_MOTD[0] and len(motd_lines) > 0:
                motd_lines[0] = center_text_by_width(motd_lines[0], FONT_WIDTHS)
            if CENTER_MOTD[1] and len(motd_lines) > 1:
                motd_lines[1] = center_text_by_width(motd_lines[1], FONT_WIDTHS)

            final_motd = '\n'.join(motd_lines)

            response_json = {
                "version": {"name": MINECRAFT_VERSION, "protocol": PROTOCOL_VERSION},
                "players": {"max": 0, "online": 0, "sample": [""]},
                "description": {"text": final_motd}
            }

            response_data = json.dumps(response_json).encode('utf-8')
            response_packet = pack_data(b'\x00' + pack_data(response_data))

            try:
                conn.sendall(response_packet)
                print(f"[INFO] Status response sent to {addr_str}")
            except Exception as e:
                print(f"[ERROR] Failed to send status response to {addr_str}: {e}")
                return

            try:
                ping_length = read_varint(conn)
                ping_packet_id = read_varint(conn)

                if ping_packet_id == 0x01 and ping_length > 1:
                    payload_size = ping_length - 1
                    if payload_size > 0 and payload_size <= 8:
                        payload = safe_recv(conn, payload_size)
                        if len(payload) == payload_size:
                            pong_packet = pack_data(b'\x01' + payload)
                            conn.sendall(pong_packet)
            except Exception as e:
                print(f"[WARN] Ping/Pong error with {addr_str}: {e}")

        elif next_state == 2:
            try:
                login_length = read_varint(conn)
                login_packet_id = read_varint(conn)

                if login_packet_id != 0x00:
                    print(f"[WARN] Invalid login packet ID: {login_packet_id}")
                    return

                username_length = read_varint(conn)
                if username_length > 0 and username_length < 17:
                    username = safe_recv(conn, username_length).decode('utf-8', errors='ignore')
                    print(f"[INFO] Login attempt from user: {username} ({addr_str})")

            except Exception as e:
                print(f"[ERROR] Error reading login packet from {addr_str}: {e}")
                return

            disconnect_json = {
                "text": LOGIN_KICK_MESSAGE
            }

            disconnect_data = json.dumps(disconnect_json).encode('utf-8')
            disconnect_packet = pack_data(b'\x00' + pack_data(disconnect_data))

            try:
                conn.sendall(disconnect_packet)
                print(f"[INFO] Disconnect message sent to {addr_str}")

                import time
                time.sleep(0.1)

            except Exception as e:
                print(f"[ERROR] Failed to send disconnect message to {addr_str}: {e}")

        else:
            print(f"[WARN] Unknown next_state from {addr_str}: {next_state}")

    except (ConnectionResetError, BrokenPipeError):
        print(f"[INFO] {addr_str} disconnected abruptly")
    except socket.timeout:
        print(f"[INFO] {addr_str} connection timed out")
    except Exception as e:
        print(f"[ERROR] Error with {addr_str}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except:
            pass
        try:
            conn.close()
        except:
            pass
        print(f"[INFO] Connection with {addr_str} closed")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"[OK] MC Server Holder running on {HOST}:{PORT}")
        print("Waiting for connections... Press Ctrl+C to stop.")

        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()

    except OSError as e:
        print(f"[ERROR] Port {PORT} may be already in use or another error occurred.")
        print(e)
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped.")
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()
