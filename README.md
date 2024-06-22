# xr_web
### 웹 서버 설정:

**최초 1회 Google SSO와 Nginx - Certbot SSL 적용이 필요합니다**
- 구글 SSO 설정 : https://support.google.com/a/answer/12032922?hl=ko
- Nginx SSL 설정(현 프로젝트는 webroot 방식 채택) : https://wonsss.github.io/deploy/https-webroot/

**위 설정 이후 아래 과정을 따라 서비스를 배포할 수 있습니다**

1. docker-compose.yml 파일을 작성합니다.
``````
services:
# 프록시 서버 설정
  proxy:
    depends_on:
      - nginx
      - fastapi
      - janus
    image: nginx:alpine
    container_name: proxyserver 
    restart: always 
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./proxyserver/nginx.conf:/etc/nginx/nginx.conf
      - ./certbot:/etc/letsencrypt
      - ./webpage/index.html:/usr/share/nginx/html/index.html

# 프론트엔드 서버 설정
  nginx:
    image: nginx:latest
    container_name: webpage
    restart: always
    volumes:
      - ./webpage:/usr/share/nginx/html

# 백엔드 서버 설정
  fastapi:
    build:
      context: ./fastapi
      dockerfile: Dockerfile
    restart: always
    container_name: api
    command: uvicorn main:app --host 0.0.0.0 --port 80
    environment:
      DATABASE_URL: {postgresql://[user]:[password]@db/[db name]}
      MINIO_ENDPOINT: {minio endpoint}
      MINIO_ACCESS_KEY: {minio access key}
      MINIO_SECRET_KEY: {minio secret key}
      MINIO_BUCKET: {minio bucket name}
      XR_WEB_SERVER_GOOGLE_CLIENT_ID: {Google SSO admin ID}
      XR_WEB_SERVER_GOOGLE_CLIENT_SECRET: {Google SSO admin password}
      XR_WEB_SERVER_GOOGLE_REDIRECT_URI: {Login redirection page (domain/auth)}
    depends_on:
      - db

# db 설정
  db:
    image: postgres:latest
    container_name: postgresdb
    volumes:
      - ./db:/docker-entrypoint-initdb.d
    restart: always
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: {db name}
      POSTGRES_USER: {db user}
      POSTGRES_PASSWORD: {db password}

# db 관리도구(Optional)
  pgadmin:
    container_name: pgadmin
    image: dpage/pgadmin4
    restart: unless-stopped
    ports:
      - "5555:80"
    # volumes:
    #   - ./pgadmin:/var/lib/pgadmin
    environment:
      - PGADMIN_DEFAULT_EMAIL={pgadmin ID}
      - PGADMIN_DEFAULT_PASSWORD={pgadmin password}
      - TZ=Asia/Seoul
    depends_on:
      - db

# 시그널링 서버
  janus:
      build:
        context: ./janus
        dockerfile: Dockerfile
      restart: always
      container_name: janus
      ports:
        - 7088:7088
        - 8088:8088
        - 8188:8188
        - 8989:8989
        - 10000-10030:10000-10030/udp

# SSL 관리 컨테이너
  certbot:
    depends_on:
      - proxy 
    image: certbot/certbot
    container_name: certbot
    volumes:
      - ../jsy/certbot:/etc/letsencrypt
      - ./webpage/index.html:/usr/share/nginx/html/index.html
    command: certonly --webroot --webroot-path=/usr/share/nginx/html --email {your email} --agree-tos --no-eff-email --keep-until-expiring -d {your domain}

# 사설 TURN 서버
  coturn:
    image: coturn/coturn:4.5.2
    container_name: coturnserver
    restart: always
    ports:
      - 3478:3478
      - 3478:3478/udp
      - 5349:5349
      - 5349:5349/udp
    volumes:
      - ./coturn/turnserver.conf:/etc/coturn/turnserver.conf
``````

2. 각 서버 Config 파일을 작성합니다.
- Proxyserver
```
user nginx;
worker_processes  auto;

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" "$request_uri" "$uri"'
                      '"$http_user_agent" "$http_x_forwarded_for"';    
    access_log  /var/log/nginx/access.log  main;
    sendfile on;
    keepalive_timeout 65;


    upstream webpage {
        server nginx:80;
    }

    upstream api {
        server fastapi:80;
    }

    upstream janus {
        server janus:8088;
    }

    upstream janus-ws {
        server janus:8188;
    }

    # upstream janus_admin {
    #     server janus:7088;
    # }

    server {
	listen 80;
	listen [::]:80;
	server_name {domain url};

        location ~ /.well-known/acme-challenge {
                allow all;
                root /usr/share/nginx/html;
        }

        location / {
        	return 301 https://$host$request_uri;
	}
    }
    
    server {
	listen 443 ssl;
	server_name {domain url};

        ssl_certificate /etc/letsencrypt/live/{domain url}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/{domain url}/privkey.pem;
        include /etc/letsencrypt/options-ssl-nginx.conf;
	ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;


        location /janus-ws {
            proxy_pass http://janus-ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # location /janus/ {
        #     proxy_pass http://janus;
        # }

        # location /admin/ {
        #     proxy_pass http://janus_admin;
        # }

        location /api/ {
            # rewrite ^/api(.*)$ $1 break;
            proxy_pass         http://api;
            proxy_redirect     off;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host $server_name;
            proxy_set_header   X-Forwarded-Proto $scheme;
        }

        location /static/ {
            # alias /api/static/;
            proxy_pass http://api;
        }

        location /socket.io/ {
            # alias /api/socket.io/;
            proxy_pass http://api; # Flask 애플리케이션으로의 실제 URL
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        location / {
            proxy_pass         http://webpage;
            proxy_redirect     off;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host $server_name;
            proxy_set_header   X-Forwarded-Proto $scheme;

            # proxy_http_version 1.1;
            # proxy_set_header Upgrade $http_upgrade;
            # proxy_set_header Connection "upgrade";

            # 캐시 비활성화
            proxy_cache off;
            proxy_cache_bypass $http_cache_control;
            proxy_no_cache $http_pragma $http_authorization;
        }
        
        # location /webmeeting/ {
        #     root /usr/share/nginx/html;
        #     index index.html index.htm;
        # }

        location /janus {
            proxy_pass http://janus;
            # proxy_http_version 1.1;
            # proxy_set_header Upgrade $http_upgrade;
            # proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```
- COTURN Server
```
# TURN server name and realm
realm=DOMAIN
server-name=turnserver

# Use fingerprint in TURN message
fingerprint

# IPs the TURN server listens to
listening-ip=0.0.0.0

# External IP-Address of the TURN server
external-ip={your ip}

# Main listening port
listening-port=3478

# Further ports that are open for communication
min-port=10000
max-port=20000

# Log file path
log-file=/var/log/turnserver.log

# Enable verbose logging
verbose

# Specify the user for the TURN authentification
user=test:test123

# Enable long-term credential mechanism
lt-cred-mech

# If running coturn version older than 4.5.2, uncomment these rules and ensure
# that you have listening-ip set to ipv4 addresses only.
# Prevent Loopback bypass https://github.com/coturn/coturn/security/advisories/GHSA-6g6j-r9rf-cm7p
#denied-peer-ip=0.0.0.0-0.255.255.255
#denied-peer-ip=127.0.0.0-127.255.255.255
#denied-peer-ip=::1
```

3. 작성된 코드 중 화상회의 관련 서버 url을 수정합니다.
- webpage/webmeeting/setting
```
var iceServers = null;
iceServers = [{urls: "turn:{your ip}:3478", username: {your turn id}, credential: {your turn password}}, {optional stun servers}, ...]
```

4. 프로젝트 최상위 폴더에서 다음 명령어로 container 구성을 완료합니다.
```
docker compsoe up -d
```
---
### 서비스 디버깅
FastAPI 관련 파일 수정 시 아래 명령어를 사용하여 직접 반영해줍니다.
```
docker compose up -d --no-deps --build fastapi
```

Proxy server 관련 설정 수정 시 아래 명령어를 사용하여 직접 반영해줍니다.
```
docker exec -it proxyserver nginx -s reload
```

---


이 프로젝트는 다음과 같은 오픈소스 라이브러리를 사용합니다:

- **FastAPI**: MIT License
- **NGINX**: BSD 2-Clause License
- **PostgreSQL**: PostgreSQL License
- **COTURN**: BSD 3-Clause License
- **Janus-Gateway**: GPLv3.0 License
- **jQuery**: MIT License
- **AdapterJS**: Apache 2.0 License
- **popperjs**: MIT License
- **Bootstrap**: MIT License
- **Bootbox**: MIT License
- **Toaster-JS**: MIT License