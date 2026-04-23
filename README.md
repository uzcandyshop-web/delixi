# DELIXI

Telegram-бот с QR-системой и бонусной программой лояльности для розничной сети.

- Клиент получает персональный QR-код и показывает его продавцу при покупке
- Продавец сканирует QR через Telegram WebApp (камера) и вводит сумму
- Бонусы начисляются по тирам (% зависит от суммы покупки)
- Клиент может обменять накопленные бонусы на призы из каталога
- Регионы изолированы: продавец Ташкента не может провести покупку клиенту Самарканда

## Стек

- **FastAPI** + **SQLAlchemy 2** + **Alembic** — REST API и миграции
- **aiogram 3.x** — Telegram-бот (long polling)
- **PostgreSQL 15** — база данных
- **html5-qrcode** — сканер в Telegram WebApp
- **Render** — хостинг (Web + Background Worker + managed Postgres)

## Структура

```
delixi/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Настройки из env
│   ├── db.py                # SQLAlchemy engine + Base
│   ├── deps.py              # FastAPI dependencies + role guards
│   ├── schemas.py           # Pydantic модели
│   ├── core/
│   │   ├── qr.py            # HMAC-подписанные QR-токены
│   │   ├── qr_image.py      # PNG-генерация
│   │   └── tg_auth.py       # Проверка Telegram WebApp initData
│   ├── models/              # SQLAlchemy ORM модели
│   ├── services/
│   │   ├── bonus.py         # Расчёт тиров, баланс
│   │   ├── transactions.py  # Создание покупки
│   │   └── redemptions.py   # Обмен на призы
│   ├── api/
│   │   ├── transactions.py  # POST /transactions
│   │   ├── me.py            # /me, /me/history, /regions
│   │   ├── prizes.py        # Каталог и заявки
│   │   └── admin.py         # Тиры, отчёты, разрешение заявок
│   └── bot/
│       ├── main.py          # Диспетчер aiogram
│       ├── notify.py        # Уведомления клиентам
│       └── handlers/
│           ├── customer.py  # /start, регистрация, меню клиента
│           ├── seller.py    # Меню продавца + WebApp кнопка
│           └── admin.py     # /pending, /sellers, /make_seller
├── static/
│   └── scanner.html         # Telegram WebApp сканер
├── migrations/              # Alembic
│   └── versions/
│       └── 20260423_0001_initial_schema.py
├── alembic.ini
├── render.yaml              # Infrastructure-as-code для Render
├── requirements.txt
├── .env.example
└── README.md
```

## Локальный запуск

### 1. Клонировать и установить зависимости

```bash
git clone <repo-url> delixi
cd delixi
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Настроить `.env`

```bash
cp .env.example .env
# Сгенерировать QR_SECRET:
python -c "import secrets; print(secrets.token_hex(32))"
# Получить BOT_TOKEN от @BotFather
# Записать свой telegram_id в ADMIN_TG_IDS
```

### 3. Запустить PostgreSQL локально

```bash
docker run -d --name delixi-pg \
  -e POSTGRES_DB=delixi \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:15

# В .env:
# DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/delixi
```

### 4. Накатить миграции

```bash
alembic upgrade head
```

Миграция создаст все таблицы, засеет 14 регионов Узбекистана и 3 дефолтных бонусных тира (0–500k: 2%, 500k–2M: 3%, 2M+: 5%).

### 5. Запустить API и бота (в двух терминалах)

```bash
# Терминал 1 — API
uvicorn app.main:app --reload --port 8000

# Терминал 2 — Бот
python -m app.bot.main
```

Swagger: http://localhost:8000/docs

### 6. Настроить WebApp

Для локальной разработки WebApp сканера нужен HTTPS. Варианты:

- **ngrok**: `ngrok http 8000`, затем в `.env` укажи `WEBAPP_URL=https://xxx.ngrok-free.app/static/scanner.html`
- **cloudflared**: `cloudflared tunnel --url http://localhost:8000`

## Деплой на Render

### Blueprint-деплой (одной кнопкой)

1. Запушь репозиторий в GitHub
2. В Render: **New** → **Blueprint** → подключи репозиторий
3. Render прочитает `render.yaml` и создаст: `delixi-api` (web), `delixi-bot` (worker), `delixi-db` (Postgres)
4. Заполни секреты в Dashboard: `BOT_TOKEN`, `QR_SECRET`, `ADMIN_TG_IDS`, `WEBAPP_URL`
5. `WEBAPP_URL` = `https://delixi-api.onrender.com/static/scanner.html`

