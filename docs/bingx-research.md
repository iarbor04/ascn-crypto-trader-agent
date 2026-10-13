# BingX: исследование для ИИ-сотрудника ASCN (12.10.2026)

## 1. Заработок: брокер и рефералка

**API Broker — главный канал.** Механика из официальной техдоки брокера: брокер получает у BingX `sourceKey` (он же Broker ID) и передаёт его в заголовке каждого торгового запроса. Цитата: «the header information needs to carry the sourceKey», пример `X-SOURCE-KEY: test_key` рядом с `X-BX-APIKEY: <ключ пользователя>`. Метка ребейта видна в заголовках ответа. Доступ к дашборду ребейтов («Kanban») включают через broker@bingx.com. Отдельного параметра в теле нет: атрибуция идёт только по заголовку.
- **Работает и на чужих (уже существующих) аккаунтах.** На странице программы есть отдельная ставка «Existing users: 10% (API brokers only)». В приватном API агента есть эндпоинт `GET /openApi/agent/v1/reward/third/commissionDataList`, «API transaction commission (non-invitation relationship)», с `commissionBizType` 81 = perpetual, 82 = spot. То есть пользователь не обязан регистрироваться по нашей ссылке: его ордера через наш `X-SOURCE-KEY` дают 10% комиссии с его торговых сборов.
- **Новые пользователи по нашей ссылке:** 40% / 45% / 50% по уровням (пороги ≥ $5M / $10M / $50M объёма в месяц; подписи уровней в таблице кривые). Выплата ежедневная.
- **Требования для входа:** свой бренд, своя продуктовая экосистема, «Must exceed $5 million in monthly trading volume», «More than 500 active users». Подача: форма + ответ менеджера за 48 ч, broker@bingx.com. Шаги: аккаунт → заявка на Sourcekey → интеграция → запуск. На старте мы не проходим по объёму: нужно договариваться о пилоте (у BingX свой интерес к AI-трафику, см. п. 4).
- **Exchange Broker** (субаккаунты под нашим мастер-аккаунтом, до 100 000 пользователей) нам не подходит: фактически это кастоди чужих средств.
- **Важная находка.** Официальные BingX AI Skills (github BingX-API/api-ai-skills, обновлены 09.10.2026) требуют на ВСЕХ запросах, включая публичные, `X-SOURCE-KEY: BX-AI-SKILL`. BingX сам размечает трафик ИИ-агентов этим механизмом. Если пользователь параллельно поставит их скиллы, этот трафик пойдёт с их меткой, не с нашей.

**Реферальная / партнёрская программа.**
- Обычная рефералка: Lv1 10%, Lv2 20% (нужно 10 приглашённых, которые торгуют). Комиссия со спота и фьючерсов. Косвенная комиссия только с Lv2. Ссылку генерирует «Invite to Earn», формат `https://bingx.com/invite/<CODE>` (подтверждён только сторонними сайтами). Срок действия официально не указан.
- Партнёрка (Affiliate, bingx.com/en/global-partner): «до 50%», выплаты ежедневно, заявка с ручной проверкой, контакт bd@bingx.com.
- **Привязка после регистрации:** официального способа нет. Код вводится только при регистрации; сторонние сайты пишут, что поменять его потом нельзя. Правила партнёров прямо запрещают «Inviting already registered users». Значит, существующих пользователей монетизируем только через брокерский sourceKey.
- **Раскрытие:** правила продвижения запрещают частные схемы возврата комиссии вне официальных условий, биддинг на «BingX»/«BingX Login», фишинг-подобные страницы и выдачу себя за BingX. Нарушение = отзыв статуса и ставка 0%. Отдельной формулировки про раскрытие рекламы у BingX нет, но действуют законы о рекламе (FTC/ASA/ФЗ «О рекламе»): в агенте и на витрине пишем явно.

Источники: https://bingx.com/en/support/articles/27623589052185-broker-access-bingx-technical-documentation · https://bingx.com/en/support/articles/27624957911961 · https://bingx.com/en/support/articles/23261003741593 · https://github.com/BingX-API/api-ai-skills (skills/agent/SKILL.md, references/authentication.md) · https://bingx.com/en/support/articles/6918229896089-Introduction-to-BingX-Referral-Program · https://bingx.com/en/global-partner · https://bingx.com/en/support/articles/14088949854223 · https://bingx.com/en/support/articles/12503488450575

