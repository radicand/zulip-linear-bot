FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY bot ./bot

RUN pip install --no-cache-dir .

USER 65532:65532

CMD ["zulip-linear-bot"]
