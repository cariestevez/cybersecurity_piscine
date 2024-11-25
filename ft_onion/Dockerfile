FROM debian:bullseye

RUN apt-get update && \
    apt-get install -y \
    netstat-nat \
    nginx \
    curl \
    gpg \
    vim \
    tor \
    supervisor \
    openssh-server && \
    mkdir -p /var/lib/tor/hidden_service/ && \
    chmod 700 /var/lib/tor/hidden_service/ && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY supervisord.conf /etc/supervisor/supervisord.conf
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./index.html /var/www/html/index.html
COPY ./torrc /etc/tor/torrc
COPY ./sshd_config /etc/ssh/sshd_config
COPY onion_keys.pub /root/.ssh/authorized_keys
COPY ./init_script.sh /usr/local/bin/init_script.sh

RUN chmod 600 /root/.ssh/authorized_keys && \
    chmod 700 /root/.ssh && \
    chmod +x /usr/local/bin/init_script.sh

ENTRYPOINT ["/usr/local/bin/init_script.sh"]
