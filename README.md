# 🎯 接单雷达 Bounty Radar（内容赏金版）

> 改自开源项目 hackathon-aggregator，原版专门**过滤掉**内容类赏金——我们反其道而行之，
> 只要内容/设计/翻译/社区类赏金，因为这才是新手的主战场。

## 它做什么

每周一自动：
1. 从 **Superteam Earn**（Solana 生态，USDC 结算、有托管）、Gitcoin、DoraHacks 抓取新赏金
2. 只保留内容类（thread、视频、文章、设计、翻译、测评…），过滤纯开发任务
3. 按奖金排序，标注 14 天内截止的 ⏰
4. 推送到你的 Telegram（可选）；**同时**在本地生成 `digest.md`

## 本地试运行（不需要任何 key，刚才已验证跑通）

```bash
cd ~/workspace/crypto-earn/bounty-radar
pip install --break-system-packages -r requirements.txt
python3 main.py
# 没有 Telegram/DeepSeek key 也能跑：打印结果 + 生成 digest.md
```

## 定时推送（每周自动，需你动手 10 分钟）

**方案 A：飞书（推荐，国内直接可用）**
1. 仓库已建好：shenbin77/bounty-radar，直接用
2. 飞书群 → 设置 → 群机器人 → 添加自定义机器人 → 复制 webhook 地址
3. GitHub 仓库 Settings → Secrets → Actions 添加 `FEISHU_WEBHOOK_URL`
4. Actions 启用工作流，每周一自动推送到飞书群；也可手动 Run workflow 立刻跑一次

**方案 B：Telegram（需科学上网）**
1. 找 @BotFather 建 bot 拿 token；找 @JsonDumpBot 查 chat id
2. Secrets 添加 `TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`
3. `DEEPSEEK_API_KEY`（可选，有则 AI 给每个赏金打难度/技能标签；没有也完全可用）

## 花费

GitHub Actions 免费额度内，DeepSeek 每月约 $0.1-0.3（可选），Telegram 免费。
不配 key 的话，**总成本 $0**。

## 改了什么（相对原版）

- `scrapers/superteam.py`：过滤逻辑反转——只收内容类赏金；门槛从 $400 降到 $100
- `main.py`：只跑 superteam/gitcoin/dorahacks 三个内容友好源
- `processor.py`：DeepSeek 提示词改成内容赏金评审口径；无 key 自动跳过（openai 包懒加载）
- `notifier.py`：每次运行同时落盘 `digest.md`，标题改成内容赏金版
