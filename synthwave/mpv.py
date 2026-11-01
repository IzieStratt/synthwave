"""A minimal client for mpv's JSON IPC socket (https://mpv.io/manual/stable/#json-ipc)."""
import contextlib, json, os, socket, subprocess, sys, tempfile, time

PROPS = ("pause", "volume", "mute", "media-title", "core-idle")
WINDOWS = sys.platform == "win32"
if WINDOWS:
    import ctypes, msvcrt


def parse(buf):
    """Split mpv's newline-delimited JSON into messages plus the leftover partial line."""
    *lines, rest = buf.split(b"\n")
    return [json.loads(l) for l in lines if l], rest


class Pipe:
    """On Windows mpv listens on a named pipe; this gives it the parts of the socket API Mpv uses."""

    def connect(self, path):
        self.f = open(path, "r+b", buffering=0)
        self.handle = msvcrt.get_osfhandle(self.f.fileno())

    def setblocking(self, flag):
        pass  # recv never blocks: it peeks first

    def sendall(self, data):
        self.f.write(data)

    def recv(self, n):
        ready = ctypes.c_ulong()
        ctypes.windll.kernel32.PeekNamedPipe(self.handle, None, 0, None, ctypes.byref(ready), None)
        if not ready.value:
            raise BlockingIOError
        return self.f.read(min(n, ready.value))

    def close(self):
        if hasattr(self, "f"):
            self.f.close()


class Mpv:
    """Headless mpv, started paused and idle; property changes arrive through events()."""

    def __init__(self, volume):
        name = f"synthwave-{os.getpid()}"
        self.path = rf"\\.\pipe\{name}" if WINDOWS else os.path.join(tempfile.gettempdir(), f"{name}.sock")
        self.proc = subprocess.Popen(
            ["mpv", "--no-video", "--no-terminal", "--idle=yes", "--pause", f"--volume={volume}",
             f"--input-ipc-server={self.path}"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.sock, self.buf = Pipe() if WINDOWS else socket.socket(socket.AF_UNIX), b""
        for _ in range(100):  # mpv needs a moment to open the socket
            try:
                self.sock.connect(self.path)
                break
            except OSError:
                time.sleep(0.05)
        else:
            self.proc.kill()
            sys.exit("synthwave: couldn't connect to mpv")
        self.sock.setblocking(False)
        for i, prop in enumerate(PROPS):
            self.send("observe_property", i, prop)

    def send(self, *cmd, **fields):
        """Run an mpv command; pass request_id=n to match its reply in events()."""
        self.sock.sendall(json.dumps({"command": cmd, **fields}).encode() + b"\n")

    def set(self, prop, value):
        self.send("set_property", prop, value)

    def events(self):
        with contextlib.suppress(BlockingIOError):
            self.buf += self.sock.recv(65536)
        msgs, self.buf = parse(self.buf)
        return msgs

    def close(self):
        with contextlib.suppress(OSError):
            self.send("quit")
        try:
            self.proc.wait(2)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.sock.close()
        if not WINDOWS:  # a named pipe goes away by itself
            with contextlib.suppress(FileNotFoundError):
                os.remove(self.path)
