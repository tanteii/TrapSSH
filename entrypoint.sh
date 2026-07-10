#!/bin/sh

# fix volume permissions at startup then drop to honeypot user
chown -R honeypot:honeypot /app/logs
exec su -s /bin/sh -c "python3 -u honeypot/server.py" honeypot