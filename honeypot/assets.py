from datetime import datetime, timedelta
import random

PROMPT = "root@ubuntu:~$ "

FAKE_RESPONSES = {
    "whoami":  "root",
    "id":      "uid=0(root) gid=0(root) groups=0(root)",
    "uname -a": "Linux ubuntu 5.15.0-91-generic #101-Ubuntu SMP Thu Jun 18 21:54:43 UTC 2026 x86_64 x86_64 x86_64 GNU/Linux",
    "uname -s -v -n -r -m": "Linux ubuntu 5.15.0-91-generic #101-Ubuntu SMP Thu Jun 18 21:54:43 UTC 2026 x86_64",
    "uname -m":   "x86_64",
    "uname -r":   "5.15.0-91-generic",
    "uname -s":   "Linux",
    "uname -n":   "ubuntu",
    "arch":       "x86_64",
    "hostname":   "ubuntu",
    #### temp (TODO: clean and check validity)
    "busybox":              "BusyBox v1.30.1 (Ubuntu 1:1.30.1-7ubuntu3) multi-call binary.",
    "busybox cat /proc/self/exe": "",
    "cat /proc/cpuinfo":    "processor\t: 0\nvendor_id\t: GenuineIntel\nmodel name\t: Intel(R) Xeon(R) CPU E5-2680 v3\ncpu MHz\t\t: 2494.224\ncache size\t: 30720 KB",
    "cat /proc/meminfo":    "MemTotal:        8175692 kB\nMemFree:         6823412 kB\nMemAvailable:    7234816 kB",
    "cat /proc/version":    "Linux version 5.15.0-91-generic (buildd@lcy02-amd64-059) (gcc (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0) #101-Ubuntu SMP Tue Nov 14 13:30:08 UTC 2023",
    "nproc":      "2",
    "lscpu":      "Architecture:            x86_64\nCPU(s):                  2\nModel name:              Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz",
    "which curl":   "/usr/bin/curl",
    "which wget":   "/usr/bin/wget",
    "which python": "/usr/bin/python",
    "which python3": "/usr/bin/python3",
    "which perl":   "/usr/bin/perl",
    ####
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

def get_last_login():
    days = random.randint(1, 7)
    hours = random.randint(0, 23)
    last = datetime.now() - timedelta(days, hours)
    return last.strftime("%a %b %d %H:%M:%S %Y")

def get_motd():
    now = datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y")
    last_login = get_last_login()
    # TODO: exclue private/reserved IP ranges in case honeypot giveaway
    last_ip = f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"

    return f"""Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

  System information as of {now}

  System load:  0.08               Processes:               112
  Usage of /:   22.3% of 39.24GB   Users logged in:         0
  Memory usage: 5%                 IPv4 address for eth0:   10.0.0.4
  Swap usage:   0%

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.
   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

14 updates can be applied immediately.
3 of these updates are standard security updates.
To see these additional updates run: apt list --upgradable

2 additional security updates can be applied with ESM Apps.
Learn more about enabling ESM Apps service at https://ubuntu.com/esm

New release '24.04.4 LTS' available.
Run 'do-release-upgrade' to upgrade to it.

*** System restart required *** 
Last login: {last_login} from {last_ip}

""".replace("\n", "\r\n")
