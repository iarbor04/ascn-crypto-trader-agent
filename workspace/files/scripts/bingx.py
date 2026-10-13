#!/usr/bin/env python3
"""BingX adapter for the exchange-agent toolkit (see exkit.py for the commands). Standard library only.
Secrets: BINGX_API_KEY, BINGX_SECRET_KEY (read + trade, never withdraw). Broker code: knowledge/partner.json -> X-SOURCE-KEY."""
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exkit  # noqa: E402
from exkit import ExchangeError, http, rnd, sign_hex  # noqa: E402

AGENT = "bingx"
EXID = "bingx"
NAME = "BingX"
KEY_ENV = ["BINGX_API_KEY", "BINGX_SECRET_KEY"]
TAKER_FEE = 0.0005
BASE = "https://open-api.bingx.com"
TF = {"1d": "1d", "4h": "4h", "1h": "1h"}


def sym(coin):
    return f"{coin}-USDT"


def pub(path, params=None):
    r = http("GET", BASE + path, params)
    if not isinstance(r, dict) or r.get("code") not in (0, "0", None):
        raise ExchangeError(f"BingX: {r.get('msg') if isinstance(r, dict) else r}")
    return r.get("data")


def priv(method, path, params=None):
    p = {k: v for k, v in (params or {}).items() if v is not None}
    p["timestamp"] = int(time.time() * 1000)
    p.setdefault("recvWindow", 5000)
    q = "&".join(f"{k}={p[k]}" for k in sorted(p))
    sig = sign_hex(os.environ["BINGX_SECRET_KEY"], q)
    enc = "&".join(f"{k}={urllib.parse.quote(str(p[k]), safe='')}" for k in sorted(p)) + f"&signature={sig}"
    h = {"X-BX-APIKEY": os.environ["BINGX_API_KEY"]}
    broker = exkit.partner(EXID)["broker_code"]
    if broker:
        h["X-SOURCE-KEY"] = broker
    r = http(method, BASE + path, raw_query=enc, headers=h)
    if not isinstance(r, dict):
        raise ExchangeError(f"BingX: unexpected answer {str(r)[:200]}")
    if r.get("code") not in (0, "0"):
        return {"error": r.get("msg") or str(r.get("code")), "code": r.get("code")}
    return {"data": r.get("data")}


def tickers(market):
    if market == "futures":
        fund = {x["symbol"]: float(x.get("lastFundingRate") or 0) * 100 for x in pub("/openApi/swap/v2/quote/premiumIndex") or []}
        rows = []
        for x in pub("/openApi/swap/v2/quote/ticker") or []:
            if not x["symbol"].endswith("-USDT"):
                continue
            rows.append({"coin": x["symbol"][:-5], "symbol": x["symbol"], "last": float(x["lastPrice"]),
                         "change_pct": rnd(x["priceChangePercent"]), "quote_volume": float(x.get("quoteVolume") or 0),
                         "funding_pct": rnd(fund.get(x["symbol"]), 4)})
        return rows
    d = pub("/openApi/spot/v1/ticker/24hr", {"timestamp": int(time.time() * 1000)}) or []
    return [{"coin": x["symbol"][:-5], "symbol": x["symbol"], "last": float(x["lastPrice"]),
             "change_pct": rnd(str(x["priceChangePercent"]).rstrip("%")), "quote_volume": float(x.get("quoteVolume") or 0)}
            for x in d if x["symbol"].endswith("-USDT")]


def candles(coin, market, tf, limit):
    if market == "futures":
        d = pub("/openApi/swap/v3/quote/klines", {"symbol": sym(coin), "interval": TF[tf], "limit": limit}) or []
        c = [[int(x["time"]), float(x["open"]), float(x["high"]), float(x["low"]), float(x["close"]),
              float(x["volume"]) * float(x["close"])] for x in d]
    else:
        d = pub("/openApi/spot/v2/market/kline", {"symbol": sym(coin), "interval": TF[tf], "limit": limit}) or []
        c = [[int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[7])] for x in d]
    return sorted(c)


def derivs(coin):
    p = pub("/openApi/swap/v2/quote/premiumIndex", {"symbol": sym(coin)}) or {}
    oi = pub("/openApi/swap/v2/quote/openInterest", {"symbol": sym(coin)}) or {}
    return {"funding_pct": rnd(float(p.get("lastFundingRate") or 0) * 100, 4), "funding_interval_h": p.get("fundingIntervalHours"),
            "mark_price": rnd(p.get("markPrice"), 6), "open_interest_usd": rnd(oi.get("openInterest"), 6),
            "note": "BingX has no public long/short ratio"}


def _futures_params(o, side_mode="BOTH"):
    side = "BUY" if o["side"] == "buy" else "SELL"
    if side_mode == "BOTH":
        ps = "BOTH"
    else:  # hedge mode: opening buy = LONG, opening sell = SHORT; closing is the opposite
        ps = ("SHORT" if side == "BUY" else "LONG") if o.get("reduce_only") else ("LONG" if side == "BUY" else "SHORT")
    p = {"symbol": sym(o["coin"]), "side": side, "positionSide": ps, "type": o["type"].upper(), "quantity": o["qty"]}
    if o["type"] == "limit":
        p["price"] = o["price"]
    if o.get("reduce_only") and ps == "BOTH":
        p["reduceOnly"] = "true"
    if o.get("stop"):
        p["stopLoss"] = json.dumps({"type": "STOP_MARKET", "stopPrice": o["stop"], "workingType": "MARK_PRICE"}, separators=(",", ":"))
    if o.get("take"):
        p["takeProfit"] = json.dumps({"type": "TAKE_PROFIT_MARKET", "stopPrice": o["take"], "workingType": "MARK_PRICE"},
                                     separators=(",", ":"))
    return p


