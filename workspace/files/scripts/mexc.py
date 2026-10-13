#!/usr/bin/env python3
"""MEXC adapter for the exchange-agent toolkit (see exkit.py for the commands). Standard library only.
Spot API v3 and USDT-M futures (contract) API. Secrets: MEXC_API_KEY, MEXC_SECRET_KEY (read + trade, never withdraw).
Broker code: knowledge/partner.json -> header `source` on every private request.
Futures order sizes are in contracts; the adapter converts coin quantity using the contract size."""
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exkit  # noqa: E402
from exkit import ExchangeError, http, rnd, sign_hex  # noqa: E402

AGENT = "mexc"
EXID = "mexc"
NAME = "MEXC"
KEY_ENV = ["MEXC_API_KEY", "MEXC_SECRET_KEY"]
TAKER_FEE = 0.0008  # API futures taker since 2026-06-01 (spot taker is lower); used for planning only
SPOT = "https://api.mexc.com"
FUT = "https://contract.mexc.com"
TF_FUT = {"1d": "Day1", "4h": "Hour4", "1h": "Min60"}
TF_SPOT = {"1d": "1d", "4h": "4h", "1h": "60m"}
SECS = {"1d": 86400, "4h": 14400, "1h": 3600}


def fsym(coin):
    return f"{coin}_USDT"


def ssym(coin):
    return f"{coin}USDT"


def fpub(path, params=None):
    r = http("GET", FUT + path, params)
    if not isinstance(r, dict) or not r.get("success", r.get("code") == 0):
        raise ExchangeError(f"MEXC futures: {r.get('message') if isinstance(r, dict) else r}")
    return r.get("data")


def spub(path, params=None):
    r = http("GET", SPOT + path, params)
    if isinstance(r, dict) and r.get("code") not in (None, 0, 200):
        raise ExchangeError(f"MEXC spot: {r.get('msg')}")
    return r


def _broker():
    b = exkit.partner(EXID)["broker_code"]
    return {"source": b} if b else {}


def spriv(method, path, params=None):
    p = {k: v for k, v in (params or {}).items() if v is not None}
    p["timestamp"] = int(time.time() * 1000)
    p.setdefault("recvWindow", 5000)
    q = urllib.parse.urlencode(p)
    q += "&signature=" + sign_hex(os.environ["MEXC_SECRET_KEY"], q)
    r = http(method, SPOT + path, raw_query=q, headers={"X-MEXC-APIKEY": os.environ["MEXC_API_KEY"], **_broker()})
    if isinstance(r, dict) and r.get("code") not in (None, 0, 200) and "msg" in r:
        return {"error": r.get("msg"), "code": r.get("code")}
    return {"data": r}


def fpriv(method, path, params=None, body=None):
    ts = str(int(time.time() * 1000))
    if method == "GET":
        p = {k: v for k, v in (params or {}).items() if v is not None}
        ps = "&".join(f"{k}={p[k]}" for k in sorted(p))
        q, b = ps, None
    else:
        ps = json.dumps(body or {}, separators=(",", ":"))
        q, b = "", ps
    sig = sign_hex(os.environ["MEXC_SECRET_KEY"], os.environ["MEXC_API_KEY"] + ts + ps)
    h = {"ApiKey": os.environ["MEXC_API_KEY"], "Request-Time": ts, "Signature": sig, "Content-Type": "application/json", **_broker()}
    r = http(method, FUT + path, raw_query=q, body=b, headers=h)
    if not isinstance(r, dict):
        raise ExchangeError(f"MEXC: unexpected answer {str(r)[:200]}")
    if not r.get("success"):
        return {"error": r.get("message") or str(r.get("code")), "code": r.get("code")}
    return {"data": r.get("data")}


_DETAIL = {}


def detail(coin):
    if coin not in _DETAIL:
        d = fpub("/api/v1/contract/detail", {"symbol": fsym(coin)}) or {}
        if not d:
            raise ExchangeError(f"no {coin} perpetual on MEXC")
        _DETAIL[coin] = d
    return _DETAIL[coin]


