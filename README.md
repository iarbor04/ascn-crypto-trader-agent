# ascn-crypto-trader-agent — crypto trading assistant (BingX, Bitget, MEXC, Bybit)

One ASCN agent for four exchanges: onboarding proposes which exchange to connect, market overview and cross-exchange comparison, coin analysis, trade plans sized from risk, orders only after the user's yes, positions and liquidation control on every connected exchange, trade journal.

| Skill | What it does |
|---|---|
| `exchange-onboarding` | First conversation: introduces the trading assistant in plain words, explains that one assistant works with four exchanges (BingX, Bitget, MEXC, Bybit) so the user does not need a separate agent or workspace per exchange, finds out where the user already trades, proposes which exchange to connect first (and gives the partner link only to someone without an account), connects it, checks the key's rights, sets the risk limits and shows a first useful result |
| `market-brief` | A short overview of the market now on the user's exchange or across all four: biggest movers with real volume, most traded coins, extreme funding, and where one coin trades cheaper or with different funding on another exchange |
| `coin-analysis` | Analysis of one coin: trend by moving averages, volatility (ATR), nearest support and resistance from swing points, 7 and 30 day change, volume vs average, funding and open interest, plus the same coin on the four exchanges, with scenarios and the levels that cancel them |
| `trade-setup` | Builds a trade on the chosen exchange from the user's idea: entry, stop, takes, size from their risk, leverage, margin, approximate liquidation, reward-to-risk and fees; shows it in plain words; after the user's explicit yes places the order with stop and take on that exchange, then reads it back |
| `portfolio-risk` | Shows the user's accounts on every connected exchange: balances, open positions with entry, mark, PnL, leverage and distance to liquidation, open orders, and the risk picture (exposure, concentration, positions without a stop) in one table |
| `position-guard` | Watches open positions on all connected exchanges and warns when one gets close to liquidation, loses more than a set amount, or has no stop; on a schedule only after the user's explicit yes |
| `trade-journal` | Reviews the trades the agent placed on all exchanges: what was planned and sent, outcomes, average reward/risk, trades without stops or above the risk limit; weekly on request |

Scripts: `trade.py` (entry: `exchanges`, `compare`, `<exchange> <command>`), `exkit.py` (shared core), adapters `bingx.py`, `bitget.py`, `mexc.py`, `bybit.py`. Partner settings per exchange: `workspace/knowledge/partner.json`.

Install: `marketplace/install-or-update-public.md`; start prompt `marketplace/startup-task.md`; soul `marketplace/soul-intro.md`. Source of truth: `exchange-agents/kit/` (`make_trader.py`).
