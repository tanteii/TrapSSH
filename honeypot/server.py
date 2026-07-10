import asyncssh
import asyncio
import os
import json
from pathlib import Path
from datetime import datetime

from assets import FAKE_RESPONSES, PROMPT, get_motd

HOST = os.getenv("HONEYPOT_HOST", "0.0.0.0")
PORT = int(os.getenv("HONEYPOT_PORT", 22))
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "honeypot.jsonl"
def log_event(event):
    event["timestamp"] = datetime.now().isoformat()
    line = json.dumps(event)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

class HoneypotSession(asyncssh.SSHServerSession):
    """Handles one attacker session — records all input and provides fake responses."""

    def __init__(self, attacker_ip, username, password):
        self.attacker_ip = attacker_ip
        self.username = username
        self.password = password
        self.commands: list[str] = []
        self.buffer = ""
        self.channel = None

    def connection_made(self, channel):
        self.channel = channel
        # mimic linux shell
        channel.write(get_motd())
        channel.write(PROMPT)

    def shell_requested(self):
        return True

    def data_received(self, data, datatype):
        self.buffer += data

        # split complete lines (enter key)
        while "\n" in self.buffer or "\r" in self.buffer:
            for sep in ("\r\n", "\n", "\r"):
                if sep in self.buffer:
                    line, self.buffer = self.buffer.split(sep, 1)
                    print(line)
                    self.handle_command(line.strip())
                    break

    def handle_command(self, cmd):
        if not cmd:
            self.channel.write(PROMPT)
            return
        
        self.commands.append(cmd)
        log_event({
            "type": "command",
            "ip": self.attacker_ip,
            "username": self.username,
            "command": cmd,
        })

        # lookup fake response
        response = FAKE_RESPONSES.get(cmd)
        
        if response is None and cmd not in FAKE_RESPONSES:
            base = cmd.split()[0]
            response = f"{base}: command not found"

        # exit/logout command received
        if response is None:
            print(f"Disconnected:  {self.attacker_ip}")
            self.channel.write("logout\r\n")
            self.channel.close()
            return
        
        response = response.replace("{ip}", self.attacker_ip)
        self.channel.write(response.replace("\n", "\r\n") + "\r\n" + PROMPT)

    def exec_requested(self, command):
        print(f"exec request from {self.attacker_ip}:\n{command}\n")

        log_event({
            "type": "exec_request",
            "ip": self.attacker_ip,
            "username": self.username,
            "command": command,
        })
        self.handle_command(command.strip())
        self.channel.close()
        return True

    def eof_received(self):
        log_event({
            "type":       "session_end",
            "ip":         self.attacker_ip,
            "username":   self.username,
            "commands":   self.commands,
            "command_count": len(self.commands),
        })
        # close channel
        return False

    def connection_lost(self, exc):
        pass

# SSH server
class HoneypotServer(asyncssh.SSHServer):
    def connection_made(self, conn):
        self.conn = conn
        self.peer = conn.get_extra_info("peername", ("unknown", 0))
        self.ip = self.peer[0]
        self.client_version = conn.get_extra_info("client_version", "unknown")
        
        log_event({
            "type": "connection",
            "ip": self.ip,
            "client_version": self.client_version,
        })

        print(f"Connection from {self.ip}")

    def begin_auth(self, username):
        # force auth for password
        self.username = username
        return True

    def password_auth_supported(self):
        return True

    async def validate_password(self, username, password):
        self.password = password

        # mimic authentication latency
        await asyncio.sleep(0.8)

        log_event({
            "type":       "login_attempt",
            "ip":         self.ip,
            "username":   username,
            "password":   password,
        })
        # accept everything
        return True
    
    def public_key_auth_supported(self):
        return True

    def validate_public_key(self, username, key):
        # print(f"public key auth attempt from {self.ip} with username: {username}")
        log_event({
            "type": "pubkey_attempt",
            "ip": self.ip,
            "username": username,
            "key": key.get_fingerprint(),
        })
        # reject and try fallback to password auth
        return False
        
    def session_requested(self):
        return HoneypotSession(
            attacker_ip=self.ip,
            username=getattr(self, "username", "unknown"),
            password=getattr(self, "password", ""),
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
        HoneypotServer, HOST, PORT,
        server_host_keys=[host_key],
        server_version="SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6",
        # line_editor=False,
    )

    log_event({"type": "server_start", "host": HOST, "port": PORT})
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
