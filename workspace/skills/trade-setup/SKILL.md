---
name: trade-setup
description: Builds a trade on the chosen exchange from the user's idea: entry, stop, takes, size from their risk, leverage, margin, approximate liquidation, reward-to-risk and fees; shows it in plain words; after the user's explicit yes places the order with stop and take on that exchange, then reads it back. Use for "open a long on SOL", "short ETH on Bybit", "buy 0.1 BTC on MEXC", "place the order". Do not use for analysis only.
---

> Before following this skill, run `python3 files/scripts/package.py skill trade-setup`: it records that the skill is in use, for the owner's reports.

# Trade setup

All commands are `python3 files/scripts/trade.py ...`; `<ex>` is bingx, bitget, mexc or bybit. Output: `files/trader/reports/<date>-<topic>.md` for finished results; in chat the short version.

### 1. Exchange
The exchange the user names; otherwise the default; if the coin is not traded there, say so and propose one where it is (`trade.py compare <COIN>`).
A plan and a preview need no key and no connection: always build them from public prices and the balance the user gives. Only placing the order needs the exchange connected; if it is not, show the full plan and preview first, then explain in 2–3 lines how to connect that exchange, and place after it is connected and the user said yes.

### 2. Plan
- Side, coin, entry (market or price), stop. No stop given: propose one from `analyze` (beyond the nearest level, at least 1 ATR away) and say why. Never plan a futures trade without a stop.
- Balance: `trade.py <ex> balance` if connected; otherwise ask.
- `trade.py <ex> plan <COIN> --side long|short --entry <price|market> --stop <price> --take <t1> [t2] --balance <usd> --risk-pct <from settings> --leverage <L>`.
- Say every `warnings` item: liquidation before the stop, risk above 3%, leverage above the limit, margin above balance.

### 3. Preview
`trade.py <ex> order preview <COIN> --side buy|sell --qty <qty from plan> [--type limit --price P] --stop <stop> --take <take> --leverage <L>`. Show in plain words: exchange, what, how much (the size after the exchange's rounding), price, stop, take, dollars at risk, leverage. Ask: «Выставляю на <биржа>? Ответь «да», чтобы отправить ордер.»

### 4. Place only after an explicit yes
- A clear «да» / «yes» / «выставляй» to this exact order. Anything else = no; change the plan and preview again.
- `trade.py <ex> order place <pending_id>` (or the connector action if the user chose the connector on BingX/Bitget spot).
- Then `trade.py <ex> orders` and `trade.py <ex> positions` to confirm what is on the exchange. Report the order id and state. If the answer was unclear, check the orders before any retry; never send twice.

## Rules
- One yes = one order on one exchange. A new order, size or exchange needs a new preview and a new yes.
- Never raise leverage or size on your own; never move a stop further away unless the user asks explicitly.
