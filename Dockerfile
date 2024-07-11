FROM python:alpine

RUN mkdir -p /app
WORKDIR /app

RUN apk add --no-cache ffmpeg git

COPY ./pyproject.toml /app/pyproject.toml
RUN pip install -e /app/

COPY ./yt_dlp_plugins /app/yt_dlp_plugins
ENV PYTHONPATH=/app/
COPY ./setup.cfg /app/setup.cfg

CMD [ "/bin/ash", "-c", "while true; do echo 'running' && sleep 30; done;" ]