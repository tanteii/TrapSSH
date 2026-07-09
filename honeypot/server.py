import asyncssh
import asyncio
import os
import json
from pathlib import Path
from datetime import datetime

HOST = os.getenv("HONEYPOT_HOST", "0.0.0.0")
PORT = int(os.getenv("HONEYPOT_PORT", 22))
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

FAKE_RESPONSES = {
    "whoami":  "root",
    "id":      "uid=0(root) gid=0(root) groups=0(root)",
    "uname -a": "Linux ubuntu 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux",
    "uname":   "Linux",
    "pwd":     "/root",
    "ls":      "snap  .bashrc  .ssh  .profile",
    "ls -la":  "total 32\ndrwx------ 4 root root 4096 Jan  8 09:12 .\ndrwxr-xr-x 20 root root 4096 Jan  8 09:10 ..\n-rw-r--r-- 1 root root 3106 Jan  8 09:10 .bashrc\ndrwx------ 2 root root 4096 Jan  8 09:12 .ssh",
    "ps":      "  PID TTY          TIME CMD\n    1 pts/0    00:00:00 bash\n   42 pts/0    00:00:00 ps",
    "ps aux":  "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nroot         1  0.0  0.1  21992  3648 ?        Ss   09:10   0:00 /bin/bash",
    "env":     "SHELL=/bin/bash\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\nHOME=/root\nLOGNAME=root",
    "ifconfig": "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n        inet 10.0.0.4  netmask 255.255.255.0  broadcast 10.0.0.255",
    "ip a":    "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536\n2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500\n    inet 10.0.0.4/24",
    "cat /etc/passwd": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin",
    "cat /etc/os-release": 'NAME="Ubuntu"\nVERSION="22.04.3 LTS (Jammy Jellyfish)"\nID=ubuntu',
    "history": "    1  apt update\n    2  apt install -y curl\n    3  ls\n    4  history",
    "uptime":  " 09:15:01 up 12 days,  3:42,  1 user,  load average: 0.00, 0.01, 0.05",
    "df -h":   "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        40G  8.2G   30G  22% /",
    "free -m": "              total        used        free\nMem:           7982        412       7234\nSwap:          2047          0       2047",
    "w":       " 09:15:01 up 12 days,  3:42,  1 user\nUSER     TTY   FROM   LOGIN@   IDLE  JCPU  PCPU WHAT\nroot     pts/0 {ip}  09:12   0.00s  0.00s  0.00s -bash",
    "last":    "root     pts/0        {ip}        Mon Jan  8 09:12   still running",
    "exit":    None,
    "logout":  None,
}

PROMPT = "root@ubuntu:~$ "

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
        channel.write(f"Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)\r\n\r\n")
        channel.write(f" * Documentation:  https://help.ubuntu.com\r\n\r\n")
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

        if response is None:
            # exit/logout
            self.channel.close()
            return
        
        response = response.replace("{ip}", self.attacker_ip)
        self.channel.write(response.replace("\n", "\r\n") + "\r\n" + PROMPT)


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
        # self.conn = conn
        # self.peer = conn.get_extra_info("peername", ("unknown", 0))
        # self.ip = self.peer[0]
        
        # log_event({
        #     "type": "connection",
        #     "ip": self.ip,
        # })

        # print(f"Connection from {self.ip}")

        try:
            self.conn = conn
            self.peer = conn.get_extra_info("peername", ("unknown", 0))
            self.ip = self.peer[0]
            
            log_event({
                "type": "connection",
                "ip": self.ip,
            })
            print(f"Connection from {self.ip}")
        except Exception as e:
            print(f"Error in connection_made: {e}")

    def begin_auth(self, username):
        # force auth for password
        self.username = username
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        self.password = password;
        log_event({
            "type":       "login_attempt",
            "ip":         self.ip,
            "username":   username,
            "password":   password,
        })
        # accept everything
        return True
    
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
