# VPN Deployment: Docker + Gluetun/Mullvad Split-Tunneling

Маршрутизация исходящего трафика к Anthropic Claude API через VPN-туннель
(Mullvad, WireGuard), при этом Telegram Bot API, PostgreSQL, Redis и Ollama
работают напрямую, без VPN. Подход: sidecar-контейнер Gluetun с встроенным
HTTP-прокси, а не `network_mode: service:gluetun` (который пристегнул бы
*весь* трафик приложения к VPN, включая Telegram — риск бана бота за
Datacenter/VPN IP, плюс лишняя задержка для локальных БД/Redis/Ollama).

## 1. Архитектура

```
                    ┌─────────────────────────┐
                    │   internet (Mullvad)     │
                    └────────────▲─────────────┘
                                 │ WireGuard
                    ┌────────────┴─────────────┐
                    │   gluetun (frontend net)  │
                    │   HTTP proxy :8888        │
                    └────────────▲─────────────┘
                                 │ http://gluetun:8888
                                 │ (Anthropic Claude only)
┌──────────────┐    ┌───────────┴───────────┐    ┌──────────────────┐
│ Telegram API │◄───┤  api / bot             ├───►│ postgres / redis │
│ (direct)     │    │  (frontend + backend)   │    │ ollama (backend, │
└──────────────┘    └────────────────────────┘    │  internal only)  │
                                                     └──────────────────┘
```

- Сеть `backend` — `internal: true` (нет маршрута наружу). В ней сидят
  `postgres`, `redis`, `ollama`, и на неё же (в дополнение к `frontend`)
  подключены `api`/`bot` — то есть эти контейнеры не могут выйти в интернет
  сами по себе, даже если их скомпрометируют.
- Сеть `frontend` — обычный bridge с доступом в интернет: `gluetun`, `api`,
  `bot`.
- `api`/`bot` явно указывают `httpx.AsyncClient(proxy="http://gluetun:8888")`
  только для клиента Anthropic (`app/services/cloud_llm.py`) — это
  application-level split-tunneling, а не сетевой `network_mode`.
- Ollama-клиент (`app/services/local_llm.py`) прокси не использует —
  трафик к Ollama всегда прямой.
- Kill-switch, блокировка IPv6-утечек и DNS через VPN — встроенные функции
  Gluetun (`FIREWALL: "on"`), в этом репозитории ничего дополнительно не
  реализуется. При обрыве туннеля Gluetun сам отключает HTTP-прокси —
  запросы к Claude падают с ошибкой подключения (graceful degradation),
  Telegram и БД продолжают работать.

## 2. Настройка

1. Создайте аккаунт Mullvad, сгенерируйте WireGuard-ключ и адрес в панели
   Mullvad.
2. Заполните в `.env` (скопируйте из `.env.example`):
   ```
   MULLVAD_WIREGUARD_PRIVATE_KEY=...
   MULLVAD_WIREGUARD_ADDRESSES=...
   MULLVAD_SERVER_COUNTRIES=Sweden
   ```
   `ANTHROPIC_PROXY_URL` для Docker-сборки задавать не нужно — она
   прописана в `docker-compose.yml` (`http://gluetun:8888`) для сервисов
   `api`/`bot` напрямую. Она нужна только если вы запускаете приложение
   вне Docker и хотите вручную указать прокси.
3. Полный стек — opt-in через Compose profile:
   ```
   docker compose --profile full up -d
   ```
   Базовый набор (`postgres`, `redis`, `ollama`) по-прежнему поднимается
   как раньше, без флага `--profile full`.

**Важно:** точные названия переменных окружения Gluetun (например,
`HTTPPROXY_LISTENING_ADDRESS` против более старых `HTTPPROXY_PORT`) могут
отличаться между версиями образа `qmcgaw/gluetun` — перед реальным
деплоем сверьтесь с актуальной документацией Gluetun.

## 3. Чек-лист верификации (вручную, после реального деплоя)

Этого нельзя проверить без Docker daemon и реального аккаунта Mullvad —
выполняется руками на сервере с уже поднятым стеком:

- [ ] `docker build -t ppai:test .` — собирается без ошибок (при первой
      сборке возможно потребуется добавить недостающие системные пакеты
      в `Dockerfile`).
- [ ] **Proxy routing test**: изнутри контейнера `api`/`bot` —
      `curl -x http://gluetun:8888 https://am.i.mullvad.net/json` —
      `mullvad_exit_ip: true`.
- [ ] **Telegram-not-through-VPN test**: бот продолжает отвечать в
      Telegram, даже когда Gluetun намеренно остановлен (см. kill-switch
      test ниже) — значит трафик к Telegram не проходит через прокси.
- [ ] **DNS leak test**: запрос DNS изнутри контейнера `gluetun` уходит
      через резолверы Mullvad, а не хостовые (dnsleaktest.com изнутри
      контейнера).
- [ ] **Kill-switch test**: `docker compose stop gluetun` — запросы к
      Claude падают с ошибкой подключения (не уходят в открытый интернет
      напрямую), а Telegram/Postgres/Redis продолжают работать.
- [ ] `docker compose start gluetun` — прокси снова доступен, следующий
      запрос к Claude проходит успешно.

## 4. Что сознательно не входит в этот репозиторий

- **Portainer / Coolify** — операционные инструменты уровня хоста, а не
  часть стека этого приложения. Portainer можно поднять отдельной
  командой на сервере (`docker run -d -p 9000:9000 -v
  /var/run/docker.sock:/var/run/docker.sock ... portainer/portainer-ce`);
  Coolify — это внешняя PaaS-платформа, под которой может (опционально)
  работать весь этот `docker-compose.yml`. Единственное требование к
  такой платформе — поддержка `cap_add: NET_ADMIN` и проброса
  `/dev/net/tun`, без которых Gluetun не поднимет туннель.
- **Kill-switch/iptables/блокировка IPv6** — ответственность самого
  образа Gluetun; здесь только корректно настраивается сам Gluetun.
