FROM node:20-bookworm-slim

# Install system dependencies (Node + Python + PostgreSQL client)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    sudo \
    ca-certificates \
    ripgrep \
    jq \
    unzip \
    iptables \
    dnsutils \
    procps \
    htop \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Make python available as 'python'
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Allow pip to install packages system-wide (PEP 668) for all users
RUN python3 -m pip config --global set global.break-system-packages true

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code

# Set up non-root user with sudo
ARG USERNAME=node
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupmod --gid $USER_GID $USERNAME 2>/dev/null || true \
    && usermod --uid $USER_UID --gid $USER_GID $USERNAME 2>/dev/null || true \
    && chown -R $USER_UID:$USER_GID /home/$USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Persist shell history across container rebuilds
RUN mkdir -p /home/$USERNAME/.bash_history_dir \
    && chown -R $USERNAME /home/$USERNAME/.bash_history_dir

# Create .claude config directory
RUN mkdir -p /home/$USERNAME/.claude \
    && chown -R $USERNAME /home/$USERNAME/.claude

RUN mkdir -p /home/node/.cache/pip && chown -R node:node /home/node/.cache
RUN mkdir -p /home/node/.config/gh && chown -R node:node /home/node/.config

USER $USERNAME
ENV PATH="/home/node/.local/bin:$PATH"
WORKDIR /workspace

# Shell history config
RUN echo 'export HISTFILE=/home/node/.bash_history_dir/.bash_history' >> ~/.bashrc \
    && echo 'export PROMPT_COMMAND="history -a"' >> ~/.bashrc
