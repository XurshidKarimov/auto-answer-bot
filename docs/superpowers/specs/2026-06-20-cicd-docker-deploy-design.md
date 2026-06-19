# CI/CD деплой бота (Docker + GHCR + SSH) — дизайн

Дата: 2026-06-20

## Цель

Автоматический деплой Telegram-бота на собственный сервер с Docker при каждом
push в ветку `main`. Бот работает в режиме polling внутри контейнера и
автоматически перезапускается после падения или перезагрузки сервера.

## Поток (data flow)

```
git push → main
   │
   ▼  GitHub Actions (.github/workflows/deploy.yml)
   ├─ job: test       — python -m pytest (gate)
   ├─ job: build-push — docker build → push ghcr.io/xurshidkarimov/auto-answer-bot:latest
   └─ job: deploy     — scp docker-compose.yml → SSH: docker compose pull && up -d
                          │
                          ▼  Сервер
                     контейнер bot (image :latest, env_file .env, restart unless-stopped)
                          │
                          ▼
                     Telegram (polling)
```

Деплой выполняется только если `test` и `build-push` прошли успешно.

## Компоненты (новые файлы в репозитории)

### Dockerfile
- База: `python:3.12-slim`.
- Устанавливает зависимости из `requirements.txt` (отдельным слоем для кэша).
- Копирует только `bot/` и `main.py`.
- Запуск под непривилегированным пользователем (не root).
- `CMD ["python", "main.py"]`.

### .dockerignore
Исключает из контекста сборки: `.git`, `.env`, `docs/`, `tests/`,
`.superpowers/`, `__pycache__/`, `*.pyc`, `.venv/`, `venv/`.

### docker-compose.yml
- Сервис `bot`:
  - `image: ghcr.io/xurshidkarimov/auto-answer-bot:latest`
  - `env_file: .env` (файл лежит рядом на сервере, в репозиторий не коммитится)
  - `restart: unless-stopped`

### .github/workflows/deploy.yml
Триггер: `push` в `main` (и `workflow_dispatch` для ручного запуска).
Джобы:
1. **test** — `actions/checkout`, `actions/setup-python@v5` (3.12),
   `pip install -r requirements.txt`, `python -m pytest -q`.
2. **build-push** (`needs: test`) — `docker/login-action` в `ghcr.io`
   (через `GITHUB_TOKEN`, права `packages: write`), `docker/build-push-action`
   с тегами `:latest` и `:${{ github.sha }}`.
3. **deploy** (`needs: build-push`) — `appleboy/scp-action` копирует
   `docker-compose.yml` в `/opt/auto-answer-bot/`, затем `appleboy/ssh-action`
   выполняет: `cd /opt/auto-answer-bot && docker compose pull && docker compose up -d && docker image prune -f`.

## Конфигурация и секреты

**GitHub Secrets (Settings → Secrets and variables → Actions):**
- `SSH_HOST` — IP или домен сервера.
- `SSH_USER` — пользователь SSH (член группы `docker`).
- `SSH_KEY` — приватный SSH-ключ; соответствующий публичный ключ добавлен в
  `~/.ssh/authorized_keys` на сервере.
- `SSH_PORT` — опционально, по умолчанию 22.

> Ранее добавленные `TELEGRAM_BOT_TOKEN` и `GEMINI_API_KEY` в этой схеме НЕ
> используются — секреты бота живут только в `.env` на сервере.

**На сервере (однократно):**
```bash
sudo mkdir -p /opt/auto-answer-bot
# создать /opt/auto-answer-bot/.env:
#   TELEGRAM_BOT_TOKEN=...
#   GEMINI_API_KEY=...
#   GEMINI_MODEL=gemini-2.5-pro
#   SYSTEM_PROMPT=...
#   MAX_HISTORY=20
chmod 600 /opt/auto-answer-bot/.env
```

**В GitHub (после первого пуша образа):** сделать GHCR-пакет публичным
(Packages → package settings → Change visibility → Public), чтобы сервер
скачивал образ без авторизации.

## Предпосылки на сервере

- Установлен Docker и плагин `docker compose` v2 (`docker compose version`
  отвечает — подтверждено).
- SSH-пользователь может выполнять `docker` без sudo (группа `docker`).

## Обработка ошибок и устойчивость

- `restart: unless-stopped` — контейнер поднимается после падения и
  ребута сервера.
- Деплой защищён гейтом тестов: красные тесты → нет сборки и деплоя.
- Тег `:${{ github.sha }}` помимо `:latest` — возможность отката на
  конкретную версию (`docker compose` с временной правкой тега).
- `docker image prune -f` после деплоя чистит старые слои.

## Проверка результата

1. Push в `main` → workflow в Actions зелёный (все три джоба).
2. На сервере: `docker compose ps` показывает `bot` в статусе `Up`.
3. `docker compose logs -f bot` содержит «Бот запущен (polling)».
4. Бот отвечает в Telegram; пятничное поздравление → фиксированный ответ.

## Вне области (YAGNI)

- Приватный GHCR-образ с server-side `docker login` (выбран публичный).
- Self-hosted runner.
- Оркестрация (k8s), несколько реплик — для одного polling-бота не нужно
  (и Telegram polling не допускает несколько одновременных инстансов).
- Healthcheck/мониторинг — можно добавить позже.
