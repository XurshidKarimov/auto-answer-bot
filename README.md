# auto-answer-bot

Telegram-бот, обрабатывающий сообщения через Google Gemini Pro.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # заполнить TELEGRAM_BOT_TOKEN и GEMINI_API_KEY
```

## Запуск

```bash
python main.py
```

## Тесты

```bash
pytest -v
```

## Поведение

Бот — автоответчик. Каждое входящее сообщение классифицирует Gemini:

- **Пятничное поздравление** («Juma muborak»/«Жума муборак» и варианты) → бот отправляет фиксированный готовый ответ
- **Любое другое поздравление** → Gemini пишет короткое взаимное поздравление (с подписью автоответчика)
- **Все остальные сообщения** (вопросы, просьбы, болтовня и т.п.) → бот молчит и ничего не пишет

### Команды бота

- `/start` — приветствие
- `/reset` — очистить историю диалога

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

> Примечание: при самом первом push пакет ещё приватный, поэтому джоб `deploy`
> может упасть на `docker compose pull`. Это ожидаемо — сделай пакет публичным
> (шаг 3) и перезапусти workflow (`Re-run jobs` или вкладка Actions →
> `Run workflow`). Последующие деплои пройдут автоматически.

### Проверка

```bash
# на сервере
cd /opt/auto-answer-bot
docker compose ps          # контейнер auto-answer-bot в статусе Up
docker compose logs -f bot # строка «Бот запущен (polling)»
```
