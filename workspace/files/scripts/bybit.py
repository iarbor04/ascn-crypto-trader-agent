#!/usr/bin/env python3
"""Bybit adapter for the exchange-agent toolkit (see exkit.py for the commands). Standard library only.
API v5, Unified Trading Account: USDT perpetuals (category linear) and spot. Secrets: BYBIT_API_KEY, BYBIT_SECRET_KEY
(read + trade, never withdraw or transfer). Broker code (optional): knowledge/partner.json -> Referer header."""
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exkit  # noqa: E402
from exkit import ExchangeError, http, rnd, sign_hex  # noqa: E402

AGENT = "bybit"
EXID = "bybit"
NAME = "Bybit"
KEY_ENV = ["BYBIT_API_KEY", "BYBIT_SECRET_KEY"]
TAKER_FEE = 0.00055
BASE = "https://api.bybit.com"
TF = {"1d": "D", "4h": "240", "1h": "60"}
RECV = "5000"


def sym(coin):
    return f"{coin}USDT"


def cat(market):
    return "linear" if market == "futures" else "spot"


def pub(path, params=None):
    r = http("GET", BASE + path, params)
    if not isinstance(r, dict) or r.get("retCode") != 0:
        raise ExchangeError(f"Bybit: {r.get('retMsg') if isinstance(r, dict) else r}")
    return r.get("result") or {}


def priv(method, path, params=None, body=None):
    ts = str(int(time.time() * 1000))
    if method == "GET":
        q = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
        payload, b = q, None
    else:
        q = ""
        b = json.dumps({k: v for k, v in (body or {}).items() if v is not None}, separators=(",", ":"))
        payload = b
    key = os.environ["BYBIT_API_KEY"]
    h = {"X-BAPI-API-KEY": key, "X-BAPI-TIMESTAMP": ts, "X-BAPI-RECV-WINDOW": RECV,
         "X-BAPI-SIGN": sign_hex(os.environ["BYBIT_SECRET_KEY"], ts + key + RECV + payload), "Content-Type": "application/json"}
    broker = exkit.partner(EXID)["broker_code"]
    if broker:
        h["Referer"] = broker
    r = http(method, BASE + path, raw_query=q, body=b, headers=h)
    if not isinstance(r, dict):
        raise ExchangeError(f"Bybit: unexpected answer {str(r)[:200]}")
    if r.get("retCode") != 0:
        return {"error": r.get("retMsg") or str(r.get("retCode")), "code": r.get("retCode")}
    return {"data": r.get("result")}


def tickers(market):
    rows = []
    for x in pub("/v5/market/tickers", {"category": cat(market)}).get("list", []):
        if not x["symbol"].endswith("USDT"):
            continue
        row = {"coin": x["symbol"][:-4], "symbol": x["symbol"], "last": float(x["lastPrice"]),
               "change_pct": rnd(float(x.get("price24hPcnt") or 0) * 100), "quote_volume": float(x.get("turnover24h") or 0)}
        if market == "futures":
            row["funding_pct"] = rnd(float(x.get("fundingRate") or 0) * 100, 4)
        rows.append(row)
    return rows


def candles(coin, market, tf, limit):
    d = pub("/v5/market/kline", {"category": cat(market), "symbol": sym(coin), "interval": TF[tf], "limit": min(limit, 1000)})
    return sorted([[int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[6])] for x in d.get("list", [])])


def derivs(coin):
    t = (pub("/v5/market/tickers", {"category": "linear", "symbol": sym(coin)}).get("list") or [None])[0]
    if not t:
        raise ExchangeError(f"no {coin} perpetual on Bybit")
    res = {"funding_pct": rnd(float(t.get("fundingRate") or 0) * 100, 4), "mark_price": rnd(t.get("markPrice"), 6),
           "open_interest_usd": rnd(t.get("openInterestValue"), 6)}
    try:
        ls = pub("/v5/market/account-ratio", {"category": "linear", "symbol": sym(coin), "period": "1h", "limit": 1}).get("list") or []
        if ls and float(ls[0]["sellRatio"]):
            res["long_short_accounts"] = rnd(float(ls[0]["buyRatio"]) / float(ls[0]["sellRatio"]), 4)
    except ExchangeError:
        pass
    return res


_INFO = {}


def info(coin, market):
    k = (coin, market)
    if k not in _INFO:
        lst = pub("/v5/market/instruments-info", {"category": cat(market), "symbol": sym(coin)}).get("list") or []
        if not lst:
            raise ExchangeError(f"{coin} is not traded on Bybit {market}")
        _INFO[k] = lst[0]
    return _INFO[k]


def _qty(o):
    lot = info(o["coin"], o["market"]).get("lotSizeFilter") or {}
    step = float(lot.get("qtyStep") or lot.get("basePrecision") or 0) or None
    q = o["qty"]
    if step:
        q = round(int(q / step) * step, 10)
    return q, lot


