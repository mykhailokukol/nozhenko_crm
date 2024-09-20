# Используем официальный образ Python
FROM python:3.12

# Устанавливаем необходимые пакеты
RUN apt-get update 
RUN apt-get install -y locales 
RUN locale-gen ru_RU.UTF-8
RUN update-locale LANG=ru_RU.UTF-8

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Устанавливаем локаль по умолчанию
ENV LANG=ru_RU.UTF-8
ENV LANGUAGE=ru_RU:ru
ENV LC_ALL=ru_RU.UTF-8

# Выполняем миграции и собираем статические файлы
RUN python src/manage.py migrate
RUN python src/manage.py collectstatic --noinput

# Указываем команду для запуска Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "src.wsgi:application"]