# YW Web Rating

Веб-приложение для загрузки 4 скриншотов таблиц серверов выбранного кластера, распознавания их через Gemini API или Qwen Cloud и сохранения результатов в PostgreSQL с последующим отображением отдельных и сводной таблиц.

## Возможности

- Выбор кластера 1 или 2.
- Переключение AI-провайдера и модели в интерфейсе.
- Обязательная загрузка всех 4 скриншотов выбранного кластера.
- Проверка MIME-типа файлов на стороне клиента и сервера.
- Распознавание таблиц через `gemini-2.5-flash`.
- Поддержка `qwen3-vl-flash` через Qwen Cloud OpenAI-compatible API.
- Повторный запрос к Gemini с уточненным промптом, если первый ответ некорректен.
- Автоматические повторы запросов к AI API только для временных ошибок `429` и `503`.
- Логирование причин ошибок Gemini и Qwen в серверные логи контейнера `app`.
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
AI_PROVIDER=qwen
QWEN_API_KEY=your_real_qwen_key
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen3-vl-flash
DATABASE_URL=postgresql+psycopg://ranks_user:ranks_password@db:5432/ranks
POSTGRES_USER=ranks_user
POSTGRES_PASSWORD=ranks_password
POSTGRES_DB=ranks
```

`AI_PROVIDER` задает провайдер по умолчанию в UI. Если ключ для провайдера не задан, он будет показан в интерфейсе как недоступный.

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
- `POST /upload/{cluster}`: multipart-форма с 4 файлами `files`, 4 значениями `server_names`, а также `provider` и `model`.
- `GET /servers/{cluster}`: данные по серверам кластера.
- `GET /summary/{cluster}`: сводка по кластеру. Вернет `409`, если загружены не все 4 сервера.
- `GET /providers`: доступные AI-провайдеры и модели для переключателя на фронтенде.

## Примечание по AI API

- Gemini вызывается через официальный SDK `google-genai`.
- Qwen Cloud вызывается через OpenAI-compatible API по адресу `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`.
- Для Qwen `qwen3-vl-flash` как минимум на официальной странице моделей указаны визуальный ввод и structured output, а на quickstart-странице Qwen Cloud показан OpenAI-compatible способ интеграции.
- Для обеих интеграций приложение валидирует JSON через Pydantic и повторяет запрос с более строгим промптом, если ответ модели не соответствует схеме.
