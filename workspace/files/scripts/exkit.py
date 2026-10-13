#!/usr/bin/env python3
"""Shared core of the ASCN exchange agents (BingX, Bitget, MEXC). Standard library only, prints JSON.
Each agent ships this file next to its exchange adapter (bingx.py / bitget.py / mexc.py), which calls main(adapter).

Market data needs no key. Account and trading use the user's API key from Settings -> Secrets (env vars named by the
adapter); the exchange connector in Integrations can be used by the agent directly for the actions it has.
Orders are two-step: `order preview` saves a pending order and prints its id; only `order place <id>` sends it, within
10 minutes, after the user's explicit yes. Partner settings (referral link, broker code) come from
knowledge/partner.json inside the package.

  context                                   profile, settings, keys present, partner link, pending orders
  movers [--market futures|spot] [--sort change|volume|funding] [--limit N]
  analyze <COIN> [--market futures|spot] [--tf 1d|4h|1h]
                                            trend (EMA 20/50/200), ATR, levels from swing highs/lows, volume vs
                                            average, 24 h change, funding and open interest (futures)
  plan <COIN> --side long|short --entry PRICE|market --stop PRICE [--take PRICE ...] [--risk-pct P | --risk-usd U]
       [--balance USD] [--leverage L] [--market futures|spot]
                                            size from risk, margin, approximate liquidation, reward/risk, fees, warnings
  order preview <COIN> --side buy|sell --qty Q [--type market|limit] [--price P] [--stop P] [--take P]
       [--leverage L] [--market futures|spot] [--reduce-only]
                                            validates and saves a pending order (no exchange call that trades)
  order place <ID>                          sends a pending order (after the user's yes), then reads it back
  order cancel <COIN> <ORDER_ID> [--market futures|spot]
  orders [--market futures|spot]            open orders
  balance                                   balances (spot and futures)
  positions                                 open futures positions with liquidation distance
  leverage <COIN> <L>                       set futures leverage
  keycheck                                  key permissions; refuses work if withdrawals are enabled
  journal [--days N]                        orders sent by the agent, from files/<x>/journal.jsonl
  partner                                   referral link and whether a broker code is set (for onboarding)
  report-path <topic>
"""
import argparse
import hashlib
import hmac
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("EXKIT_ROOT") or HERE.parents[1])
UA = "Mozilla/5.0 (compatible; ascn-exchange-agent/1.0)"


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, indent=1))
    sys.exit(code)


def fail(msg, **kw):
    out({"ok": False, "error": msg, **kw}, 1)


def now():
    return datetime.now(timezone.utc)


def read_json(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def rnd(x, n=4):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    if abs(x) >= 1000:
        return round(x, 2)
    return float(f"{x:.{n}g}") if x else 0.0


class ExchangeError(Exception):
    pass


def http(method, url, params=None, body=None, headers=None, timeout=20, raw_query=None):
    q = raw_query if raw_query is not None else (urllib.parse.urlencode(params) if params else "")
    full = url + ("?" + q if q else "")
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(headers or {})
    data = None
    if body is not None:
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        h.setdefault("Content-Type", "application/json")
    last = None
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(full, data=data, headers=h, method=method), timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "replace")[:400]
            if e.code in (451, 403):
                raise ExchangeError(f"HTTP {e.code}: blocked from this server ({txt[:120]})")
            if method != "GET" or e.code < 500 and e.code != 429:
                try:
                    return json.loads(txt)
                except Exception:
                    raise ExchangeError(f"HTTP {e.code}: {txt[:200]}")
            last = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError) as e:
            last = str(e)
            if method != "GET":
                raise ExchangeError(f"no answer to a {method} request ({last}): check the order list before retrying")
        time.sleep(1.5 * (i + 1))
    raise ExchangeError(f"request failed: {url} ({last})")


def sign_hex(secret, msg):
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


def partner(exid=None):
    p = read_json(ROOT / "knowledge" / "partner.json", {})
    if exid and isinstance(p.get(exid), dict):
        p = p[exid]
    return {"referral_link": p.get("referral_link") or None, "referral_code": p.get("referral_code") or None,
            "broker_code": p.get("broker_code") or None, "disclosure": p.get("disclosure")}


# ---------- indicators ----------

def ema(vals, n):
    if len(vals) < n:
        return None
    k = 2 / (n + 1)
    e = sum(vals[:n]) / n
    for v in vals[n:]:
        e = v * k + e * (1 - k)
    return e


