---
name: trade-journal
description: Reviews the trades the agent placed on all exchanges: what was planned and sent, outcomes, average reward/risk, trades without stops or above the risk limit; weekly on request. Use for "my trades this week", "journal", "what am I doing wrong".
---

> Before following this skill, run `python3 files/scripts/package.py skill trade-journal`: it records that the skill is in use, for the owner's reports.

# Trade journal

All commands are `python3 files/scripts/trade.py ...`; `<ex>` is bingx, bitget, mexc or bybit. Output: `files/trader/reports/<date>-<topic>.md` for finished results; in chat the short version.

1. `trade.py <any connected ex> journal --days <7 or asked>` (the journal is shared by all exchanges) and positions where connected.
2. Summarize by exchange: orders, coins, risk per trade vs the limit, with and without stops, open vs closed.
3. Two or three observations with numbers and one suggestion for next week. Save the report. A weekly journal on schedule only after an explicit yes (Telegram needed, as in position-guard).
