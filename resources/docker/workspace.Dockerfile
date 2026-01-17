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

# Configure Poetry: Create virtual environment in project directory (.venv)
# Set this both as environment variable and via poetry config
ENV POETRY_VENV_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip -q awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws

# Set permissions for Python cache and Poetry directories
RUN mkdir -p /tmp/poetry_cache /home/workspace/.cache/pypoetry && \
    chown -R workspace:workspace /tmp/poetry_cache /home/workspace/.cache

# Disable AWS CLI pager for non-interactive use
ENV AWS_PAGER=""

# Set working directory and ensure workspace user owns it
WORKDIR /workspace
RUN chown -R workspace:workspace /workspace

# Switch to non-root user
USER workspace

# Configure Poetry for workspace user: Create virtual environment in project directory (.venv)
RUN poetry config virtualenvs.in-project true

# Default command
CMD ["/bin/bash"]
