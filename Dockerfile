# runtime container
FROM python:3.12-slim

# create restricted, non-root user
RUN groupadd -r honeypot && useradd -r -g honeypot -d /app -s /sbin/nologin honeypot

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy source code into image
COPY honeypot/ ./honeypot/
RUN mkdir -p /app/logs && chown honeypot:honeypot /app/logs

# copy entrypoint code
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

# store logs in persistent volume (if not docker-compose)
VOLUME ["/app/logs"]

# permissions dropped to 'honeypot' in entrypoint.sh
EXPOSE 22
CMD ["./entrypoint.sh"]