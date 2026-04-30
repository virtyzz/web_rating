# YW Web Rating

Веб-приложение для загрузки 4 скриншотов таблиц серверов выбранного кластера, распознавания их через Gemini API и сохранения результатов в PostgreSQL с последующим отображением отдельных и сводной таблиц.

## Возможности

- Выбор кластера 1 или 2.
- Обязательная загрузка всех 4 скриншотов выбранного кластера.
- Проверка MIME-типа файлов на стороне клиента и сервера.
- Распознавание таблиц через `gemini-2.5-flash`.
- Повторный запрос к Gemini с уточненным промптом, если первый ответ некорректен.
- Автоматические повторы запросов к Gemini только для временных ошибок `429` и `503`.
- Логирование причин ошибок Gemini в серверные логи контейнера `app`.
- Полная замена старых данных кластера новыми после успешной обработки всех 4 серверов.
- Отдельные таблицы по серверам и сводная таблица по кластеру.
- Запуск через Docker Compose: `app`, `db`, `pgadmin`.

## Структура

```text
.
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── docker-compose.yml
├── requirements.txt
└── app
    ├── __init__.py
    ├── config.py
    ├── constants.py
    ├── database.py
    ├── main.py
    ├── models.py
    ├── schemas.py
    ├── services
    │   ├── __init__.py
    │   ├── gemini.py
    │   └── storage.py
    └── static
        ├── app.js
        ├── index.html
        └── styles.css
```

## Переменные окружения

1. Создайте файл `.env` на основе `.env.example`.
2. Укажите действующий ключ Gemini API:

```env
GEMINI_API_KEY=your_real_key
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=postgresql+psycopg://ranks_user:ranks_password@db:5432/ranks
POSTGRES_USER=ranks_user
POSTGRES_PASSWORD=ranks_password
POSTGRES_DB=ranks
```

## Запуск

```bash
docker-compose up --build
```

После запуска:

- Приложение: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- pgAdmin: `http://localhost:5050`
  - Email: `admin@example.com`
  - Password: `admin`

## API

- `POST /upload/{cluster}`: multipart-форма с 4 файлами `files` и 4 значениями `server_names`.
- `GET /servers/{cluster}`: данные по серверам кластера.
- `GET /summary/{cluster}`: сводка по кластеру. Вернет `409`, если загружены не все 4 сервера.

## Примечание по Gemini API

Приложение использует официальный Python SDK `google-genai` и передает изображение inline-байтами. Для структурированного ответа используется JSON-режим со схемой Pydantic, а при ошибке валидации выполняется повторный запрос с более строгим промптом.
