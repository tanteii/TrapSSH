# runtime container
FROM python:3.12-slim

# create restricted, non-root user
RUN groupadd -r honeypot && useradd -r -g honeypot -d /app -s /sbin/nologin honeypot

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY honeypot/ ./honeypot/
RUN mkdir -p /app/logs && chown honeypot:honeypot /app/logs

# store logs externally
VOLUME ["/app/logs"]

USER honeypot
EXPOSE 2222
CMD ["python3", "-u", "honeypot/server.py"]