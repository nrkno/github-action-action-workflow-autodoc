FROM python:3.14-alpine@sha256:c6ead215bfd31f1e433d968853b7a769989117115b728874824e6c0a27cb96fc

RUN apk --no-cache add coreutils util-linux-misc git bash

COPY autodoc.py /autodoc.py 
COPY entrypoint.sh /entrypoint.sh

WORKDIR /github/workspace/

ENTRYPOINT ["/entrypoint.sh"]