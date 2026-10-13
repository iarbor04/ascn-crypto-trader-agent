#!/usr/bin/env python3
"""Crypto trading assistant: one entry point for four exchanges (BingX, Bitget, MEXC, Bybit). Standard library only.

  python3 files/scripts/trade.py exchanges                 which exchanges are connected (keys in Secrets), the user's
                                                           default, what each is good for, partner link present or not
  python3 files/scripts/trade.py compare <COIN> [--market futures|spot]
                                                           price, 24 h change, volume and funding of a coin on all four
  python3 files/scripts/trade.py <exchange> <command> ...  any toolkit command on one exchange, e.g.
                                                           trade.py bybit analyze SOL --tf 4h
                                                           trade.py bingx plan SOL --side long --stop 100 --balance 1000
                                                           trade.py bitget order preview SOL --side buy --qty 1 --stop 100
                                                           Commands: context, movers, analyze, plan, order preview|place|cancel,
                                                           orders, balance, positions, leverage, keycheck, journal, partner,
                                                           report-path (see exkit.py)
  <exchange> may be omitted: the default from files/trader/settings.json ("default_exchange") is used.
"""
import importlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import exkit  # noqa: E402

EXCHANGES = {
    "bingx": "BingX: futures with many altcoins, copy trading on the site, works for most CIS users",
    "bitget": "Bitget: futures and the biggest copy-trading section, spot",
    "mexc": "MEXC: earliest listings of new and meme coins, many small coins, low spot fees",
    "bybit": "Bybit: deep futures liquidity, unified account for spot and futures",
}
ALIASES = {"bing": "bingx", "bingx": "bingx", "bitget": "bitget", "mexc": "mexc", "mex": "mexc", "bybit": "bybit", "by": "bybit"}


def load(ex):
    m = importlib.import_module(ex)
    m.DATA = "trader"  # one data folder for all exchanges
    return m


def settings():
    return exkit.read_json(exkit.ROOT / "files" / "trader" / "settings.json", {})


def cmd_exchanges():
    s = settings()
    rows = []
    for ex, note in EXCHANGES.items():
        m = load(ex)
        p = exkit.partner(ex)
        rows.append({"exchange": m.NAME, "id": ex, "key_in_secrets": all(os.environ.get(k) for k in m.KEY_ENV),
                     "secret_names": m.KEY_ENV, "good_for": note, "referral_link": p["referral_link"],
                     "broker_code_set": bool(p["broker_code"])})
    exkit.out({"ok": True, "default_exchange": s.get("default_exchange"), "exchanges": rows,
               "note": "One workspace serves all four exchanges: connect only the ones the user trades on."})


def cmd_compare(coin, market):
    coin = coin.upper()

    def one(ex):
        m = load(ex)
        try:
            t = next((r for r in m.tickers(market) if r["coin"] == coin), None)
            return {"exchange": m.NAME, **(t or {"note": "not traded here"})}
        except exkit.ExchangeError as e:
            return {"exchange": m.NAME, "error": str(e)}
    with ThreadPoolExecutor(4) as pool:
        rows = list(pool.map(one, EXCHANGES))
    prices = [r["last"] for r in rows if r.get("last")]
    res = {"ok": True, "coin": coin, "market": market, "fetched_at": exkit.now().isoformat(timespec="seconds"), "rows": rows}
    if len(prices) >= 2:
        res["price_spread_pct"] = exkit.rnd((max(prices) / min(prices) - 1) * 100, 3)
    exkit.out(res)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "exchanges":
        return cmd_exchanges()
    if args[0] == "compare":
        if len(args) < 2:
            exkit.fail("compare needs a coin")
        market = args[args.index("--market") + 1] if "--market" in args else "futures"
        return cmd_compare(args[1], market)
    ex = ALIASES.get(args[0].lower())
    if ex:
        args = args[1:]
    else:
        ex = settings().get("default_exchange")
        if not ex:
            exkit.fail("say which exchange: bingx, bitget, mexc or bybit (no default exchange set yet)")
    sys.argv = [f"trade.py {ex}"] + args
    exkit.main(load(ex))


if __name__ == "__main__":
    main()
