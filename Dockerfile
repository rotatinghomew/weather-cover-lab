FROM python:3.11-slim-bookworm@sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app
RUN python -m pip install --no-index --find-links=/app/vendor/wheels -r /app/requirements.lock
CMD ["python", "-m", "weather_cover", "demo"]