def atr(c, n=14):
    if len(c) < n + 1:
        return None
    trs = [max(c[i][2] - c[i][3], abs(c[i][2] - c[i - 1][4]), abs(c[i][3] - c[i - 1][4])) for i in range(1, len(c))]
    return sum(trs[-n:]) / n


def swing_levels(c, width=3, keep=4):
    """Support and resistance from swing lows/highs, merged when within 0.6 ATR, ranked by touches and recency."""
    a = atr(c) or 0
    highs, lows = [], []
    for i in range(width, len(c) - width):
        if c[i][2] == max(x[2] for x in c[i - width:i + width + 1]):
            highs.append((c[i][2], i))
        if c[i][3] == min(x[3] for x in c[i - width:i + width + 1]):
            lows.append((c[i][3], i))

    def merge(pts):
        groups = []
        for p, i in sorted(pts):
            if groups and a and abs(p - groups[-1]["price"]) <= 0.6 * a:
                g = groups[-1]
                g["price"] = (g["price"] * g["touches"] + p) / (g["touches"] + 1)
                g["touches"] += 1
                g["last"] = max(g["last"], i)
            else:
                groups.append({"price": p, "touches": 1, "last": i})
        return groups
    last = c[-1][4]
    res = [g for g in merge(highs) if g["price"] > last]
    sup = [g for g in merge(lows) if g["price"] < last]
    res = sorted(res, key=lambda g: g["price"])[:keep]
    sup = sorted(sup, key=lambda g: -g["price"])[:keep]
    fmt = lambda gs: [{"price": rnd(g["price"], 6), "touches": g["touches"], "distance_pct": rnd((g["price"] / last - 1) * 100, 3)}
                      for g in gs]
    return fmt(sup), fmt(res)


def analyze_candles(c):
    closes = [x[4] for x in c]
    last = closes[-1]
    e20, e50, e200 = ema(closes, 20), ema(closes, 50), ema(closes, 200)
    a = atr(c)
    vols = [x[5] for x in c]
    vol_ratio = vols[-2] / (sum(vols[-32:-2]) / 30) if len(vols) >= 33 and sum(vols[-32:-2]) else None
    if e20 and e50:
        if last > e20 > e50:
            trend = "up (price above EMA20 above EMA50)"
        elif last < e20 < e50:
            trend = "down (price below EMA20 below EMA50)"
        else:
            trend = "sideways / mixed"
    else:
        trend = "not enough history"
    sup, res = swing_levels(c)
    hi = max(x[2] for x in c[-30:])
    lo = min(x[3] for x in c[-30:])
    return {"last": rnd(last, 6), "trend": trend, "ema20": rnd(e20, 6), "ema50": rnd(e50, 6), "ema200": rnd(e200, 6),
            "atr": rnd(a, 6), "atr_pct": rnd(a / last * 100, 3) if a else None,
            "range_30": {"high": rnd(hi, 6), "low": rnd(lo, 6), "position_pct": rnd((last - lo) / (hi - lo) * 100, 3) if hi > lo else None},
            "change_7_pct": rnd((last / closes[-8] - 1) * 100, 3) if len(closes) > 8 else None,
            "change_30_pct": rnd((last / closes[-31] - 1) * 100, 3) if len(closes) > 31 else None,
            "last_closed_volume_vs_30avg": rnd(vol_ratio, 3), "support": sup, "resistance": res, "candles": len(c)}


# ---------- CLI ----------

