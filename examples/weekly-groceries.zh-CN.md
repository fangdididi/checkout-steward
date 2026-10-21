# 示例：每周买菜自取 + 快到期的券

*示例中的门店、商品和价格均为虚构。*

**用户：**「帮我把这周的菜买了，还是到小区门口那家自取，预算 50 以内。我有几张券好像快过期了，看看能不能用上。」

## 1. 委托书

智能体复述：*单人，周三傍晚到小区门口店自取，预算 50 元封顶；只查和算价，不经你同意不下单、不领券。*

## 2. 清点工具

看：`门店`、`商品搜索`、`我的券`、`服务器时间`；算：`购物车算价`；提交：`创建订单`、`领券`、`预约自取时段`。先读服务器时间：2026-10-21。

## 3. 购物篮

按上周订单和这周的要求，从该门店「自取」渠道的实时商品里挑出：鸡蛋、番茄、青菜、豆腐、鸡胸肉、牛奶、米。算价：**46.30 元**（参考号 Q-8812）。

## 4. 优惠逐张下结论

把券整理成 `examples/weekly-offers.json`（今天日期、渠道 pickup、购物篮 46.30、预算 50），运行：

```bash
python3 scripts/steward.py offers examples/weekly-offers.json
```

```
[USE IF QUOTE CONFIRMS] Spend 40 save 5: expires in 2 day(s); claims to save 5.00; unverified until the merchant quote shows it
[SKIP] Spend 70 save 10: expires in 1 day(s); needs 23.70 more spend to save 10.00: filler costs more than it saves; would still be over budget
[ONLY IF FILLER IS WANTED] Spend 50 save 6: needs 3.70 more spend; net gain 2.30 only if you'd want that extra anyway
[DROP] Free delivery: only valid for delivery, this order is pickup
[DROP] Yogurt 2-for-1: already expired
[USE IF QUOTE CONFIRMS] Mystery member coupon: expiry not stated: do not guess it; channel unconfirmed: check with a quote; claims to save 2.00; unverified until the merchant quote shows it
```

智能体用中文转述给用户：

- **满 40 减 5**（后天过期）：不用多买，可以用，等算价确认。
- **满 70 减 10**（明天过期）：要多花 23.70 才能省 10 元，还会超预算。**跳过**，别为了它多买。
- **满 50 减 6**：差 3.70 元。你平时会买的酸奶正好 3.90，想要的话净省约 2 元；不想要就不必凑。
- **免配送费**：只限外送，这单是自取，剔除。
- **酸奶买一送一**：前天已过期，剔除。
- **会员券**：有效期和渠道都没写，我不猜，用算价试一下就知道。

## 5. 算价确认

用户说「酸奶加上吧，本来就要买」。智能体重新算价：商品 50.20，满 50 减 6，会员券 -2（算价确认有效），**实付 42.20 元**（参考号 Q-8820）。满 40 减 5 和满 50 减 6 不能叠加，算价里系统自动选了减 6，智能体照实说明。

## 6. 确认小票

```
待确认订单
门店／渠道：小区门口店，到店自取，今天 18:00–18:30
商品：      鸡蛋、番茄、青菜、豆腐、鸡胸肉、牛奶、米、酸奶（共 8 件）
已用优惠：  满 50 减 6  -6.00；会员券  -2.00   （来自算价 Q-8820，17:05）
费用：      无
合计：      42.20   预算：50   支付方式：已绑定的账户
回复「好，下单」即提交这一单；回复其他内容不会产生任何操作。
```

用户回复「好，下单」。只调用一次创建订单，返回订单号 G-5531，实付 42.20。

## 7. 记账

```bash
python3 scripts/steward.py ledger add --merchant "小区门口店" --total 42.20 --quote-ref G-5531 --note "每周买菜"
python3 scripts/steward.py ledger summary --month 2026-10
```

那张满 70 减 10 明天就会过期，智能体最后补一句：「这张不值得为它多花钱，就让它过期吧。」
