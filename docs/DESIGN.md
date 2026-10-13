# Design decisions

- Owner request 2026-10-13: merge the exchange agents into one agent for four exchanges (BingX, Bitget, MEXC, Bybit) so a user doesn't pay for a workspace per exchange; at the start the agent proposes which exchange to connect. Bybit without a broker code (owner: «байбит апи без брокерского кода подойдёт»); the Referer header field stays available in partner.json.
- One data folder files/trader for all exchanges; previews remember their exchange and cannot be placed on another one.
- trade.py dispatches to adapters; exkit.py is the shared core (same as in the single-exchange repos).
- Pipedream coverage: BingX full, Bitget spot only, MEXC none, Bybit no app: keys in Secrets cover all four.
- Private endpoints follow official docs and were not exercised without real keys.