def _send_futures(path, o):
    r = priv("POST", path, _futures_params(o))
    if r.get("error") and "position" in r["error"].lower() and "side" in r["error"].lower():
        r = priv("POST", path, _futures_params(o, "HEDGE"))  # account in hedge mode
    return r


def validate(o):
    if not all(os.environ.get(k) for k in KEY_ENV):
        return {"checked_by_exchange": False, "note": "no key in Secrets: the exchange will check the order when it is placed"}
    if o["market"] == "futures":
        r = _send_futures("/openApi/swap/v2/trade/order/test", o)
        return {"checked_by_exchange": True, **({"error": r["error"]} if r.get("error") else {"result": "test order accepted"})}
    return {"checked_by_exchange": False, "note": "spot orders have no test endpoint on BingX"}


def place(o):
    if o["market"] == "futures":
        if o.get("leverage"):
            set_leverage(o["coin"], o["leverage"])
        r = _send_futures("/openApi/swap/v2/trade/order", o)
    else:
        p = {"symbol": sym(o["coin"]), "side": "BUY" if o["side"] == "buy" else "SELL", "type": o["type"].upper(), "quantity": o["qty"]}
        if o["type"] == "limit":
            p.update(price=o["price"], timeInForce="GTC")
        r = priv("POST", "/openApi/spot/v1/trade/order", p)
    if r.get("error"):
        return r
    d = r["data"] or {}
    order = d.get("order", d)
    return {"order_id": order.get("orderId"), "status": order.get("status"), "raw": order}


def cancel(coin, oid, market):
    if market == "futures":
        return priv("DELETE", "/openApi/swap/v2/trade/order", {"symbol": sym(coin), "orderId": oid})
    return priv("POST", "/openApi/spot/v1/trade/cancel", {"symbol": sym(coin), "orderId": oid})


def open_orders(market):
    r = priv("GET", "/openApi/swap/v2/trade/openOrders" if market == "futures" else "/openApi/spot/v1/trade/openOrders")
    if r.get("error"):
        raise ExchangeError(r["error"])
    d = r["data"] or {}
    return {"market": market, "orders": d.get("orders", d)}


def balance():
    res = {}
    r = priv("GET", "/openApi/swap/v3/user/balance")
    if not r.get("error"):
        res["futures"] = [{"asset": x.get("asset"), "balance": rnd(x.get("balance")), "equity": rnd(x.get("equity")),
                           "available": rnd(x.get("availableMargin")), "unrealized_pnl": rnd(x.get("unrealizedProfit"))}
                          for x in (r["data"] or []) if float(x.get("balance") or 0) or float(x.get("equity") or 0)]
    else:
        res["futures_error"] = r["error"]
    r = priv("GET", "/openApi/spot/v1/account/balance")
    if not r.get("error"):
        res["spot"] = [{"asset": x["asset"], "free": rnd(x["free"]), "locked": rnd(x["locked"])}
                       for x in (r["data"] or {}).get("balances", []) if float(x["free"]) + float(x["locked"]) > 0]
    else:
        res["spot_error"] = r["error"]
    return res


def positions():
    r = priv("GET", "/openApi/swap/v2/user/positions")
    if r.get("error"):
        raise ExchangeError(r["error"])
    rows = []
    for x in r["data"] or []:
        mark, liq = float(x.get("markPrice") or 0), float(x.get("liquidationPrice") or 0)
        rows.append({"coin": x["symbol"].replace("-USDT", ""), "side": x.get("positionSide"), "qty": rnd(x.get("positionAmt")),
                     "entry": rnd(x.get("avgPrice"), 6), "mark": rnd(mark, 6), "leverage": x.get("leverage"),
                     "unrealized_pnl": rnd(x.get("unrealizedProfit")), "liquidation": rnd(liq, 6),
                     "to_liquidation_pct": rnd(abs(mark - liq) / mark * 100, 3) if mark and liq else None,
                     "margin_mode": "isolated" if x.get("isolated") else "cross"})
    return {"positions": rows}


def set_leverage(coin, lev):
    res = {}
    for side in ("LONG", "SHORT"):
        r = priv("POST", "/openApi/swap/v2/trade/leverage", {"symbol": sym(coin), "side": side, "leverage": int(lev)})
        res[side] = r.get("error") or "ok"
    return {"leverage": int(lev), "result": res}


def keycheck():
    r = priv("GET", "/openApi/account/v1/apiKey/query")
    if r.get("error"):
        return {"checked": False, "error": r["error"]}
    keys = r["data"] or {}
    items = keys.get("apiInfos", keys) if isinstance(keys, dict) else keys
    perms = set()
    for k in items if isinstance(items, list) else [items]:
        for pmn in (k.get("permissions") or []):
            perms.add(int(pmn))
    names = {1: "spot trading", 2: "read", 3: "futures trading", 4: "universal transfer", 5: "withdraw", 7: "internal transfer"}
    return {"checked": True, "permissions": [names.get(p, str(p)) for p in sorted(perms)], "withdraw": 5 in perms,
            "transfer": bool({4, 7} & perms), "can_trade": bool({1, 3} & perms)}


if __name__ == "__main__":
    exkit.main(sys.modules[__name__])
