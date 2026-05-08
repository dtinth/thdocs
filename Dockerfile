FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq && apt-get install -y -qq \
    texlive-xetex \
    latexmk \
    make \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ARG THDOCS_REF=main
RUN uv tool install git+https://github.com/dtinth/thdocs.git@${THDOCS_REF}

ENV PATH="/root/.local/bin:${PATH}"

ENTRYPOINT ["thdocs"]
