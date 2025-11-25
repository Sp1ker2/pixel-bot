# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости для PIL и шрифтов
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY pixel_bot.py .

# Устанавливаем переменную окружения для Python
ENV PYTHONUNBUFFERED=1

# Запускаем бота (используем exec form для правильной обработки сигналов)
ENTRYPOINT ["python", "-u", "pixel_bot.py"]
