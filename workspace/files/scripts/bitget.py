#!/usr/bin/env python3
"""Bitget adapter for the exchange-agent toolkit (see exkit.py for the commands). Standard library only.
Classic v2 API (USDT-M futures and spot). Secrets: BITGET_API_KEY, BITGET_SECRET_KEY, BITGET_PASSPHRASE (read + trade,
never withdraw or transfer). Broker code: knowledge/partner.json -> X-CHANNEL-API-CODE on every private request."""
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exkit  # noqa: E402
from exkit import ExchangeError, http, rnd  # noqa: E402

AGENT = "bitget"
EXID = "bitget"
NAME = "Bitget"
KEY_ENV = ["BITGET_API_KEY", "BITGET_SECRET_KEY", "BITGET_PASSPHRASE"]
TAKER_FEE = 0.0006
BASE = "https://api.bitget.com"
PT = "USDT-FUTURES"
TF_FUT = {"1d": "1D", "4h": "4H", "1h": "1H"}
TF_SPOT = {"1d": "1day", "4h": "4h", "1h": "1h"}


def sym(coin):
    return f"{coin}USDT"


def pub(path, params=None):
    r = http("GET", BASE + path, params)
    if not isinstance(r, dict) or r.get("code") != "00000":
        raise ExchangeError(f"Bitget: {r.get('msg') if isinstance(r, dict) else r}")
    return r.get("data")


def priv(method, path, params=None, body=None):
    q = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
    b = json.dumps({k: v for k, v in (body or {}).items() if v is not None}, separators=(",", ":")) if body is not None else ""
    ts = str(int(time.time() * 1000))
    pre = ts + method + path + (("?" + q) if q else "") + b
    sig = base64.b64encode(hmac.new(os.environ["BITGET_SECRET_KEY"].encode(), pre.encode(), hashlib.sha256).digest()).decode()
    h = {"ACCESS-KEY": os.environ["BITGET_API_KEY"], "ACCESS-SIGN": sig, "ACCESS-TIMESTAMP": ts,
         "ACCESS-PASSPHRASE": os.environ["BITGET_PASSPHRASE"], "Content-Type": "application/json", "locale": "en-US"}
    broker = exkit.partner(EXID)["broker_code"]
    if broker:
        h["X-CHANNEL-API-CODE"] = broker
    r = http(method, BASE + path, raw_query=q, body=b if body is not None else None, headers=h)
    if not isinstance(r, dict):
        raise ExchangeError(f"Bitget: unexpected answer {str(r)[:200]}")
    if r.get("code") != "00000":
        return {"error": r.get("msg") or r.get("code"), "code": r.get("code")}
    return {"data": r.get("data")}


def tickers(market):
    if market == "futures":
        d = pub("/api/v2/mix/market/tickers", {"productType": PT}) or []
        return [{"coin": x["symbol"][:-4], "symbol": x["symbol"], "last": float(x["lastPr"]),
                 "change_pct": rnd(float(x["change24h"]) * 100), "quote_volume": float(x.get("usdtVolume") or 0),
                 "funding_pct": rnd(float(x.get("fundingRate") or 0) * 100, 4)} for x in d if x["symbol"].endswith("USDT")]
    d = pub("/api/v2/spot/market/tickers") or []
    return [{"coin": x["symbol"][:-4], "symbol": x["symbol"], "last": float(x["lastPr"]),
             "change_pct": rnd(float(x["change24h"]) * 100), "quote_volume": float(x.get("usdtVolume") or 0)}
            for x in d if x["symbol"].endswith("USDT")]


def candles(coin, market, tf, limit):
    if market == "futures":
        d = pub("/api/v2/mix/market/candles", {"symbol": sym(coin), "productType": PT, "granularity": TF_FUT[tf], "limit": limit}) or []
    else:
        d = pub("/api/v2/spot/market/candles", {"symbol": sym(coin), "granularity": TF_SPOT[tf], "limit": limit}) or []
    return sorted([[int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[6])] for x in d])


def derivs(coin):
    t = next((x for x in pub("/api/v2/mix/market/tickers", {"productType": PT}) or [] if x["symbol"] == sym(coin)), None)
    if not t:
        raise ExchangeError(f"no {coin} perpetual on Bitget")
    res = {"funding_pct": rnd(float(t.get("fundingRate") or 0) * 100, 4), "mark_price": rnd(t.get("markPrice"), 6),
           "open_interest_usd": rnd(float(t.get("holdingAmount") or 0) * float(t.get("markPrice") or 0), 6)}
    try:
        ls = pub("/api/v2/mix/market/account-long-short", {"symbol": sym(coin), "period": "1h"}) or []
        if ls:
            res["long_short_accounts"] = rnd(ls[-1].get("longShortAccountRatio") or ls[-1].get("longShortRatio"), 4)
    except ExchangeError:
        pass
    return res


def _fut_body(o, hedge=False):
    b = {"symbol": sym(o["coin"]), "productType": PT, "marginMode": "crossed", "marginCoin": "USDT", "size": str(o["qty"]),
         "side": o["side"], "orderType": o["type"]}
    if o["type"] == "limit":
        b.update(price=str(o["price"]), force="gtc")
    if hedge:
        b["tradeSide"] = "close" if o.get("reduce_only") else "open"
        if o.get("reduce_only"):  # in hedge mode, closing a long is side=buy with tradeSide=close
            b["side"] = "buy" if o["side"] == "sell" else "sell"
    elif o.get("reduce_only"):
        b["reduceOnly"] = "YES"
    if o.get("stop"):
        b["presetStopLossPrice"] = str(o["stop"])
    if o.get("take"):
        b["presetStopSurplusPrice"] = str(o["take"])
    return b


