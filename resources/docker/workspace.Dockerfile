FROM python:3.12-slim

# Install build dependencies and development tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    make \
    bash \
    curl \
    ca-certificates \
    unzip \
    less \
    build-essential \
    postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user first (needed for Poetry installation)
RUN groupadd -g 1000 workspace && \
    useradd -u 1000 -g workspace -m -s /bin/bash workspace

# Install Poetry system-wide (pinned to version 2.2.1)
RUN pip install --no-cache-dir poetry==2.2.1

# Install Poetry export plugin
RUN poetry self add poetry-plugin-export

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip -q awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws

ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    VIRTUAL_ENV=/home/workspace/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set permissions for Python cache, Poetry, and venv directories
RUN mkdir -p /tmp/poetry_cache /home/workspace/.cache/pypoetry "$VIRTUAL_ENV" && \
    chown -R workspace:workspace /tmp/poetry_cache /home/workspace/.cache "$VIRTUAL_ENV"

# Disable AWS CLI pager for non-interactive use
ENV AWS_PAGER=""

# Set working directory and ensure workspace user owns it
WORKDIR /workspace
RUN chown -R workspace:workspace /workspace

# Switch to non-root user
USER workspace

RUN python -m venv "$VIRTUAL_ENV"

# Default command
CMD ["/bin/bash"]
