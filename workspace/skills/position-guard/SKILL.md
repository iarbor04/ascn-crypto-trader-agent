---
name: position-guard
description: Watches open positions on all connected exchanges and warns when one gets close to liquidation, loses more than a set amount, or has no stop; on a schedule only after the user's explicit yes. Use for "watch my positions", "warn me before liquidation", "stop watching".
---

> Before following this skill, run `python3 files/scripts/package.py skill position-guard`: it records that the skill is in use, for the owner's reports.

# Position guard

All commands are `python3 files/scripts/trade.py ...`; `<ex>` is bingx, bitget, mexc or bybit. Output: `files/trader/reports/<date>-<topic>.md` for finished results; in chat the short version.

1. Agree on thresholds: distance to liquidation (default 10%), loss per position, how often (default every hour; never more often than every 15 minutes). Save them to the profile.
2. One check now: `trade.py <ex> positions` for each connected exchange.
3. On ASCN, scheduled results are delivered to Telegram and the platform refuses a schedule until Telegram is connected in Channels: say so before asking for the yes and start the Connect step if needed. Only after an explicit yes (and Telegram connected), create one cron task with the prompt: "For each exchange in files/trader/profile/trader-profile.md marked connected, run python3 files/scripts/trade.py <exchange> positions. If no position is closer to liquidation than <N>% and none lost more than <limit>, send nothing. Otherwise one short message per risky position: exchange, coin, side, mark, liquidation, distance, PnL, and the options. Never act on the account."
4. Stopping: remove the task on request and confirm.

## Rules
- The guard warns; it never closes, reduces or adds margin by itself.
