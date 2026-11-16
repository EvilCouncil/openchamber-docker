# Stage 1: base OS packages (Node >= 24.14.0 required by @openchamber/web)
FROM node:24-slim AS base

ENV LANG=C.UTF-8

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        less \
        openssh-client \
        python3 \
        ripgrep \
        unzip && \
    rm -rf /var/lib/apt/lists/* && \
    usermod -l openchamber -d /home/openchamber -m node && \
    groupmod -n openchamber node

# Stage 2: Bun runtime (used by OpenChamber's bun-pty terminal backend)
FROM oven/bun:1.4-debian AS bun-stage

# Stage 3: install @openchamber/web + opencode v2 binary into /npm-global
FROM base AS npm-builder

ARG OPENCHAMBER_VERSION=2.7.2
ARG OPENCODE_VERSION=2.3.0

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    npm install -g --prefix /npm-global \
        @openchamber/web@${OPENCHAMBER_VERSION}

# OpenChamber's startup checkOpenCodeCLI() requires `opencode` on PATH even when
# OPENCODE_SKIP_START=true points it at an external `opencode serve` container.
RUN mkdir -p /npm-global/bin && \
    curl -fsSL "https://opencode.ai/files/bin/${OPENCODE_VERSION}/opencode-linux-x64.tar.gz" \
        -o /tmp/opencode.tar.gz && \
    tar -xzf /tmp/opencode.tar.gz -C /tmp && \
    mv /tmp/opencode /npm-global/bin/opencode && \
    chmod 755 /npm-global/bin/opencode && \
    rm -rf /tmp/opencode /tmp/opencode.tar.gz && \
    echo "opencode v${OPENCODE_VERSION} installed: $(/npm-global/bin/opencode --version)" && \
    test "$(/npm-global/bin/opencode --version)" = "opencode v${OPENCODE_VERSION}" && \
    echo "openchamber installed: $(/npm-global/bin/openchamber --version)"

# Stage 4: runtime image
FROM base

COPY --from=bun-stage /usr/local/bin/bun /usr/local/bin/bun
COPY --from=npm-builder /npm-global /npm-global
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

ENV PATH="/npm-global/bin:$PATH"
ENV NODE_ENV=production

RUN chmod 755 /usr/local/bin/docker-entrypoint.sh && \
    mkdir -p /home/openchamber/.config/openchamber \
             /home/openchamber/.config/opencode \
             /home/openchamber/.local/share/openchamber \
             /home/openchamber/.ssh \
             /workspace && \
    chown -R openchamber:openchamber /home/openchamber /workspace

USER openchamber
WORKDIR /workspace

EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
