FROM python:3.14-alpine@sha256:26730869004e2b9c4b9ad09cab8625e81d256d1ce97e72df5520e806b1709f92

RUN apk --no-cache add coreutils util-linux-misc git bash && pip3 install --no-cache-dir pyyaml configargparse

COPY autodoc.py /autodoc.py 
COPY entrypoint.sh /entrypoint.sh

WORKDIR /github/workspace/

ENTRYPOINT ["/entrypoint.sh"]