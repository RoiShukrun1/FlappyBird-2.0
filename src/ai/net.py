# net.py
import json
import socket
import threading

ENC = "utf-8"
DELIM = b"\n"

def make_server(host: str, port: int) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(1)
    return s

def connect(host: str, port: int, timeout: float = 5.0) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))
    s.settimeout(None)
    return s

def send_json(sock: socket.socket, obj: dict):
    try:
        data = json.dumps(obj, separators=(",", ":")).encode(ENC) + DELIM
        sock.sendall(data)
    except OSError:
        # socket closed/disconnected
        pass

def start_reader(sock: socket.socket, on_msg):
    """
    Read newline-delimited JSON on a background thread and call on_msg(dict).
    Quits quietly if the socket is closed/reset.
    """
    buf = b""

    def _run():
        nonlocal buf
        try:
            while True:
                try:
                    chunk = sock.recv(4096)
                except (ConnectionResetError, OSError):
                    break
                if not chunk:
                    break
                buf += chunk
                while True:
                    i = buf.find(DELIM)
                    if i < 0:
                        break
                    line = buf[:i]
                    buf = buf[i + 1:]
                    if not line:
                        continue
                    try:
                        on_msg(json.loads(line.decode(ENC)))
                    except Exception:
                        pass
        finally:
            try:
                sock.close()
            except Exception:
                pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t