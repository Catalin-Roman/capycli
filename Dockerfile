# SPDX-FileCopyrightText: (c) 2018-2025 Siemens
# SPDX-License-Identifier: MIT

FROM python:3.12-slim@sha256:31551bd80310d95ed82a4a14dba8c908c85098f07457e8a5b6a946385cfd86c8

ARG VERSION

ARG MY_PATH=/opt/capycli
ARG MY_VENV=${MY_PATH}/venv

RUN mkdir -p "${MY_PATH}"
RUN python -m venv --without-pip "${MY_VENV}"
ENV VIRTUAL_ENV=${MY_VENV}
ENV PATH=${VIRTUAL_ENV}/bin:${PATH}

COPY ./dist ${MY_PATH}/dist
RUN pip --python "${MY_VENV}" \
   install --no-cache-dir --no-input --progress-bar=off \
   --verbose --debug \
   --prefix "${MY_VENV}" --require-virtualenv \
   --compile \
   "capycli==${VERSION}" --find-links "file://${MY_PATH}/dist"
RUN rm -rf ${MY_PATH}/dist

# reset entrypoint
ENTRYPOINT []
