FROM python:3.8-slim as base

ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONHASHSEED random
ENV DEBIAN_FRONTEND noninteractive

RUN pip install --upgrade pip

WORKDIR /app

FROM base as builder

# install and setup poetry
RUN apt update \
    && apt install -y curl \
    && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
ENV PATH=${PATH}:/root/.local/bin

# package & distribution
COPY src/ src/
COPY pyproject.toml poetry.lock ./
COPY README.rst .env* ./
RUN python -m venv /venv
RUN . /venv/bin/activate && poetry install --no-interaction --no-dev --no-root
RUN . /venv/bin/activate && poetry build

FROM base

# install system dependencies
RUN apt update \
    # identity discovery modules
    && apt install -y libsasl2-dev libldap2-dev libssl-dev \
    && apt install -y libnss-ldapd libpam-ldapd ldap-utils

# system configurations
COPY etc/nslcd.conf /etc/
COPY etc/nsswitch.conf /etc/
RUN chmod 0700 /etc/nslcd.conf
RUN chmod 0755 /etc/nsswitch.conf

# create system user
ENV USER filesystem-api
RUN useradd --system -u 1000 $USER

COPY src/ src/
COPY bootstrap .
COPY --from=builder /app/dist .
RUN pip install *.whl

RUN chown -R 1000:1000 .
RUN chmod -R 0500 .

# run process as non root
USER 1000:1000

# command to run on container start
ARG env="production"
ENV ENV $env
CMD ./bootstrap && gunicorn --bind 0.0.0.0:5000 "src.app:create_app('${ENV}')"
