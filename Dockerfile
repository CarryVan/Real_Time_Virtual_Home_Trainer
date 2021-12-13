FROM python:3.8

WORKDIR /app

RUN apt-get update
RUN apt install linbnss3-tools
RUN brew install mkcert
RUN mkcert -install
RUN mkcert localhost 127.0.0.1 ::1