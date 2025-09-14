# SPDX-FileCopyrightText: (c) 2018-2025 Siemens
# SPDX-License-Identifier: MIT

FROM python:3.12-slim@sha256:abc799c7ee22b0d66f46c367643088a35e048bbabd81212d73c2323aed38c64f

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
