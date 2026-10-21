# Checkout Steward

**English** | [简体中文](README.zh-CN.md)

An agent skill for ordering food, groceries, and goods through a merchant's own tools (MCP servers, APIs, CLIs) **without overspending, false savings, or surprise orders**. It works with Claude Code, Codex, Cursor, and any agent that reads `SKILL.md` files.

## Why

Merchants are opening their ordering systems to AI agents. That makes "order lunch for the team" a few tool calls away, and it also makes a careless agent expensive: item codes reused from the wrong store, a delivery-only coupon used for pickup, fees left out of the total, a double order after a timeout, a "you saved $9" that never happened.

Checkout Steward gives the agent the habits of a careful assistant holding the company card: look freely, price only through the merchant's quote, buy only after a clear yes on a specific receipt, count a coupon as a saving only when it lowers what the user would have bought anyway, and leave a traceable record of who owes what.

## Features

- **Mandate first**: budget cap, channel, time, diet, solo or group, and what the agent may do alone, all asked once.
- **Tool census**: sorts merchant tools into look, quote, and commit; commit tools stay locked until confirmation.
- **Quote-only prices**: every total, fee, and discount comes from the merchant's price tool for that exact store, channel, and time.
- **Two or three honest candidate baskets**: plain, best offer, and (only when close) a threshold top-up.
- **Offer triage**: drop, use if the quote confirms, only if the filler is wanted, skip, and "don't spend to save" for expiring coupons.
- **Confirmation receipt**: one clear receipt, a re-quote if anything changed or the quote is stale, and exactly one commit with a check before any retry.
- **Fair group bill**: own items, personal coupons stay personal, shared discounts by share of the order, shared fees equal or proportional, totals that match the merchant to the cent.
- **Spend ledger**: a local JSONL log with monthly summaries, every entry tied to an order or quote reference.
- **Honest limits**: no stock promises without a stock tool, no claims that a modifier applied when the system never echoed it.

## Installation

Clone the repo into your agent's skills folder:

```bash
# Claude Code (personal skills)
git clone https://github.com/fangdididi/checkout-steward ~/.claude/skills/checkout-steward

# Codex
git clone https://github.com/fangdididi/checkout-steward ~/.codex/skills/checkout-steward

# Cursor (project skills)
git clone https://github.com/fangdididi/checkout-steward .cursor/skills/checkout-steward
```

For other agents, put the folder wherever the agent loads skills from, or paste `SKILL.md` into its instructions. The skill does nothing on its own: connect the merchant's MCP server, API, or CLI to your agent as usual.

## Usage

Just ask in plain words:

- "Order lunch for the five of us, deliver to the office by 12:30, about $15 each."
- "Which of my coupons are worth using this week? Budget 50."
- "Reorder last Wednesday's groceries for pickup."
- "How much did I spend on takeaway in October?"

The agent will confirm the mandate, price candidates, triage offers, and show a confirmation receipt. Nothing is ordered until you reply with a clear yes to that receipt.

### Helper script

`scripts/steward.py` needs only Python 3:

```bash
python3 scripts/steward.py split examples/team-lunch.json        # per-person bill, checked against the quote
python3 scripts/steward.py offers examples/weekly-offers.json    # verdict for each coupon or offer
python3 scripts/steward.py ledger add --merchant "Grocer" --total 46.30 --quote-ref Q-8812
python3 scripts/steward.py ledger summary --month 2026-10
python3 -m unittest discover -s tests                            # run the tests
```

## Examples

- [Team lunch for five, delivery](examples/team-lunch.md): spend threshold, a personal coupon, shared fees, and a split that matches the quote exactly.
- [Weekly grocery pickup (Chinese)](examples/weekly-groceries.zh-CN.md): six coupons triaged, one skipped because the filler costs more than it saves, a budget cap respected.

## File structure

```
checkout-steward/
├── SKILL.md                     # the skill (English)
├── SKILL.zh-CN.md               # the skill (Chinese)
├── README.md
├── README.zh-CN.md
├── LICENSE
├── scripts/
│   └── steward.py               # split / offers / ledger helper
├── examples/
│   ├── team-lunch.md            # worked example (English)
│   ├── team-lunch.json          # input for `split`
│   ├── weekly-groceries.zh-CN.md# worked example (Chinese)
│   └── weekly-offers.json       # input for `offers`
└── tests/
    └── test_steward.py
```

## License

[MIT](LICENSE)
