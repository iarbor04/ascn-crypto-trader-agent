# Торговый помощник (Bybit, BingX, Bitget, MEXC): тексты маркетплейса

## Поля формы

- **name_ru:** Торговый ИИ-помощник для Bybit, BingX, Bitget и MEXC
- **name_en:** AI Crypto Trading Assistant for Bybit, BingX, Bitget & MEXC
- **slug:** ai-crypto-trading-bot
- **cat_ru / cat_en:** Крипто, трейдинг / Crypto, Trading
- **integrations:** Bybit, BingX, Bitget, MEXC
- **related:** Скринер криптовалют, Аналитика Polymarket
- **short_ru:** Торговый ИИ-помощник сразу для четырёх бирж: разбирает монету, считает сделку со стопом и объёмом под ваш риск и выставляет ордер на Bybit, BingX, Bitget или MEXC только после вашего «да».
- **short_en:** An AI trading assistant for four exchanges at once: analyses a coin, sizes a trade with a stop to fit your risk and places the order on Bybit, BingX, Bitget or MEXC only after your yes.
- **seo_title_ru:** Торговый бот для Bybit, BingX, Bitget и MEXC с ИИ
- **seo_title_en:** AI Crypto Trading Bot: Bybit, BingX, Bitget, MEXC
- **seo_desc_ru:** Торговый бот с ИИ: план сделки со стопом, объём от риска, цена ликвидации, сравнение бирж. Ордер на Bybit, BingX, Bitget и MEXC только после вашего «да».
- **seo_desc_en:** AI crypto trading bot for Bybit, BingX, Bitget and MEXC: trade plans with a stop, position size from your risk, liquidation price. Orders only after your yes.

## Страница агента (RU)

### Заголовок

**Торговый бот с ИИ для Bybit, BingX, Bitget и MEXC: сделка со стопом под ваш риск, ордер только после вашего «да»**

Один помощник работает сразу с четырьмя биржами, поэтому ставить отдельного агента на каждую биржу не нужно. Он разбирает монету, сравнивает её на четырёх биржах, считает объём позиции от вашего риска и цену ликвидации, а ордер отправляет только после вашего подтверждения.

### Пример работы

Внутренний тест ASCN, 13 октября. Пользователь написал: «хочу лонг соланы на Bybit, стоп 100, баланс 1000, риск 1%, плечо 5». Помощник посчитал:

- объём 1,646 SOL по цене около 106 $;
- при срабатывании стопа убыток 10 $, это 1% депозита;
- маржа 34,88 $, примерная цена ликвидации около 85,3 $, то есть ниже стопа;
- два тейка от ближайших уровней сопротивления и соотношение прибыли к риску для каждого.

Ордер он выставляет только после «да». Без подключённой биржи всё равно показывает полный план и объясняет, как подключиться.

В том же тесте на просьбу «слил депо, дай плечо 50, чтобы отбить» он отказал. И показал на цифрах, что при плече 50 ликвидация наступает уже на ходе цены около 2%.

### Для кого

- Тем, кто торгует фьючерсами на Bybit, BingX, Bitget или MEXC и хочет каждую сделку со стопом и понятным риском
- Тем, у кого аккаунты на нескольких биржах и кто хочет видеть все позиции в одном месте
- Новичкам, которые выбирают биржу: помощник предложит подходящую под их задачу

### Что вы получите

- **План сделки:** вход, стоп, тейки, объём от процента риска, плечо, маржа, примерная цена ликвидации, комиссии
- **Ордер со стопом и тейком:** отправляется после вашего «да», после этого помощник проверяет, что ордер встал
- **Сравнение бирж:** цена, объём и фандинг монеты на Bybit, BingX, Bitget и MEXC в одной таблице
- **Разбор монеты:** тренд, уровни поддержки и сопротивления, волатильность, фандинг и открытый интерес
- **Портфель:** балансы и позиции на всех подключённых биржах, расстояние до ликвидации, позиции без стопа
- **Слежка за позициями:** предупреждение до ликвидации, по расписанию и после вашего «да»
- **Журнал сделок:** разбор ошибок за неделю

### Как начать

1. **Скажите, где у вас аккаунты.** Если аккаунта нет, помощник предложит одну биржу под вашу задачу.
2. **Подключите биржу.** Через Интеграции или API-ключ в Секретах, только с правами на чтение и торговлю, без вывода.
3. **Задайте риск.** Например, 1% депозита на сделку и максимальное плечо.
4. **Назовите идею сделки.** Помощник покажет план и предпросмотр ордера.
5. **Ответьте «да».** Ордер уходит на биржу, помощник проверяет, что он встал.

### Чего помощник не делает

- Не торгует сам, без подтверждения и по расписанию
- Не выводит и не переводит деньги и не принимает ключи с правом вывода
- Не обещает прибыль и не называет сделку безопасной
- Не помогает отыгрываться и не поднимает плечо и объём сам
- Не помогает обходить ограничения бирж по странам

### Что подключить

Биржи, на которых вы торгуете. Подключаются через Интеграции или API-ключ в Секретах, только с правами на чтение и торговлю. Для предупреждений по расписанию нужен Telegram в разделе «Каналы».

### Вопросы

**Это торговый бот, который торгует сам?** Нет. Помощник считает сделку и выставляет ордер только после вашего «да». Каждый ордер подтверждаете вы.

**Какие биржи поддерживаются?** Bybit, BingX, Bitget и MEXC, фьючерсы на USDT и спот. Одной установки хватает на все четыре.

**Нужно подключать все биржи?** Нет. Подключите только те, на которых торгуете. Разбор монет и планы сделок работают и без подключения.

**Как считается объём позиции?** От процента риска: если стоп сработает, вы потеряете ровно ту долю депозита, которую задали. Помощник также показывает, не наступит ли ликвидация раньше стопа.

**Что с безопасностью ключей?** Ключ нужен только с правами на чтение и торговлю. Если у ключа есть право вывода, помощник откажется с ним работать.

## Agent page (EN)

### Headline

**AI crypto trading bot for Bybit, BingX, Bitget and MEXC: every trade with a stop sized to your risk, orders only after your yes**

One assistant works with four exchanges, so you don't need a separate agent for each. It analyses a coin, compares it across the four exchanges, sizes the position from your risk with the liquidation price, and sends the order only after you confirm.

### What it looks like

Internal ASCN test, October 13. «Long SOL on Bybit, stop 100, balance 1000, 1% risk, 5x». The assistant sized 1.646 SOL at about $106: a stop-out loses $10 (1% of the balance), margin $34.88, approximate liquidation around $85.3, below the stop, with two takes from the nearest resistance levels. The order goes out only after a yes. Asked for 50x leverage to win back a loss, it declined and showed that liquidation would come after a move of about 2%.

### What you get

Trade plans with stop, takes, size from risk, leverage, margin and liquidation price; orders with stop and take after your yes; a cross-exchange table of price, volume and funding; coin analysis with levels; balances and positions on every connected exchange; liquidation alerts on a schedule; a weekly trade journal.

### What it won't do

Trade on its own or on a schedule, withdraw or transfer funds, accept keys with withdrawal rights, promise profit, help chase losses or get around exchange restrictions.

### FAQ

**Does it trade by itself?** No. Every order needs your yes.

**Which exchanges?** Bybit, BingX, Bitget and MEXC, USDT perpetuals and spot. One install covers all four.
