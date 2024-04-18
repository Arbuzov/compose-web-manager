FROM debian:bullseye
LABEL org.opencontainers.image.authors="Serge Arbuzov <Serge.Arbuzov@spacebridge.com>"

ENV DEBIAN_FRONEND=noninteractive
ENV DEB_BUILD_OPTIONS=nocheck

RUN apt-get update \
    && apt-get install -y \
    ca-certificates \
    curl \
    debhelper \
    dh-python \
    dpkg-dev \
    fakeroot \
    git \
    gnupg \
    graphviz \
    libffi-dev \
    libssl-dev \
    libyaml-dev \
    libxml2-dev \
    libxslt1-dev \
    lintian \
    locales \
    pylint \
    python-all \
    python3 \
    python3-all \
    python3-all-dev \
    python3-click \
    python3-cryptography \
    python3-dev \
    python3-inflect \
    python3-lxml \
    python3-pip \
    python3-pytest-xdist \
    python3-decorator \
    sudo \
    wget \
    zlib1g \
    zlib1g-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

ENV LANG en_US.UTF-8 
ENV LANGUAGE en_US:en 
ENV LC_ALL en_US.UTF-8

RUN ln -sf /usr/bin/python3 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip \
    && pip3 config --global set global.index https://nexus.asatnet.net/repository/pypi \
    && pip3 config --global set global.index-url https://nexus.asatnet.net/repository/pypi/simple \
    && pip3 config --global set global.trusted-host nexus.asatnet.net \
    && pip3 install --ignore-installed \
    aiohttp \
    aiohttp_jinja2 \
    astroid==2.4.2 \
    anyio \
    cffi \
    clickclick \
    dictdiffer \
    flake8 \
    ujson \
    inflection \
    mock \
    pytest==6.1.2 \
    pylint==2.6.2\
    requests \
    testfixtures \
    inflection \
    jsonschema \
    stdeb3

