---
name: coin-analysis
description: Analysis of one coin: trend by moving averages, volatility (ATR), nearest support and resistance from swing points, 7 and 30 day change, volume vs average, funding and open interest, plus the same coin on the four exchanges, with scenarios and the levels that cancel them. Use for "analyse SOL", "where are the levels", "where to trade SOL". Do not use for placing a trade (trade-setup).
---

> Before following this skill, run `python3 files/scripts/package.py skill coin-analysis`: it records that the skill is in use, for the owner's reports.

# Coin analysis

All commands are `python3 files/scripts/trade.py ...`; `<ex>` is bingx, bitget, mexc or bybit. Output: `files/trader/reports/<date>-<topic>.md` for finished results; in chat the short version.

1. `trade.py <ex> analyze <COIN> --tf 1d` on the user's exchange (or the one with the most volume), and `--tf 4h` for a shorter view.
2. `trade.py compare <COIN>`: where it trades, price differences, funding on each exchange.
3. Write: trend; position in the 30-day range; nearest supports and resistances with distance in %; ATR in %; funding and open interest; which exchange has the deepest market for it.
4. Scenarios up / sideways / down, each with the confirming and the cancelling level. No promises.
5. If the user wants to trade: offer a plan (trade-setup). Save the report.
