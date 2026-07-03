FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install runtime deps straight from pyproject — no PEP 517 build of the
# local package. Building the local wheel in BuildKit's isolated env hangs
# at get_requires_for_build_wheel; this sidesteps it entirely and caches
# the dependency layer independent of code changes.
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    $(python -c "import tomllib; print(' '.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))")

COPY bot ./bot

USER 65532:65532
CMD ["python", "-m", "bot.main"]
