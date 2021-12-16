FROM python:3.8

WORKDIR /app

RUN apt update
RUN apt install libgl1-mesa-glx -y
RUN apt install libnss3-tools -y
RUN wget -O mkcert https://github.com/FiloSottile/mkcert/releases/download/v1.4.3/mkcert-v1.4.3-linux-amd64
RUN chmod +x mkcert
RUN cp mkcert /usr/local/bin/
RUN mkcert -install
RUN mkcert -key-file ../key.pem -cert-file ../cert.pem localhost 127.0.0.1 ::1

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . .

# CMD uvicorn server:app --host 0.0.0.0 --port 80
CMD uvicorn server:app --host 0.0.0.0 --port 80 --ssl-keyfile ../key.pem --ssl-certfile ../cert.pem --reload