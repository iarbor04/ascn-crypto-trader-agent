# Bitget: исследование для ИИ-сотрудника ASCN (12.10.2026)

Метод: WebSearch/WebFetch, разбор HTML официальной документации (bitget.com/docs, после миграции `/api-doc/*` редиректит туда), публичные GET через curl. Регистраций, форм и ключей не было. Где источники противоречат друг другу или устарели, это помечено.

## 1. Брокерская и партнёрская программы

**Брокер (FD / ND).** Bitget делит брокеров на два типа. **FD (fully-disclosed)** приводят пользователей в API Bitget и раскрывают их данные бирже. **ND (non-disclosed)** ведут клиентов на суб-аккаунтах своего мастер-аккаунта и данные клиентов не раскрывают. Подходят биржи, терминалы, asset management, social trading, **поставщики торговых ботов** и кошельки. Канальный код выдают «в тот же день», когда одобрен статус брокера. Источник: https://www.bitget.com/support/articles/12560603831454

**Атрибуция ордеров.** В официальной документации UTA v3, на страницах Place Order, Batch Order и Place Strategy Order, написано дословно: *"API Broker rebate identifier: The following code block needs to be added to the HTTP Header of the request. `"X-CHANNEL-API-CODE":"your-channel-api-code"`"*. Источники: https://www.bitget.com/docs/catalog/trading/order-management и https://www.bitget.com/docs/catalog/trading/strategy-trading. Тот же заголовок ccxt ставит в каждый приватный запрос со своим кодом `p4sve` (`python/ccxt/bitget.py`, функция sign: `'X-CHANNEL-API-CODE': broker`): https://github.com/ccxt/ccxt/blob/master/python/ccxt/bitget.py. Значит, механизм работает на **собственных API-ключах пользователей**, суб-аккаунты для него не нужны. ccxt зарабатывает на нём со всех своих пользователей Bitget.

**Работает ли на существующих пользователях.** Таблица ставок в FAQ брокера разделяет два случая. Первый: «прямые/органические» пользователи, у которых нет пригласителя. Второй: «API-пользователи других аффилиатов», и по ним ставка ниже. Так что код учитывается и для уже зарегистрированных людей, но процент зависит от их привязки. Точные условия по «органике» (например, нужна ли привязка новых пользователей к брокеру) надо подтвердить у BD.

| Уровень | Spot, объём/мес | Деривативы, объём/мес | Органика / прямые | Чужие аффилиаты |
|---|---|---|---|---|
| 0 | новый | новый | до 25% | 5% |
| 1 | ≥10k USDT | ≥100k | 30% | 5% |
| 2 | ≥1M | ≥5M | 35% | 8% |
| 3 | ≥5M | ≥20M | 40% | 10% |
| 4 | ≥20M | ≥100M | 45% | 10% |
| 5 | ≥40M | ≥300M | 50% | 12% |

Формула ребейта: (базовая комиссия − скидки, включая BGB −20%, − maker rebate) × объём. Выплаты за день T приходят T+1 между 15:30 и 21:00 (UTC+8). Если несколько месяцев подряд не выполнять порог, уровень понижают. В новости от 17.09.2025 описаны 6 уровней, вход от 100k USDT/мес и ежедневный расчёт: https://www.bitget.com/news/detail/12560604971057

**Как подать заявку.** Зарегистрироваться на Bitget Partner **без реферального кода**, затем пройти настройку с BD-менеджером и получить broker ID / channel code в Broker Portal. Контакт: broker@bitget.com.

**ND-эндпоинты** (только мастер-аккаунт с типом ND Broker): `/api/v3/broker/create-sub`, `create-sub-apikey`, `sub-list`, `commission` (окно ≤30 дней), `sub-withdrawal` и другие. Документация: https://www.bitget.com/docs/catalog/broker/broker. Нам ND не нужен, потому что мы не держим клиентские средства.

**Аффилиатка (реферальная программа).** «До 50%» комиссий, **пожизненно** («relationship will not expire»), есть суб-аффилиаты, расчёт ежедневно, для вывода нужен KYC. Источник: https://www.bitget.com/academy/bitget-affiliate-faq-beginner-guide. Акция Q1-2026 давала «permanent 40% base + 10% первый месяц» при условиях KYC, ≥10k USDT объёма приглашённых за 30 дней и 100 подписчиков / 500 участников группы: https://www.bitget.com/support/articles/12560603873376. Ссылку создают в Promotion Center партнёрского портала. По сторонним источникам формат такой: `partner.bitget.com/bg/<code>`, плюс поле кода при регистрации. **Существующего пользователя привязать нельзя.** В правилах программы сказано: «Referring users who already have Bitget accounts… will result in a revoked affiliate status and a reduction of your rebate percentage to 0%». Self-referral с того же IP или устройства влечёт конфискацию. Источник: https://www.bitget.com/support/articles/12560603796198. Policy (обновлена 21.08.2026) требует соблюдать «advertising, social media… regulations» и не продвигать программу в Prohibited Countries. Отдельных правил раскрытия Bitget не задаёт, но запрещает обещать доходность и выдавать себя за Bitget: https://www.bitget.com/support/articles/12560603824255

