FROM python:3.14-alpine@sha256:05b2b8b732ecd268fee8727a369f936f022d1321b59befd13c30ede22769dcdc

RUN apk --no-cache add coreutils util-linux-misc git bash

COPY autodoc.py /autodoc.py 
COPY entrypoint.sh /entrypoint.sh

WORKDIR /github/workspace/

ENTRYPOINT ["/entrypoint.sh"]