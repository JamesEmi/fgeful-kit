FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config ffmpeg libcairo2-dev libpango1.0-dev \
    texlive-latex-base texlive-latex-extra texlive-fonts-recommended dvisvgm \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/fgeful-kit
COPY . .
RUN python -m pip install '.[all]' -c constraints-tested.txt && python -m playwright install --with-deps chromium
WORKDIR /work
ENTRYPOINT ["fgeful-kit"]