### Постдеплой

- `alembic upgrade head` запускается автоматически в `buildCommand` для `delixi-api`
- В `@BotFather` → Bot Settings → Menu Button → установить на `WEBAPP_URL` для быстрого запуска сканера

## Пользовательские сценарии

### Клиент

1. `/start` → отправляет контакт → выбирает регион → получает QR-картинку
2. Показывает QR продавцу при покупке
3. В меню: **📱 Мой QR**, **💰 Баланс**, **🎁 Призы**, **📜 История**

### Продавец

Админ назначает роль командой в боте: `/make_seller <telegram_id> <region_code>` (например `/make_seller 123456789 TAS`)

1. `/seller` → откроется клавиатура с кнопкой **📸 Сканировать QR** (запускает WebApp)
2. Камера сканирует QR клиента → ввод суммы → подтверждение
3. **📊 Сегодня** — оборот и количество транзакций за сутки

### Админ

Админом становится автоматически любой `telegram_id` из `ADMIN_TG_IDS` после `/start`.

- `/admin` — список команд
- `/pending` — inline-кнопки «Одобрить / Отклонить» на каждой заявке
- `/sellers` — список продавцов с telegram_id
- `/make_seller <id> <region_code>` — назначить продавца
- `/report` — (TODO) оборот за 7 дней

Админские отчёты и CRUD тиров/призов доступны через API: `/api/v1/admin/*`.

## Ключевые архитектурные решения

### QR-токен = HMAC, не ID

Токен в QR — это `base64(user_id + timestamp + HMAC)`, подписанный `QR_SECRET`. Подпись проверяется на лету, без обращения к БД. TTL — 1 год, после этого токен можно ротировать.

### Баланс = SUM() из ledger

Балансы **не хранятся** в колонке. Каждое начисление и списание — запись в `bonus_ledger` с `delta` (+/-), `reason` ('purchase', 'redeem', 'adjust', 'expire'). Балансы считаются через `SUM(delta)` или view `v_user_balance`. Это даёт бесплатный аудит и защиту от рассинхрона.

### Идемпотентность

Каждая транзакция имеет уникальный `idempotency_key` (uuid от клиента WebApp). Если продавец случайно нажмёт «Подтвердить» дважды — сервер вернёт существующую транзакцию с флагом `replayed: true`, не создавая дубликат.

### Обмен призов: двухфазный

1. Клиент нажимает «Заказать» → создаётся `redemption` со статусом `pending`. Бонусы **пока не списываются**.
2. Админ нажимает «Одобрить» → списание в `bonus_ledger` (delta = -cost_bonus) + декремент `stock` + статус `approved`.

Это защищает от гонок (двойные заявки при одинаковом балансе) и даёт админу возможность отклонить, если приз физически закончился.

### Региональная изоляция

При создании транзакции проверяется `seller.region_id == customer.region_id`. Ошибка `region_mismatch` возвращается с обоими регионами, чтобы продавцу было понятно, что происходит.

## API

Все эндпоинты WebApp требуют заголовок `Authorization: tg <initData>`. Сервер валидирует подпись через HMAC(BOT_TOKEN).

| Метод | Путь                                           | Роль      |
|-------|-------------------------------------------------|-----------|
| GET   | `/health`                                       | public    |
| GET   | `/api/v1/me`                                    | any       |
| GET   | `/api/v1/me/history`                            | any       |
| GET   | `/api/v1/regions`                               | any       |
| POST  | `/api/v1/transactions`                          | seller    |
| GET   | `/api/v1/prizes`                                | any       |
| POST  | `/api/v1/redemptions`                           | customer  |
| GET   | `/api/v1/redemptions/me`                        | any       |
| POST  | `/api/v1/admin/tiers`                           | admin     |
| GET   | `/api/v1/admin/redemptions/pending`             | admin     |
| POST  | `/api/v1/admin/redemptions/{id}/resolve`        | admin     |
| GET   | `/api/v1/admin/reports/turnover?days=7`         | admin     |

Полная документация: `/docs` (Swagger UI).

## TODO / V2

- [ ] Уведомления клиенту при approve/reject заявки (каркас уже в `notify.py`)
- [ ] Автоматический expire бонусов через N месяцев (cron + `LedgerReason.EXPIRE`)
- [ ] Push-рассылки от админа (акции, поздравления)
- [ ] Роль «Региональный менеджер» (сужённый админ)
- [ ] Узбекский UI (i18n)
- [ ] Redis-кеш для балансов при росте нагрузки
- [ ] Интеграция со Smartup / 1С