## 2. Публичный API (без ключа)

Base URL: `https://open-api.bingx.com`, резерв `https://open-api.bingx.pro` (только при сетевых ошибках). Демо (VST): `https://open-api-vst.bingx.com`. Символы в формате `BTC-USDT`.

| Данные | Spot | Perpetual USDT-M |
|---|---|---|
| Тикер 24h | `/openApi/spot/v1/ticker/24hr` | `/openApi/swap/v2/quote/ticker` |
| Свечи | `/openApi/spot/v2/market/kline` | `/openApi/swap/v3/quote/klines` |
| Стакан | `/openApi/spot/v1/market/depth` | `/openApi/swap/v2/quote/depth` |
| Фандинг / марк-цена | — | `/openApi/swap/v2/quote/premiumIndex`, `/quote/fundingRate` |
| Open interest | — | `/openApi/swap/v2/quote/openInterest` |
| Контракты / правила | `/openApi/spot/v1/common/symbols` | `/openApi/swap/v2/quote/contracts` |

Проверено curl 12.10.2026 (BTC ≈ 82 500):
- `premiumIndex` → `markPrice, indexPrice, lastFundingRate (0.000041), nextFundingTime, fundingIntervalHours: 8, min/maxFundingRate ±0.003`.
- `openInterest` → `openInterest: "605830643.3"` (в USDT), `time`.
- spot `ticker/24hr` → `lastPrice, priceChangePercent: "-1.68%"` (строка с %!), `quoteVolume, bidPrice/askPrice`. Числа здесь числами, а в swap строками.
- swap `klines` → объекты `{open, close, high, low, volume, time}`. Spot `kline` → массивы `[openTime, o, h, l, c, vol, closeTime, quoteVol]`.
- `depth` → `bids/asks` в виде `[price, qty]` + `bidsCoin/asksCoin`.
- Первый вызов swap klines вернул `{"code":100410,"msg":"请稍后重试"}`: нужен ретрай с backoff. HTTP-статус 200 при бизнес-ошибке, проверять `code`.
- **Long/short ratio в API нет** (в бандле доков нет такого эндпоинта). Нужен внешний источник или пропуск.

**Лимиты:** заголовки ответа `x-ratelimit-requests-remain: 499`, `x-ratelimit-requests-expire: 10000`. По докам IP-группа 1 = 500 запросов / 10 с. Лимиты групп 2/3 (2000/10 с, 300/10 с на эндпоинт) убраны 16.12.2025, остаются UID-лимиты на эндпоинтах (например openOrders 5/с, inviteRelationCheck 20/с).

**Гео:** BingX не обслуживает США (включая территории); сторонние списки также называют Канаду, материковый Китай, Гонконг, Макао, Нидерланды, Сингапур и Великобританию. Наш сэндбокс достучался из PoP ARN (Стокгольм), блока нет. Если сэндбокс ASCN хостится в США, вероятен блок CloudFront: проверить до запуска.

Источники: https://github.com/BingX-API/api-ai-skills (skills/references/base-urls.md, rate-limits.md, swap-market, spot-market) · https://github.com/BingX-API/docs-v3 · https://bingx.com/es/support/articles/360034028153-disclaimer · https://coinmarketcap.com/de/exchanges/bingx

## 3. Приватный API (ключ пользователя)

**Подпись:** все параметры (query + body) сортируются по ключу ASCII → `k=v&k=v` без URL-encode → `HMAC_SHA256(secret)` hex lowercase → `&signature=...`. Обязательны `timestamp` (мс) и `recvWindow` (по умолчанию 5000). Заголовок `X-BX-APIKEY`, плюс наш `X-SOURCE-KEY`. Если значения содержат `[` или `{`, URL-encode только значения. Всё делается на stdlib (`hmac`, `hashlib`, `urllib`).

