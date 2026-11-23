FROM python:3.15-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mapper.py .
COPY twitch.py .
COPY osctotwitch.py .

RUN useradd --uid 1000 --create-home app && mkdir /config
USER app

VOLUME /config
EXPOSE 1338/udp
ENTRYPOINT ["python", "osctotwitch.py"]
CMD ["--config", "/config/config.yaml"]
