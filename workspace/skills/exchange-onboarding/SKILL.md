---
name: exchange-onboarding
description: First conversation: introduces the trading assistant in plain words, explains that one assistant works with four exchanges (BingX, Bitget, MEXC, Bybit) so the user does not need a separate agent or workspace per exchange, finds out where the user already trades, proposes which exchange to connect first (and gives the partner link only to someone without an account), connects it, checks the key's rights, sets the risk limits and shows a first useful result. Use for a new user, an empty profile, "what can you do", "how do I connect", "which exchange is better". Do not use when the user already asks about a coin or a trade.
---

> Before following this skill, run `python3 files/scripts/package.py skill exchange-onboarding`: it records that the skill is in use, for the owner's reports.

# Exchange onboarding

All commands are `python3 files/scripts/trade.py ...`; `<ex>` is bingx, bitget, mexc or bybit. Output: `files/trader/reports/<date>-<topic>.md` for finished results; in chat the short version.

### 1. Check
`python3 files/scripts/trade.py exchanges` (which are connected, default, partner links) and `python3 files/scripts/trade.py <any> context` if a default exists. If the profile is filled, say what is connected and ask what to do.

### 2. Intro (first message only)
First line: how the user gains: trades with a plan, a stop and a size that fit their risk, fewer liquidations, less time at the screen. Second line: «Работаю сразу с четырьмя биржами — BingX, Bitget, MEXC и Bybit — в одном месте: отдельный агент на каждую биржу не нужен.» Then 4–5 lines, one per line with an emoji: market overview and comparison across exchanges, coin analysis with levels, a trade plan with stop and take, placing the order after their yes, portfolio and liquidation control on all connected exchanges. One line: nothing is placed without their explicit yes.

### 3. Questions (numbered, all skippable, in the same reply)
1. On which of these exchanges do you already have an account: BingX, Bitget, MEXC, Bybit?
2. What do you trade: futures, spot or both? Usual leverage?
3. How much of the balance are you ready to risk on one trade (1% is a common choice)?

### 4. Propose the exchange to connect
- The user has accounts: propose connecting the one they trade on most; others can be added later in the same workspace.
- The user has no account: propose one exchange that fits what they said, using `good_for` from `trade.py exchanges` (memecoins and new listings → MEXC; deep futures → Bybit; copy trading → Bitget or BingX; most users from CIS → BingX). One exchange, one reason. If that exchange has a `referral_link`, give it once with: «Это партнёрская ссылка ASCN: если зарегистрируешься по ней, ASCN получит часть комиссии биржи, для тебя условия не меняются.» Never offer a link for an exchange where the user already has an account.
- Connecting: the table in AGENTS.md («Connecting an exchange»): the connector where it covers the job, otherwise a key in Settings -> Secrets with read and trade rights only. Then `trade.py <exchange> keycheck`; if withdrawals or transfers are enabled, stop and ask for a new key.
- Save `default_exchange` in `files/trader/settings.json` and the list of connected exchanges in the profile.

### 5. First useful result
If connected: balances and positions (`trade.py <exchange> balance`, `positions`). If not: `trade.py <exchange> movers --limit 5` on the proposed exchange.
