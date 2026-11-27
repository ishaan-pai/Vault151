# python-oracledb runs in thin mode, so no Oracle Instant Client is needed and the
# slim image is enough.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/srv/.venv/bin:$PATH"

# Unpinned deliberately, and only until `uv --version` is confirmed locally so that
# the image and the development machine agree. See DECISIONS.md 3.13.
RUN pip install --no-cache-dir uv

WORKDIR /srv

# Dependencies first: this layer is rebuilt only when the manifests change.
# uv.lock must exist - run `uv sync` once on the host before building.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

# Drop privileges: nothing here needs root at runtime.
#
# /srv/media is created here on purpose. A named volume mounted over a path that does
# not exist in the image is created root-owned, and the non-root process below could
# not then write uploads into it.
RUN useradd --create-home --shell /usr/sbin/nologin cardshop \
    && mkdir -p /srv/media \
    && chown -R cardshop:cardshop /srv
USER cardshop

EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
