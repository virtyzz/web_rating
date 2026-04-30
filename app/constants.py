CLUSTERS: dict[int, list[str]] = {
    1: ["cherno1", "cherno2", "deadfall1", "dungeon1"],
    2: ["cherno3", "cherno4", "deadfall2", "dungeon2"],
}

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}

BASE_PROMPT = (
    "Извлеки таблицу из этого скриншота. "
    "Колонки: Имена игроков, Текущий ранг, Количество очков, "
    "Убийств инфицированных и животных. "
    'Верни в формате JSON: {"players": [{"name": str, "rank": int, "points": int, "kills": int}]}. '
    "Если число распознано неоднозначно, выбери наиболее вероятное целое значение. "
    "Не добавляй комментарии, markdown и лишний текст."
)

RETRY_PROMPT = (
    "Верни только валидный JSON без markdown и пояснений. "
    'Строго соблюдай структуру {"players": [{"name": str, "rank": int, "points": int, "kills": int}]}. '
    "Все rank, points и kills должны быть целыми числами."
)

