SHELL := /bin/bash
COMPOSE_FILE ?= docker-compose.prod.yml
ENV_FILE ?= .env
DC := docker compose -f $(COMPOSE_FILE)

# Параметры для htpasswd / backend-админки
ADMIN_USER ?= admin
ADMIN_PASS ?= admin

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Targets:"
	@echo "  up                - start (build if needed)"
	@echo "  down              - stop & remove"
	@echo "  pull              - pull images"
	@echo "  build             - build images (hybrid mode)"
	@echo "  deploy            - pull & up -d --remove-orphans"
	@echo "  ps                - show services"
	@echo "  logs              - tail all logs"
	@echo "  logs-web          - tail web logs"
	@echo "  logs-bot          - tail bot logs"
	@echo "  logs-nginx        - tail nginx logs"
	@echo "  logs-db           - tail db logs"
	@echo "  logs-cache        - tail redis logs"
	@echo "  restart S=svc     - restart service (S=web|bot|nginx|db|cache)"
	@echo "  bash-web          - shell into web"
	@echo "  bash-bot          - shell into bot"
	@echo "  nginx:test        - nginx -t inside container (container must be running)"
	@echo "  nginx:reload      - graceful reload of nginx"
	@echo "  health            - GET /healthz via nginx"
	@echo "  auth              - generate nginx/htpasswd with ADMIN_USER/PASS (nginx only)"
	@echo "  admin-sync        - sync admin creds: nginx/htpasswd + .env (backend)"
	@echo "  admin-show        - show current ADMIN_USER from .env"
	@echo "  admin-rotate      - generate random ADMIN_PASS and sync (prints new pass)"
	@echo "  prune             - prune dangling images"

## ---------- базовые операции docker compose ----------
.PHONY: up
up:
	$(DC) up -d

.PHONY: down
down:
	$(DC) down

.PHONY: pull
pull:
	$(DC) pull

.PHONY: build
build:
	$(DC) build

.PHONY: deploy
deploy: pull
	$(DC) up -d --remove-orphans

.PHONY: ps
ps:
	$(DC) ps

## ---------- логи ----------
.PHONY: logs
logs:
	$(DC) logs -f --tail=200

.PHONY: logs-web
logs-web:
	$(DC) logs -f --tail=200 web

.PHONY: logs-bot
logs-bot:
	$(DC) logs -f --tail=200 bot

.PHONY: logs-nginx
logs-nginx:
	$(DC) logs -f --tail=200 nginx

.PHONY: logs-db
logs-db:
	$(DC) logs -f --tail=200 db

.PHONY: logs-cache
logs-cache:
	$(DC) logs -f --tail=200 cache

## ---------- сервисные утилиты ----------
.PHONY: restart
restart:
	@if [ -z "$$S" ]; then echo "Usage: make restart S=web|bot|nginx|db|cache"; exit 1; fi
	$(DC) restart $$S

.PHONY: bash-web
bash-web:
	$(DC) exec web /bin/sh -lc 'env | sort; echo; exec /bin/sh'

.PHONY: bash-bot
bash-bot:
	$(DC) exec bot /bin/bash -lc 'env | sort; echo; exec /bin/bash'

.PHONY: nginx:test
nginx:test:
	$(DC) exec nginx nginx -t

.PHONY: nginx:reload
nginx:reload:
	$(DC) exec nginx nginx -s reload

.PHONY: health
health:
	@$(DC) exec nginx sh -lc 'wget -qO- http://127.0.0.1/healthz && echo' || (echo "healthz failed" && exit 1)

## ---------- BasicAuth для nginx ----------
# Генерация BasicAuth-файла без локальной установки htpasswd:
# Используем официальный httpd-образ, он содержит утилиту htpasswd.
.PHONY: auth
auth: ensure_nginx_dir
	@docker run --rm -i httpd:2.4-alpine \
		sh -lc 'htpasswd -Bbn "$(ADMIN_USER)" "$(ADMIN_PASS)"' \
		> nginx/htpasswd
	@echo "Generated nginx/htpasswd for user '$(ADMIN_USER)'"

