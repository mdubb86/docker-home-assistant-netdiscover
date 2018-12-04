FROM ubuntu:xenial

RUN apt-get update && apt-get install -y \
  python3 \
  python3-pip \
  netdiscover && \
  pip3 install requests 

# Set the entry point
ENTRYPOINT ["/init"]

# Install services
COPY services /etc/services.d

# Install init.sh as init script
COPY init.sh /etc/cont-init.d/

# Install nginx sites
COPY netdiscover.py /

# Download and extract s6 init
ADD https://github.com/just-containers/s6-overlay/releases/download/v1.19.1.1/s6-overlay-amd64.tar.gz /tmp/
RUN tar xzf /tmp/s6-overlay-amd64.tar.gz -C /

