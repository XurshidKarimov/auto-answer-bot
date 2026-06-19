# CI/CD деплой бота (Docker + GHCR + SSH) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Автоматический деплой Telegram-бота на собственный сервер с Docker при каждом push в `main` через GitHub Actions (тесты → сборка и пуш образа в GHCR → SSH-перезапуск на сервере).

**Architecture:** В репозиторий добавляются `Dockerfile`, `.dockerignore`, `docker-compose.yml` и workflow `.github/workflows/deploy.yml` с тремя джобами (test → build-push → deploy). Сервер хранит секреты в локальном `.env` и через `docker compose` поднимает контейнер из публичного образа GHCR. Код приложения не меняется.

**Tech Stack:** Docker, docker compose v2, GitHub Actions, GitHub Container Registry (ghcr.io), SSH.

## Global Constraints

- Имя образа (строго в нижнем регистре): `ghcr.io/xurshidkarimov/auto-answer-bot`.
- Теги при пуше: `:latest` и `:${{ github.sha }}`.
- Триггер деплоя: `push` в `main` (плюс `workflow_dispatch`).
- Деплой выполняется только после зелёных `test` и `build-push` (через `needs:`).
- Секреты бота (`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, …) живут ТОЛЬКО в `/opt/auto-answer-bot/.env` на сервере; в образ и в GitHub Actions они не попадают.
- На сервере путь деплоя: `/opt/auto-answer-bot`.
- `.env` не коммитится и не попадает в образ (уже в `.gitignore`; продублировать в `.dockerignore`).
- Базовый Python-образ: `python:3.12-slim`. Контейнер запускается под непривилегированным пользователем.
- GitHub Secrets для SSH: `SSH_HOST`, `SSH_USER`, `SSH_KEY`, `SSH_PORT` (опц.).

---

### Task 1: Dockerfile и .dockerignore

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

**Interfaces:**
- Consumes: существующие `requirements.txt`, `bot/`, `main.py`.
- Produces: образ, запускающий `python main.py`; используется в `docker-compose.yml` (Task 2) и собирается в CI (Task 3).

- [ ] **Step 1: Создать `Dockerfile`**

```dockerfile
FROM python:3.12-slim

# Не писать .pyc и не буферизовать stdout — логи видны сразу
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Зависимости отдельным слоём для кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY bot/ ./bot/
COPY main.py .

# Непривилегированный пользователь
RUN useradd --create-home --uid 1000 appuser
USER appuser

CMD ["python", "main.py"]
```

- [ ] **Step 2: Создать `.dockerignore`**

```
.git
.gitignore
.github/
.env
.env.example
docs/
tests/
.superpowers/
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/
README.md
```

- [ ] **Step 3: Проверить сборку образа**

Если локально доступен Docker:
Run: `docker build -t auto-answer-bot:test .`
Expected: сборка завершается `naming to docker.io/library/auto-answer-bot:test` / `FINISHED` без ошибок.

Если Docker локально НЕ установлен — пропустить и отметить в отчёте; сборка будет проверена джобом `build-push` в CI (Task 3). Не устанавливать Docker ради этого шага.

- [ ] **Step 4: (если Docker есть) Проверить, что образ стартует и читает конфиг**

Run: `docker run --rm -e TELEGRAM_BOT_TOKEN=x -e GEMINI_API_KEY=y auto-answer-bot:test python -c "import main; print('assembles')"`
Expected: вывод `assembles` (модуль импортируется внутри контейнера; polling не запускается, т.к. вызывается не `main()`).

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: Dockerfile и .dockerignore для контейнеризации бота"
```

---

### Task 2: docker-compose.yml

**Files:**
- Create: `docker-compose.yml`

**Interfaces:**
- Consumes: образ `ghcr.io/xurshidkarimov/auto-answer-bot:latest` (Task 1/Task 3); файл `.env` рядом на сервере.
- Produces: описание сервиса, которое scp-ится и запускается на сервере в Task 3.

- [ ] **Step 1: Создать `docker-compose.yml`**

```yaml
services:
  bot:
    image: ghcr.io/xurshidkarimov/auto-answer-bot:latest
    container_name: auto-answer-bot
    env_file: .env
    restart: unless-stopped
```

- [ ] **Step 2: Проверить синтаксис compose-файла**

Если локально доступен `docker compose`:
Run: `docker compose -f docker-compose.yml config`
Expected: печатает нормализованную конфигурацию без ошибок (предупреждение об отсутствии `.env` допустимо локально).

Если `docker compose` локально недоступен — проверить как валидный YAML:
Run: `python -m pip install pyyaml -q && python -c "import yaml; d=yaml.safe_load(open('docker-compose.yml')); assert d['services']['bot']['image'].startswith('ghcr.io/xurshidkarimov/auto-answer-bot'); assert d['services']['bot']['restart']=='unless-stopped'; print('compose yaml ok')"`
Expected: `compose yaml ok`

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: docker-compose для запуска бота на сервере"
```

---

### Task 3: GitHub Actions workflow (test → build-push → deploy)

**Files:**
- Create: `.github/workflows/deploy.yml`

**Interfaces:**
- Consumes: `Dockerfile` (Task 1), `docker-compose.yml` (Task 2), GitHub Secrets `SSH_HOST`/`SSH_USER`/`SSH_KEY`/`SSH_PORT`, встроенный `GITHUB_TOKEN`.
- Produces: автоматический pipeline сборки и деплоя.

- [ ] **Step 1: Создать `.github/workflows/deploy.yml`**

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python -m pytest -q

  build-push:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ghcr.io/xurshidkarimov/auto-answer-bot:latest
            ghcr.io/xurshidkarimov/auto-answer-bot:${{ github.sha }}

  deploy:
    needs: build-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Copy compose file to server
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          port: ${{ secrets.SSH_PORT }}
          source: docker-compose.yml
          target: /opt/auto-answer-bot
      - name: Pull and restart on server
        uses: appleboy/ssh-action@v1.2.0
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          port: ${{ secrets.SSH_PORT }}
          script: |
            cd /opt/auto-answer-bot
            docker compose pull
            docker compose up -d
            docker image prune -f
```

- [ ] **Step 2: Проверить, что workflow — валидный YAML и содержит нужные джобы**

Run: `python -m pip install pyyaml -q && python -c "import yaml; w=yaml.safe_load(open('.github/workflows/deploy.yml')); j=w['jobs']; assert set(['test','build-push','deploy']) <= set(j); assert j['build-push']['needs']=='test'; assert j['deploy']['needs']=='build-push'; assert j['build-push']['permissions']['packages']=='write'; print('workflow ok')"`
Expected: `workflow ok`

> Примечание: в YAML ключ `on:` может распарситься как булево `True`. Это нормально — проверяем `jobs`, а не `on`. GitHub Actions трактует `on` корректно.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: workflow деплоя (test → build-push в GHCR → SSH на сервер)"
```

---

### Task 4: Раздел «Деплой» в README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: имена секретов и путь сервера из Global Constraints.
- Produces: пошаговую инструкцию однократной настройки сервера и GitHub.

- [ ] **Step 1: Добавить в конец `README.md` раздел**

Добавить (в конец файла) ровно следующий блок:

```markdown
## Деплой (CI/CD)

Деплой автоматический: push в `main` → GitHub Actions прогоняет тесты,
собирает Docker-образ, пушит в `ghcr.io/xurshidkarimov/auto-answer-bot:latest`
и по SSH перезапускает контейнер на сервере.

### Однократная настройка

**1. GitHub Secrets** (Settings → Secrets and variables → Actions → New repository secret):

| Secret | Значение |
|---|---|
| `SSH_HOST` | IP или домен сервера |
| `SSH_USER` | пользователь SSH (в группе `docker`) |
| `SSH_KEY` | приватный SSH-ключ (публичный — в `~/.ssh/authorized_keys` на сервере) |
| `SSH_PORT` | порт SSH (опционально, по умолчанию 22) |

**2. На сервере** (по SSH):

```bash
sudo mkdir -p /opt/auto-answer-bot
sudo chown $USER:$USER /opt/auto-answer-bot
cat > /opt/auto-answer-bot/.env <<'EOF'
TELEGRAM_BOT_TOKEN=ваш-токен
GEMINI_API_KEY=ваш-ключ
GEMINI_MODEL=gemini-2.5-pro
SYSTEM_PROMPT=Ты — полезный универсальный ассистент. Отвечай кратко и по делу на языке пользователя.
MAX_HISTORY=20
EOF
chmod 600 /opt/auto-answer-bot/.env
```

**3. Сделать GHCR-пакет публичным** (после первого успешного `build-push`):
GitHub → профиль/репозиторий → Packages → `auto-answer-bot` → Package settings →
Change visibility → Public. Иначе сервер не скачает образ.

### Проверка

```bash
# на сервере
cd /opt/auto-answer-bot
docker compose ps          # контейнер auto-answer-bot в статусе Up
docker compose logs -f bot # строка «Бот запущен (polling)»
```
```

- [ ] **Step 2: Проверить, что раздел добавлен**

Run: `grep -c "Деплой (CI/CD)" README.md`
Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: инструкция по деплою в README"
```

---

## Manual Deploy & Verification (выполняет пользователь)

Эти шаги требуют доступа к серверу и GitHub — не автоматизируются в плане:

1. Добавить GitHub Secrets `SSH_HOST`, `SSH_USER`, `SSH_KEY` (и `SSH_PORT` при необходимости).
2. На сервере создать `/opt/auto-answer-bot/.env` (см. README) и сгенерировать пару SSH-ключей; публичный — в `authorized_keys`, приватный — в секрет `SSH_KEY`.
3. `git push origin main` → открыть вкладку **Actions**, дождаться зелёных `test` и `build-push`.
4. Сделать GHCR-пакет публичным (один раз).
5. Перезапустить workflow (`Re-run` или пустой commit), дождаться зелёного `deploy`.
6. На сервере: `docker compose ps` → `Up`; `docker compose logs -f bot` → «Бот запущен (polling)»; проверить ответ бота в Telegram.

---

## Self-Review

**Spec coverage:**
- Dockerfile (slim, non-root, CMD python main.py) → Task 1. ✓
- .dockerignore (исключения, .env) → Task 1. ✓
- docker-compose.yml (image, env_file, restart) → Task 2. ✓
- Workflow test → build-push → deploy с `needs` и `packages: write` → Task 3. ✓
- scp compose + SSH `docker compose pull && up -d && image prune` → Task 3. ✓
- Теги `:latest` и `:${{ github.sha }}` → Task 3. ✓
- GitHub Secrets и серверная настройка `.env`, публичный GHCR → Task 4 (README) + Manual. ✓
- Проверка результата (compose ps/logs, Telegram) → Task 4 README + Manual. ✓

**Placeholder scan:** плейсхолдеров нет; всё содержимое файлов приведено целиком.

**Type/имя-consistency:** имя образа `ghcr.io/xurshidkarimov/auto-answer-bot` идентично в Dockerfile-потоке, docker-compose.yml (Task 2), workflow тегах (Task 3) и README (Task 4). Путь `/opt/auto-answer-bot` одинаков в compose target, SSH-скрипте и README. Имена секретов `SSH_HOST/SSH_USER/SSH_KEY/SSH_PORT` совпадают между Task 3 и Task 4.
