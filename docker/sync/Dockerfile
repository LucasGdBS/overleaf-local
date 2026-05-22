FROM python:3.12-alpine

RUN pip install --no-cache-dir requests

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /repo

ENTRYPOINT ["/entrypoint.sh"]
