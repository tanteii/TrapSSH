import asyncssh
import asyncio
import os
from pathlib import Path
from datetime import datetime, timezone

HOST = os.getenv("HONEYPOT_HOST", "0.0.0.0")
PORT = int(os.getenv("HONEYPOT_PORT", 2222))
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

class HoneypotSession(asyncssh.SSHServerSession):
    """Handles one attacker session — records all input and provides fake responses."""

    def __init__(self, attacker_ip, username, password):
        self.attacker_ip = attacker_ip
        self.username = username
        self.password = password
        self.commands: list[str] = []
        self.buf = ""
        self.chan = None

    def connection_made(self, chan):
        self.chan = chan
        chan.write(f"Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)\r\n\r\n")
        chan.write(f" * Documentation:  https://help.ubuntu.com\r\n\r\n")
        self.chan.write(PROMPT)

    def shell_requested(self):
        return True

    def data_received(self, data, datatype):
        self.buf += data

        # Process complete lines (Enter key)
        while "\n" in self.buf or "\r" in self.buf:
            for sep in ("\r\n", "\n", "\r"):
                if sep in self.buf:
                    line, self.buf = self.buf.split(sep, 1)
                    print(line)

                    self.chan.write(PROMPT)
                    break

    def eof_received(self):
        return False

    def connection_lost(self, exc):
        pass

# SSH server
PROMPT = "root@ubuntu:~# "
class HoneypotServer(asyncssh.SSHServer):
    def connection_made(self, conn):
        self.conn = conn
        self.peer = conn.get_extra_info("peername", ("unknown", 0))
        self.ip = self.peer[0]

        print(f"Connection from {self.ip}")

    def begin_auth(self, username):
        # force auth for password
        self.username = username
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        print(f"Login attempt from ({self.ip}):  {username} / {password}")
        # accept everything
        return True
    
    def session_requested(self):
        return HoneypotSession(
            attacker_ip=self.ip,
            username=getattr(self, "username", "unknown"),
            password="",
        )

# generate host key (first run only)
KEY_PATH = LOG_DIR / "host_key"
def get_host_key():
    if not KEY_PATH.exists():
        key = asyncssh.generate_private_key("ssh-rsa")
        KEY_PATH.write_bytes(key.export_private_key())
        KEY_PATH.chmod(0o600)
        print(f"[honeypot] Generated host key at {KEY_PATH}", flush=True)
    return asyncssh.read_private_key(str(KEY_PATH))


async def run_server():
    host_key = get_host_key()

    server = await asyncssh.create_server(
        HoneypotServer,
        HOST,
        PORT,
        server_host_keys=[host_key],
        server_version="placeholder",
        # line_editor=False,
    )

    print(f"[honeypot] Listening on {HOST}:{PORT}", flush=True)

    async with server:
        await asyncio.get_event_loop().create_future()  # run forever

def main():
    loop = asyncio.new_event_loop()

    try:
        loop.run_until_complete(run_server())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
