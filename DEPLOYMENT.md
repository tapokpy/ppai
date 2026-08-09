# Деплой через Coolify + Gluetun (VPN) + Mullvad

## Как устроена сеть

- `postgres`, `redis`, `chromadb`, `ollama` — обычные сервисы в сети `app_net`, наружу не торчат, VPN им не нужен (внутренний трафик).
- `gluetun` — поднимает WireGuard-туннель до Mullvad и тоже подключён к `app_net`.
- `backend` и `bot` используют `network_mode: "service:gluetun"` — это значит, что они **полностью разделяют сетевой namespace gluetun**, а не просто ходят через него как через прокси. Отсюда два следствия:
  1. Весь исходящий интернет-трафик backend и bot (запросы к Anthropic Claude API, Telegram API) идёт через VPN-туннель.
  2. Так как gluetun сам подключён к `app_net`, backend и bot по-прежнему видят `postgres`, `redis`, `chromadb`, `ollama` по именам сервисов — Docker DNS работает и через shared namespace.
  3. Порт backend (8000) публикуется в `ports:` не у самого backend, а у **gluetun** — иначе порт наружу не пробросится.
  4. `bot` обращается к `backend` через `http://localhost:8000`, а не по имени сервиса — они в одном network namespace.

## Что нужно подготовить перед запуском

1. **Ключи Mullvad**: зарегистрировать аккаунт (только номер, без email), в личном кабинете сгенерировать WireGuard-конфиг, взять оттуда `PrivateKey` → `WIREGUARD_PRIVATE_KEY`, `Address` → `WIREGUARD_ADDRESSES`.
2. Заполнить `.env` на основе `.env.example` (пароли БД, `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, ключи Mullvad).
3. В коде проекта должны появиться `requirements.txt`, `app/main.py`, `bot/main.py`, `alembic/` — `Dockerfile.backend`/`Dockerfile.bot` их ожидают (сейчас в репозитории кода ещё нет).

## Разворачивание в Coolify

1. New Resource → **Docker Compose**, указать репозиторий `ppai` и ветку.
2. Coolify подхватит `docker-compose.yml` из корня.
3. Все переменные из `.env.example` добавить в Coolify как Environment Variables ресурса; `WIREGUARD_PRIVATE_KEY`, `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD` пометить как **Secret** (скрываются в UI).
4. Деплой. Coolify сам поднимет все 6 сервисов + разовый `ollama-pull`.

## Проверка после деплоя

- Статус туннеля: `docker logs pridprom_gluetun` — должно быть сообщение об успешном подключении к Mullvad.
- Реальная страна исходящего трафика: `docker exec pridprom_gluetun wget -qO- https://am.i.mullvad.net/json`.
- DNS-утечка: `docker exec pridprom_gluetun wget -qO- https://am.i.mullvad.net/connected` — должно возвращать `You are connected to Mullvad`.
- Если backend недоступен снаружи — проверить, что порт проброшен именно в блоке `gluetun.ports`, а не потерялся.

## Важно

- Панель Coolify и SSH-доступ к серверу **не** проходят через gluetun — управление сервером остаётся напрямую, VPN влияет только на трафик backend/bot.
- Если туннель Mullvad оборвётся, backend и bot потеряют сеть целиком (в т.ч. доступ к postgres/redis) — это осознанный kill-switch, а не баг.