class Agent:
    def __init__(self, ad):
        self.ad = ad
        self.data = ROOT / "files" / getattr(ad, "DATA", ad.AGENT)
        self.pending = self.data / "pending.json"
        self.journal = self.data / "journal.jsonl"
        self.reports = self.data / "reports"

    def settings(self):
        s = {"language": "ru", "default_risk_pct": 1.0, "max_leverage": 10, "default_market": "futures",
             "taker_fee": self.ad.TAKER_FEE, "maint_margin": 0.005}
        s.update(read_json(self.data / "settings.json", {}))
        return s

    def need_keys(self):
        missing = [k for k in self.ad.KEY_ENV if not os.environ.get(k)]
        if missing:
            fail("no API key in Settings -> Secrets", missing=missing,
                 hint="Create a key on the exchange with read + trade rights, without withdrawals and transfers, and add it "
                      "in Settings -> Secrets under these names; or use the exchange connector in Integrations.")

    def log(self, rec):
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        with self.journal.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # commands
    def context(self, a):
        pf = self.data / "profile" / f"{getattr(self.ad, 'DATA', self.ad.AGENT)}-profile.md"
        prof = pf.read_text(encoding="utf-8") if pf.exists() else ""
        filled = [l for l in prof.splitlines() if ":" in l and not l.startswith(("#", "Updated"))
                  and l.split(":", 1)[1].strip() and not l.split(":", 1)[1].strip().startswith("(")]
        pend = read_json(self.pending, {})
        out({"ok": True, "exchange": self.ad.NAME, "today_utc": now().date().isoformat(), "profile_filled": bool(filled),
             "profile": prof.strip() if filled else "", "settings": self.settings(),
             "keys_in_secrets": all(os.environ.get(k) for k in self.ad.KEY_ENV), "partner": partner(getattr(self.ad, "EXID", None)),
             "pending_orders": [{"id": k, **{x: v.get(x) for x in ("exchange", "coin", "side", "qty", "type", "market")}} for k, v in pend.items()]})

    def movers(self, a):
        rows = self.ad.tickers(a.market)
        rows = [r for r in rows if (r.get("quote_volume") or 0) >= a.min_volume]
        key = {"volume": lambda r: -(r["quote_volume"] or 0), "funding": lambda r: -abs(r.get("funding_pct") or 0)}.get(
            a.sort, lambda r: -abs(r["change_pct"] or 0))
        rows.sort(key=key)
        out({"ok": True, "exchange": self.ad.NAME, "market": a.market, "sort": a.sort, "count": len(rows),
             "rows": rows[:a.limit], "fetched_at": now().isoformat(timespec="seconds")})

    def analyze(self, a):
        coin = a.coin.upper()
        c = self.ad.candles(coin, a.market, a.tf, 220)
        if not c or len(c) < 30:
            fail(f"not enough candles for {coin} on {self.ad.NAME} {a.market}", got=len(c or []))
        res = {"ok": True, "exchange": self.ad.NAME, "coin": coin, "market": a.market, "timeframe": a.tf,
               "fetched_at": now().isoformat(timespec="seconds"), **analyze_candles(c)}
        t = next((r for r in self.ad.tickers(a.market) if r["coin"] == coin), None)
        if t:
            res["ticker_24h"] = t
        if a.market == "futures":
            try:
                res["derivatives"] = self.ad.derivs(coin)
            except ExchangeError as e:
                res["derivatives"] = {"error": str(e)}
        out(res)

    def plan(self, a):
        s = self.settings()
        coin = a.coin.upper()
        t = next((r for r in self.ad.tickers(a.market) if r["coin"] == coin), None)
        if not t:
            fail(f"{coin} is not traded on {self.ad.NAME} {a.market}")
        entry = t["last"] if a.entry == "market" else float(a.entry)
        stop = float(a.stop)
        long = a.side == "long"
        if (long and stop >= entry) or (not long and stop <= entry):
            fail("the stop must be below the entry for a long and above it for a short", entry=entry, stop=stop)
        balance = a.balance
        if balance is None:
            fail("need --balance (ask the user, or read it with `balance` when a key is connected)")
        risk_usd = a.risk_usd if a.risk_usd else balance * (a.risk_pct or s["default_risk_pct"]) / 100
        per_unit = abs(entry - stop)
        fee_rt = s["taker_fee"] * 2
        qty = risk_usd / (per_unit + entry * fee_rt)
        notional = qty * entry
        lev = a.leverage or 1
        res = {"ok": True, "exchange": self.ad.NAME, "coin": coin, "side": a.side, "market": a.market,
               "entry": rnd(entry, 6), "entry_source": "last price" if a.entry == "market" else "user",
               "stop": rnd(stop, 6), "stop_distance_pct": rnd(per_unit / entry * 100, 3),
               "risk_usd": rnd(risk_usd, 4), "risk_pct_of_balance": rnd(risk_usd / balance * 100, 3),
               "qty": rnd(qty, 6), "notional_usd": rnd(notional, 6), "fees_round_trip_usd": rnd(notional * fee_rt, 4)}
        warn = []
        if a.market == "futures":
            margin = notional / lev
            liq = entry * (1 - 1 / lev + s["maint_margin"]) if long else entry * (1 + 1 / lev - s["maint_margin"])
            res.update({"leverage": lev, "margin_usd": rnd(margin, 6), "liquidation_approx": rnd(liq, 6),
                        "liquidation_note": "isolated margin estimate; the exchange shows the exact price"})
            if (long and liq >= stop) or (not long and liq <= stop):
                warn.append("liquidation comes before the stop: lower the leverage or move the stop")
            if margin > balance:
                warn.append("margin is larger than the balance: lower the size or raise the leverage")
            if lev > s["max_leverage"]:
                warn.append(f"leverage above the user's limit ({s['max_leverage']}x)")
        elif notional > balance:
            warn.append("position is larger than the balance (spot has no leverage)")
        if risk_usd / balance > 0.03:
            warn.append("risk above 3% of the balance on one trade")
        takes = []
        for tp in a.take or []:
            tp = float(tp)
            rr = (tp - entry) / per_unit if long else (entry - tp) / per_unit
            takes.append({"take": rnd(tp, 6), "reward_risk": rnd(rr, 3), "profit_usd": rnd(abs(tp - entry) * qty - notional * fee_rt, 4)})
            if rr <= 0:
                warn.append(f"take {tp} is on the wrong side of the entry")
        res["takes"] = takes
        res["warnings"] = warn
        res["next"] = "Show the plan; if the user says yes, build `order preview` with this qty and stop/take."
        out(res)

    def order_preview(self, a):
        coin = a.coin.upper()
        if a.qty <= 0:
            fail("qty must be positive")
        if a.type == "limit" and not a.price:
            fail("a limit order needs --price")
        t = next((r for r in self.ad.tickers(a.market) if r["coin"] == coin), None)
        if not t:
            fail(f"{coin} is not traded on {self.ad.NAME} {a.market}")
        px = a.price or t["last"]
        order = {"coin": coin, "market": a.market, "side": a.side, "qty": a.qty, "type": a.type, "price": a.price,
                 "stop": a.stop, "take": a.take, "leverage": a.leverage, "reduce_only": a.reduce_only,
                 "created": time.time(), "ref_price": t["last"], "notional_usd": rnd(px * a.qty, 6)}
        check = self.ad.validate(order)
        if check.get("error"):
            fail(check["error"], details=check)
        if check.get("qty_rounded") is not None and check["qty_rounded"] != order["qty"]:
            order["qty_requested"] = order["qty"]
            order["qty"] = check["qty_rounded"]
            order["notional_usd"] = rnd(px * order["qty"], 6)
        oid = uuid.uuid4().hex[:8]
        pend = {k: v for k, v in read_json(self.pending, {}).items() if time.time() - v["created"] < 600}
        order["exchange"] = self.ad.NAME
        pend[oid] = order
        write_json(self.pending, pend)
        out({"ok": True, "pending_id": oid, "order": order, "exchange_check": check, "expires_in_min": 10,
             "next": "Show this to the user in plain words and wait for an explicit yes; then run order place " + oid})

    def order_place(self, a):
        self.need_keys()
        pend = read_json(self.pending, {})
        o = pend.get(a.id)
        if not o:
            fail("no such pending order: build a new preview", known=list(pend))
        if o.get("exchange") and o["exchange"] != self.ad.NAME:
            fail(f"this preview was built for {o['exchange']}: place it with that exchange")
        if time.time() - o["created"] > 600:
            pend.pop(a.id)
            write_json(self.pending, pend)
            fail("the preview is older than 10 minutes: prices moved, build a new preview")
        res = self.ad.place(o)
        pend.pop(a.id, None)
        write_json(self.pending, pend)
        self.log({"at": now().isoformat(timespec="seconds"), "exchange": self.ad.NAME, "action": "place", "order": o, "result": res,
                  "broker_code_set": bool(partner(getattr(self.ad, "EXID", None))["broker_code"])})
        out({"ok": not res.get("error"), "exchange": self.ad.NAME, "result": res})

    def order_cancel(self, a):
        self.need_keys()
        res = self.ad.cancel(a.coin.upper(), a.order_id, a.market)
        self.log({"at": now().isoformat(timespec="seconds"), "action": "cancel", "coin": a.coin.upper(), "order_id": a.order_id,
                  "result": res})
        out({"ok": not res.get("error"), "result": res})

    def simple(self, fn, *args):
        self.need_keys()
        try:
            out({"ok": True, "exchange": self.ad.NAME, "fetched_at": now().isoformat(timespec="seconds"), **fn(*args)})
        except ExchangeError as e:
            fail(str(e))

    def keycheck(self, a):
        self.need_keys()
        r = self.ad.keycheck()
        if r.get("withdraw"):
            r["verdict"] = "STOP: this key can withdraw funds. Ask the user to create a new key without withdrawal and transfer rights."
        out({"ok": True, **r})

    def journal_cmd(self, a):
        rows = [json.loads(l) for l in self.journal.read_text().splitlines()] if self.journal.exists() else []
        since = (now() - timedelta(days=a.days)).isoformat()
        out({"ok": True, "rows": [r for r in rows if r["at"] >= since]})

    def report_path(self, a):
        topic = re.sub(r"[^\w-]+", "-", a.topic.lower()).strip("-")[:60] or "report"
        self.reports.mkdir(parents=True, exist_ok=True)
        out({"ok": True, "path": str((self.reports / f"{now().date().isoformat()}-{topic}.md").relative_to(ROOT))})