def validate(o):
    if o["market"] == "spot" and (o.get("stop") or o.get("take")):
        return {"error": "Bitget spot orders here take no stop or take: place the order, then set them separately"}
    return {"checked_by_exchange": False, "note": "Bitget has no test endpoint: the exchange checks the order when it is placed"}


def place(o):
    if o["market"] == "futures":
        if o.get("leverage"):
            set_leverage(o["coin"], o["leverage"])
        r = priv("POST", "/api/v2/mix/order/place-order", body=_fut_body(o))
        if r.get("error") and ("unilateral" in str(r["error"]).lower() or "position mode" in str(r["error"]).lower()
                                or r.get("code") in ("40774", "40775")):
            r = priv("POST", "/api/v2/mix/order/place-order", body=_fut_body(o, hedge=True))
    else:
        b = {"symbol": sym(o["coin"]), "side": o["side"], "orderType": o["type"], "force": "gtc"}
        if o["type"] == "limit":
            b.update(price=str(o["price"]), size=str(o["qty"]))
        else:  # Bitget spot market buy takes the amount in USDT, market sell in coins
            b["size"] = str(round(o["qty"] * o["ref_price"], 2)) if o["side"] == "buy" else str(o["qty"])
        r = priv("POST", "/api/v2/spot/trade/place-order", body=b)
    if r.get("error"):
        return r
    d = r["data"] or {}
    return {"order_id": d.get("orderId"), "client_id": d.get("clientOid")}


def cancel(coin, oid, market):
    if market == "futures":
        return priv("POST", "/api/v2/mix/order/cancel-order", body={"symbol": sym(coin), "productType": PT, "orderId": oid})
    return priv("POST", "/api/v2/spot/trade/cancel-order", body={"symbol": sym(coin), "orderId": oid})


def open_orders(market):
    if market == "futures":
        r = priv("GET", "/api/v2/mix/order/orders-pending", {"productType": PT})
    else:
        r = priv("GET", "/api/v2/spot/trade/unfilled-orders")
    if r.get("error"):
        raise ExchangeError(r["error"])
    d = r["data"] or {}
    return {"market": market, "orders": d.get("entrustedList", d) if isinstance(d, dict) else d}


def balance():
    res = {}
    r = priv("GET", "/api/v2/mix/account/accounts", {"productType": PT})
    if r.get("error"):
        res["futures_error"] = r["error"]
    else:
        res["futures"] = [{"asset": x.get("marginCoin"), "equity": rnd(x.get("accountEquity")), "available": rnd(x.get("available")),
                           "unrealized_pnl": rnd(x.get("unrealizedPL"))} for x in r["data"] or []]
    r = priv("GET", "/api/v2/spot/account/assets")
    if r.get("error"):
        res["spot_error"] = r["error"]
    else:
        res["spot"] = [{"asset": x["coin"], "available": rnd(x["available"]), "frozen": rnd(x.get("frozen"))}
                       for x in r["data"] or [] if float(x["available"]) + float(x.get("frozen") or 0) > 0]
    if res.get("futures_error") and res.get("spot_error"):
        res["hint"] = "If this is a Unified Trading Account, the classic endpoints may refuse it; tell the user."
    return res


def positions():
    r = priv("GET", "/api/v2/mix/position/all-position", {"productType": PT, "marginCoin": "USDT"})
    if r.get("error"):
        raise ExchangeError(r["error"])
    rows = []
    for x in r["data"] or []:
        mark, liq = float(x.get("markPrice") or 0), float(x.get("liquidationPrice") or 0)
        rows.append({"coin": x["symbol"].replace("USDT", ""), "side": x.get("holdSide"), "qty": rnd(x.get("total")),
                     "entry": rnd(x.get("openPriceAvg"), 6), "mark": rnd(mark, 6), "leverage": x.get("leverage"),
                     "unrealized_pnl": rnd(x.get("unrealizedPL")), "liquidation": rnd(liq, 6),
                     "to_liquidation_pct": rnd(abs(mark - liq) / mark * 100, 3) if mark and liq > 0 else None,
                     "margin_mode": x.get("marginMode")})
    return {"positions": rows}


def set_leverage(coin, lev):
    r = priv("POST", "/api/v2/mix/account/set-leverage",
             body={"symbol": sym(coin), "productType": PT, "marginCoin": "USDT", "leverage": str(int(lev))})
    return {"leverage": int(lev), "result": r.get("error") or "ok"}


def keycheck():
    r = priv("GET", "/api/v2/spot/account/info")
    if r.get("error"):
        return {"checked": False, "error": r["error"]}
    d = r["data"] or {}
    auth = [str(a).lower() for a in d.get("authorities") or []]
    return {"checked": True, "permissions": auth, "ip_whitelist": d.get("ips"),
            "withdraw": any("withdraw" in a or a in ("wd", "wdw") for a in auth),
            "transfer": any("transfer" in a for a in auth), "can_trade": any("trade" in a or a.endswith("t") for a in auth)}


if __name__ == "__main__":
    exkit.main(sys.modules[__name__])
