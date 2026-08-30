# syntax=docker/dockerfile:1.7
FROM node:22-bookworm-slim AS node

FROM python:3.14-slim-bookworm AS base

ARG BLENDER_VERSION=4.5.13
ARG BLENDER_SHA256=da4e69b06b75b9e642d106496c50e7e240218b411d2f6e18271c1d1d819cef91

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    BLENDER_EXECUTABLE=/opt/blender/blender

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl xz-utils \
    libdbus-1-3 libegl1 libfontconfig1 libfreetype6 libgl1 libglib2.0-0 \
    libice6 libsm6 libx11-6 libxext6 libxfixes3 libxi6 libxkbcommon0 \
    libxrender1 libxxf86vm1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /usr/local/bin/
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

RUN curl -fsSL "https://download.blender.org/release/Blender4.5/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    -o /tmp/blender.tar.xz \
    && echo "${BLENDER_SHA256}  /tmp/blender.tar.xz" | sha256sum -c - \
    && mkdir -p /opt/blender \
    && tar -xJf /tmp/blender.tar.xz --strip-components=1 -C /opt/blender \
    && rm /tmp/blender.tar.xz \
    && /opt/blender/blender --version

WORKDIR /app
COPY pyproject.toml uv.lock package.json package-lock.json ./
RUN uv sync --frozen --no-dev --no-install-project && npm ci
COPY . .
RUN uv sync --frozen --no-dev && npm run build

FROM base AS production
ENV RIGNOSTIC_HOST=0.0.0.0 RIGNOSTIC_DEBUG=0
EXPOSE 5000
CMD ["uv", "run", "--frozen", "--no-dev", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "180", "rignostic.web:create_app()"]

FROM base AS development
RUN uv sync --frozen --dev
ENV RIGNOSTIC_HOST=0.0.0.0 RIGNOSTIC_DEBUG=1
EXPOSE 5000
CMD ["bash", "scripts/docker-dev.sh"]
