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
