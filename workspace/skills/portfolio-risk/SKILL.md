---
name: portfolio-risk
description: Shows the user's accounts on every connected exchange: balances, open positions with entry, mark, PnL, leverage and distance to liquidation, open orders, and the risk picture (exposure, concentration, positions without a stop) in one table. Use for "my portfolio", "my positions", "am I at risk". Do not use for opening trades.
---

> Before following this skill, run `python3 files/scripts/package.py skill portfolio-risk`: it records that the skill is in use, for the owner's reports.

# Portfolio risk

All commands are `python3 files/scripts/trade.py ...`; `<ex>` is bingx, bitget, mexc or bybit. Output: `files/trader/reports/<date>-<topic>.md` for finished results; in chat the short version.

1. `trade.py exchanges` to see which are connected; for each connected one: `trade.py <ex> balance`, `positions`, `orders`.
2. One table across exchanges: exchange, coin, side, size, entry, mark, PnL, leverage, liquidation and distance.
3. Flag: any position closer than 10% to liquidation; positions without a stop; one coin > 40% of exposure; the same coin on two exchanges in opposite directions.
4. Options for each flag (add margin, reduce, set a stop) with numbers; the user decides. Offer position-guard. Save the report.