def tickers(market):
    if market == "futures":
        return [{"coin": x["symbol"][:-5], "symbol": x["symbol"], "last": float(x["lastPrice"]),
                 "change_pct": rnd(float(x.get("riseFallRate") or 0) * 100), "quote_volume": float(x.get("amount24") or 0),
                 "funding_pct": rnd(float(x.get("fundingRate") or 0) * 100, 4)}
                for x in fpub("/api/v1/contract/ticker") or [] if x["symbol"].endswith("_USDT")]
    return [{"coin": x["symbol"][:-4], "symbol": x["symbol"], "last": float(x["lastPrice"]),
             "change_pct": rnd(float(x.get("priceChangePercent") or 0) * 100), "quote_volume": float(x.get("quoteVolume") or 0)}
            for x in spub("/api/v3/ticker/24hr") or [] if x["symbol"].endswith("USDT")]


def candles(coin, market, tf, limit):
    if market == "futures":
        d = fpub(f"/api/v1/contract/kline/{fsym(coin)}", {"interval": TF_FUT[tf], "start": int(time.time()) - SECS[tf] * limit}) or {}
        return [[int(t) * 1000, float(o), float(h), float(l), float(c), float(a)]
                for t, o, h, l, c, a in zip(d.get("time", []), d.get("open", []), d.get("high", []), d.get("low", []),
                                            d.get("close", []), d.get("amount", []))]
    d = spub("/api/v3/klines", {"symbol": ssym(coin), "interval": TF_SPOT[tf], "limit": limit}) or []
    return sorted([[int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[7])] for x in d])


def derivs(coin):
    t = fpub("/api/v1/contract/ticker", {"symbol": fsym(coin)}) or {}
    d = detail(coin)
    return {"funding_pct": rnd(float(t.get("fundingRate") or 0) * 100, 4), "fair_price": rnd(t.get("fairPrice"), 6),
            "open_interest_usd": rnd(float(t.get("holdVol") or 0) * float(d.get("contractSize") or 0) * float(t.get("lastPrice") or 0), 6),
            "max_leverage": d.get("maxLeverage"), "note": "MEXC has no public long/short ratio"}


def _contracts(o):
    d = detail(o["coin"])
    vol = round(o["qty"] / float(d["contractSize"]))
    return vol, d


def validate(o):
    if o["market"] == "futures":
        vol, d = _contracts(o)
        if vol < float(d.get("minVol") or 1):
            return {"error": f"size too small: {o['qty']} {o['coin']} is {vol} contracts, minimum {d.get('minVol')}",
                    "contract_size": d["contractSize"]}
        return {"checked_by_exchange": False, "contracts": vol, "contract_size": d["contractSize"],
                "note": "MEXC futures have no test endpoint; API futures need a KYC-verified account"}
    if not all(os.environ.get(k) for k in KEY_ENV):
        return {"checked_by_exchange": False, "note": "no key in Secrets: the exchange will check the order when it is placed"}
    r = spriv("POST", "/api/v3/order/test", _spot_params(o))
    return {"checked_by_exchange": True, **({"error": r["error"]} if r.get("error") else {"result": "test order accepted"})}


def _spot_params(o):
    p = {"symbol": ssym(o["coin"]), "side": o["side"].upper(), "type": o["type"].upper()}
    if o["type"] == "limit":
        p.update(price=o["price"], quantity=o["qty"])
    elif o["side"] == "buy":
        p["quoteOrderQty"] = round(o["qty"] * o["ref_price"], 2)
    else:
        p["quantity"] = o["qty"]
    return p


def place(o):
    if o["market"] == "spot":
        r = spriv("POST", "/api/v3/order", _spot_params(o))
        if r.get("error"):
            return r
        return {"order_id": (r["data"] or {}).get("orderId"), "raw": r["data"]}
    vol, d = _contracts(o)
    opening = not o.get("reduce_only")
    side = (1 if o["side"] == "buy" else 3) if opening else (2 if o["side"] == "buy" else 4)
    b = {"symbol": fsym(o["coin"]), "vol": vol, "side": side, "type": 5 if o["type"] == "market" else 1, "openType": 2,
         "leverage": int(o.get("leverage") or 1), "price": o.get("price") or o["ref_price"]}
    if o.get("stop"):
        b["stopLossPrice"] = o["stop"]
    if o.get("take"):
        b["takeProfitPrice"] = o["take"]
    r = fpriv("POST", "/api/v1/private/order/submit", body=b)
    if r.get("error"):
        return r
    return {"order_id": r["data"], "contracts": vol}


