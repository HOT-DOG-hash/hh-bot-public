# простая HTTP-конфигурация; после релиза повесь TLS-терминатор!
server {
    listen 80;
    server_name ${SERVER_NAME:-_};

    # статика админки (без FastAPI)
    location / {
        root /usr/share/nginx/html;  # adminka/ будет смонтирована сюда
        try_files $uri /index.html;
    }

    # защищаем /admin/* на уровне Nginx
    location /admin/ {
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;

        root /usr/share/nginx/html;
        try_files $uri /admin/index.html;
    }

    # API → FastAPI
    location /api/ {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }
}
