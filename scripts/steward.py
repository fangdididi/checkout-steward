#!/usr/bin/env python3
"""checkout-steward helper: fair group-bill split, offer triage, and a spend ledger.

All money is handled as integer cents so totals always add up exactly.
Standard library only. Run `python3 steward.py -h` for usage.
"""
import argparse
import datetime as dt
import json
import sys
from decimal import Decimal, ROUND_HALF_UP


# ---------- money helpers ----------

def cents(value):
    """'12.5' / 12.5 / '12.50' -> 1250. Rejects garbage loudly."""
    if value is None or value == "":
        return 0
    try:
        d = Decimal(str(value))
    except Exception:
        raise SystemExit(f"error: not a money amount: {value!r}")
    return int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def fmt(c, cur=""):
    sign = "-" if c < 0 else ""
    c = abs(c)
    return f"{sign}{cur}{c // 100}.{c % 100:02d}"


def allocate(total, weights):
    """Split `total` cents across keys in proportion to `weights` (dict key->int).

    Largest-remainder rounding: shares are exact and always sum to `total`.
    Ties are broken by key name so the result is reproducible.
    """
    keys = sorted(weights)
    wsum = sum(max(0, weights[k]) for k in keys)
    if total == 0 or not keys:
        return {k: 0 for k in keys}
    if wsum == 0:  # nobody has weight: fall back to equal
        weights = {k: 1 for k in keys}
        wsum = len(keys)
    raw = {k: total * max(0, weights[k]) for k in keys}
    base = {k: raw[k] // wsum for k in keys}
    rest = total - sum(base.values())
    order = sorted(keys, key=lambda k: (-(raw[k] % wsum), k))
    for k in order[:rest]:
        base[k] += 1
    return base


# ---------- split ----------

def cmd_split(args):
    data = json.load(open(args.file, encoding="utf-8"))
    cur = data.get("currency_symbol", "")
    lines = data.get("lines", [])
    if not lines:
        raise SystemExit("error: 'lines' is empty; nothing to split")
    people = sorted({l["who"] for l in lines})
    sub = {p: 0 for p in people}
    for l in lines:
        sub[l["who"]] += cents(l["price"]) * int(l.get("qty", 1))

    own = {p: 0 for p in people}
    for d in data.get("line_discounts", []):
        if d["who"] not in own:
            raise SystemExit(f"error: line discount for unknown person {d['who']!r}")
        own[d["who"]] += cents(d["amount"])
    after_own = {p: sub[p] - own[p] for p in people}

    basket_disc = sum(cents(d["amount"]) for d in data.get("basket_discounts", []))
    disc_policy = data.get("discount_policy", "proportional")
    w = after_own if disc_policy == "proportional" else {p: 1 for p in people}
    disc_share = allocate(basket_disc, w)

    fees = sum(cents(f["amount"]) for f in data.get("shared_fees", []))
    fee_policy = data.get("fee_policy", "equal")
    w = {p: 1 for p in people} if fee_policy == "equal" else after_own
    fee_share = allocate(fees, w)

    owed = {p: after_own[p] - disc_share[p] + fee_share[p] for p in people}
    total = sum(owed.values())

    rows = []
    for p in people:
        rows.append({"who": p, "items": fmt(sub[p]), "own_discounts": fmt(-own[p]),
                     "basket_discount_share": fmt(-disc_share[p]),
                     "fee_share": fmt(fee_share[p]), "owes": fmt(owed[p])})
    quote = data.get("quote_total")
    result = {"people": rows, "computed_total": fmt(total),
              "discount_policy": disc_policy, "fee_policy": fee_policy}
    status = 0
    if quote is not None:
        diff = total - cents(quote)
        result["quote_total"] = fmt(cents(quote))
        result["matches_quote"] = diff == 0
        if diff:
            result["gap"] = fmt(diff)
            status = 2
    payer = data.get("payer")
    if payer:
        result["transfers"] = [f"{p} -> {payer}: {fmt(owed[p], cur)}"
                               for p in people if p != payer and owed[p] > 0]

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{'who':<14}{'items':>10}{'own disc':>10}{'shared disc':>13}{'fees':>9}{'owes':>10}")
        for r in rows:
            print(f"{r['who']:<14}{r['items']:>10}{r['own_discounts']:>10}"
                  f"{r['basket_discount_share']:>13}{r['fee_share']:>9}{r['owes']:>10}")
        print(f"computed total {fmt(total, cur)}  (discounts: {disc_policy}, fees: {fee_policy})")
        if quote is not None:
            if status:
                print(f"MISMATCH: merchant quote says {fmt(cents(quote), cur)}; gap {fmt(total - cents(quote), cur)}."
                      " The quote wins. Find the missing fee/discount before sharing the bill.")
            else:
                print("matches the merchant quote exactly.")
        for t in result.get("transfers", []):
            print("  " + t)
    return status


# ---------- offers ----------

def parse_day(s):
    return dt.date.fromisoformat(s) if s else None


def cmd_offers(args):
    data = json.load(open(args.file, encoding="utf-8"))
    today = parse_day(data.get("today")) or dt.date.today()
    channel = data.get("channel")
    basket = cents(data.get("basket_total"))
    budget = data.get("budget")
    window = int(data.get("expiry_window_days", args.window))
    out = []
    for o in data.get("offers", []):
        name = o.get("title") or o.get("id", "?")
        exp = parse_day(o.get("expires"))
        saves = cents(o.get("saves"))
        minimum = cents(o.get("min_spend"))
        notes = []
        if exp is None:
            notes.append("expiry not stated: do not guess it")
        if exp is not None and exp < today:
            out.append((name, "DROP", "already expired")); continue
        oc = o.get("channel")
        if oc in (None, "", "unknown"):
            notes.append("channel unconfirmed: check with a quote")
        elif oc != "any" and channel and oc != channel:
            out.append((name, "DROP", f"only valid for {oc}, this order is {channel}")); continue
        if exp is not None and (exp - today).days <= window:
            notes.append(f"expires in {(exp - today).days} day(s)")
        extra = max(0, minimum - basket)
        if extra == 0:
            verdict = "USE IF QUOTE CONFIRMS"
            notes.append(f"claims to save {fmt(saves)}; unverified until the merchant quote shows it")
        elif extra >= saves:
            verdict = "SKIP"
            notes.append(f"needs {fmt(extra)} more spend to save {fmt(saves)}: filler costs more than it saves")
        else:
            verdict = "ONLY IF FILLER IS WANTED"
            notes.append(f"needs {fmt(extra)} more spend; net gain {fmt(saves - extra)} only if you'd want that extra anyway")
        if budget is not None and basket + extra - saves > cents(budget):
            notes.append("would still be over budget")
        out.append((name, verdict, "; ".join(notes)))
    if args.json:
        print(json.dumps([{"offer": a, "verdict": b, "why": c} for a, b, c in out], ensure_ascii=False, indent=2))
    else:
        for a, b, c in out:
            print(f"[{b}] {a}: {c}")
        if not out:
            print("no offers given")
    return 0


# ---------- ledger ----------

def cmd_ledger_add(args):
    entry = {"date": args.date or dt.date.today().isoformat(), "merchant": args.merchant,
             "total": fmt(cents(args.total)), "quote_ref": args.quote_ref, "note": args.note}
    with open(args.file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print("logged:", json.dumps(entry, ensure_ascii=False))
    return 0


def cmd_ledger_summary(args):
    rows = []
    try:
        for line in open(args.file, encoding="utf-8"):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    except FileNotFoundError:
        raise SystemExit(f"error: no ledger at {args.file}")
    if args.month:
        rows = [r for r in rows if r["date"].startswith(args.month)]
    by = {}
    for r in rows:
        m = by.setdefault(r["merchant"], [0, 0])
        m[0] += 1
        m[1] += cents(r["total"])
    total = sum(v[1] for v in by.values())
    print(f"{len(rows)} order(s){' in ' + args.month if args.month else ''}, total {fmt(total)}")
    for k, (n, c) in sorted(by.items(), key=lambda kv: -kv[1][1]):
        print(f"  {k}: {n} order(s), {fmt(c)}")
    missing = sum(1 for r in rows if not r.get("quote_ref"))
    if missing:
        print(f"  note: {missing} order(s) have no quote/order reference; they cannot be traced")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("split", help="fair per-person bill from a basket JSON")
    s.add_argument("file"); s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_split)

    o = sub.add_parser("offers", help="triage coupons/offers against a basket")
    o.add_argument("file"); o.add_argument("--window", type=int, default=3)
    o.add_argument("--json", action="store_true")
    o.set_defaults(fn=cmd_offers)

    l = sub.add_parser("ledger", help="append to or summarize a spend ledger (JSONL)")
    lsub = l.add_subparsers(dest="lcmd", required=True)
    a = lsub.add_parser("add")
    a.add_argument("--file", default="spend.jsonl"); a.add_argument("--merchant", required=True)
    a.add_argument("--total", required=True); a.add_argument("--date")
    a.add_argument("--quote-ref", default=""); a.add_argument("--note", default="")
    a.set_defaults(fn=cmd_ledger_add)
    m = lsub.add_parser("summary")
    m.add_argument("--file", default="spend.jsonl"); m.add_argument("--month")
    m.set_defaults(fn=cmd_ledger_summary)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
