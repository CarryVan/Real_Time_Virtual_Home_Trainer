"# Real-Time Virtual Home Trainer Dev" 

## Dev 세팅

docker 로 https 서버 세팅

```bash
docker-compose up -d
```
서버 중지

```bash
docker-compose stop
```

서버 시작

```bash
docker-compose start
```

## 접속 IP 주소 

로컬 80번 포트와 docker 80번 포트가 바인딩 되어있음

-> https://127.0.0.1:80 

-> https://{IPv4 Address}:80