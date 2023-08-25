# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
        DEBCONF_NONINTERACTIVE_SEEN=true \
        LC_ALL=C.UTF-8 \
        LANG=C.UTF-8 \
        PIPENV_VENV_IN_PROJECT=1 \
        PYTHONUNBUFFERED=true

RUN apt-get -yqq update && apt-get install -yq \
        make \
        && \
        rm -rf /var/lib/apt/lists/* /var/cache/apt/*

RUN pip install pipenv

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . ./
# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
ENV PORT 8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 p6t:app