**Ключевые эндпоинты:**
- Баланс: `GET /openApi/swap/v3/user/balance`, `/openApi/spot/v1/account/balance`, сводка `/openApi/account/v1/allAccountBalance`. Позиции: `/openApi/swap/v2/user/positions`. Доход/фандинг: `/swap/v2/user/income`. Комиссии: `/swap/v2/user/commissionRate`.
- Ордера perp: `POST|DELETE /openApi/swap/v2/trade/order`, `/order/test` (сухой прогон!), batch (до 5), `allOpenOrders`, `closeAllPositions`, `cancelAllAfter` (kill switch), `amend`, `cancelReplace`, `reverse`, TWAP `/swap/v1/twap/order`.
- TP/SL: типы `STOP_MARKET`/`TAKE_PROFIT_MARKET` (`stopPrice`, `closePosition`), либо JSON-параметры `stopLoss`/`takeProfit` прямо в MARKET/LIMIT ордере.
- Плечо и маржа: `POST /swap/v2/trade/leverage`, `/marginType` (ISOLATED/CROSSED), `/swap/v1/positionSide/dual`.
- Spot: `POST /openApi/spot/v1/trade/order`, `/cancel`, `/openOrders`, `/myTrades`, OCO `/spot/v1/oco/order`.
- Copy trading: только сторона **трейдера-лидера** (`/openApi/copyTrading/v1/swap/trace/currentTrack`, `closeTrackOrder`, `setTPSL`, `PFutures/traderDetail`, `profitDetail`, `setCommission`). API для подписчика (выбрать и подписаться на трейдера) нет.
- **Grid / ботов в API нет.** Сеточные боты BingX доступны только в UI (обновление в мае 2026: до 500 сеток, сдвиг диапазона). Агент может эмулировать сетку лимитками, но тогда ему нужна постоянная работа.
- Проверка ключа: `GET /openApi/account/v1/apiKey/query` → `permissions` (1 спот, 2 чтение, 3 фьючерсы, 4 universal transfer, **5 withdraw**, 7 внутренние переводы) и `ipAddresses`.

**Рекомендуемые права:** по умолчанию новый ключ только на чтение. Режим «аналитик» = только 2. Режим «трейдер» = 2 + 1 и/или 3. **Никогда 5 и 4.** Агент при старте вызывает `apiKey/query` и отказывается работать, если есть 5. IP-whitelist BingX «strongly recommended». Правило про истечение ключей без IP официально не найдено. Если у ASCN есть статичный egress IP, давать его пользователю для whitelist.

Источники: https://github.com/BingX-API/api-ai-skills (authentication.md, swap-trade, swap-account, spot-trade, copytrade-swap) · https://bingx.com/en/support/articles/15401202348303 · https://cryptoslate.com/press-releases/bingx-upgrades-bot-trading-infrastructure-to-enhance-futures-strategy-flexiblity/

## 4. Что хотят пользователи и конкуренты

- **Продукты BingX:** copy trading (флагман, есть Telegram Mini App), бессрочные фьючерсы USDT-M/Coin-M, «стандартные контракты», grid/DCA-боты, демо-счёт VST.
- **Свой AI у BingX:** AI Bingo (май 2025, ассистент, по их данным 2 млн пользователей и 20 млн запросов за 100 дней), AI Master (сент. 2025, «AI-стратег» на 5 стратегиях, бэктест, алерты), AI Skills Hub (март 2026, 29 скиллов для Claude Code/Cursor с подтверждением CONFIRM на запись).
- **Пробелы для нас:**
  1. Нет готового агента в чате без IDE: Skills требуют Claude Code или Cursor.
  2. Нет кросс-аналитики «мои позиции + фандинг + OI + риски» по расписанию с отчётом.
  3. Нет API для подписчиков copy trading и для grid: помощь с выбором трейдера и сетки только советом.
  4. Нет журнала сделок и разбора ошибок на русском и других языках.
- **Конкуренты:**
  - 3Commas: Free / $20 / $50 / $140 в месяц.
  - Cryptohopper: Free / $29 / $69 / $129.
  - WunderTrading (официальный партнёр BingX с 2023): Free / $19 / $39 / $69, плюс DCA, grid, TradingView-сигналы.
  - Altrady, Gunbot; коннекторы Latenode/Pipedream.
  - Отдельных популярных TG-ботов-трейдеров для BingX не найдено.

