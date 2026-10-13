---
name: market-brief
description: A short overview of the market now on the user's exchange or across all four: biggest movers with real volume, most traded coins, extreme funding, and where one coin trades cheaper or with different funding on another exchange. Use for "what's moving", "market overview", "morning brief", "where is funding highest". Do not use for one coin in depth (coin-analysis).
---

> Before following this skill, run `python3 files/scripts/package.py skill market-brief`: it records that the skill is in use, for the owner's reports.

# Market brief

All commands are `python3 files/scripts/trade.py ...`; `<ex>` is bingx, bitget, mexc or bybit. Output: `files/trader/reports/<date>-<topic>.md` for finished results; in chat the short version.

1. On the user's default exchange: `trade.py <ex> movers --sort change --limit 15`, `--sort volume --limit 10`, `--sort funding --limit 10` (add `--market spot` for spot traders).
2. For the 2–3 coins that stand out, `trade.py compare <COIN>`: price, change, volume and funding on all four exchanges.
3. Pick at most 8 items: big moves on real volume (skip tiny volume), the most traded coins, crowded funding (very positive = longs pay; very negative = shorts pay), a funding or price gap between exchanges.
4. One line each with numbers and the fetch time. Offer: analyse a coin, or a trade plan. Save the report.
