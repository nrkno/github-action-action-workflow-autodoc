FROM python:3.13-alpine

RUN apk --no-cache add coreutils util-linux-misc git bash && pip3 install --no-cache-dir pyyaml configargparse

COPY autodoc.py /autodoc.py 
COPY entrypoint.sh /entrypoint.sh

WORKDIR /github/workspace/

ENTRYPOINT ["/entrypoint.sh"]