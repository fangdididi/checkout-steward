# 下单管家 Checkout Steward

[English](README.md) | **简体中文**

一个智能体技能：通过商家自己的工具（MCP 服务、API、命令行）替用户点餐、买菜、买东西，**不超支、不虚报省钱、不误下单**。适用于 Claude Code、Codex、Cursor，以及任何能读取 `SKILL.md` 的智能体。

## 为什么需要它

商家正在把下单系统开放给 AI 智能体。「帮团队点个午饭」只差几次工具调用，可一个粗心的智能体也会因此变得很费钱：用错门店的商品编码、只限外送的券拿去自取、总价漏了费用、超时后重复下单、一句从没发生过的「为你省了 9 元」。

下单管家让智能体养成「拿着公司卡的靠谱助理」的习惯：随便看，价格只认商家算价，对一张具体小票得到明确同意才下单，只有让用户本来就要买的东西变便宜了才算省钱，并且留下谁该付多少、可以回溯的记录。

## 功能

- **先写委托书**：预算上限、渠道、时间、忌口、单人还是多人、哪些事可以自己做主，一次问完。
- **清点工具**：把商家工具分成「看」「算」「提交」三类；确认之前，「提交」类工具一律锁住。
- **价格只认算价**：每个总价、费用、优惠都来自商家针对该门店、该渠道、该时段的算价工具。
- **两三个诚实的候选方案**：原样、最优惠，以及（仅在接近门槛时）凑单。
- **优惠逐张下结论**：剔除、算价确认后使用、想要凑单商品才用、跳过，以及对快过期券的「别为了用券而消费」。
- **确认小票**：一张清楚的小票；有变化或算价过时就重算；只提交一次，重试前先查订单。
- **公平的拼单账单**：各付各的商品，个人券归个人，整单优惠按点单金额比例分摊，公共费用平摊或按比例，总额与商家分毫不差。
- **消费账本**：本地 JSONL 记录加月度汇总，每条都关联订单号或算价参考号。
- **诚实的边界**：没有库存接口就不承诺有货；系统没回显的特殊要求，不说「已生效」。

## 安装

把仓库克隆到智能体的技能目录：

```bash
# Claude Code（个人技能）
git clone https://github.com/fangdididi/checkout-steward ~/.claude/skills/checkout-steward

# Codex
git clone https://github.com/fangdididi/checkout-steward ~/.codex/skills/checkout-steward

# Cursor（项目技能）
git clone https://github.com/fangdididi/checkout-steward .cursor/skills/checkout-steward
```

其他智能体：把文件夹放到它加载技能的位置，或者把 `SKILL.md` 内容粘进它的指令里。技能本身不连接任何商家：请照常把商家的 MCP 服务、API 或命令行接入你的智能体。

## 使用方法

直接用大白话说：

- 「帮我们五个人点午饭，12:30 前送到公司，人均 15 左右。」
- 「这周我哪些券值得用？预算 50。」
- 「把上周三买的菜再下一单，自取。」
- 「我十月份外卖一共花了多少？」

智能体会先确认委托书，再给候选方案算价、逐张判断优惠，然后出一张确认小票。你对这张小票明确回复同意之前，什么都不会下单。

### 辅助脚本

`scripts/steward.py` 只需要 Python 3：

```bash
python3 scripts/steward.py split examples/team-lunch.json        # 每人账单，并与算价总额核对
python3 scripts/steward.py offers examples/weekly-offers.json    # 每张券／每个活动的结论
python3 scripts/steward.py ledger add --merchant "生鲜超市" --total 46.30 --quote-ref Q-8812
python3 scripts/steward.py ledger summary --month 2026-10
python3 -m unittest discover -s tests                            # 运行测试
```

## 示例

- [五人团队午餐（英文）](examples/team-lunch.md)：外送、满减门槛、个人券、公共费用，分账结果与算价总额完全一致。
- [每周买菜自取](examples/weekly-groceries.zh-CN.md)：六张券逐张判断，一张因为凑单花的比省的多而跳过，守住预算上限。

## 文件结构

```
checkout-steward/
├── SKILL.md                     # 技能本体（英文）
├── SKILL.zh-CN.md               # 技能本体（中文）
├── README.md
├── README.zh-CN.md
├── LICENSE
├── scripts/
│   └── steward.py               # 分账 / 优惠判断 / 账本 辅助脚本
├── examples/
│   ├── team-lunch.md            # 完整示例（英文）
│   ├── team-lunch.json          # `split` 的输入
│   ├── weekly-groceries.zh-CN.md# 完整示例（中文）
│   └── weekly-offers.json       # `offers` 的输入
└── tests/
    └── test_steward.py
```

## 许可证

[MIT](LICENSE)
