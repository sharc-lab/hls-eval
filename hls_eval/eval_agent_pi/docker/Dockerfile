FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Bootstrap certificates, then use HTTPS for the larger package downloads.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    sed -i 's|http://|https://|g' /etc/apt/sources.list

# install git, curl, clang, tree, make, cmake
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    clang \
    tree \
    make \
    cmake \
    build-essential \
    xz-utils \
    ca-certificates \
    time \
    gawk \
    coreutils \
    findutils \
    grep \
    sed \
    linux-tools-generic \
    linux-tools-common \
    ripgrep \
    jq \
    less \
    nano \
    vim \
    diffutils \
    patch \
    unzip \
    bsdmainutils \
    moreutils \
    psmisc \
    tzdata \
    util-linux \
    file \
    csvkit \
    parallel \
    mc \
    htop \
    lsof \
    xmlstarlet \
    sqlite3 \
    bzip2 \
    zip \
    zstd \
    poppler-utils \
    dos2unix \
    ssmtp \
    whois \
    nmap \
    net-tools \
    iputils-ping \
    at \
    && rm -rf /var/lib/apt/lists/*

RUN if command -v clang >/dev/null 2>&1 && command -v clang++ >/dev/null 2>&1; then \
    echo "Found clang and clang++, setting as default compilers"; \
    clang --version; \
    clang++ --version; \
    else \
    echo "ERROR: clang and/or clang++ not found!"; \
    exit 1; \
    fi

ENV CC=clang
ENV CXX=clang++

### Setup for Node, npm, and pi-coding-agent ###

ENV NODE_VERSION=24.15.0

RUN curl -fsSL https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.xz \
    | tar -xJ -C /usr/local --strip-components=1

RUN npm install -g @mariozechner/pi-coding-agent

# Runtime support for host-mounted Vitis; no vendor installation in the image.
RUN sed -i 's|http://|https://|g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends locales libtinfo5 && \
    localedef -i en_US -f UTF-8 en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
COPY --chmod=755 with-vitis /usr/local/bin/with-vitis

# Install uv and uvx on the agent's PATH, including in docker exec sessions.
RUN bash -o pipefail -c \
    'curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh' && \
    uv --version && uvx --version

# Install Pixi system-wide using its official installer.
RUN bash -o pipefail -c \
    'curl -fsSL https://pixi.sh/install.sh | env PIXI_BIN_DIR=/usr/local/bin PIXI_NO_PATH_UPDATE=1 sh' && \
    pixi --version

RUN mkdir -p /workspace
WORKDIR /workspace