## 2. Публичный API (без ключа)

Base URL: `https://api.bitget.com`. Лимит 6000 запросов/IP/мин, у каждого эндпоинта свой лимит, при превышении HTTP 429. WebSocket: `wss://ws.bitget.com/v3/ws/public`. Демо-режим: заголовок `paptrading: 1` и Demo-ключ. Источник: https://www.bitget.com/docs/uta/quick-start. Сейчас работают два поколения API: **v3 (UTA)** и **classic v2**. Оба проверены живыми запросами 12.10.2026, код ответа `"00000"`.

| Данные | v3 (проверено) | v2 classic (проверено) |
|---|---|---|
| Тикеры | `/api/v3/market/tickers?category=USDT-FUTURES&symbol=BTCUSDT`: поля `lastPrice, bid1Price, ask1Price, price24hPcnt, turnover24h, markPrice, indexPrice, fundingRate, openInterest` | spot `/api/v2/spot/market/tickers` (`lastPr, bidPr, askPr, change24h, usdtVolume`); фьючерсы `/api/v2/mix/market/ticker?productType=USDT-FUTURES` (`markPrice, fundingRate, holdingAmount`) |
| Свечи | `/api/v3/market/candles?category=SPOT&symbol=BTCUSDT&interval=1H` (массив [ts,o,h,l,c,vol,turnover]) | `/api/v2/spot/market/candles?granularity=1h` |
| Стакан | `/api/v3/market/orderbook` | `/api/v2/spot/market/orderbook` (`asks/bids`) |
| Funding | `/api/v3/market/current-fund-rate?symbol=` (`fundingRate, fundingRateInterval=8, nextUpdate, min/maxFundingRate`), `history-fund-rate` | `/api/v2/mix/market/current-fund-rate` |
| OI | `/api/v3/market/open-interest` (`openInterest`) | `/api/v2/mix/market/open-interest` (`size`) |
| Long/short | `futures-account-long-short`, `futures-long-short`, `futures-position-long-short`, `futures-active-buy-sell` | `/api/v2/mix/market/account-long-short?period=1h` (`longAccountRatio, shortAccountRatio, longShortAccountRatio`) |
| Прочее | `liquidations` (проверено), `spot-whale-flow`, `spot-net-flow`, `proof-of-reserves`, `instruments`, `position-tier` | — |

Полный список: https://www.bitget.com/docs/catalog/market/market-data. Снимок на момент проверки: BTCUSDT perp 82 508, funding 0.0041%/8ч, OI ≈33.8k BTC, доля лонг-аккаунтов 63.8%.

**Гео.** Из нашей среды публичный API отвечает без ограничений. ToS запрещает резидентов США (включая территории). По Канаде и Великобритании источники расходятся: у одних запрещена вся Канада, у других только Альберта, Великобритания местами «с ограничениями». В EU Bitget **не получил лицензию MiCA**: заявка в австрийский FMA на рассмотрении, по сообщениям с 01.07.2026 новые сделки и депозиты для EU-аккаунтов прекращены, вывод остаётся. Источники: https://en.cryptonomist.ch/2026/07/02/bitget-micar-authorization-eu/ и https://www.cryptowinrate.com/bitget-restricted-supported-countries. Нужно проверить, из какой страны выходит IP песочницы ASCN.

## 3. Приватный API (ключ пользователя)

**Подпись.** `ACCESS-SIGN = Base64(HMAC_SHA256(secret, timestamp + METHOD + requestPath + ["?"+query] + body))`. Заголовки: `ACCESS-KEY`, `ACCESS-SIGN`, `ACCESS-TIMESTAMP` (мс), `ACCESS-PASSPHRASE`, `Content-Type: application/json`, `locale: en-US`. Есть вариант с RSA. Источники: https://www.bitget.com/docs/uta/quick-start и https://www.bitget.com/docs/classic/rest-api. Реализуется на stdlib (`hmac`, `hashlib`, `base64`, `urllib`).

