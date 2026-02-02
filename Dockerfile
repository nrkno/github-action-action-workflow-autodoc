FROM python:3.14-alpine@sha256:31da4cb527055e4e3d7e9e006dffe9329f84ebea79eaca0a1f1c27ce61e40ca5

RUN apk --no-cache add coreutils util-linux-misc git bash && pip3 install --no-cache-dir pyyaml configargparse

COPY autodoc.py /autodoc.py 
COPY entrypoint.sh /entrypoint.sh

WORKDIR /github/workspace/

ENTRYPOINT ["/entrypoint.sh"]