def cancel(coin, oid, market):
    if market == "futures":
        return fpriv("POST", "/api/v1/private/order/cancel", body=[oid])
    return spriv("DELETE", "/api/v3/order", {"symbol": ssym(coin), "orderId": oid})


def open_orders(market):
    if market == "futures":
        r = fpriv("GET", "/api/v1/private/order/list/open_orders", {"page_num": 1, "page_size": 100})
        if r.get("error"):
            raise ExchangeError(r["error"])
        return {"market": market, "orders": r["data"]}
    acct = spriv("GET", "/api/v3/account")
    if acct.get("error"):
        raise ExchangeError(acct["error"])
    coins = [b["asset"] for b in (acct["data"] or {}).get("balances", []) if float(b.get("locked") or 0) > 0 and b["asset"] != "USDT"]
    orders = []
    for c in coins[:20]:
        r = spriv("GET", "/api/v3/openOrders", {"symbol": ssym(c)})
        if not r.get("error"):
            orders += r["data"] or []
    return {"market": market, "orders": orders, "note": "spot orders found for coins with a locked balance"}


def balance():
    res = {}
    r = spriv("GET", "/api/v3/account")
    if r.get("error"):
        res["spot_error"] = r["error"]
    else:
        res["spot"] = [{"asset": b["asset"], "free": rnd(b["free"]), "locked": rnd(b["locked"])}
                       for b in (r["data"] or {}).get("balances", []) if float(b["free"]) + float(b["locked"]) > 0]
    r = fpriv("GET", "/api/v1/private/account/assets")
    if r.get("error"):
        res["futures_error"] = r["error"]
    else:
        res["futures"] = [{"asset": x.get("currency"), "equity": rnd(x.get("equity")), "available": rnd(x.get("availableBalance")),
                           "unrealized_pnl": rnd(x.get("unrealized"))} for x in r["data"] or [] if float(x.get("equity") or 0)]
    return res


def positions():
    r = fpriv("GET", "/api/v1/private/position/open_positions")
    if r.get("error"):
        raise ExchangeError(r["error"])
    rows = []
    for x in r["data"] or []:
        coin = x["symbol"].replace("_USDT", "")
        size = float(detail(coin).get("contractSize") or 0)
        t = fpub("/api/v1/contract/ticker", {"symbol": x["symbol"]}) or {}
        mark, liq = float(t.get("fairPrice") or 0), float(x.get("liquidatePrice") or 0)
        rows.append({"coin": coin, "side": "long" if x.get("positionType") == 1 else "short",
                     "qty": rnd(float(x.get("holdVol") or 0) * size), "entry": rnd(x.get("holdAvgPrice"), 6), "mark": rnd(mark, 6),
                     "leverage": x.get("leverage"), "liquidation": rnd(liq, 6),
                     "to_liquidation_pct": rnd(abs(mark - liq) / mark * 100, 3) if mark and liq else None,
                     "margin_mode": "isolated" if x.get("openType") == 1 else "cross"})
    return {"positions": rows}


def set_leverage(coin, lev):
    res = {}
    for pt in (1, 2):
        r = fpriv("POST", "/api/v1/private/position/change_leverage",
                  body={"symbol": fsym(coin), "leverage": int(lev), "openType": 2, "positionType": pt})
        res["long" if pt == 1 else "short"] = r.get("error") or "ok"
    return {"leverage": int(lev), "result": res}


def keycheck():
    r = spriv("GET", "/api/v3/apiKeyInfo")
    if r.get("error"):
        return {"checked": False, "error": r["error"], "note": "check the key's rights in the MEXC API settings"}
    d = r["data"] or {}
    text = json.dumps(d).lower()
    return {"checked": True, "raw_permissions": d, "withdraw": "withdraw" in text and '"withdraw": false' not in text,
            "note": "MEXC keys without an IP whitelist expire after 90 days"}


if __name__ == "__main__":
    exkit.main(sys.modules[__name__])
