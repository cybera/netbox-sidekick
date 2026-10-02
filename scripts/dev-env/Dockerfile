# Runtime test environment for netbox-sidekick.
#
# Builds NetBox at the version the plugin targets (see NETBOX_VERSION below and
# the max_version pin in sidekick/__init__.py), installs this checkout as an
# editable plugin, and points NetBox at throwaway Postgres/Redis containers.
#
# Use scripts/dev-env/run-tests.sh, which wires up the database containers.
#
#   docker build -f scripts/dev-env/Dockerfile -t sidekick-test .
#
# There is no NetBox/Django environment on the bastion host, so this is the
# only way to execute the test suite; CI should use the same recipe.
#
# Layer order matters for iteration speed: requirements.txt is copied and
# installed BEFORE the rest of the checkout, so editing plugin code does not
# re-install the (large) sidekick dependency tree. pip uses a BuildKit cache
# mount, so even a cold layer rebuild does not re-download wheels.

FROM python:3.12-bookworm

ARG NETBOX_VERSION=v4.7.0

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# librrd is needed by the rrdtool/whisper dependencies in requirements.txt.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        librrd-dev \
        build-essential \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
        libffi-dev \
        libssl-dev \
        zlib1g-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
    git clone --depth 1 --branch "${NETBOX_VERSION}" \
        https://github.com/netbox-community/netbox /opt/netbox \
    && pip install -r /opt/netbox/requirements.txt

# The plugin. Its setup.py has an empty install_requires, so requirements.txt
# has to be installed separately -- first, on its own layer, keyed only on
# requirements.txt so code changes do not invalidate it.
COPY requirements.txt /opt/sidekick/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /opt/sidekick/requirements.txt

COPY . /opt/sidekick
RUN pip install -e /opt/sidekick

COPY scripts/dev-env/configuration.py /opt/netbox/netbox/netbox/configuration.py

WORKDIR /opt/netbox/netbox