def main(ad):
    ag = Agent(ad)
    mk = lambda p: p.add_argument("--market", choices=["futures", "spot"], default=ag.settings()["default_market"])
    ap = argparse.ArgumentParser(description=f"{ad.NAME} agent toolkit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("context").set_defaults(f=ag.context)
    p = sub.add_parser("movers"); mk(p); p.add_argument("--sort", choices=["change", "volume", "funding"], default="change")
    p.add_argument("--limit", type=int, default=15); p.add_argument("--min-volume", type=float, default=1_000_000); p.set_defaults(f=ag.movers)
    p = sub.add_parser("analyze"); p.add_argument("coin"); mk(p); p.add_argument("--tf", choices=["1d", "4h", "1h"], default="1d")
    p.set_defaults(f=ag.analyze)
    p = sub.add_parser("plan"); p.add_argument("coin"); p.add_argument("--side", choices=["long", "short"], required=True)
    p.add_argument("--entry", default="market"); p.add_argument("--stop", required=True); p.add_argument("--take", nargs="*")
    p.add_argument("--risk-pct", type=float); p.add_argument("--risk-usd", type=float); p.add_argument("--balance", type=float)
    p.add_argument("--leverage", type=float); mk(p); p.set_defaults(f=ag.plan)
    p = sub.add_parser("order"); osub = p.add_subparsers(dest="ocmd", required=True)
    q = osub.add_parser("preview"); q.add_argument("coin"); q.add_argument("--side", choices=["buy", "sell"], required=True)
    q.add_argument("--qty", type=float, required=True); q.add_argument("--type", choices=["market", "limit"], default="market")
    q.add_argument("--price", type=float); q.add_argument("--stop", type=float); q.add_argument("--take", type=float)
    q.add_argument("--leverage", type=float); q.add_argument("--reduce-only", action="store_true"); mk(q); q.set_defaults(f=ag.order_preview)
    q = osub.add_parser("place"); q.add_argument("id"); q.set_defaults(f=ag.order_place)
    q = osub.add_parser("cancel"); q.add_argument("coin"); q.add_argument("order_id"); mk(q); q.set_defaults(f=ag.order_cancel)
    p = sub.add_parser("orders"); mk(p); p.set_defaults(f=lambda a: ag.simple(ad.open_orders, a.market))
    sub.add_parser("balance").set_defaults(f=lambda a: ag.simple(ad.balance))
    sub.add_parser("positions").set_defaults(f=lambda a: ag.simple(ad.positions))
    p = sub.add_parser("leverage"); p.add_argument("coin"); p.add_argument("value", type=float)
    p.set_defaults(f=lambda a: ag.simple(ad.set_leverage, a.coin.upper(), a.value))
    sub.add_parser("keycheck").set_defaults(f=ag.keycheck)
    p = sub.add_parser("journal"); p.add_argument("--days", type=int, default=7); p.set_defaults(f=ag.journal_cmd)
    sub.add_parser("partner").set_defaults(f=lambda a: out({"ok": True, **partner(getattr(ad, "EXID", None))}))
    p = sub.add_parser("report-path"); p.add_argument("topic"); p.set_defaults(f=ag.report_path)
    a = ap.parse_args()
    try:
        a.f(a)
    except ExchangeError as e:
        fail(str(e), hint="Exchange did not answer as expected. Never guess the result of a trade: read orders and positions.")
