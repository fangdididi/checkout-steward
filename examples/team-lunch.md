# Example: team lunch for five (delivery)

*A worked example with made-up store, items and prices.*

**Request:** "Can you order lunch for the team? Usual place, deliver to the office by 12:30."

## 1. Mandate

The agent asks once: *"Is this for you alone or a group? Who's in, and is there a per-person cap? Delivery to the office, right?"*

Maya answers: five people (Maya, Leo, Priya, Sam, Jun), about $15 a head, delivery, Maya pays and everyone pays her back. Priya avoids sesame.

Mandate repeated back: *Group of 5, delivery to the office for 12:30, about $15 each, Maya pays, no sesame for Priya, I won't place anything without your OK.*

## 2. Tool census

Look: `stores`, `menu`, `my_coupons`, `offers`, `server_time`. Quote: `price_basket`. Commit: `create_order`, `claim_coupon`, `cancel_order`. Commit stays locked.

The agent reads `server_time` first (11:42), then the delivery menu for the office's store. It does not reuse the pickup item codes it saw last week.

## 3. Basket

| Who | Item | Price |
|---|---|---|
| Maya | Chicken rice bowl | 13.50 |
| Leo | Veggie wrap, iced tea | 10.90 + 2.80 |
| Priya | Salmon poke (note: no sesame) | 15.20 |
| Sam | Falafel plate | 11.40 |
| Jun | Beef noodles | 14.30 |

Items come to 68.10. The note field exists for delivery, so "no sesame" goes in it as its own line.

## 4. Candidates (all quoted)

| Basket | Quote total | Notes |
|---|---|---|
| Plain | 74.10 | items 68.10 + delivery 4.99 + service 1.01 |
| Best offer | **64.10** | store offer "spend 60, save 8" + Sam's own first-order coupon -2.00 |

Threshold basket not needed: the order already clears 60.

## 5. Offer triage

- "Spend 60, save 8": use if the quote confirms. It did.
- Sam's first-order coupon: personal, so its saving goes to Sam.
- "Free delivery on pickup orders": dropped, wrong channel.

## 6. Confirmation receipt

```
ORDER TO CONFIRM
Store / channel: Main St kitchen, delivery to the office, ASAP (quoted ETA 12:20)
Items:          6 items for 5 people (list above), Priya: no sesame
Offers applied: spend 60 save 8  -8.00 ; first-order coupon  -2.00   (quote Q-4471, 11:46)
Fees:           delivery 4.99, service 1.01
TOTAL:          64.10   Budget: ~75 (5 x 15)   Paid with: Maya's card on file
Reply "yes, order it" to place this order.
```

Maya replies "yes, order it" at 11:49. The quote is three minutes old and nothing changed, so the agent makes one `create_order` call. It returns order #A-2207, ETA 12:20, paid 64.10.

## 7. Split and log

```bash
python3 scripts/steward.py split examples/team-lunch.json
```

```
who                items  own disc  shared disc     fees      owes
Jun                14.30      0.00        -1.73     1.20     13.77
Leo                13.70      0.00        -1.66     1.20     13.24
Maya               13.50      0.00        -1.63     1.20     13.07
Priya              15.20      0.00        -1.84     1.20     14.56
Sam                11.40     -2.00        -1.14     1.20      9.46
computed total $64.10  (discounts: proportional, fees: equal)
matches the merchant quote exactly.
  Jun -> Maya: $13.77
  Leo -> Maya: $13.24
  Priya -> Maya: $14.56
  Sam -> Maya: $9.46
```

The shared $8 discount is spread by how much each person ordered; the $6 of fees are split equally; Sam keeps his own coupon. The shares add up to exactly 64.10.

```bash
python3 scripts/steward.py ledger add --merchant "Main St kitchen" --total 64.10 --quote-ref A-2207 --note "team lunch x5"
```

The message to the group lists the transfers above and the order number. Nothing else gets ordered without a new yes.
