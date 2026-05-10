# Склад и заказы (прототип)

Клиент‑серверное приложение: REST API на **FastAPI** + панель на **React**. По умолчанию БД — **SQLite**; для Docker с **PostgreSQL** есть отдельный compose‑файл.

## Требования

- **Без Docker:** Python 3.12+, Node.js 20+ (для фронтенда).
- **С Docker:** Docker Engine и Docker Compose v2.

---

## Запуск без Docker

### Бэкенд

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000/api/...` (большинство методов требуют заголовок `Authorization: Bearer <токен>`; выдаётся через `POST /api/auth/login`).
- Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (для проверки защищённых методов нажмите «Authorize» и вставьте `Bearer <токен>`).

**Учётные записи по умолчанию** (создаются при первом старте, если таблица пользователей пуста):

| Логин   | Пароль    | Роль        |
|---------|-----------|-------------|
| `admin` | `admin123`| администратор (в т.ч. склады) |
| `worker`| `worker123`| рабочий (товары, остатки, заказы; склады только просмотр) |
- SQLite создаётся в файле `warehouse.db` в текущей рабочей директории (как в `DATABASE_URL` по умолчанию).

**Демо-данные (склады, товары, остатки, заказы в разных статусах):** при первом запуске на пустой БД включите `SEED_DEMO_DATA=true` (или `1`). Повторно сидер не выполняется, пока в таблице товаров есть записи. Чтобы заполнить заново — удалите `warehouse.db` и перезапустите с той же переменной.

```bash
# Windows PowerShell
$env:SEED_DEMO_DATA="true"; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**PostgreSQL (локально):** задайте переменную окружения перед запуском, например:

```bash
set DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/warehouse
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Фронтенд (это и есть веб-интерфейс для проверки)

Панель **не** встроена в FastAPI: её нужно запускать отдельно. Сначала поднимите бэкенд (порт **8000**), затем:

```bash
cd frontend
npm install
npm run dev
```

После запуска Vite обычно **сам откроет вкладку** в браузере. Если нет — откройте вручную:

- **http://127.0.0.1:5173/** или **http://localhost:5173/**

В шапке будут ссылки: Товары, Склады, Остатки, Заказы.

**Docker:** полный UI с прокси к API — **http://localhost:8080** (`docker compose up`).

Запросы к API идут на `http://127.0.0.1:8000` (см. `src/api/client.ts`).

Опционально файл `frontend/.env` (указывайте **хост без** суффикса `/api` — иначе раньше получался двойной путь и ответ **Not Found**):

```env
VITE_API_URL=http://127.0.0.1:8000
```

В режиме **`npm run dev`** при отсутствии `VITE_API_URL` запросы идут на **`/api`** на том же хосте, что и Vite; прокси в `vite.config.ts` перенаправляет их на бэкенд **:8000** (его нужно запустить отдельно).

Для сборки статики без смены origin:

```bash
npm run build
```

### Переменные окружения (бэкенд)

| Переменная       | Назначение |
|------------------|------------|
| `DATABASE_URL`   | Строка SQLAlchemy (SQLite или PostgreSQL). |
| `CORS_ORIGINS`   | Разрешённые origin через запятую (по умолчанию localhost Dev и Docker UI). |
| `API_PREFIX`     | Префикс API (по умолчанию `/api`). |
| `SEED_DEMO_DATA` | `true` / `1` — один раз заполнить пустую БД примером данных (см. выше). |
| `JWT_SECRET_KEY` | Секрет подписи JWT (переопределите в проде). |

---

## Запуск в Docker (SQLite в volume)

Из **корня репозитория**:

```bash
docker compose up --build
```

- UI (nginx + прокси `/api`): [http://localhost:8080](http://localhost:8080)
- API напрямую (для отладки): [http://localhost:8000](http://localhost:8000)
- БД SQLite хранится в volume `warehouse_data` (файл `/data/warehouse.db` внутри контейнера API).

Фронт собирается с `VITE_USE_RELATIVE_API=true`, запросы идут на тот же хост (`/api/...`), nginx проксирует их в сервис `api`.

---

## Docker + PostgreSQL

```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up --build
```

Поднимается Postgres 16, API подключается по URL из второго файла. Порт БД проброшен на `5432` (можно убрать в прод‑сценарии).

---

## Тесты

Установка зависимостей для тестов:

```bash
cd backend
python -m pip install -r requirements-dev.txt
```

Запуск:

```bash
python -m pytest
```

Содержимое:

- **Интеграционные / CRUD** — `tests/test_crud.py`, `tests/test_orders.py`, `tests/test_health.py`.
- **Фаззинг (Hypothesis)** — `tests/test_fuzz_hypothesis.py`: случайные строки, бинарные тела, произвольные JSON и ID; проверяется отсутствие необработанных **5xx**.
- **Фаззинг по контракту OpenAPI (Schemathesis)** — `tests/test_schemathesis_fuzz.py`: генерация запросов по схеме `/openapi.json`, проверка отсутствия **5xx** и валидация успешных ответов.

Пример быстрого прогона без лишнего вывода:

```bash
python -m pytest -q
```

### CI (GitHub Actions)

При пуше в ветки `main` или `master` и в pull request запускается [`.github/workflows/ci.yml`](.github/workflows/ci.yml): **pytest** в `backend/` и **`npm run build`** в `frontend/`.

---

## Структура каталогов (кратко)

- `backend/app` — модели, схемы, сервисы, роутеры.
- `frontend/src` — страницы React, API‑клиент.
- `infra/nginx.conf` — конфиг nginx для Docker‑сборки UI.
