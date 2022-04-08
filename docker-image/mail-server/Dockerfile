FROM mailserver/docker-mailserver:10.5.0

RUN useradd -m -s /bin/bash "catchall" \
    && echo "catchall:catchall" | chpasswd
