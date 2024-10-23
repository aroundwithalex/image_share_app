FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Install UV so we can install from the lock file
ADD https://astral.sh/uv/0.4.24/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.cargo/bin:$PATH"

# Copy directory into container
COPY . ./image_share

WORKDIR /image_share

# Install requirements from lockfile
RUN uv sync

# Start the server
CMD ["uv", "run", "fastapi", "run", "app.py"]