**Эндпоинты v3 (UTA):**
- **Баланс и настройки:** `/api/v3/account/assets`, `/account/settings`, `/account/fee-rate`.
- **Позиции:** `/api/v3/position/current-position`, `/position/history-position`.
- **Ордера:** `POST /api/v3/trade/place-order` (category SPOT/MARGIN/USDT-FUTURES…, symbol, qty, side, orderType; 10/с/UID), `place-batch`, `cancel-order`, `cancel-symbol-order`, `modify-order`, `close-positions`, `unfilled-orders`, `fills`, `countdown-cancel-all` (dead-man switch).
- **TP/SL и алго:** `place-strategy-order` с type `tpsl | trigger | oco | trailing_stop | iceberg | twap`.
- **Плечо и режим:** `/api/v3/account/set-leverage`, `set-hold-mode`, `set-margin`.
- **Grid-боты:** `/api/v3/trade/grid/create-bot`, `create-neutral-bot`, `bot-detail`, `close-bot`, `add-investment`.
- **Копитрейдинг (фьючерсы):** `/api/v3/copy/futures/follower-settings`, `modify-follower-settings`, `current-copy`, `unfollow`, `place-tpsl`, `close-positions`, `profit-summary`, `portfolio-overview`, `trading-pairs`. Источник: https://www.bitget.com/docs/catalog/copy-trading/public-private

**Classic v2** (проверено по ccxt): `/api/v2/spot/account/assets`, `/api/v2/mix/account/accounts`, `/api/v2/mix/position/all-position`, `/api/v2/spot/trade/place-order`, `/api/v2/mix/order/place-order`, `place-tpsl-order`, `place-plan-order`, `/api/v2/mix/account/set-leverage`, `/api/v2/copy/mix-follower/*`. Аккаунт бывает либо UTA, либо classic, поэтому агент должен определить режим (`/api/v3/account/settings`) и выбрать нужное API.

**Права ключа.** В UTA четыре типа: trade read-only, trade read/write, management read-only, management read/write. В classic: Read-only / Trade / Transfer / Withdraw, причём вывод возможен только с IP из whitelist. На один UID приходится 10 ключей. Bitget «strongly recommended» привязывать IP. Рекомендация пользователю: **trade read/write и management read-only, без transfer и withdraw**. Для режима «только аналитика» достаточно read-only. IP привязывать, если у песочницы ASCN стабильный egress-IP. Если IP динамический, нужно честно предупредить, что ключ без IP-привязки слабее защищён.

## 4. Собственный ИИ Bitget, конкуренты, боли пользователей

- **GetAgent** запущен 01.07.2025, веб-версия вышла в феврале 2026. Это чат внутри приложения: 50+ инструментов, исполнение spot и futures, swap/on-chain, тарифы Free / Plus (~10 вопросов в день) / Ultra (до 50). В сентябре 2026 добавлены модули контрактов, earn и ботов. **GetAgent 2.0** (23.09.2026) добавил мультиактивное исследование, отчёты по расписанию и отслеживание тем. Источники: https://www.coingecko.com/learn/what-is-getagent-bitget, https://www.bitget.com/news/detail/12560604992675, https://invezz.com/news/2026/09/23/bitget-expands-getagent-2-0-to-multi-asset-ai-research/
- **Bitget Agent Hub** (официальный, MIT, февраль–март 2026): MCP-сервер, CLI `bgc`, skills, TS SDK (89 операций UTA v3), `bitget-signal` без ключа. Есть режимы `--read-only` и `--paper-trading`. Источник: https://github.com/Bitget-AI/agent_hub. В коде SDK (`rest-client.ts`) заголовка `X-CHANNEL-API-CODE` нет, поэтому сторонние агенты на Agent Hub брокерский доход не несут.
- **Пробелы GetAgent.** Работает только внутри Bitget: нет других бирж и общего портфеля. Лимиты вопросов на тарифах. Ограничен контекст пользователя: нет его стратегии, журнала сделок, налогов. Нет проактивной работы вне приложения (Telegram, отчёты в .md). Нет независимого риск-контроля, потому что ассистент принадлежит той же бирже, которая зарабатывает на объёме.
- **Чего хотят пользователи.** Отзывы (Trustpilot, r/bitget ~3k участников, Coin Bureau 02.2026) сводятся к трём болям: поддержка и выводы, проскальзывание и нестабильность копитрейдинга («стратегия прошлого месяца не работает»), выбор трейдера для копирования. Источник: https://www.coinbureau.com/review/bitget-copy-trading-review
- **Сторонние боты** (цены по агрегаторам, расходятся): 3Commas $15–60 (по другим данным $20–140)/мес, WunderTrading $19–69, Cryptohopper $29–129. У Bitget есть свои бесплатные grid, DCA и copy-боты.