Источники: https://bingx.com/en/support/articles/13715394523023 · https://thepaypers.com/crypto-web3-and-cbdc/news/bingx-rolls-out-ai-master-crypto-trading-strategist · https://bingx.com/en/learn/article/what-is-bingx-ai-and-how-to-get-started · https://hackernoon.com/top-10-best-ai-bot-trading-in-2026-features-and-pricing · https://comparedge.com/tools/cryptohopper/pricing · https://comparebestai.com/tools/wundertrading · https://wundertrading.com/en/bingx-trading-bot · https://www.aap.com.au/aapreleases/cision20241011ae28980

## 5. Правила и риски

- **Сторонние агенты:** запрета на сторонние API-инструменты нет. BingX рекомендует «use the BingX official API and strictly follow the request rate limits», а Broker-программа прямо задумана для внешних инструментов. Риск: в 2024 BingX ограничивал copy trading через сторонние платформы «abnormal trading». Запрещены арбитраж ради ребейтов и бонусов, а также самореферальство.
- **Брокерский код в инструменте** легален только при одобренном sourceKey. Подставлять чужой код (в том числе `BX-AI-SKILL`) нельзя.
- **Раскрытие:** в описании агента указываем, что ASCN получает от BingX долю комиссии с ордеров, отправленных агентом (ставка для пользователя не меняется). Реф-ссылку помечаем как партнёрскую.
- **Регуляторика:** США и другие запрещённые юрисдикции исключаем (гео-предупреждение в онбординге). В ЕС MiCA: BingX не CASP в ЕС, и консультирование по криптоактивам — регулируемая услуга. Агент даёт аналитику и исполняет команды пользователя, «рекомендацией» это не называем, есть дисклеймер. В РФ реклама криптовалют ограничена: не продвигать витрину как «заработок».
- **Операционные риски:** только подтверждённые пользователем ордера; `order/test` перед реальным; без ретраев на запись при неясном ответе (сначала сверка); утечка ключа = только торговые права, без вывода.

Источники: https://bingx.com/en/support/articles/11258377067407 · https://bingx.com/en/support/articles/16392168865679 · https://bingx.com/en/support/articles/12503488450575

## 6. Рекомендация

**Как встроить заработок:**
1. **Сейчас:** подать заявку API Broker (broker@bingx.com) как «AI-агент на маркетплейсе ASCN», просить пилот без порога $5M. Аргумент: BingX сам продвигает AI-скиллы и меряет их трафик через `X-SOURCE-KEY`.
2. **В коде:** единый `bingx_client.py` (stdlib), который добавляет `X-SOURCE-KEY` из константы ASCN (не из секретов пользователя) ко ВСЕМ запросам. Ключи пользователя берутся из env `BINGX_API_KEY` / `BINGX_SECRET_KEY`, те же имена, что у BingX Skills. Агент не может отправить запрос в обход клиента.
3. **Новым пользователям:** в онбординге, если аккаунта нет, даём нашу affiliate-ссылку `bingx.com/invite/<CODE>` с пометкой «партнёрская» (40–50% vs 10%).
4. **Учёт:** ежедневно по нашему брокерскому ключу (отдельный сервис ASCN, не в агенте пользователя) тянуть `agent/v1/reward/third/commissionDataList` (81/82) и `agent/v2/reward/commissionDataList`, проверять `inviteRelationCheck`. Дашборд дохода по агенту.
5. **Пока sourceKey нет:** агент работает без заголовка. Монетизация только подпиской ASCN и реф-ссылкой.

**MVP:**
1. Онбординг: язык → есть ли аккаунт (иначе реф-ссылка) → создание ключа (чтение + торговля, без вывода, IP) → `apiKey/query`, проверка прав → демо VST по желанию.
2. Рынок: цена, свечи, фандинг, OI, стакан по монете; сканер «топ фандинга и роста OI»; технический анализ (RSI, EMA, уровни).
3. Портфель: балансы всех счетов, позиции с PnL и ценой ликвидации, фандинг-расходы; ежедневный .md-отчёт.
4. Риск-гард: алерт, если до ликвидации меньше X%, если плечо выше лимита или позиции без SL; предложение поставить SL/TP.
5. Торговля по команде: market/limit, TP/SL, плечо и режим маржи, закрытие; всегда превью → `order/test` → «ПОДТВЕРДИТЬ» → ордер.
6. План сделки и журнал: вход, стоп, размер от риска в %, разбор закрытых сделок (`positionHistory`, `income`).
7. Copy trading и grid: советник по выбору трейдера и параметров сетки (без исполнения, нет API).
