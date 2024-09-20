# Используем официальный образ Python
FROM python:3.12

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Выполняем миграции и собираем статические файлы
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

# Указываем команду для запуска Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "src.wsgi:application"]