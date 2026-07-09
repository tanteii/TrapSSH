# TrapSSH
Containerised, low-interaction SSH honeypot for threat intelligence analysis.
The honeypot captures real-world attacker behaviour with an extensive logging system that records credentials, commands and session data from automated bots and manual intrusion attemps. 

Built with Python, asyncssh and Docker. Deployed on Oracle Cloud.

## Features
- Accepts any SSH username and password combination on a publicly hosted honeypot
- Mimics a Ubuntu 22.04 shell with realistic CLI and responses
- Logs connection attempts, credential pair and command sequences to structured JSON
- Containerised in Docker for safer isolation from host system

## Setup

### Prerequisites

**IMPORTANT**: This honeypot is intended to be run on a public-facing VPS to attract real attack traffic. Port forwarding on a home network can publicly expose the honeypot in the same way but risks your personal network in the case of a compromised honeypot. A VPS provides the same internet exposure while keeping attacker traffic isolated from personal devices.

- Isolated virtual machine / virtual private server (VPS) for hosting honeypot
- Docker and Docker compose installed on the VPS
- Port 22 open on the VPS (eg. through firewall, security group)

### Running the honeypot

#### Connect to VPS
Example:

```bash
ssh -p (port) -i ~/.ssh/id_ed25519 ubuntu@<your-vps-ip>
```
where (port) is whatever port your SSH daemon is listening on.

**Note:** If your VPS uses port 22 for legitimate SSH access, change the real SSH daemon to listen on a different port before deployment (e.g. 2222).

#### Clone and run
```bash
git clone https://github.com/tanteii/TrapSSH.git
cd TrapSSH
docker compose up -d
```

The honeypot will begin listening on port 22 immediately.

## Commands
Once connected to VPS and in cloned project directory:

### Start/stop honeypot

```bash
docker compose up -d

docker compose down
```

### Rebuild after code changes

```bash
docker compose up -d --build
```

### Check running status

```bash
docker ps
```

### View live logs

```bash
docker logs -f ssh-honeypot
```

### Read log file

```bash
# raw logs
cat logs/honeypot.jsonl

# pretty print
cat logs/honeypot.jsonl | python3 -m json.tool
```

### Copy logs to local machine

```bash
scp -i ~/.ssh/id_ed25519 ubuntu@<your-vps-ip>:~/TrapSSH/logs/honeypot.jsonl .
```

## Log format example

TBA

## Ethics

This honeypot is deployed on infrastructure owned and controlled by me and it does not probe, scan or interact with any external systems. All collected data is used for research and educational purposes only.

## Built with
 
- [asyncssh](https://asyncssh.readthedocs.io/) — async SSH server library
- [Docker](https://www.docker.com/) — containerisation
- Oracle Cloud — VPS hosting
