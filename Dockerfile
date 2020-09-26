FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y upgrade

RUN ln -sf bash /bin/sh

RUN apt-get update && apt-get -y install apt-utils apt-transport-https ca-certificates curl software-properties-common locales curl wget git debianutils netcat-openbsd iputils-ping tzdata htop bsd-mailx

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
RUN update-locale LANG="en_US.UTF-8" LANGUAGE="en_US"
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV ACCEPT_EULA=Y

RUN apt-get update && apt-get install -y python3-pip zlib1g-dev libzip-dev libssl-dev libreadline-dev libsqlite3-dev libbz2-dev python3-minimal

RUN pip3 install --upgrade pip
RUN pip install pipenv

COPY Pipfile.lock Pipfile /app/
WORKDIR /app
RUN pipenv sync

COPY . /app

EXPOSE 8080

ENV PORT=8080

ENTRYPOINT make run-flask-prod