## 5. Правила и риски

- **Брокерский код** законен и предусмотрен документацией. Пока нет договора с BD, слать чужой или выдуманный код нельзя. Код в заголовке не меняет комиссию пользователя: ребейт идёт из доли Bitget. Это стоит прямо написать в карточке агента.
- **Реферальная ссылка** только для новых пользователей. Нельзя предлагать существующим «перерегистрироваться», нельзя обещать доходность, нельзя выдавать себя за Bitget, нельзя таргетировать US и другие запрещённые страны. Раскрытие партнёрских отношений требуют законы о рекламе (FTC, ASA, ЕС), и Bitget отсылает к ним. Нужна явная пометка «партнёрская ссылка, ASCN получает комиссию».
- **Регуляторика.** Агент, который сам торгует и советует, в ряде юрисдикций близок к инвест-консультированию. Поэтому нужны дисклеймер «не инвестиционный совет», подтверждение каждого ордера пользователем и запрет на автоторговлю по умолчанию. Для EU (без MiCA) и US сервис не продвигать.
- **Безопасность.** Ключи хранятся только в Secrets, не логируются и никогда не имеют прав на вывод. Нужны лимиты на размер ордера и плечо, а также `countdown-cancel-all` для автономных сценариев.

## 6. Рекомендация

**Модель дохода (две ветки, без конфликта):**
1. **Брокерский канал (основной).** Подать заявку как *trading bot / AI agent provider* (FD) на broker@bitget.com и Bitget Partner (без реф-кода, отдельный аккаунт ASCN). Полученный channel code зашить **в код агента** как константу `BITGET_CHANNEL_CODE` (не в Secrets пользователя) и добавлять заголовок `X-CHANNEL-API-CODE` во **все** торговые POST: place-order, place-batch, place-strategy-order, grid create-bot, close-positions. Ребейт идёт со всех пользователей, включая существующих: до 25–50% по «органике», 5–12% по чужим рефералам. Учёт через Broker Portal; эндпоинт `/api/v3/broker/commission` доступен только ND, для FD нужно уточнить у BD.
2. **Аффилиат-ссылка** показывается только на онбординге человеку *без* аккаунта Bitget, с пометкой о партнёрстве. Пользователи, зарегистрированные по ней, становятся «прямыми», и брокерская ставка по ним будет максимальной. Нужно уточнить у BD, суммируются ли аффилиатский и брокерский доход по одному пользователю или учитывается только один.

**Техдизайн.** Единый модуль `bitget.py` на stdlib. Функция `request(method, path, params, body, signed, trade)` подписывает HMAC, добавляет `locale`, при `trade=True` добавляет `X-CHANNEL-API-CODE`, а при `BITGET_DEMO=1` добавляет `paptrading: 1`. Модуль автоматически определяет UTA или classic, ретраит с бэкоффом при 429 и пишет журнал ордеров в `.md`. Secrets: `BITGET_API_KEY`, `BITGET_API_SECRET`, `BITGET_PASSPHRASE`. Перед стартом проверяются права ключа; если обнаружен withdraw или transfer, агент выдаёт предупреждение и отказывается работать. Каждая сделка проходит предпросмотр с ценой, размером, плечом, ликвидационной ценой и комиссией и исполняется только после подтверждения «да».

**MVP:**
1. Рыночный бриф без ключа: цена, funding, OI, long/short, ликвидации, whale-flow, всё в .md-отчёте.
2. Портфель: балансы, позиции, PnL, ликвидационные уровни, риск-алерты.
3. Ордер в одну фразу: spot и futures, плечо, обязательные TP/SL через `place-strategy-order`, предпросмотр и подтверждение.
4. Защита позиций: перенос SL в безубыток, trailing stop, «закрой всё».
5. Помощник по копитрейдингу: сравнение трейдеров, настройка follower-settings, контроль и отписка.
6. Grid-бот через API: создание с валидацией (`grid/validate`), мониторинг, закрытие.
7. Демо-режим (paptrading) для новичков.
8. Еженедельный отчёт по сделкам и комиссиям в .md.

**Открытые вопросы к BD Bitget:** ставки FD для AI-агента; учёт существующих «органических» пользователей; совместимость с аффилиаткой; эндпоинт статистики для FD; влияние классического и UTA-режима на атрибуцию.