## ---------- Двойной контур защиты: nginx + backend ----------
# admin-sync обновляет И nginx/htpasswd, И .env (ADMIN_USER/ADMIN_PASS).
.PHONY: admin-sync
admin-sync: ensure_nginx_dir
	@if [ -z "$$ADMIN_USER" ] || [ -z "$$ADMIN_PASS" ]; then \
		echo "Usage: make admin-sync ADMIN_USER=<user> ADMIN_PASS=<plain_password>"; \
		exit 1; \
	fi
	@# 1) htpasswd для nginx (bcrypt)
	@docker run --rm -i httpd:2.4-alpine \
		sh -lc 'htpasswd -Bbn "$$ADMIN_USER" "$$ADMIN_PASS"' \
		> nginx/htpasswd
	@echo "[ok] nginx/htpasswd updated for user '$$ADMIN_USER'"

	@# 2) .env: стереть старые строки и записать новые
	@if [ -f "$(ENV_FILE)" ]; then \
		sed -i '/^ADMIN_USER=/d' "$(ENV_FILE)"; \
		sed -i '/^ADMIN_PASS=/d' "$(ENV_FILE)"; \
	fi
	@echo "ADMIN_USER=$$ADMIN_USER" >> "$(ENV_FILE)"
	@echo "ADMIN_PASS=$$ADMIN_PASS" >> "$(ENV_FILE)"
	@echo "[ok] $(ENV_FILE) updated (ADMIN_USER/ADMIN_PASS)"
	@echo "[done] Admin credentials synced (nginx + backend)."
	@echo "       WARNING: $(ENV_FILE) хранит пароль в ОТКРЫТОМ виде — не коммить!"

# Печать текущего ADMIN_USER из .env (без пароля)
.PHONY: admin-show
admin-show:
	@if [ -f "$(ENV_FILE)" ]; then \
		awk -F'=' '/^ADMIN_USER=/{print $$2}' "$(ENV_FILE)"; \
	else \
		echo "no $(ENV_FILE)"; \
	fi

# Сгенерировать случайный пароль, вывести его и синхронизировать.
.PHONY: admin-rotate
admin-rotate:
	@PASS="$$(head -c 64 /dev/urandom | tr -dc 'A-Za-z0-9!@#%^_+=' | head -c 24)"; \
	$(MAKE) admin-sync ADMIN_USER="$(ADMIN_USER)" ADMIN_PASS="$$PASS"; \
	echo; echo "New ADMIN creds:"; \
	echo "  user: $(ADMIN_USER)"; \
	echo "  pass: $$PASS"; \
	echo; echo "IMPORTANT: пароль показан один раз. Сохрани его."

## ---------- Прочее ----------
.PHONY: prune
prune:
	docker image prune -f

.PHONY: ensure_nginx_dir
ensure_nginx_dir:
	@mkdir -p nginx

## ---------- Dev контейнер ----------
.PHONY: dev-up
dev-up:
	docker compose -f docker-compose.dev.yml up -d db redis
	docker compose -f docker-compose.dev.yml up --build app

.PHONY: dev-down
dev-down:
	docker compose -f docker-compose.dev.yml down -v

.PHONY: dev-lint
dev-lint:
	docker compose -f docker-compose.dev.yml run --rm app uvx ruff check .

.PHONY: dev-type
dev-type:
	docker compose -f docker-compose.dev.yml run --rm app uvx mypy .

.PHONY: dev-test
dev-test:
	docker compose -f docker-compose.dev.yml run --rm app uvx pytest -q

.PHONY: dev-fmt
dev-fmt:
	docker compose -f docker-compose.dev.yml run --rm app uvx black .


.PHONY: alembic-up
alembic-up:
	alembic upgrade head

.PHONY: alembic-down
alembic-down:
	alembic downgrade -1