def validate(o):
    q, lot = _qty(o)
    mn = float(lot.get("minOrderQty") or 0)
    if q < mn or q <= 0:
        return {"error": f"size too small: minimum {mn} {o['coin']} (step {lot.get('qtyStep') or lot.get('basePrecision')})"}
    return {"checked_by_exchange": False, "qty_rounded": q, "min_qty": mn,
            "note": "Bybit has no test endpoint: the exchange checks the order when it is placed"}


def place(o):
    q, _ = _qty(o)
    b = {"category": cat(o["market"]), "symbol": sym(o["coin"]), "side": "Buy" if o["side"] == "buy" else "Sell",
         "orderType": "Market" if o["type"] == "market" else "Limit", "qty": str(q)}
    if o["type"] == "limit":
        b.update(price=str(o["price"]), timeInForce="GTC")
    if o["market"] == "futures":
        if o.get("leverage"):
            set_leverage(o["coin"], o["leverage"])
        b["positionIdx"] = 0
        if o.get("reduce_only"):
            b["reduceOnly"] = True
        if o.get("stop"):
            b["stopLoss"] = str(o["stop"])
        if o.get("take"):
            b["takeProfit"] = str(o["take"])
    else:
        b["marketUnit"] = "baseCoin"
    r = priv("POST", "/v5/order/create", body=b)
    if r.get("error") and o["market"] == "futures" and "position idx" in str(r["error"]).lower():
        b["positionIdx"] = (1 if o["side"] == "buy" else 2) if not o.get("reduce_only") else (2 if o["side"] == "buy" else 1)
        r = priv("POST", "/v5/order/create", body=b)  # hedge-mode account
    if r.get("error"):
        return r
    return {"order_id": (r["data"] or {}).get("orderId"), "qty_sent": q}


def cancel(coin, oid, market):
    return priv("POST", "/v5/order/cancel", body={"category": cat(market), "symbol": sym(coin), "orderId": oid})


def open_orders(market):
    p = {"category": cat(market)}
    if market == "futures":
        p["settleCoin"] = "USDT"
    r = priv("GET", "/v5/order/realtime", p)
    if r.get("error"):
        raise ExchangeError(r["error"])
    return {"market": market, "orders": (r["data"] or {}).get("list", [])}


def balance():
    r = priv("GET", "/v5/account/wallet-balance", {"accountType": "UNIFIED"})
    if r.get("error"):
        return {"error": r["error"], "hint": "Bybit keys of a classic (non-unified) account may need accountType CONTRACT/SPOT."}
    acc = ((r["data"] or {}).get("list") or [{}])[0]
    return {"account": "unified", "equity_usd": rnd(acc.get("totalEquity")), "available_usd": rnd(acc.get("totalAvailableBalance")),
            "coins": [{"asset": c["coin"], "balance": rnd(c.get("walletBalance")), "usd": rnd(c.get("usdValue")),
                       "unrealized_pnl": rnd(c.get("unrealisedPnl"))} for c in acc.get("coin", []) if float(c.get("walletBalance") or 0)]}


def positions():
    r = priv("GET", "/v5/position/list", {"category": "linear", "settleCoin": "USDT"})
    if r.get("error"):
        raise ExchangeError(r["error"])
    rows = []
    for x in (r["data"] or {}).get("list", []):
        if not float(x.get("size") or 0):
            continue
        mark, liq = float(x.get("markPrice") or 0), float(x.get("liqPrice") or 0)
        rows.append({"coin": x["symbol"].replace("USDT", ""), "side": x.get("side"), "qty": rnd(x.get("size")),
                     "entry": rnd(x.get("avgPrice"), 6), "mark": rnd(mark, 6), "leverage": x.get("leverage"),
                     "unrealized_pnl": rnd(x.get("unrealisedPnl")), "liquidation": rnd(liq, 6),
                     "to_liquidation_pct": rnd(abs(mark - liq) / mark * 100, 3) if mark and liq else None,
                     "stop": x.get("stopLoss") or None, "take": x.get("takeProfit") or None})
    return {"positions": rows}


def set_leverage(coin, lev):
    r = priv("POST", "/v5/position/set-leverage", body={"category": "linear", "symbol": sym(coin),
                                                         "buyLeverage": str(int(lev)), "sellLeverage": str(int(lev))})
    err = r.get("error")
    return {"leverage": int(lev), "result": "ok" if not err or "not modified" in str(err).lower() else err}


def keycheck():
    r = priv("GET", "/v5/user/query-api")
    if r.get("error"):
        return {"checked": False, "error": r["error"]}
    d = r["data"] or {}
    perms = d.get("permissions") or {}
    flat = {k: v for k, v in perms.items() if v}
    withdraw = bool(perms.get("Withdraw")) or any("withdraw" in str(v).lower() for v in perms.values())
    transfer = any("transfer" in str(v).lower() for v in perms.values())
    return {"checked": True, "permissions": flat, "read_only": d.get("readOnly") == 1, "withdraw": withdraw,
            "transfer": transfer, "ip_whitelist": d.get("ips")}


if __name__ == "__main__":
    exkit.main(sys.modules[__name__])
